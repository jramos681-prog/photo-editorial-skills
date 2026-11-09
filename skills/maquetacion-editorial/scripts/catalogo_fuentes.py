#!/usr/bin/env python3
"""Genera maquetacion/catalogo.md con las fuentes aptas para el encargo."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Sequence

import configuracion

# Límite de la nota de licencia dentro de la línea de cada familia.
LICENCIA_MAXIMA = 120

# Punto tipográfico en milímetros: el avance se informa a 10 pt.
PT_A_MM = 25.4 / 72.0

# Muestras neutras para el avance medio, una por idioma configurable. Son
# prosa de prueba sin nombres propios ni topónimos, con mayúsculas, cifras,
# comillas y guiones; los caracteres que la fuente no tenga se omiten.
MUESTRAS = {
    "es": (
        "Una página de libro se compone con una familia, un cuerpo y una "
        "interlínea decididos antes de escribir el texto. ¿Qué busca quien "
        "lee? ¡Claridad! El texto corre en columnas estrechas, con «comillas "
        "angulares», guiones —como este— y cifras 0123456789. Las mayúsculas "
        "ÁÉÍÓÚÜÑ y las minúsculas áéíóúüñ cuentan igual en la prueba de avance."
    ),
    "en": (
        "A book page is set with one family, one size and one leading chosen "
        "before the writing starts. What does the reader need? Clarity! The "
        "text runs in narrow columns, with “curly quotes”, dashes —like this "
        "one— and figures 0123456789. Capitals and lowercase letters both "
        "count in the average of the advance sample."
    ),
}


def _numero(valor: float | None, decimales: int) -> str:
    """Número con coma decimal, o raya cuando no hay medida."""
    if valor is None:
        return "—"
    return f"{valor:.{decimales}f}".replace(".", ",")


@dataclass
class Familia:
    nombre: str
    rutas: list[tuple[Path, int]] = field(default_factory=list)
    embebida_typst: bool = False
    fs_type: set[int] = field(default_factory=set)
    caracteres_faltantes: set[str] = field(default_factory=set)
    licencia_fuente: set[str] = field(default_factory=set)
    errores: list[str] = field(default_factory=list)
    recursos_medidos: bool = False
    versalitas: str = ""
    cifras_altura: str = ""
    cifras_ancho: str = ""
    alternativas: set[str] = field(default_factory=set)
    x_em: float | None = None
    mayuscula_em: float | None = None
    avance_mm: float | None = None
    cpl_140: float | None = None
    alturas_contorno: bool = False

    @property
    def fs_type_texto(self) -> str:
        return ", ".join(f"0x{x:04X}" for x in sorted(self.fs_type)) if self.fs_type else "no disponible"

    @property
    def verificada(self) -> bool:
        """True si se pudo medir el archivo: hay fsType y cmap comprobados."""
        return bool(self.fs_type)

    @property
    def incrustable(self) -> bool:
        # Bits OS/2: 0x0002 restringe incrustación; 0x0100 prohíbe subsetting;
        # 0x0200 limita a mapas de bits y no sirve para este flujo editorial.
        return bool(self.fs_type) and all(not (x & (0x0002 | 0x0100 | 0x0200)) for x in self.fs_type)

    @property
    def marca_medida(self) -> str:
        """Marca explícita cuando la familia no se pudo medir y es de Typst."""
        return (
            "incluida en Typst (OFL); cobertura no medida"
            if self.embebida_typst and not self.verificada
            else ""
        )

    @property
    def metricas_texto(self) -> str:
        """Versalitas, cifras, alternativas y métricas de la familia medida.

        Solo se escribe cuando hay archivo medido: las familias que trae Typst
        no declaran versalitas, cifras ni métricas porque no se han podido
        comprobar.
        """
        if not self.recursos_medidos:
            return ""
        if self.versalitas == "smcp+c2sc":
            versalitas = "VC (smcp+c2sc)"
        elif self.versalitas == "smcp":
            versalitas = "VC (smcp)"
        else:
            versalitas = "sin VC"
        if self.cifras_altura in ("alineadas", "antiguas"):
            cifras = "alin." if self.cifras_altura == "alineadas" else "ant."
            if self.cifras_ancho == "tabulares":
                cifras += ", tab."
            elif self.cifras_ancho == "proporcionales":
                cifras += ", prop."
        elif self.cifras_altura == "por verificar":
            cifras = "por verificar"
        else:
            cifras = "no medidas"
        alternativas = [x for x in ("lnum", "onum", "tnum", "pnum") if x in self.alternativas]
        partes = [
            versalitas,
            f"cifras: {cifras}",
            f"alt.: {', '.join(alternativas) if alternativas else 'ninguna'}",
        ]
        if self.x_em is not None:
            partes.append(f"x: {_numero(self.x_em, 3)}")
        if self.mayuscula_em is not None:
            altura = f"M: {_numero(self.mayuscula_em, 3)}"
            if self.alturas_contorno:
                altura += " (alturas del contorno)"
            partes.append(altura)
        if self.avance_mm is not None:
            partes.append(f"av.: {_numero(self.avance_mm, 4)} mm/car")
        if self.cpl_140 is not None:
            partes.append(f"CPL: {_numero(self.cpl_140, 1)}")
        return "; ".join(partes)


def _fonttools():
    try:
        from fontTools.ttLib import TTCollection, TTFont
    except ImportError:
        return None, None
    return TTCollection, TTFont


def _nombres(fuente) -> dict[int, str]:
    salida: dict[int, str] = {}
    for nombre in fuente["name"].names:
        if nombre.nameID not in (1, 2, 4, 6, 13, 16, 17):
            continue
        try:
            texto = nombre.toUnicode().strip()
        except Exception:
            continue
        if texto:
            salida.setdefault(nombre.nameID, texto)
    return salida


def _cargar_rutas(rutas: list[Path]) -> dict[str, list[tuple[Path, int]]]:
    TTCollection, TTFont = _fonttools()
    resultado: dict[str, list[tuple[Path, int]]] = {}
    if TTFont is None:
        return resultado
    for ruta in rutas:
        try:
            fuentes = list(TTCollection(str(ruta)).fonts) if ruta.suffix.lower() == ".ttc" else [TTFont(str(ruta), lazy=True)]
        except Exception:
            continue
        for indice, fuente in enumerate(fuentes):
            try:
                nombre = _nombres(fuente).get(16) or _nombres(fuente).get(1) or ruta.stem
                resultado.setdefault(nombre, []).append((ruta, indice))
            except Exception:
                continue
            finally:
                try:
                    fuente.close()
                except Exception:
                    pass
    return resultado


def _caracteristicas(fuente) -> set[str]:
    """Etiquetas de características OpenType presentes en GSUB."""
    etiquetas: set[str] = set()
    if "GSUB" not in fuente:
        return etiquetas
    try:
        tabla = fuente["GSUB"].table
        if tabla.FeatureList is None:
            return etiquetas
        for registro in tabla.FeatureList.FeatureRecord:
            etiquetas.add(str(registro.FeatureTag))
    except Exception:
        return etiquetas
    return etiquetas


def _glifo_alto(fuente, caracter: str, upm: int) -> float | None:
    """Altura del contorno de un carácter, como respaldo de OS/2."""
    from fontTools.pens.boundsPen import BoundsPen

    cmap = fuente.getBestCmap() or {}
    if ord(caracter) not in cmap:
        return None
    try:
        glifos = fuente.getGlyphSet()
        lapiz = BoundsPen(glifos)
        glifos[cmap[ord(caracter)]].draw(lapiz)
        if lapiz.bounds is None:
            return None
        return (lapiz.bounds[3] - lapiz.bounds[1]) / upm
    except Exception:
        return None


def _cifras_por_defecto(
    fuente, upm: int, x_em: float | None, mayuscula_em: float | None
) -> tuple[str, str]:
    """Clase de las cifras por defecto, medida en el dibujo de 0 a 9.

    Antiguas: al menos tres de 3 4 5 7 9 bajan de la línea base y el 0 no pasa
    de la media entre altura de x y de mayúscula. Alineadas: ninguna baja y el
    0 llega a esa media. Lo demás queda «por verificar» (visualmente).
    Tabulares: las diez cifras tienen el mismo avance. Solo se devuelve la
    clase: el catálogo no escribe alturas, avances ni ningún otro valor.
    """
    from fontTools.pens.boundsPen import BoundsPen

    mapa = fuente.getBestCmap() or {}
    if not all(ord(d) in mapa for d in "0123456789"):
        return "—", "—"
    limites: dict[str, tuple] = {}
    try:
        glifos = fuente.getGlyphSet()
        for d in "0123456789":
            lapiz = BoundsPen(glifos)
            glifos[mapa[ord(d)]].draw(lapiz)
            if lapiz.bounds is None:
                return "por verificar", "—"
            limites[d] = lapiz.bounds
    except Exception:
        return "por verificar", "—"
    bajan = sum(1 for d in "34579" if limites[d][1] < -0.05 * upm)
    tope_cero = limites["0"][3] / upm
    media = (x_em + mayuscula_em) / 2 if x_em and mayuscula_em else None
    if bajan >= 3 and (media is None or tope_cero < media):
        altura = "antiguas"
    elif bajan == 0 and (media is None or tope_cero >= media):
        altura = "alineadas"
    else:
        altura = "por verificar"
    try:
        avances = {fuente["hmtx"][mapa[ord(d)]][0] for d in "0123456789"}
    except Exception:
        return altura, "—"
    return altura, "tabulares" if len(avances) == 1 else "proporcionales"


def _altura(fuente, os2, campo: str, glifo: str, upm: int) -> tuple[float | None, bool]:
    """Altura en fracción de em y si se tomó del contorno y no de OS/2."""
    declarada = getattr(os2, campo, 0) if os2 is not None else 0
    if declarada:
        return declarada / upm, False
    contorno = _glifo_alto(fuente, glifo, upm)
    return contorno, contorno is not None


def _avance(fuente, upm: int, muestra: str) -> tuple[float | None, float | None]:
    """Avance medio en mm por carácter a 10 pt y CPL que caben en 140 mm.

    Se suman los avances de la muestra y se dividen entre los caracteres que la
    fuente tiene: los ausentes no cuentan, igual que en la cobertura. El avance
    no incluye kerning ni ligaduras, así que el CPL es una referencia.
    """
    try:
        mapa = fuente.getBestCmap() or {}
        hmtx = fuente["hmtx"]
        avances = [hmtx[mapa[ord(caracter)]][0] for caracter in muestra if ord(caracter) in mapa]
    except Exception:
        return None, None
    if not avances:
        return None, None
    avance = (sum(avances) / len(avances)) / upm * 10 * PT_A_MM
    return avance, 140.0 / avance if avance else None


@dataclass
class Recursos:
    """Datos OpenType y métricas leídos de la cara representante."""

    versalitas: str = ""
    altura: str = ""
    ancho: str = ""
    alternativas: set[str] = field(default_factory=set)
    x_em: float | None = None
    mayuscula_em: float | None = None
    avance_mm: float | None = None
    cpl_140: float | None = None
    alturas_contorno: bool = False


def _recursos(fuente, muestra: str) -> Recursos:
    """Versalitas, cifras por defecto y métricas de una cara representante."""
    try:
        upm = int(fuente["head"].unitsPerEm)
    except Exception:
        upm = 1000
    caracteristicas = _caracteristicas(fuente)
    versalitas = ""
    if "smcp" in caracteristicas:
        versalitas = "smcp+c2sc" if "c2sc" in caracteristicas else "smcp"
    os2 = fuente.get("OS/2")
    x_em, x_contorno = _altura(fuente, os2, "sxHeight", "x", upm)
    mayuscula_em, mayuscula_contorno = _altura(fuente, os2, "sCapHeight", "H", upm)
    altura, ancho = _cifras_por_defecto(fuente, upm, x_em, mayuscula_em)
    avance, cpl = _avance(fuente, upm, muestra)
    return Recursos(
        versalitas=versalitas,
        altura=altura,
        ancho=ancho,
        alternativas={t for t in ("lnum", "onum", "tnum", "pnum") if t in caracteristicas},
        x_em=x_em,
        mayuscula_em=mayuscula_em,
        avance_mm=avance,
        cpl_140=cpl,
        alturas_contorno=x_contorno or mayuscula_contorno,
    )


def _medir_familia(familia: Familia, requeridos: set[int], muestra: str) -> None:
    """Mide fsType, licencia, cobertura, recursos y métricas de una familia.

    Una familia sin archivo no se mide: si la trae Typst, el catálogo la marca
    como «incluida en Typst (OFL)» y no se registra error; si no, queda fuera de
    las aptas con el motivo.
    """
    if not familia.rutas:
        if familia.embebida_typst:
            return
        familia.errores.append("No hay archivo de fuente disponible; no se pudo verificar cmap ni OS/2.fsType")
        return
    TTCollection, TTFont = _fonttools()
    if TTFont is None:
        familia.errores.append("fontTools no está instalado; no se pudo verificar cmap ni OS/2.fsType")
        return
    fuentes = []
    candidatos: list[tuple[int, object]] = []
    for ruta, cara in familia.rutas:
        try:
            fuente = TTCollection(str(ruta)).fonts[cara] if ruta.suffix.lower() == ".ttc" else TTFont(str(ruta), lazy=True)
            fuentes.append(fuente)
            nombres = _nombres(fuente)
            os2 = fuente.get("OS/2")
            if os2 is None or not hasattr(os2, "fsType"):
                familia.errores.append(f"{ruta.name}: no contiene OS/2.fsType")
                continue
            familia.fs_type.add(int(os2.fsType))
            licencia = nombres.get(13)
            if licencia:
                familia.licencia_fuente.add(licencia)
            subfamilia = (nombres.get(17) or nombres.get(2) or "").casefold()
            prioridad = 0 if subfamilia in ("regular", "book", "roman") else 2 if "italic" in subfamilia or "oblique" in subfamilia else 1
            candidatos.append((prioridad, fuente))
        except Exception as exc:
            familia.errores.append(f"{ruta.name}: no se pudo leer ({type(exc).__name__})")
    if not familia.fs_type:
        familia.errores.append("OS/2.fsType no disponible")
    if candidatos:
        representante = min(candidatos, key=lambda candidato: candidato[0])[1]
        cmap = set((representante.getBestCmap() or {}).keys())
        familia.caracteres_faltantes.update(chr(cp) for cp in requeridos if cp not in cmap)
        datos = _recursos(representante, muestra)
        familia.recursos_medidos = True
        familia.versalitas = datos.versalitas
        familia.cifras_altura = datos.altura
        familia.cifras_ancho = datos.ancho
        familia.alternativas = datos.alternativas
        familia.x_em = datos.x_em
        familia.mayuscula_em = datos.mayuscula_em
        familia.avance_mm = datos.avance_mm
        familia.cpl_140 = datos.cpl_140
        familia.alturas_contorno = datos.alturas_contorno
    for fuente in fuentes:
        try:
            fuente.close()
        except Exception:
            pass


def _clave(texto: str) -> str:
    return re.sub(r"\s+", " ", texto.casefold()).strip()


def _primera_frase(texto: str, limite: int = LICENCIA_MAXIMA) -> str:
    """Primera frase de una nota, en una sola línea y acotada.

    Los nameID 13 traen bloques MIT/OFL de varias líneas: sin colapsar y
    recortar, el catálogo deja de ser compacto y rompe el Markdown.
    """
    limpio = re.sub(r"\s+", " ", texto).strip()
    corte = re.search(r"(?<=[.!?])\s", limpio)
    if corte:
        limpio = limpio[: corte.start()].strip()
    if len(limpio) > limite:
        limpio = limpio[:limite].rstrip() + "…"
    return limpio


def _nota(config: dict, familia: Familia) -> str:
    """Licencia en una sola línea: la declarada primero y, si hay, la del archivo."""
    licencias = {_clave(nombre): nota for nombre, nota in config["licencias"].items()}
    declarada = licencias.get(_clave(familia.nombre))
    partes = []
    if declarada:
        partes.append("licencia declarada: " + _primera_frase(declarada))
    if familia.licencia_fuente:
        partes.append("licencia del archivo: " + _primera_frase(" / ".join(sorted(familia.licencia_fuente))))
    return "; ".join(partes) if partes else "sin nota de licencia (ver archivo)"


def _inventario(config: dict) -> dict[str, Familia]:
    inventario: dict[str, Familia] = {}
    rutas = configuracion.ficheros_fuente(config)
    for nombre, caras in _cargar_rutas(rutas).items():
        inventario.setdefault(nombre, Familia(nombre)).rutas.extend(caras)

    for nombre, fuentes_typst in configuracion.inventario_typst(config, incluir_sistema=False).items():
        item = inventario.setdefault(nombre, Familia(nombre))
        for ruta in fuentes_typst:
            if ruta is None:
                item.embebida_typst = True
            else:
                # La carpeta propia aparece por ambas vías: no duplicar una cara.
                caras = _cargar_rutas([ruta]).get(nombre, [])
                for cara in caras:
                    if cara not in item.rutas:
                        item.rutas.append(cara)

    return inventario


def _marcas(config: dict, familia: Familia) -> list[str]:
    preferencias = {_clave(x) for x in config["preferidas"]}
    evitar = {_clave(x) for x in config["evitar"]}
    salida = []
    if _clave(familia.nombre) in preferencias:
        salida.append("preferida")
    if _clave(familia.nombre) in evitar:
        salida.append("evitar")
    if familia.marca_medida:
        salida.append(familia.marca_medida)
    return salida


def _grupo(familia: Familia) -> str:
    """Grupo del catálogo: «apta», «titulos» o «no_apta».

    Una familia con archivo medido va a «apta» si permite incrustar y cubre el
    juego, y a «titulos» si permite incrustar pero le faltan caracteres. Sin
    medida, solo cuenta la marca de Typst: las embebidas van a «apta» y el resto
    a «no_apta».
    """
    if familia.errores:
        return "no_apta"
    if familia.verificada:
        if not familia.incrustable:
            return "no_apta"
        return "titulos" if familia.caracteres_faltantes else "apta"
    return "apta" if familia.embebida_typst else "no_apta"


def _motivo_no_apta(familia: Familia) -> str:
    """Motivo breve de una familia no apta."""
    if familia.errores:
        return "; ".join(dict.fromkeys(familia.errores))
    if familia.verificada and not familia.incrustable:
        return f"OS/2.fsType no permite incrustar ({familia.fs_type_texto})"
    return "sin archivo de fuente disponible que medir"


def _avisos(config: dict, familias: dict[str, Familia]) -> list[str]:
    """Nombres de la configuración que no existen y carpeta propia ausente."""
    avisos: list[str] = []
    if config.get("carpeta_fuentes") and config.get("carpeta_fuentes_en_config"):
        ruta = configuracion.carpeta_fuentes(config)
        if ruta is None or not ruta.is_dir():
            avisos.append(f"la carpeta propia de fuentes no existe: {ruta}")
    nombres = {_clave(nombre) for nombre in familias}
    for campo in ("preferidas", "evitar"):
        faltan = [x for x in config[campo] if _clave(x) not in nombres]
        if faltan:
            avisos.append(f"{campo}: nombres que no aparecen en el inventario: " + ", ".join(faltan))
    faltan = [x for x in config["licencias"] if _clave(x) not in nombres]
    if faltan:
        avisos.append("licencias: nombres que no aparecen en el inventario: " + ", ".join(faltan))
    return avisos


def _sha256(ruta: Path) -> str:
    """SHA-256 del contenido, leído por bloques para no cargar el archivo entero."""
    resumen = hashlib.sha256()
    with ruta.open("rb") as fichero:
        for bloque in iter(lambda: fichero.read(1 << 20), b""):
            resumen.update(bloque)
    return resumen.hexdigest()


def _huella(config: dict, rutas: list[Path]) -> str:
    """Huella del catálogo: configuración relevante y contenido de cada fuente.

    Se incluye el SHA-256 de cada archivo, no solo su tamaño: una fuente que
    cambia sin cambiar de tamaño produce la misma huella y el catálogo dejaría
    de señalar que está caducado.
    """
    datos = json.dumps(
        {
            "idiomas": config["idiomas"],
            "sistema": config["sistema"],
            "carpeta_fuentes": config["carpeta_fuentes"],
            "preferidas": config["preferidas"],
            "evitar": config["evitar"],
            "licencias": config["licencias"],
            "caracteres_extra": config["caracteres_extra"],
            "fuentes": [[str(ruta), ruta.stat().st_size, _sha256(ruta)] for ruta in rutas],
        },
        ensure_ascii=False,
        sort_keys=True,
    )
    return hashlib.sha256(datos.encode("utf-8")).hexdigest()[:16]


def escribir_catalogo(config: dict, destino: Path) -> tuple[int, int, int, list[str]]:
    _, TTFont = _fonttools()
    if TTFont is None:
        raise ValueError("falta fontTools: sin él no se puede medir cmap ni OS/2.fsType")
    requeridos = set(map(ord, configuracion.caracteres_requeridos(config)))
    muestra = MUESTRAS.get(config["idiomas"][0], MUESTRAS["es"])
    rutas = configuracion.ficheros_fuente(config)
    familias = _inventario(config)
    for familia in familias.values():
        _medir_familia(familia, requeridos, muestra)
    avisos = _avisos(config, familias)

    grupos: dict[str, list[Familia]] = {"apta": [], "titulos": [], "no_apta": []}
    for familia in sorted(familias.values(), key=lambda f: f.nombre.casefold()):
        grupos[_grupo(familia)].append(familia)
    aptas, titulos, no_aptas = grupos["apta"], grupos["titulos"], grupos["no_apta"]
    lineas = [
        "# Catálogo de fuentes",
        "",
        "Generado desde la configuración del encargo. «Aptas para texto» cubre el conjunto de",
        "caracteres de los idiomas configurados y `OS/2.fsType` permite incrustar; «solo para",
        "títulos y rótulos» se pueden incrustar pero les falta algún carácter del conjunto;",
        "«no aptas» no se pueden incrustar o no se pueden leer.",
        "Las familias que Typst trae embebidas (OFL) se marcan cuando no hay archivo que medir.",
        "La licencia declarada por el usuario y el permiso técnico de incrustación son datos distintos.",
        "Leyenda: «VC» son versalitas, con la característica OpenType que las trae (`smcp`, `c2sc`);",
        "«sin VC» significa que el archivo no trae `smcp`. «Cifras» da la clase del dibujo por",
        "defecto de 0 a 9: `alin.` alineadas o `ant.` antiguas, y `tab.` tabulares o `prop.`",
        "proporcionales. «Alt.» son las alternativas OpenType presentes (`lnum`, `onum`, `tnum`,",
        "`pnum`). Una alternativa ausente no quita las cifras que ya salen por defecto.",
        "«x» y «M» son la altura de x y de mayúscula en fracción de em; «alturas del contorno» avisa",
        "de que se tomaron del dibujo y no de OS/2. «av.» es el avance en mm por carácter medio a",
        "10 pt sobre una muestra neutra del idioma principal, y «CPL» los caracteres que caben en",
        "140 mm a 10 pt, como referencia para comparar familias. Las familias sin archivo que medir",
        "no llevan versalitas, cifras ni métricas.",
        "",
        f"Idiomas: {', '.join(config['idiomas'])}. Caracteres del conjunto comprobado: `{''.join(sorted(chr(c) for c in requeridos))}`.",
        f"Fuentes del sistema: {'sí' if config['sistema'] else 'no'}; carpeta propia: `{config['carpeta_fuentes'] or 'ninguna'}`.",
        f"Huella: `{_huella(config, rutas)}` (configuración y archivos de fuente al generarlo; si cambia, el catálogo está caducado).",
        "",
        f"## Aptas para texto ({len(aptas)})",
        "",
    ]
    if aptas:
        for familia in aptas:
            marcas = _marcas(config, familia)
            sufijo = f" — {'; '.join(marcas)}" if marcas else ""
            partes = [f"`fsType`: {familia.fs_type_texto}", _nota(config, familia)]
            if familia.metricas_texto:
                partes.append(familia.metricas_texto)
            lineas.append(f"- **{familia.nombre}** — " + "; ".join(partes) + sufijo)
    else:
        lineas.append("- Ninguna.")
    lineas += ["", f"## Solo para títulos y rótulos ({len(titulos)})", ""]
    if titulos:
        for familia in titulos:
            marcas = _marcas(config, familia)
            sufijo = f" — {'; '.join(marcas)}" if marcas else ""
            faltan = "".join(sorted(familia.caracteres_faltantes))
            partes = [f"`fsType`: {familia.fs_type_texto}", f"faltan: {faltan}", _nota(config, familia)]
            if familia.metricas_texto:
                partes.append(familia.metricas_texto)
            lineas.append(f"- **{familia.nombre}** — " + "; ".join(partes) + sufijo)
    else:
        lineas.append("- Ninguna.")
    lineas += ["", f"## No aptas ({len(no_aptas)})", ""]
    if no_aptas:
        for familia in no_aptas:
            lineas.append(f"- **{familia.nombre}** — {_motivo_no_apta(familia)}")
    else:
        lineas.append("- Ninguna.")
    if avisos:
        lineas += ["", "## Avisos", ""]
        lineas += [f"- {aviso}" for aviso in avisos]
    destino.parent.mkdir(parents=True, exist_ok=True)
    destino.write_text("\n".join(lineas) + "\n", encoding="utf-8")
    return len(aptas), len(titulos), len(no_aptas), avisos


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Genera maquetacion/catalogo.md desde config.md.")
    parser.add_argument(
        "--config",
        default=None,
        help=(
            "archivo de configuración; sin esta opción se usa maquetacion/config.md si existe y, "
            "si no, los valores predeterminados. Una ruta explícita que no exista es un error"
        ),
    )
    args = parser.parse_args(argv)
    try:
        config = configuracion.cargar_configuracion(args.config)
        destino = Path(config["directorio_proyecto"]) / "maquetacion" / "catalogo.md"
        aptas, titulos, no_aptas, avisos = escribir_catalogo(config, destino)
    except (OSError, ValueError) as exc:
        parser.error(str(exc))
        return 2
    print(
        f"Familias aptas para texto: {aptas}; solo para títulos y rótulos: {titulos}; "
        f"no aptas: {no_aptas}."
    )
    print(f"Catálogo: {destino}")
    for aviso in avisos:
        sys.stderr.write(f"catalogo_fuentes: {aviso}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
