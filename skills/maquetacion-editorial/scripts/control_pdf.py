#!/usr/bin/env python3
"""Control de calidad de un PDF editorial con PyMuPDF.

Comprueba el PDF producido: páginas y corte, fuentes usadas, glifos ausentes,
cobertura de los idiomas configurados, resolución de imágenes mediante su
matriz de transformación, tamaño decimal, metadatos, anonimato, caracteres por
línea y franja de seguridad/sangrado. La medida por bloques es heurística y
admite excepciones declaradas; los controles duros no admiten excepciones.

Uso:
    python control_pdf.py documento.pdf [--config maquetacion/config.md] [opciones]

La salida Markdown se imprime siempre; JSON y Markdown a archivo son opcionales.
Código de salida: 0 sin fallos (puede haber avisos o excepciones declaradas),
1 con fallo duro o heurístico, o cuando el PDF no se puede abrir, 2 por uso o
configuración no válida (incluida una ruta de configuración que no existe).
"""

from __future__ import annotations

import argparse
import io
import json
import math
import re
import sys
import unicodedata
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Sequence
from xml.etree import ElementTree as ET

import configuracion

try:
    import pymupdf
except ImportError:  # pragma: no cover - dependencia del entorno
    sys.stderr.write("control_pdf: falta PyMuPDF (import pymupdf)\n")
    raise SystemExit(2)

PT_POR_MM = 72.0 / 25.4
MM_POR_PT = 25.4 / 72.0

# Firmas de datos personales en el texto.
RE_EMAIL = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")
RE_URL = re.compile(r"(?:https?://|www\.)[^\s<>\"']+", re.IGNORECASE)
# Teléfono: grupos de 2 a 4 dígitos separados por espacio, punto o guion.
# Las fechas también caen en este patrón, así que el candidato se filtra
# después con `_es_telefono`, que exige 9 dígitos o más y descarta las
# formas de fecha conocidas.
RE_TELEFONO = re.compile(r"(?<![\d])(?:\+\d{1,3}[\s.\-]?)?\d{2,4}(?:[\s.\-]\d{2,4}){2,4}(?![\d])")
RE_FECHA = re.compile(
    r"(?<!\d)(?:\d{4}[-./]\d{1,2}[-./]\d{1,2}|\d{1,2}[-./]\d{1,2}[-./]\d{4})(?!\d)"
)

ESTADOS = ("ok", "aviso", "fallo", "fallo heurístico", "excepción declarada", "no-aplica")


@dataclass
class Resultado:
    """Un control con su veredicto y los datos que lo sostienen."""

    id: str
    nombre: str
    estado: str
    detalle: str
    datos: dict[str, Any] = field(default_factory=dict)




def _clave_fuente(nombre: str) -> str:
    """Normaliza un nombre de fuente PDF: quita el prefijo de subconjunto y separadores."""
    nombre = re.sub(r"^[A-Z]{6}\+", "", nombre)
    return re.sub(r"[^a-z0-9]", "", nombre.lower())


def _plural(n: int, singular: str, plural: str) -> str:
    """Concordancia mínima para los mensajes del informe."""
    return f"{n} {singular if n == 1 else plural}"


def _percentil(valores: Sequence[float], p: float) -> float:
    """Percentil con interpolación lineal (p entre 0 y 1)."""
    if not valores:
        return 0.0
    ordenados = sorted(valores)
    if len(ordenados) == 1:
        return float(ordenados[0])
    pos = p * (len(ordenados) - 1)
    bajo = math.floor(pos)
    alto = math.ceil(pos)
    if bajo == alto:
        return float(ordenados[bajo])
    return ordenados[bajo] + (ordenados[alto] - ordenados[bajo]) * (pos - bajo)


# ---------------------------------------------------------------------------
# Lectura del PDF
# ---------------------------------------------------------------------------


@dataclass
class FuentePDF:
    """Una fuente tal como la declara el PDF, con lo que realmente dibuja."""

    basefont: str
    clave: str
    ext: str
    tipo: str
    xref: int
    incrustada: bool
    caracteres: set[str] = field(default_factory=set)
    notdef: int = 0
    paginas: set[int] = field(default_factory=set)


def _esta_incrustada(doc: pymupdf.Document, xref: int, ext: str) -> bool:
    """True si el PDF lleva el programa de la fuente (directo o en la descendiente)."""
    if ext in ("n/a", ""):
        return False
    claves = ("FontFile", "FontFile2", "FontFile3")
    for x in _xrefs_fuente(doc, xref):
        for clave in claves:
            tipo, valor = doc.xref_get_key(x, clave)
            if tipo != "null" and valor not in ("null", ""):
                return True
    # Una fuente CFF/Type0 puede colgar de una descendiente.
    return ext not in ("n/a", "")


def _xrefs_fuente(doc: pymupdf.Document, xref: int) -> list[int]:
    """El propio xref y los de sus fuentes descendientes (Type0)."""
    salida = [xref]
    tipo, valor = doc.xref_get_key(xref, "DescendantFonts")
    if tipo == "array":
        for trozo in re.findall(r"(\d+) 0 R", valor):
            salida.append(int(trozo))
    return salida


def _recoger_fuentes(doc: pymupdf.Document) -> dict[str, FuentePDF]:
    """Reúne las fuentes del documento y los caracteres/glyph ids que dibujan."""
    fuentes: dict[str, FuentePDF] = {}
    for pagina in doc:
        for entrada in pagina.get_fonts(full=True):
            xref, ext, tipo, basefont = entrada[0], entrada[1], entrada[2], entrada[3]
            clave = _clave_fuente(basefont)
            if clave not in fuentes:
                fuentes[clave] = FuentePDF(
                    basefont=basefont,
                    clave=clave,
                    ext=ext,
                    tipo=tipo,
                    xref=xref,
                    incrustada=_esta_incrustada(doc, xref, ext),
                )
            fuentes[clave].paginas.add(pagina.number + 1)
        # get_texttrace da, por cada glifo, el carácter y su glyph id.
        for tramo in pagina.get_texttrace():
            clave = _clave_fuente(str(tramo.get("font", "")))
            fuente = fuentes.get(clave)
            if fuente is None:
                continue
            for caracter, gid, _origen, _caja in tramo.get("chars", []):
                if gid == 0 or caracter in (0xFFFD, 0):
                    fuente.notdef += 1
                elif 0x20 <= caracter < 0x110000:
                    letra = chr(caracter)
                    # Los guiones blandos (U+00AD) que Typst escribe al partir
                    # palabras y otros caracteres invisibles no son glifos que
                    # haya que exigir a la fuente.
                    if unicodedata.category(letra) not in ("Cc", "Cf") and not letra.isspace():
                        fuente.caracteres.add(letra)
    return fuentes


def _texto_documento(doc: pymupdf.Document) -> list[tuple[int, str]]:
    """Texto por página, para las comprobaciones de contenido."""
    return [(pagina.number + 1, pagina.get_text()) for pagina in doc]


# ---------------------------------------------------------------------------
# Comprobaciones
# ---------------------------------------------------------------------------


def comprobar_paginas(doc: pymupdf.Document, esperadas: int | None, minimo: int | None, maximo: int | None) -> Resultado:
    n = doc.page_count
    datos: dict[str, Any] = {"paginas": n}
    if esperadas is not None:
        datos["esperadas"] = esperadas
        estado = "ok" if n == esperadas else "fallo"
        detalle = f"{_plural(n, 'página', 'páginas')} (se esperaban {esperadas})"
    elif minimo is not None or maximo is not None:
        estado = "ok"
        if minimo is not None and n < minimo:
            estado = "fallo"
        if maximo is not None and n > maximo:
            estado = "fallo"
        detalle = f"{_plural(n, 'página', 'páginas')} (rango {minimo or '—'}–{maximo or '—'})"
    else:
        estado = "no-aplica"
        detalle = f"{_plural(n, 'página', 'páginas')} (sin valor esperado)"
    # La divisibilidad por 8 es un dato, no un veredicto por defecto.
    datos["mod8"] = n % 8
    datos["mod16"] = n % 16
    return Resultado("paginas", "Número de páginas", estado, detalle, datos)


def _caja_pagina(pagina: pymupdf.Page) -> tuple[pymupdf.Rect, pymupdf.Rect]:
    """(corte, sangrado) en puntos, con respaldo al MediaBox."""
    corte = pymupdf.Rect(pagina.trimbox)
    if corte.is_empty or corte.is_infinite:
        corte = pymupdf.Rect(pagina.mediabox)
    sangrado = pymupdf.Rect(pagina.bleedbox)
    if sangrado.is_empty or sangrado.is_infinite:
        sangrado = pymupdf.Rect(pagina.mediabox)
    return corte, sangrado


def comprobar_tamanos(doc: pymupdf.Document, esperados: list[tuple[float, float]], tolerancia: float) -> Resultado:
    if not esperados:
        return Resultado("tamanos", "Tamaño de página", "no-aplica", "sin tamaño esperado")
    discrepancias: list[dict[str, Any]] = []
    medidas: list[dict[str, Any]] = []
    for pagina in doc:
        corte, _ = _caja_pagina(pagina)
        ancho = corte.width * MM_POR_PT
        alto = corte.height * MM_POR_PT
        medidas.append({"pagina": pagina.number + 1, "ancho_mm": round(ancho, 2), "alto_mm": round(alto, 2)})
        if not any(abs(ancho - a) <= tolerancia and abs(alto - b) <= tolerancia for a, b in esperados):
            discrepancias.append({"pagina": pagina.number + 1, "ancho_mm": round(ancho, 2), "alto_mm": round(alto, 2)})
    if discrepancias:
        detalle = (
            f"{_plural(len(discrepancias), 'página', 'páginas')} fuera de "
            + ", ".join(f"{a:g}×{b:g} mm" for a, b in esperados)
            + f" (±{tolerancia:g} mm); primera: pág. {discrepancias[0]['pagina']} "
            f"{discrepancias[0]['ancho_mm']}×{discrepancias[0]['alto_mm']} mm"
        )
        return Resultado("tamanos", "Tamaño de página", "fallo", detalle, {"discrepancias": discrepancias, "medidas": medidas})
    return Resultado(
        "tamanos",
        "Tamaño de página",
        "ok",
        f"{_plural(len(medidas), 'página', 'páginas')} a {medidas[0]['ancho_mm']}×{medidas[0]['alto_mm']} mm",
        {"medidas": medidas},
    )


def comprobar_fuentes(
    doc: pymupdf.Document, fuentes: dict[str, FuentePDF], ficheros: list[Path], requerido: str
) -> list[Resultado]:
    """Comprueba incrustación, glifos ausentes y cobertura configurada.

    Solo es fallo un carácter que el PDF usa y la fuente no tiene. Una fuente
    con archivo que no cubre parte del juego pero no los caracteres usados deja
    aviso: sirve para títulos y rótulos, no para texto corrido. Un subconjunto
    incrustado que cubre todos los caracteres usados, pero no demuestra el resto
    del juego, queda en correcto con esa nota. Una fuente que no se puede
    verificar —no hay archivo configurado para ella, el archivo es ilegible o
    falta `fontTools`— queda en aviso con su motivo. Antes de darla por no
    verificada se intenta medir el programa que el propio PDF lleva incrustado
    con `doc.extract_font`.
    """
    listado = [
        {
            "fuente": f.basefont,
            "tipo": f.tipo,
            "incrustada": f.incrustada,
            "extension": f.ext,
            "paginas": sorted(f.paginas),
            "caracteres": len(f.caracteres),
            "notdef": f.notdef,
        }
        for f in sorted(fuentes.values(), key=lambda x: x.basefont.lower())
    ]
    sin_incrustar = [f.basefont for f in fuentes.values() if not f.incrustada]
    resultados = [
        Resultado(
            "fuentes",
            "Fuentes e incrustación",
            "fallo" if sin_incrustar else "ok",
            (
                f"{_plural(len(listado), 'fuente', 'fuentes')}; sin incrustar: {', '.join(sin_incrustar)}"
                if sin_incrustar
                else f"{_plural(len(listado), 'fuente', 'fuentes')}, todas incrustadas"
            ),
            {"fuentes": listado},
        )
    ]
    con_notdef = {f.basefont: f.notdef for f in fuentes.values() if f.notdef}
    if con_notdef:
        detalle = "; ".join(f"{k}: {v} glifos .notdef o U+FFFD" for k, v in con_notdef.items())
        resultados.append(Resultado("glifos-ausentes", "Glifos ausentes (.notdef / U+FFFD)", "fallo", detalle, {"notdef": con_notdef}))
    else:
        resultados.append(Resultado("glifos-ausentes", "Glifos ausentes (.notdef / U+FFFD)", "ok", "ningún glifo .notdef ni U+FFFD"))

    mapa = _mapa_ficheros(ficheros) if ficheros else {}
    verificadas: list[dict[str, Any]] = []
    no_verificadas: list[dict[str, Any]] = []
    faltan_usados: dict[str, list[str]] = {}
    faltantes_no_usados: dict[str, list[str]] = {}
    subconjuntos: dict[str, list[str]] = {}
    formatos: dict[str, str] = {}
    for fuente in sorted(fuentes.values(), key=lambda f: f.basefont.lower()):
        motivos: list[str] = []
        cmap: set[int] | None = None
        origen = ""
        ext = ""
        desde_archivo = False
        desde_incrustado = False
        fichero = mapa.get(fuente.clave)
        if fichero is None:
            motivos.append("ningún archivo configurado corresponde a esta fuente")
        else:
            cmap, motivo = _cmap_fichero(fichero)
            if cmap is None:
                motivos.append(motivo)
            else:
                origen = str(fichero)
                desde_archivo = True
        if cmap is None:
            # Sin archivo medible, o con uno ilegible, se intenta el programa
            # que el PDF lleva incrustado: es la única evidencia disponible.
            cmap, info = _medir_incrustada(doc, fuente, requerido)
            ext = info["ext"]
            if ext:
                formatos[fuente.basefont] = ext
            if cmap is not None:
                origen = f"programa incrustado en el PDF ({ext})"
                desde_incrustado = True
            else:
                motivos.append(info["motivo"])
                if info["medidos"]:
                    motivos.append(
                        f"{info['medidos']} caracteres medidos en el programa incrustado ({ext or 'formato desconocido'})"
                    )
        if cmap is None:
            entrada: dict[str, Any] = {
                "fuente": fuente.basefont,
                "motivo": "; ".join(dict.fromkeys(m for m in motivos if m)),
            }
            if ext:
                entrada["ext"] = ext
            no_verificadas.append(entrada)
            continue
        usados_fuera = sorted(c for c in fuente.caracteres if ord(c) not in cmap)
        fuera_del_juego = sorted(c for c in requerido if ord(c) not in cmap)
        verificadas.append({"fuente": fuente.basefont, "origen": origen, "huecos": usados_fuera})
        if usados_fuera:
            faltan_usados[fuente.basefont] = usados_fuera
        elif fuera_del_juego:
            if desde_archivo:
                faltantes_no_usados[fuente.basefont] = fuera_del_juego
            elif desde_incrustado:
                subconjuntos[fuente.basefont] = fuera_del_juego

    datos: dict[str, Any] = {
        "verificadas": verificadas,
        "no_verificadas": no_verificadas,
        "requerido": requerido,
        "usadas": len(fuentes),
        "formatos_incrustados": formatos,
        "faltan_usados": faltan_usados,
        "faltantes_no_usados": faltantes_no_usados,
        "subconjuntos": subconjuntos,
    }
    if faltan_usados:
        detalle = "; ".join(f"{k}: falta {''.join(v)}" for k, v in faltan_usados.items())
        if no_verificadas:
            detalle += " · sin verificar: " + "; ".join(f"{x['fuente']} ({x['motivo']})" for x in no_verificadas)
        resultados.append(Resultado("cobertura", "Cobertura de glifos", "fallo", detalle, datos))
    elif faltantes_no_usados:
        detalle = "; ".join(
            f"{k} no cubre {''.join(v)} (no usados aquí): sirve para títulos y rótulos, no para texto corrido"
            for k, v in faltantes_no_usados.items()
        )
        if no_verificadas:
            detalle += " · sin verificar: " + "; ".join(f"{x['fuente']} ({x['motivo']})" for x in no_verificadas)
        resultados.append(Resultado("cobertura", "Cobertura de glifos", "aviso", detalle, datos))
    elif no_verificadas and not ficheros and not verificadas:
        resultados.append(
            Resultado(
                "cobertura",
                "Cobertura de glifos",
                "no-aplica",
                "no hay archivos de fuentes propios ni del sistema, y el programa incrustado no permite medir "
                + _plural(len(fuentes), "fuente usada", "fuentes usadas"),
                datos,
            )
        )
    elif no_verificadas:
        detalle = (
            f"comprobadas {len(verificadas)} de {len(fuentes)} fuentes usadas; sin verificar: "
            + "; ".join(f"{x['fuente']} ({x['motivo']})" for x in no_verificadas)
        )
        resultados.append(Resultado("cobertura", "Cobertura de glifos", "aviso", detalle, datos))
    elif subconjuntos:
        detalle = "; ".join(
            f"{k}: cubre los caracteres usados; el juego completo no se puede comprobar en un subconjunto"
            for k in subconjuntos
        )
        resultados.append(Resultado("cobertura", "Cobertura de glifos", "ok", detalle, datos))
    else:
        detalle = f"{_plural(len(verificadas), 'fuente usada verificada cubre', 'fuentes usadas verificadas cubren')} el conjunto requerido"
        resultados.append(Resultado("cobertura", "Cobertura de glifos", "ok", detalle, datos))
    return resultados


_CACHE_CMAP: dict[Path, tuple[set[int] | None, str]] = {}


def _ttfont():
    """TTFont de fontTools o None con el motivo para el informe."""
    try:
        from fontTools.ttLib import TTFont  # importación diferida: solo si hay fuentes
    except ImportError:
        return None, "fontTools no está instalado: no se puede medir la cobertura"
    return TTFont, ""


def _fonttools_cff():
    """CFFFontSet y toUnicode de fontTools, o None con el motivo."""
    try:
        from fontTools.agl import toUnicode
        from fontTools.cffLib import CFFFontSet
    except ImportError:
        return None, "fontTools no está instalado: no se puede medir la cobertura"
    return (CFFFontSet, toUnicode), ""


def _cmap_fichero(fichero: Path) -> tuple[set[int] | None, str]:
    """cmap del archivo y, cuando no se puede leer, el motivo."""
    if fichero in _CACHE_CMAP:
        return _CACHE_CMAP[fichero]
    TTFont, motivo = _ttfont()
    cmap: set[int] | None = None
    if TTFont is None:
        motivo = f"{motivo}; no se pudo leer el cmap de {fichero.name}"
    else:
        motivo = f"no se pudo leer el cmap de {fichero.name}"
        try:
            fuente = TTFont(str(fichero), lazy=True, fontNumber=0)
            tabla = fuente.getBestCmap()
            cmap = set(tabla.keys()) if tabla else set()
            fuente.close()
        except Exception:
            cmap = None
    _CACHE_CMAP[fichero] = (cmap, motivo)
    return cmap, motivo


def _codepoints_cff(datos: bytes) -> tuple[set[int] | None, str]:
    """Codepoints de un CFF1 incrustado, deducidos de los nombres de glifo.

    Los subconjuntos CFF de un PDF conservan, en general, el nombre del glifo
    (`aacute`, `uni00F1`…), y `fontTools.agl.toUnicode` los traduce. Los glifos
    CID o sin nombre Unicode no se pueden traducir: quedan fuera de la medida.
    """
    modulos, motivo = _fonttools_cff()
    if modulos is None:
        return None, motivo
    CFFFontSet, toUnicode = modulos
    try:
        conjunto = CFFFontSet()
        conjunto.decompile(io.BytesIO(datos), None)
    except Exception as exc:
        return None, f"el CFF incrustado no se pudo leer ({type(exc).__name__})"
    codepoints: set[int] = set()
    for cima in conjunto.topDictIndex:
        try:
            nombres = list(cima.CharStrings.keys())
        except Exception:
            continue
        for nombre in nombres:
            if not nombre or nombre == ".notdef":
                continue
            texto = toUnicode(nombre)
            if len(texto) == 1:
                codepoints.add(ord(texto))
    if not codepoints:
        return None, "el CFF incrustado usa glifos CID o sin nombre Unicode: no se pueden deducir caracteres"
    return codepoints, ""


def _codepoints_sfnt(datos: bytes) -> tuple[set[int] | None, str]:
    """cmap de un programa TrueType/OpenType incrustado."""
    TTFont, motivo = _ttfont()
    if TTFont is None:
        return None, motivo
    try:
        programa = TTFont(io.BytesIO(datos), lazy=True, fontNumber=0)
    except Exception as exc:
        return None, f"el programa incrustado no se pudo leer ({type(exc).__name__})"
    try:
        try:
            tabla = programa.getBestCmap()
        except Exception:
            tabla = None
    finally:
        try:
            programa.close()
        except Exception:
            pass
    if not tabla:
        return None, "el programa incrustado no trae tabla cmap"
    return set(tabla.keys()), ""


def _utf16_codepoints(hexadecimal: str) -> set[int]:
    """Codepoints de un valor UTF-16BE en hexadecimal, como los del CMap ToUnicode."""
    try:
        texto = bytes.fromhex(hexadecimal).decode("utf-16-be", errors="ignore")
    except ValueError:
        return set()
    return {ord(c) for c in texto}


def _codepoints_cmap(datos: bytes) -> set[int]:
    """Codepoints de un CMap ToUnicode: bloques bfchar y bfrange."""
    texto = datos.decode("latin-1", errors="replace")
    codepoints: set[int] = set()
    for bloque in re.findall(r"beginbfchar(.*?)endbfchar", texto, re.S):
        for destino in re.findall(r"<[0-9A-Fa-f]+>\s*<([0-9A-Fa-f]+)>", bloque):
            codepoints |= _utf16_codepoints(destino)
    for bloque in re.findall(r"beginbfrange(.*?)endbfrange", texto, re.S):
        for _inicio, _fin, destino in re.findall(r"<([0-9A-Fa-f]+)>\s*<([0-9A-Fa-f]+)>\s*<([0-9A-Fa-f]+)>", bloque):
            codepoints |= _utf16_codepoints(destino)
        for _inicio, _fin, lista in re.findall(r"<([0-9A-Fa-f]+)>\s*<([0-9A-Fa-f]+)>\s*\[(.*?)\]", bloque, re.S):
            for destino in re.findall(r"<([0-9A-Fa-f]+)>", lista):
                codepoints |= _utf16_codepoints(destino)
    return codepoints


def _codepoints_tounicode(doc: pymupdf.Document, fuente: FuentePDF) -> set[int]:
    """Caracteres que el propio PDF declara para esta fuente en su CMap ToUnicode.

    Es la evidencia que queda cuando el programa incrustado usa nombres de glifo
    CID (`cid00001`…), como hacen los subconjuntos de Typst: el CMap demuestra
    qué caracteres del subconjunto son cuáles, y no dice nada de los ausentes.
    """
    for x in _xrefs_fuente(doc, fuente.xref):
        tipo, valor = doc.xref_get_key(x, "ToUnicode")
        if tipo != "xref":
            continue
        encontrado = re.search(r"(\d+)\s+0\s+R", valor or "")
        if not encontrado:
            continue
        try:
            datos = doc.xref_stream(int(encontrado.group(1))) or b""
        except Exception:
            continue
        codepoints = _codepoints_cmap(datos)
        if codepoints:
            return codepoints
    return set()


def _medir_incrustada(doc: pymupdf.Document, fuente: FuentePDF, requerido: str) -> tuple[set[int] | None, dict[str, Any]]:
    """Mide el programa de fuente que el PDF lleva incrustado.

    `doc.extract_font` devuelve `(nombre, extensión, tipo, contenido)`; la
    extensión decide cómo se lee, porque un CFF no es un SFNT y `TTFont` no
    puede abrirlo. Los subconjuntos de Typst llegan como `cid` (CIDFontType0C):
    su CFF conserva nombres de glifo CID, sin Unicode, así que se completa la
    medida con el CMap ToUnicode del propio PDF, que demuestra qué carácter es
    cada glifo del subconjunto. Un programa incrustado suele ser un subconjunto:
    si no demuestra todo el conjunto requerido, se devuelven los caracteres que
    sí se pudieron medir y el resto queda como no medido, nunca como hueco. Un
    TrueType/OpenType sin tabla cmap se mide también con ese CMap ToUnicode.
    """
    info: dict[str, Any] = {"ext": "", "tipo": "", "medidos": 0, "motivo": ""}
    try:
        extraida = doc.extract_font(fuente.xref)
    except Exception as exc:
        info["motivo"] = f"no se pudo extraer la fuente del PDF ({type(exc).__name__})"
        return None, info
    if not isinstance(extraida, (tuple, list)) or len(extraida) < 4:
        info["motivo"] = "doc.extract_font no devolvió (nombre, extensión, tipo, contenido)"
        return None, info
    ext = str(extraida[1] or "").strip().lower()
    info["ext"] = ext
    info["tipo"] = str(extraida[2] or "")
    datos = extraida[3] or b""
    if not datos:
        info["motivo"] = "el PDF no lleva un programa de fuente que se pueda extraer"
        return None, info
    motivo = ""
    if ext in ("cff", "cid"):
        medidos, motivo = _codepoints_cff(datos)
        del_cmap = _codepoints_tounicode(doc, fuente)
        if del_cmap:
            # Los nombres CID no dan Unicode: el CMap ToUnicode del PDF
            # completa la medida con los caracteres que el subconjunto sí
            # demuestra.
            if not medidos:
                if motivo:
                    motivo = f"{motivo}; la medida sale del CMap ToUnicode del PDF"
                else:
                    motivo = (
                        f"el CFF incrustado ({ext}) usa glifos CID sin nombre Unicode; "
                        "la medida sale del CMap ToUnicode del PDF"
                    )
            medidos = (medidos or set()) | del_cmap
        if not medidos:
            medidos = None
    elif ext in ("ttf", "otf"):
        medidos, motivo = _codepoints_sfnt(datos)
        if medidos is None:
            # Un subconjunto TrueType puede no traer cmap: el CMap ToUnicode
            # del PDF demuestra, igual que en CID/CFF, qué caracteres usa.
            del_cmap = _codepoints_tounicode(doc, fuente)
            if del_cmap:
                if motivo:
                    motivo = f"{motivo}; la medida sale del CMap ToUnicode del PDF"
                else:
                    motivo = (
                        f"el programa incrustado ({ext}) no trae tabla cmap; "
                        "la medida sale del CMap ToUnicode del PDF"
                    )
                medidos = del_cmap
    else:
        medidos = None
        motivo = f"formato de fuente incrustada no soportado ({ext or 'sin extensión'})"
    if medidos is None:
        info["motivo"] = motivo
        return None, info
    info["medidos"] = len(medidos)
    faltan = [c for c in requerido if ord(c) not in medidos]
    info["faltan"] = faltan
    if faltan:
        prefijo = f"{motivo}; " if motivo else ""
        info["motivo"] = (
            f"{prefijo}el programa incrustado ({ext}) es un subconjunto y no demuestra el conjunto "
            f"requerido: sin medir {''.join(faltan)}"
        )
    return medidos, info


_CACHE_MAPA: list[tuple[dict[str, Path], list[Path]]] = []


def _mapa_ficheros(ficheros: list[Path]) -> dict[str, Path]:
    """Clave normalizada de familia, nombre PostScript y nombre de fichero → ruta."""
    if _CACHE_MAPA and _CACHE_MAPA[0][1] == ficheros:
        return _CACHE_MAPA[0][0]
    mapa: dict[str, Path] = {}
    try:
        from fontTools.ttLib import TTFont

        for ruta in ficheros:
            try:
                fuente = TTFont(str(ruta), lazy=True, fontNumber=0)
                nombres = []
                for ident in (1, 4, 6, 16, 17):
                    valor = fuente["name"].getDebugName(ident)
                    if valor:
                        nombres.append(valor)
                fuente.close()
            except Exception:
                nombres = []
            # El nombre del fichero también sirve de clave: así una fuente
            # ilegible se empareja con su fuente usada y se informa como tal,
            # en vez de quedar silenciosamente sin comprobar.
            nombres.append(ruta.stem)
            for nombre in nombres:
                mapa.setdefault(_clave_fuente(nombre), ruta)
    except Exception:
        for ruta in ficheros:
            mapa.setdefault(_clave_fuente(ruta.stem), ruta)
    _CACHE_MAPA[:] = [(mapa, ficheros)]
    return mapa


def comprobar_imagenes(
    doc: pymupdf.Document, ppi_objetivo: float, ppi_minimo: float, copias_trabajo: bool = False
) -> Resultado:
    """ppp efectivos a partir de la matriz de transformación real de cada imagen.

    La escala singular máxima de la matriz en puntos por píxel conserva el ppp
    ante giros arbitrarios y cizallas. Una transformación ausente, singular o
    no finita se informa como no soportada y no como una medición válida. Con
    copias de trabajo se omite el veredicto y se informa del tamaño final.
    """
    imagenes: list[dict[str, Any]] = []
    for pagina in doc:
        for indice, info in enumerate(pagina.get_image_info(xrefs=True)):
            caja = pymupdf.Rect(info["bbox"])
            if caja.is_empty:
                continue
            px_w, px_h = int(info["width"]), int(info["height"])
            if px_w <= 0 or px_h <= 0 or caja.width <= 0 or caja.height <= 0:
                continue
            transform = info.get("transform")
            transform_error = None
            ppi: float | None = None
            lado_corto_final_px: int | None = None
            if not isinstance(transform, (tuple, list)) or len(transform) != 6:
                transform_error = "matriz de transformación ausente o no compatible"
            else:
                try:
                    a, b, c, d, _e, _f = (float(x) for x in transform)
                except (TypeError, ValueError, OverflowError):
                    transform_error = "matriz de transformación no numérica"
                else:
                    if not all(math.isfinite(x) for x in (a, b, c, d)):
                        transform_error = "matriz de transformación no finita"
                    else:
                        # MuPDF expresa la transformación del cuadrado unidad en
                        # puntos. Se convierte cada eje a puntos por píxel y se
                        # toma la mayor escala singular, válida para giros y cizallas.
                        m00, m01 = a / px_w, c / px_h
                        m10, m11 = b / px_w, d / px_h
                        traza = m00 * m00 + m01 * m01 + m10 * m10 + m11 * m11
                        determinante = m00 * m11 - m01 * m10
                        discriminante = max(0.0, traza * traza - 4 * determinante * determinante)
                        escala = math.sqrt(max(0.0, (traza + math.sqrt(discriminante)) / 2))
                        if escala <= 0 or abs(determinante) <= 1e-15:
                            transform_error = "matriz de transformación singular"
                        else:
                            ppi = 72.0 / escala
                            lado_x = math.hypot(a, b)
                            lado_y = math.hypot(c, d)
                            if lado_x > 0 and lado_y > 0:
                                lado_corto_final_px = round(min(lado_x, lado_y) / 72 * ppi_objetivo)
                            else:
                                transform_error = "eje nulo en la matriz de transformación"
            caja_ratio = caja.width / caja.height
            imagenes.append(
                {
                    "pagina": pagina.number + 1,
                    "indice": indice,
                    "xref": info.get("xref"),
                    "px": [px_w, px_h],
                    "caja_pt": [round(v, 2) for v in caja],
                    "colocada_mm": [round(caja.width * MM_POR_PT, 2), round(caja.height * MM_POR_PT, 2)],
                    "ratio_colocada": round(caja_ratio, 5),
                    "transformacion": list(transform) if isinstance(transform, (tuple, list)) else None,
                    "transformacion_no_soportada": transform_error,
                    "ppi": round(ppi, 1) if ppi is not None else None,
                    "lado_corto_final_px": lado_corto_final_px,
                }
            )
    if not imagenes:
        return Resultado("imagenes", "Resolución efectiva de las imágenes", "no-aplica", "sin imágenes colocadas")
    if copias_trabajo:
        verificables = [i for i in imagenes if i["lado_corto_final_px"] is not None]
        if not verificables:
            sin_transformacion = "; ".join(
                f"pág. {i['pagina']} imagen {i['indice']}: {i['transformacion_no_soportada']}"
                for i in imagenes
            )
            detalle = f"copias de trabajo: {_plural(len(imagenes), 'imagen', 'imágenes')}; no se pudo medir la matriz: {sin_transformacion}"
            return Resultado("imagenes", "Resolución efectiva de las imágenes", "no-aplica", detalle, {"imagenes": imagenes, "ppi_objetivo": ppi_objetivo, "copias_trabajo": True})
        exigente = max(verificables, key=lambda i: i["lado_corto_final_px"])
        no_medibles = [i for i in imagenes if i["lado_corto_final_px"] is None]
        sufijo = (
            "; transformaciones no soportadas: "
            + "; ".join(f"pág. {i['pagina']} imagen {i['indice']}: {i['transformacion_no_soportada']}" for i in no_medibles)
            if no_medibles
            else ""
        )
        detalle = (
            f"copias de trabajo: {_plural(len(imagenes), 'imagen', 'imágenes')}; para la versión final, "
            f"la más exigente necesita {exigente['lado_corto_final_px']} px de lado corto a {ppi_objetivo:g} ppp "
            f"(pág. {exigente['pagina']}, {exigente['colocada_mm'][0]}×{exigente['colocada_mm'][1]} mm){sufijo}"
        )
        return Resultado("imagenes", "Resolución efectiva de las imágenes", "no-aplica", detalle, {"imagenes": imagenes, "ppi_objetivo": ppi_objetivo, "copias_trabajo": True})
    no_medibles = [i for i in imagenes if i["ppi"] is None]
    criticas = [i for i in imagenes if i["ppi"] is None or i["ppi"] < ppi_minimo]
    bajas = [i for i in imagenes if i["ppi"] is not None and ppi_minimo <= i["ppi"] < ppi_objetivo]
    medidas = [i for i in imagenes if i["ppi"] is not None]
    minima = min(medidas, key=lambda i: i["ppi"]) if medidas else None
    peor = (
        f"pág. {minima['pagina']} a {minima['ppi']:g} ppp "
        f"({minima['px'][0]}×{minima['px'][1]} px en "
        f"{minima['colocada_mm'][0]}×{minima['colocada_mm'][1]} mm)"
        if minima
        else "no se pudo medir ninguna transformación"
    )
    no_soportadas = "; ".join(
        f"pág. {i['pagina']} imagen {i['indice']}: {i['transformacion_no_soportada']}"
        for i in no_medibles[:5]
    )
    if criticas:
        estado = "fallo"
        cola = f" y {len(bajas)} en aviso ({ppi_minimo:g}–{ppi_objetivo:g} ppp)" if bajas else ""
        sin_transformacion = f"; transformaciones no soportadas: {no_soportadas}" if no_medibles else ""
        detalle = f"{_plural(len(criticas), 'imagen', 'imágenes')} por debajo de {ppi_minimo:g} ppp o sin medir{cola}; la peor: {peor}{sin_transformacion}"
    elif bajas:
        estado = "aviso"
        detalle = (
            f"{_plural(len(bajas), 'imagen', 'imágenes')} entre {ppi_minimo:g} y {ppi_objetivo:g} ppp; "
            f"la peor: {peor}"
        )
    else:
        estado = "ok"
        detalle = f"{_plural(len(imagenes), 'imagen', 'imágenes')}, la menor a {minima['ppi']:g} ppp (objetivo {ppi_objetivo:g})"
    return Resultado(
        "imagenes",
        "Resolución efectiva de las imágenes",
        estado,
        detalle,
        {"imagenes": imagenes, "ppi_objetivo": ppi_objetivo, "ppi_minimo": ppi_minimo},
    )


def comprobar_tamano_archivo(ruta: Path, max_mb: float | None) -> Resultado:
    bytes_archivo = ruta.stat().st_size
    mb = bytes_archivo / 1_000_000
    if max_mb is None:
        return Resultado("archivo", "Tamaño del archivo", "no-aplica", f"{mb:.3f} MB decimales ({bytes_archivo:,} bytes)", {"mb": round(mb, 6), "bytes": bytes_archivo})
    estado = "ok" if mb <= max_mb else "fallo"
    detalle = f"{mb:.3f} MB decimales ({bytes_archivo:,} bytes; límite {max_mb:g} MB)"
    return Resultado("archivo", "Tamaño del archivo", estado, detalle, {"mb": round(mb, 6), "bytes": bytes_archivo, "max_mb": max_mb})


def comprobar_metadatos(doc: pymupdf.Document, exigir: bool) -> Resultado:
    """Título y creador declarados; con `exigir`, su ausencia es fallo duro."""
    meta = {k: (v or "") for k, v in (doc.metadata or {}).items() if v}
    campos = {k: meta.get(k, "") for k in ("title", "author", "creator", "producer")}
    vacios = [k for k in ("title", "creator") if not campos[k]]
    if vacios and exigir:
        estado = "fallo"
        detalle = "faltan metadatos: " + ", ".join(vacios)
    elif vacios:
        estado = "aviso"
        detalle = "sin declarar: " + ", ".join(vacios)
    else:
        estado = "ok"
        detalle = f"título «{campos['title']}», creador «{campos['creator']}»"
    return Resultado("metadatos", "Metadatos", estado, detalle, {"metadatos": campos, "exigidos": exigir})


def _es_telefono(candidato: str) -> bool:
    """Descarta fechas y cifras cortas que caen en el patrón de teléfono.

    La fecha se busca en cualquier posición del candidato: un XMP con un valor
    `00` seguido de otro valor con la fecha no puede contar diez dígitos como
    si fueran un teléfono.
    """
    digitos = re.sub(r"\D", "", candidato)
    if len(digitos) < 9:
        return False
    if RE_FECHA.search(candidato):
        return False
    return True


# Extensiones cuyo contenido es, por convenio, texto.
EXT_TEXTO_ADJUNTO = {
    ".txt", ".csv", ".tsv", ".xml", ".json", ".html", ".htm", ".md", ".markdown",
    ".yml", ".yaml", ".svg", ".rtf", ".log", ".ini", ".tex", ".css", ".js",
}

# Profundidad con la que se recorren los adjuntos de un PDF adjunto.
PROFUNDIDAD_ADJUNTOS = 3


def _normalizar_busqueda(texto: str) -> str:
    """Normaliza para buscar: NFKC y fuera los caracteres de formato invisibles.

    Los caracteres de categoría Cf (U+200B–U+200F, U+2060, U+FEFF, el guion
    blando U+00AD…) permiten escribir un correo que se lee bien pero no coincide
    con el patrón; se eliminan antes de aplicar los patrones.
    """
    return "".join(
        caracter
        for caracter in unicodedata.normalize("NFKC", texto)
        if unicodedata.category(caracter) != "Cf"
    )


def _texto_sin_etiquetas(xml: str) -> str:
    """Texto de un XML mal formado: fuera las etiquetas, se conservan los valores."""
    return re.sub(r"<[^>]*>", " ", xml)


def _variantes_de_texto(datos: bytes) -> list[tuple[str, str]]:
    """Todas las lecturas plausibles del contenido, sin elegir ninguna.

    Se prueban siempre UTF-8, UTF-16 LE/BE, UTF-32 LE/BE y Latin-1 con
    `errors="ignore"`, y además una versión con los bytes NUL eliminados, que
    recupera cadenas como `private@\x00example.com` o un UTF-16 con NUL
    minoritarios. Los patrones se aplican a todas y los resultados se unen.
    """
    variantes: list[tuple[str, str]] = []
    for nombre, codificacion in (
        ("utf-8", "utf-8"),
        ("utf-16-le", "utf-16-le"),
        ("utf-16-be", "utf-16-be"),
        ("utf-32-le", "utf-32-le"),
        ("utf-32-be", "utf-32-be"),
        ("latin-1", "latin-1"),
    ):
        try:
            texto = datos.decode(codificacion, errors="ignore")
        except LookupError:
            continue
        variantes.append((nombre, texto.replace("\ufeff", "")))
    sin_nulos = datos.replace(b"\x00", b"")
    variantes.append(("utf-8 sin NUL", sin_nulos.decode("utf-8", errors="ignore").replace("\ufeff", "")))
    variantes.append(("latin-1 sin NUL", sin_nulos.decode("latin-1").replace("\ufeff", "")))
    return variantes


def _es_pdf(datos: bytes) -> bool:
    return datos[:5] == b"%PDF-"


def _leer_adjunto(
    nombre: str, datos: bytes, error: str | None
) -> tuple[list[tuple[str, str]] | None, str, bool]:
    """Devuelve (variantes de texto, motivo, revisado) de un contenido no PDF.

    Los PDF se tratan aparte, en `revisar_payload`, para no extraer y registrar
    su texto dos veces. `revisado` solo es True cuando el contenido parece
    texto; un binario se escanea igualmente (por si acaso) pero se marca como no
    revisado. Un error de lectura nunca devuelve variantes.
    """
    if error:
        return None, f"no se pudo leer el adjunto ({error})", False
    if not datos:
        return None, "adjunto vacío: no hay contenido que verificar", False
    extension = Path(nombre).suffix.lower()
    variantes = _variantes_de_texto(datos)
    es_texto = (
        extension in EXT_TEXTO_ADJUNTO
        or (datos.count(b"\x00") < len(datos) // 10 and datos.decode("utf-8", errors="ignore").isprintable())
    )
    if es_texto:
        return variantes, f"texto adjunto ({', '.join(c for c, _ in variantes)})", True
    return variantes, f"formato no revisado ({extension.lstrip('.') or 'sin extensión'}): se escanea igualmente", False


def comprobar_anonimato(doc: pymupdf.Document, nombres: list[str]) -> Resultado:
    """Busca datos personales en todos los canales que el PDF expone como texto.

    Los PDF que llevan adjuntos no se certifican: como mínimo se informa un aviso,
    y cualquier dato personal encontrado sigue siendo fallo. El contenido se busca
    en lecturas plausibles (UTF-8, UTF-16, UTF-32, Latin-1 y sin bytes NUL); los
    PDF adjuntos se abren recursivamente hasta `PROFUNDIDAD_ADJUNTOS`.

    Para detectar nombres, el texto y cada nombre usan la misma normalización:
    NFKC sin caracteres invisibles, NFKD sin diacríticos, mayúsculas y espacios,
    saltos, guiones y puntuación colapsados, de modo que «Ana López» y «Ana
    Lopez» coinciden. Para los patrones de correo, URL y teléfono también se
    eliminan caracteres de formato invisibles. Un XMP que no se puede analizar
    como XML se barre como texto, y ese fallo de análisis queda como aviso. El
    texto dibujado dentro de imágenes requiere OCR y no se revisa.
    """
    hallazgos: list[dict[str, Any]] = []
    canales: dict[str, int] = {}
    adjuntos: list[dict[str, Any]] = []
    no_revisados: list[dict[str, Any]] = []
    nombres_norm = [(_normalizar_identidad(n), n) for n in nombres]
    vistos: set[tuple[str, str, str, str]] = set()

    def buscar_nombres(canal: str, texto: str, ubicacion: str, raiz: str | None = None) -> None:
        """Busca los nombres personales en un texto de un canal."""
        if not texto:
            return
        normalizado = _normalizar_identidad(texto)
        for buscado, original in nombres_norm:
            if buscado and f" {buscado} " in f" {normalizado} ":
                clave = (canal, "nombre", original, raiz or ubicacion)
                if clave not in vistos:
                    vistos.add(clave)
                    hallazgos.append({"canal": canal, "tipo": "nombre", "valor": original, "ubicacion": ubicacion})

    def registrar(canal: str, texto: str, ubicacion: str, raiz: str | None = None) -> None:
        """Registra un texto de un canal; `raiz` agrupa ubicaciones equivalentes."""
        canales[canal] = canales.get(canal, 0) + 1
        if not texto:
            return
        buscar_nombres(canal, texto, ubicacion, raiz)
        limpio = _normalizar_busqueda(texto)
        # Una fecha pegada a un teléfono hace que el patrón capture un candidato
        # que la contiene y se descarte entero; se quitan las fechas antes de
        # buscar el número que viene detrás.
        sin_fechas = RE_FECHA.sub(" ", limpio)
        for tipo, patron in (("correo", RE_EMAIL), ("url", RE_URL), ("telefono", RE_TELEFONO)):
            objetivo = sin_fechas if tipo == "telefono" else limpio
            for encontrado in patron.findall(objetivo):
                valor = _limpiar(encontrado)
                if tipo == "telefono" and not _es_telefono(valor):
                    continue
                clave = (canal, tipo, valor, raiz or ubicacion)
                if clave not in vistos:
                    vistos.add(clave)
                    hallazgos.append({"canal": canal, "tipo": tipo, "valor": valor, "ubicacion": ubicacion})

    def revisar_payload(
        nombre: str,
        datos: bytes | None,
        error: str | None,
        contexto: str,
        profundidad: int,
        origen: str,
    ) -> None:
        """Revisa un contenido adjunto (incrustado o anotación) y, si es PDF, su interior.

        Es el único camino por el que se registra el texto de un adjunto: el PDF
        se abre aquí y se registra página a página, sin pasar antes por
        `_leer_adjunto`, para no contar dos veces la misma coincidencia.
        """
        etiqueta = f"{contexto}{nombre}"
        revisado = False
        codificaciones: list[str] = []
        motivo = ""
        if error:
            motivo = f"no se pudo leer el adjunto ({error})"
        elif not datos:
            motivo = "adjunto vacío: no hay contenido que verificar"
        elif _es_pdf(datos):
            if profundidad >= PROFUNDIDAD_ADJUNTOS:
                motivo = f"adjuntos anidados más allá de {PROFUNDIDAD_ADJUNTOS} niveles"
            else:
                try:
                    interno = pymupdf.open(stream=datos, filetype="pdf")
                except Exception as exc:
                    motivo = f"PDF adjunto ilegible ({exc})"
                else:
                    try:
                        for pagina in interno:
                            registrar(
                                "adjuntos-contenido",
                                pagina.get_text(),
                                f"{etiqueta} pág. {_numero(pagina)}",
                                raiz=etiqueta,
                            )
                        recorrer_adjuntos(interno, f"{etiqueta}/", profundidad + 1)
                    finally:
                        interno.close()
                    revisado = True
                    motivo = "PDF adjunto: páginas y adjuntos internos revisados"
        else:
            variantes, motivo, revisado = _leer_adjunto(nombre, datos, None)
            if variantes is not None:
                codificaciones = [c for c, _ in variantes]
                for _codificacion, texto in variantes:
                    registrar("adjuntos-contenido", texto, etiqueta, raiz=etiqueta)
        adjuntos.append(
            {
                "adjunto": nombre,
                "origen": origen,
                "contexto": contexto or "raíz",
                "profundidad": profundidad,
                "bytes": len(datos or b""),
                "revisado": revisado,
                "motivo": motivo,
                "codificaciones": codificaciones,
            }
        )
        if not revisado:
            no_revisados.append({"elemento": etiqueta, "bytes": len(datos or b""), "motivo": motivo})

    def recorrer_adjuntos(documento: pymupdf.Document, contexto: str, profundidad: int) -> None:
        """Revisa los adjuntos incrustados de un PDF (y entra en los PDF adjuntos)."""
        for indice in range(documento.embfile_count()):
            try:
                info = documento.embfile_info(indice)
            except Exception:
                info = {}
            nombre = str(info.get("filename") or info.get("ufilename") or f"adjunto {indice}")
            registrar(
                "adjuntos",
                " ".join(str(info.get(k) or "") for k in ("filename", "description", "ufilename")),
                f"{contexto}adjunto {indice} ({nombre})",
            )
            datos: bytes | None = None
            error_lectura: str | None = None
            try:
                datos = documento.embfile_get(indice)
            except Exception as exc:
                # Un error de lectura no puede confundirse con un adjunto vacío.
                error_lectura = f"{type(exc).__name__}: {exc}"
            revisar_payload(nombre, datos, error_lectura, contexto, profundidad, "incrustado")

    for pagina, texto in _texto_documento(doc):
        registrar("texto", texto, f"pág. {pagina}")
    for clave, valor in (doc.metadata or {}).items():
        registrar("metadatos", valor or "", f"metadatos:{clave}")
    try:
        xmp = doc.get_xml_metadata() or ""
    except Exception as exc:
        xmp = ""
        no_revisados.append({"elemento": "XMP", "bytes": 0, "motivo": f"no se pudo leer el XMP ({type(exc).__name__})"})
    if xmp.strip():
        try:
            raiz_xmp = ET.fromstring(xmp)
        except ET.ParseError as exc:
            # Un XMP mal formado no puede dejar el canal sin revisar: se barre
            # como texto tras quitar las etiquetas con una expresión regular,
            # que es lo que hacía el control original. Los valores de atributo
            # también se registran: un nombre puede vivir solo ahí.
            for valor in re.findall(r'="([^"]*)"', xmp):
                registrar("xmp", valor, "XMP")
            registrar("xmp", _texto_sin_etiquetas(xmp), "XMP")
            no_revisados.append(
                {
                    "elemento": "XMP",
                    "bytes": len(xmp.encode("utf-8", errors="replace")),
                    "motivo": f"no se pudo analizar como XML ({exc}); se barrió como texto",
                }
            )
        else:
            # Cada texto, cola y atributo se registra por separado: unirlos en
            # una sola cadena deja que el patrón de teléfono combine dígitos de
            # valores distintos a través del salto de línea. Solo los nombres se
            # buscan además en la unión, para ver un nombre repartido en dos
            # elementos.
            valores_xmp: list[str] = []
            for elemento in raiz_xmp.iter():
                for valor in [elemento.text, elemento.tail, *elemento.attrib.values()]:
                    if valor:
                        valores_xmp.append(valor)
                        registrar("xmp", valor, "XMP")
            buscar_nombres("xmp", " ".join(valores_xmp), "XMP")
    anotaciones_fichero = 0
    for pagina in doc:
        for anotacion in pagina.annots() or []:
            info = anotacion.info or {}
            partes = [str(info.get(k) or "") for k in ("content", "title", "subject", "author")]
            try:
                partes.append(anotacion.get_text() or "")
            except Exception:
                pass
            registrar("anotaciones", "\n".join(partes), f"pág. {_numero(pagina)} {anotacion.type[1]}")
            if anotacion.type[1] == "FileAttachment":
                anotaciones_fichero += 1
                # El fichero de una anotación FileAttachment no está en
                # `embfile_*`: se lee con `get_file()` y se revisa igual.
                try:
                    ficha = anotacion.file_info or {}
                except Exception:
                    ficha = {}
                nombre = str(
                    ficha.get("filename") or ficha.get("ufilename") or f"anotación {anotaciones_fichero}"
                )
                payload: bytes | None = None
                error_payload: str | None = None
                try:
                    payload = anotacion.get_file()
                except Exception as exc:
                    error_payload = f"{type(exc).__name__}: {exc}"
                registrar(
                    "adjuntos",
                    " ".join(str(ficha.get(k) or "") for k in ("filename", "description", "ufilename")),
                    f"pág. {_numero(pagina)} FileAttachment ({nombre})",
                )
                revisar_payload(nombre, payload, error_payload, f"pág. {_numero(pagina)}/", 0, "anotación")
        for enlace in pagina.get_links() or []:
            registrar(
                "enlaces",
                " ".join(str(enlace.get(k) or "") for k in ("uri", "file", "page")),
                f"pág. {_numero(pagina)}",
            )
        for campo in pagina.widgets() or []:
            registrar(
                "formularios",
                " ".join(str(getattr(campo, k, "") or "") for k in ("field_name", "field_value", "field_label")),
                f"pág. {_numero(pagina)}",
            )
    recorrer_adjuntos(doc, "", 0)

    lleva_adjuntos = bool(adjuntos) or anotaciones_fichero > 0
    limitacion = (
        "no se revisa el texto contenido en imágenes (requiere OCR); el contenido de un "
        "adjunto no puede certificarse, solo revisarse"
    )
    resumen_canales = ", ".join(f"{k}: {v}" for k, v in sorted(canales.items()))
    titulo = (
        "Anonimato (texto, metadatos, XMP, anotaciones, enlaces, formularios, "
        "adjuntos y su contenido textual o PDF)"
    )
    datos_comunes: dict[str, Any] = {
        "hallazgos": hallazgos,
        "canales": canales,
        "adjuntos": adjuntos,
        "no_revisados": no_revisados,
        "lleva_adjuntos": lleva_adjuntos,
        "anotaciones_fichero": anotaciones_fichero,
        "limitacion": limitacion,
    }
    mensaje_adjuntos = (
        "el PDF lleva adjuntos: en convocatorias anónimas, elimínalos; "
        "su contenido no puede certificarse"
    )
    if hallazgos:
        muestra = ", ".join(f"{h['canal']} «{h['valor']}»" for h in hallazgos[:6])
        extra = f" {mensaje_adjuntos}." if lleva_adjuntos else ""
        if no_revisados:
            extra += " Sin revisar: " + "; ".join(f"{a['elemento']} ({a['motivo']})" for a in no_revisados)
        return Resultado(
            "anonimato",
            titulo,
            "fallo",
            f"{_plural(len(hallazgos), 'coincidencia', 'coincidencias')}: {muestra}.{extra} {limitacion}",
            datos_comunes,
        )
    if lleva_adjuntos:
        detalle = mensaje_adjuntos
        if no_revisados:
            detalle += "; sin revisar: " + "; ".join(f"{a['elemento']} ({a['motivo']})" for a in no_revisados)
        return Resultado("anonimato", titulo, "aviso", f"{detalle}. {limitacion}", datos_comunes)
    if no_revisados:
        return Resultado(
            "anonimato",
            titulo,
            "aviso",
            "sin coincidencias en "
            + (resumen_canales or "los canales disponibles")
            + f", pero {_plural(len(no_revisados), 'elemento', 'elementos')} sin revisar: "
            + "; ".join(f"{a['elemento']} ({a['motivo']})" for a in no_revisados)
            + f". {limitacion}",
            datos_comunes,
        )
    return Resultado(
        "anonimato",
        titulo,
        "ok",
        f"sin coincidencias en {resumen_canales or 'los canales disponibles'}; {limitacion}",
        datos_comunes,
    )


def _limpiar(encontrado: str) -> str:
    """Quita la puntuación final que arrastra una URL o un teléfono."""
    return encontrado.rstrip(".,;:)]»").strip()[:80]


def _normalizar_identidad(texto: str) -> str:
    """Forma común para nombres y texto.

    Se aplica NFKC y se eliminan los caracteres de formato invisibles, se
    descompone con NFKD y se quitan las marcas combinantes, se pasa a
    mayúsculas y se colapsan espacios, saltos, guiones y puntuación. Así
    coinciden «Ana López», «ANA LOPEZ», una tilde descompuesta (U+0301), un
    guion blando (U+00AD) o un espacio de ancho cero (U+200B) intercalados y una
    forma de compatibilidad como «Ｌｏｐｅｚ».
    """
    texto = unicodedata.normalize("NFKD", _normalizar_busqueda(texto)).upper()
    partes = []
    for caracter in texto:
        if unicodedata.combining(caracter):
            continue
        categoria = unicodedata.category(caracter)
        partes.append(caracter if categoria[0] in ("L", "N") else " ")
    return " ".join("".join(partes).split())



@dataclass
class Bloque:
    """Un bloque de texto del PDF con lo necesario para clasificarlo y medirlo."""

    pagina: int
    indice: int
    caja: tuple[float, float, float, float]
    lineas: list[str]
    huecos: list[bool]
    tipo: str = "prosa"

    @property
    def texto(self) -> str:
        return "\n".join(self.lineas)

    @property
    def longitud(self) -> list[int]:
        return [len(l) for l in self.lineas]

    @property
    def mediana(self) -> float:
        return _percentil(self.longitud, 0.5)


# Viñetas y numeraciones que delatan una lista.
RE_VINETA = re.compile(r"^\s*(?:[•·‣▪–—-]|\d{1,2}[.)]|[a-z][.)])\s+")
# Separación entre columnas dentro de una línea (tablas y cuadros).
HUECO_COLUMNA_PT = 6.0


def _bloques_texto(doc: pymupdf.Document) -> list[Bloque]:
    """Bloques de texto del PDF, con la separación entre spans anotada por línea."""
    bloques: list[Bloque] = []
    for pagina in doc:
        indice_pagina = 0
        for bloque in pagina.get_text("dict").get("blocks", []):
            if bloque.get("type") != 0:
                continue
            lineas: list[str] = []
            huecos: list[bool] = []
            for linea in bloque.get("lines", []):
                tramos = linea.get("spans", [])
                texto = "".join(t.get("text", "") for t in tramos).rstrip()
                if not texto:
                    continue
                lineas.append(texto)
                huecos.append(
                    any(
                        b["bbox"][0] - a["bbox"][2] > HUECO_COLUMNA_PT
                        for a, b in zip(tramos, tramos[1:])
                    )
                )
            if lineas:
                indice_pagina += 1
                bloques.append(
                    Bloque(
                        pagina=_numero(pagina),
                        indice=indice_pagina,
                        caja=tuple(round(v, 2) for v in bloque["bbox"]),
                        lineas=lineas,
                        huecos=huecos,
                    )
                )
    return bloques


def _numero(pagina: pymupdf.Page) -> int:
    return pagina.number + 1


def _mm(puntos: float) -> str:
    """Puntos → milímetros con un decimal y coma decimal."""
    return f"{puntos * MM_POR_PT:.1f}".replace(".", ",")


def _clasificar(bloque: Bloque, mediana_minima: float = 25.0) -> str:
    """Clasifica un bloque por geometría y contenido: prosa, tabla, lista o rótulo.

    Es una heurística, no una lectura semántica: una tabla sin separación entre
    columnas parece prosa, y un párrafo muy estrecho puede parecer un rótulo.
    """
    lineas = bloque.lineas
    if not lineas:
        return "vacío"
    if bloque.mediana < mediana_minima:
        return "rótulo"
    if len(lineas) >= 2 and sum(bloque.huecos) >= max(1, 0.6 * len(lineas)):
        return "tabla"
    con_vineta = sum(1 for l in lineas if RE_VINETA.match(l))
    if len(lineas) >= 2 and con_vineta >= max(1, 0.5 * len(lineas)):
        return "lista"
    return "prosa"


def _coincide_bloque(bloque: Bloque, selector: Any) -> bool:
    if isinstance(selector, int):
        return bloque.indice == selector
    texto = str(selector).strip()
    if texto.isdigit():
        return bloque.indice == int(texto)
    prefijo = _normalizar_identidad(texto)
    return bool(prefijo) and _normalizar_identidad(bloque.texto).startswith(prefijo)


def comprobar_medida(
    bloques: list[Bloque],
    minimo: int,
    maximo: int,
    duro_min: int,
    duro_max: int,
    mediana_minima: float = 25.0,
    excepciones: list[dict[str, Any]] | None = None,
) -> Resultado:
    """Mide cpl por bloque: aviso en el tramo objetivo y fallo heurístico fuera de los límites duros.

    Solo se juzga prosa con al menos tres líneas útiles; las líneas menores que
    la mitad de la mediana se excluyen. Una mediana fuera de [minimo, maximo] —el
    tramo objetivo, 45–75 cpl por defecto— es aviso, igual que más de un 2 % de
    líneas fuera de los límites duros [duro_min, duro_max], que es el aviso por
    líneas extremas del control original. Una mediana fuera de los límites duros
    (40–85 cpl por defecto) sí es fallo heurístico. Una excepción se declara por
    página y bloque (índice desde 1 o texto inicial), con tipo y motivo, y solo
    puede levantar el fallo heurístico.
    """
    fichas: list[dict[str, Any]] = []
    fallos: list[dict[str, Any]] = []
    avisos: list[dict[str, Any]] = []
    excepciones_usadas: set[int] = set()
    juzgados: list[int] = []
    tipos: dict[str, int] = {}
    cortos: list[dict[str, Any]] = []
    excepciones = excepciones or []
    for bloque in bloques:
        tipo = _clasificar(bloque, mediana_minima)
        bloque.tipo = tipo
        tipos[tipo] = tipos.get(tipo, 0) + 1
        longitudes = bloque.longitud
        mediana = bloque.mediana
        utiles = [n for n in longitudes if n >= 0.5 * mediana]
        mediana_util = _percentil(utiles, 0.5)
        p10 = _percentil(utiles, 0.1)
        p90 = _percentil(utiles, 0.9)
        fuera_duro = [n for n in utiles if n < duro_min or n > duro_max]
        ficha: dict[str, Any] = {
            "pagina": bloque.pagina,
            "indice": bloque.indice,
            "inicio": bloque.texto[:100],
            "tipo": tipo,
            "caja": list(bloque.caja),
            "lineas": len(longitudes),
            "lineas_utiles": len(utiles),
            "mediana": round(mediana, 1),
            "mediana_util": round(mediana_util, 1),
            "p10": round(p10, 1),
            "p90": round(p90, 1),
            "fuera_de_duro": len(fuera_duro),
        }
        if tipo == "prosa" and len(utiles) >= 3:
            juzgados.extend(utiles)
            ficha["juzgado"] = True
            lineas_extremas = len(fuera_duro) > max(0, 0.02 * len(utiles))
            if mediana_util < duro_min or mediana_util > duro_max:
                ficha["juicio"] = "fallo heurístico"
                fallos.append(ficha)
                for indice, excepcion in enumerate(excepciones):
                    if indice not in excepciones_usadas and excepcion["pagina"] == bloque.pagina and _coincide_bloque(bloque, excepcion["bloque"]):
                        ficha["juicio"] = "excepción declarada"
                        ficha["excepcion"] = {
                            "tipo": excepcion["tipo"],
                            "motivo": excepcion["motivo"],
                            "bloque": excepcion["bloque"],
                        }
                        excepciones_usadas.add(indice)
                        fallos.pop()
                        break
            elif lineas_extremas or not (minimo <= mediana_util <= maximo):
                ficha["juicio"] = "aviso"
                avisos.append(ficha)
            else:
                ficha["juicio"] = "ok"
        else:
            ficha["juzgado"] = False
            ficha["juicio"] = "no-juzgado"
            if tipo == "prosa":
                cortos.append(ficha)
        fichas.append(ficha)

    no_aplicadas = [
        {"pagina": ex["pagina"], "bloque": ex["bloque"], "tipo": ex["tipo"], "motivo": ex["motivo"]}
        for indice, ex in enumerate(excepciones)
        if indice not in excepciones_usadas
    ]
    resumen: dict[str, Any] = {
        "bloques": fichas,
        "tipos": tipos,
        "juzgados": sum(1 for ficha in fichas if ficha["juzgado"]),
        "prosa_corta": len(cortos),
        "rango": [minimo, maximo],
        "rango_duro": [duro_min, duro_max],
        "avisos": len(avisos),
        "excepciones_declaradas": len(excepciones_usadas),
        "excepciones_no_aplicadas": no_aplicadas,
        "nota": (
            "heurística: solo se juzga la mediana de bloques de prosa (≥3 líneas y "
            + str(int(mediana_minima))
            + " caracteres); tablas, listas y rótulos quedan fuera. "
            "Se excluyen finales de párrafo (líneas menores que la mitad de la mediana). "
            "Entre el tramo objetivo y los límites duros, o con más de un 2 % de líneas "
            "fuera de los límites duros, el bloque queda en aviso. Una mediana fuera de "
            "los límites duros es fallo heurístico; la excepción declarada solo lo "
            "identifica y no altera el juicio de los demás bloques."
        ),
    }
    if juzgados:
        resumen["global"] = {
            "mediana": round(_percentil(juzgados, 0.5), 1),
            "p10": round(_percentil(juzgados, 0.1), 1),
            "p90": round(_percentil(juzgados, 0.9), 1),
            "lineas": len(juzgados),
        }
    if not fichas:
        return Resultado("medida", "Caracteres por línea", "no-aplica", "sin bloques de texto", resumen)
    if not juzgados:
        desglose = ", ".join(f"{k}: {v}" for k, v in sorted(tipos.items()))
        detalle = f"{_plural(len(fichas), 'bloque', 'bloques')} ({desglose}); ninguno de prosa con tres líneas útiles"
        if cortos:
            detalle += f"; {_plural(len(cortos), 'bloque de prosa corto', 'bloques de prosa cortos')} sin juzgar"
        estado = "aviso" if no_aplicadas else "no-aplica"
        if no_aplicadas:
            detalle += f"; {len(no_aplicadas)} excepción(es) no aplicada(s)"
        return Resultado("medida", "Caracteres por línea", estado, detalle, resumen)
    if fallos:
        peor = fallos[0]
        detalle = (
            f"{_plural(len(fallos), 'bloque de prosa', 'bloques de prosa')} fuera de la medida: "
            f"pág. {peor['pagina']} bloque {peor['indice']} ({_mm(peor['caja'][0])} mm, {_mm(peor['caja'][1])} mm), "
            f"mediana {peor['mediana_util']} cpl (objetivo {minimo}–{maximo}; p10 {peor['p10']}, p90 {peor['p90']}; "
            f"{_plural(peor['fuera_de_duro'], 'línea', 'líneas')} fuera de límites duros {duro_min}–{duro_max} "
            f"en {peor['lineas_utiles']} útiles)."
        )
        return Resultado("medida", "Caracteres por línea", "fallo heurístico", detalle, resumen)
    if avisos:
        peor = avisos[0]
        detalle = (
            f"{_plural(len(avisos), 'bloque en aviso', 'bloques en aviso')}: "
            f"pág. {peor['pagina']} bloque {peor['indice']} con mediana {peor['mediana_util']} cpl "
            f"(tramo objetivo {minimo}–{maximo}; "
            f"{_plural(peor['fuera_de_duro'], 'línea', 'líneas')} fuera de {duro_min}–{duro_max} "
            f"en {peor['lineas_utiles']} útiles)."
        )
        if excepciones_usadas:
            detalle += f" {len(excepciones_usadas)} bloque(s) con excepción declarada."
        if no_aplicadas:
            detalle += f" {len(no_aplicadas)} excepción(es) no aplicada(s)."
        return Resultado("medida", "Caracteres por línea", "aviso", detalle, resumen)
    if excepciones_usadas:
        detalle = f"{len(excepciones_usadas)} bloque(s) con excepción declarada; el resto dentro de {minimo}–{maximo} cpl"
        if no_aplicadas:
            detalle += f"; {len(no_aplicadas)} excepción(es) no aplicada(s)"
        return Resultado("medida", "Caracteres por línea", "excepción declarada", detalle, resumen)
    if no_aplicadas:
        return Resultado("medida", "Caracteres por línea", "aviso", f"{len(no_aplicadas)} excepción(es) no aplicada(s)", resumen)
    detalle = (
        f"{resumen['juzgados']} bloques de prosa dentro de {minimo}–{maximo}: mediana global "
        f"{resumen['global']['mediana']} (p10 {resumen['global']['p10']}, "
        f"p90 {resumen['global']['p90']})"
    )
    return Resultado("medida", "Caracteres por línea", "ok", detalle, resumen)


def _bordes_alcanzados(caja: pymupdf.Rect, corte: pymupdf.Rect) -> set[str]:
    """Bordes del corte a los que la caja llega (los cruza o toca su línea).

    Alcanzar no es acercarse: la comparación es exacta, sin tolerancia, así que
    un elemento a una décima de punto por dentro del corte no es sangre en ese
    borde. Un rectángulo que cubre la página entera de un PDF sin sangrado
    declarado (TrimBox igual a MediaBox) alcanza los cuatro bordes.
    """
    bordes: set[str] = set()
    if caja.x0 <= corte.x0 <= caja.x1:
        bordes.add("izquierdo")
    if caja.x1 >= corte.x1 >= caja.x0:
        bordes.add("derecho")
    if caja.y0 <= corte.y0 <= caja.y1:
        bordes.add("superior")
    if caja.y1 >= corte.y1 >= caja.y0:
        bordes.add("inferior")
    return bordes


def comprobar_fuera_de_caja(doc: pymupdf.Document, margen_seguro_mm: float, tolerancia_mm: float) -> Resultado:
    """Texto y dibujos fuera del área segura, con una única exención de sangre.

    Reglas, idénticas para prosa y para dibujo vectorial:

    - El texto nunca se considera a sangre. Si sale del corte, o cae en la
      franja de seguridad, es fallo.
    - Un dibujo vectorial solo es sangre en los bordes del corte que alcanza
      (los cruza o llega exactamente a ellos). En los bordes que no alcanza
      tiene que respetar el área segura: un filete de lado a lado a 1 mm del
      borde superior es fallo por ese borde aunque toque los lados. Además, el
      dibujo entero tiene que quedar dentro del sangrado.
    - Las imágenes se admiten dentro del corte más el sangrado.
    - `--tolerancia` solo se aplica al tamaño de página y a la comparación de
      cajas; no exime de la franja de seguridad.
    """
    tol = tolerancia_mm * PT_POR_MM
    seguro = margen_seguro_mm * PT_POR_MM
    incidencias: list[dict[str, Any]] = []
    for pagina in doc:
        corte, sangrado = _caja_pagina(pagina)
        area_segura = pymupdf.Rect(corte.x0 + seguro, corte.y0 + seguro, corte.x1 - seguro, corte.y1 - seguro)
        for bloque in pagina.get_text("dict").get("blocks", []):
            if bloque.get("type") != 0:
                continue
            caja = pymupdf.Rect(bloque["bbox"])
            texto = " ".join(
                tramo.get("text", "") for linea in bloque.get("lines", []) for tramo in linea.get("spans", [])
            ).strip()
            if not texto:
                continue
            # El texto se comprueba sin tolerancia: la tolerancia solo sirve
            # para medir; con margen seguro 0 dejaría pasar texto fuera del corte.
            if not _dentro(caja, corte, 0):
                causa = "texto fuera del corte"
            elif not _dentro(caja, area_segura, 0):
                causa = "texto en la franja de seguridad"
            else:
                continue
            incidencias.append({"pagina": _numero(pagina), "tipo": causa, "texto": texto[:60], "caja": [round(v, 1) for v in caja]})
        for dibujo in pagina.get_drawings():
            caja = pymupdf.Rect(dibujo["rect"])
            if not _dentro(caja, sangrado, tol):
                causa = "dibujo fuera del corte+sangrado"
            else:
                alcanzados = _bordes_alcanzados(caja, corte)
                fuera = []
                if "izquierdo" not in alcanzados and caja.x0 < area_segura.x0 - tol:
                    fuera.append("izquierdo")
                if "derecho" not in alcanzados and caja.x1 > area_segura.x1 + tol:
                    fuera.append("derecho")
                if "superior" not in alcanzados and caja.y0 < area_segura.y0 - tol:
                    fuera.append("superior")
                if "inferior" not in alcanzados and caja.y1 > area_segura.y1 + tol:
                    fuera.append("inferior")
                if not fuera:
                    continue
                causa = "dibujo en la franja de seguridad (" + " y ".join(fuera) + ")"
            incidencias.append({"pagina": _numero(pagina), "tipo": causa, "caja": [round(v, 1) for v in caja]})
        for info in pagina.get_image_info():
            caja = pymupdf.Rect(info["bbox"])
            if not _dentro(caja, sangrado, tol):
                incidencias.append({"pagina": _numero(pagina), "tipo": "imagen fuera del corte+sangrado", "caja": [round(v, 1) for v in caja]})
    comprobado = (
        f"texto: dentro del corte y del área segura de {margen_seguro_mm:g} mm, sin exención de sangre; "
        f"dibujos vectoriales: a sangre solo en los bordes del corte que alcanzan (sin tolerancia), dentro del "
        f"sangrado y, en los demás bordes, dentro del área segura; "
        f"imágenes: dentro del corte+sangrado; tolerancia de medida {tolerancia_mm:g} mm"
    )
    if incidencias:
        detalle = f"{_plural(len(incidencias), 'elemento', 'elementos')}: " + "; ".join(
            f"pág. {i['pagina']} {i['tipo']}" for i in incidencias[:5]
        )
        return Resultado("caja", "Franja de seguridad y sangrado", "fallo", f"{detalle}. Comprobado: {comprobado}.", {"incidencias": incidencias, "comprobado": comprobado})
    return Resultado("caja", "Franja de seguridad y sangrado", "ok", f"Sin incidencias. Comprobado: {comprobado}.", {"comprobado": comprobado})


def _dentro(caja: pymupdf.Rect, contenedor: pymupdf.Rect, tol: float) -> bool:
    return (
        caja.x0 >= contenedor.x0 - tol
        and caja.y0 >= contenedor.y0 - tol
        and caja.x1 <= contenedor.x1 + tol
        and caja.y1 <= contenedor.y1 + tol
    )


# ---------------------------------------------------------------------------
# Salida
# ---------------------------------------------------------------------------

def _icono(estado: str) -> str:
    return {
        "ok": "[ok]",
        "aviso": "[aviso]",
        "fallo": "[FALLO]",
        "fallo heurístico": "[FALLO HEURÍSTICO]",
        "excepción declarada": "[EXCEPCIÓN DECLARADA]",
        "no-aplica": "[—]",
    }.get(estado, "")


def informe_markdown(ruta: Path, resultados: list[Resultado]) -> str:
    resumen = {e: sum(1 for r in resultados if r.estado == e) for e in ESTADOS}
    excepciones_bloque = sum(
        1
        for r in resultados
        for ficha in r.datos.get("bloques", [])
        if ficha.get("juicio") == "excepción declarada"
    )
    lineas = [
        f"# Control de PDF — {ruta.name}",
        "",
        f"`{ruta}`",
        "",
        f"**Resultado:** {_plural(resumen['fallo'], 'fallo', 'fallos')}, "
        f"{_plural(resumen['fallo heurístico'], 'fallo heurístico', 'fallos heurísticos')}, "
        f"{_plural(resumen['excepción declarada'], 'excepción declarada', 'excepciones declaradas')}, "
        f"{_plural(resumen['aviso'], 'aviso', 'avisos')}, "
        f"{resumen['ok']} correctos, {resumen['no-aplica']} no aplicables; "
        f"{_plural(excepciones_bloque, 'excepción de bloque declarada', 'excepciones de bloque declaradas')}.",
        "",
        "| Control | Estado | Detalle |",
        "|---|---|---|",
    ]
    for r in resultados:
        detalle = r.detalle.replace("|", "\\|")
        lineas.append(f"| {r.nombre} | {_icono(r.estado)} | {detalle} |")
        for ficha in r.datos.get("bloques", []):
            estado_bloque = ficha.get("juicio")
            if estado_bloque not in ("fallo heurístico", "excepción declarada"):
                continue
            inicio = str(ficha.get("inicio", "")).replace("|", "\\|").replace("\n", " ")
            detalle_bloque = (
                f"pág. {ficha['pagina']}, bloque {ficha['indice']}; mediana {ficha['mediana_util']} cpl; "
                f"«{inicio}»"
            )
            if estado_bloque == "excepción declarada":
                excepcion = ficha["excepcion"]
                detalle_bloque += f"; {excepcion['tipo']}: {excepcion['motivo']}"
            lineas.append(f"| ↳ {r.nombre} | {_icono(estado_bloque)} | {detalle_bloque} |")
        for excepcion in r.datos.get("excepciones_no_aplicadas", []):
            motivo = str(excepcion["motivo"]).replace("|", "\\|")
            lineas.append(
                f"| ↳ {r.nombre} | [aviso] | excepción no aplicada en pág. {excepcion['pagina']}, "
                f"bloque {excepcion['bloque']}; {excepcion['tipo']}: {motivo} |"
            )
    return "\n".join(lineas) + "\n"


def informe_json(ruta: Path, resultados: list[Resultado]) -> dict[str, Any]:
    resumen = {e: sum(1 for r in resultados if r.estado == e) for e in ESTADOS}
    resumen_bloques = {
        estado: sum(
            1
            for r in resultados
            for ficha in r.datos.get("bloques", [])
            if ficha.get("juicio") == estado
        )
        for estado in ("fallo heurístico", "excepción declarada")
    }
    return {
        "pdf": str(ruta),
        "resumen": resumen,
        "resumen_bloques_medida": resumen_bloques,
        "salida": 1 if resumen["fallo"] or resumen["fallo heurístico"] else 0,
        "resultados": [
            {"id": r.id, "nombre": r.nombre, "estado": r.estado, "detalle": r.detalle, "datos": r.datos}
            for r in resultados
        ],
    }


def _leer_nombres(ruta: Path | None) -> list[str]:
    if ruta is None:
        return []
    texto = ruta.read_text(encoding="utf-8")
    return [linea.strip() for linea in texto.splitlines() if linea.strip() and not linea.startswith("#")]

def _leer_excepciones(ruta: Path | None) -> list[dict[str, Any]]:
    """Excepciones del control heurístico, en JSON o en YAML.

    Se intenta JSON y, si no lo es, YAML: así un archivo que empieza por `[` no
    se rechaza con un error de JSON engañoso. `bloque` es un índice (empieza en
    1) cuando llega como número; si llega como texto, se compara con el inicio
    del bloque. Para citar un bloque cuyo texto empieza por dígitos se escribe
    el texto entre comillas junto a alguna letra, o se usa el índice.
    """
    if ruta is None:
        return []
    texto = ruta.read_text(encoding="utf-8-sig")
    try:
        dato = json.loads(texto)
    except json.JSONDecodeError as error_json:
        try:
            dato = configuracion.leer_yaml(texto)
        except ValueError as error_yaml:
            raise ValueError(
                f"el archivo de excepciones no es JSON ni YAML válido ({error_json}; {error_yaml})"
            ) from error_yaml
    if not isinstance(dato, list):
        raise ValueError("el archivo de excepciones debe contener una lista YAML o JSON")
    salida = []
    for indice, elemento in enumerate(dato, 1):
        if not isinstance(elemento, dict):
            raise ValueError(f"excepción {indice}: se esperaba un mapa")
        campos = {"pagina", "control", "bloque", "tipo", "motivo"}
        if set(elemento) != campos:
            raise ValueError(f"excepción {indice}: los campos obligatorios son pagina, control, bloque, tipo y motivo")
        if not isinstance(elemento["pagina"], int) or isinstance(elemento["pagina"], bool) or elemento["pagina"] < 1:
            raise ValueError(f"excepción {indice}: pagina debe ser un entero positivo")
        if elemento["control"] != "medida":
            raise ValueError(f"excepción {indice}: solo se permiten excepciones del control heurístico medida")
        if not isinstance(elemento["bloque"], (str, int)) or not str(elemento["bloque"]).strip():
            raise ValueError(f"excepción {indice}: bloque debe ser texto inicial o índice positivo")
        if isinstance(elemento["bloque"], int) and (isinstance(elemento["bloque"], bool) or elemento["bloque"] < 1):
            raise ValueError(f"excepción {indice}: el índice de bloque empieza en 1")
        if isinstance(elemento["bloque"], str) and elemento["bloque"].strip().isdigit() and int(elemento["bloque"].strip()) < 1:
            raise ValueError(f"excepción {indice}: el índice de bloque empieza en 1")
        if elemento["tipo"] not in ("cita", "pie", "titular", "otro"):
            raise ValueError(f"excepción {indice}: tipo debe ser cita, pie, titular u otro")
        if not isinstance(elemento["motivo"], str) or not elemento["motivo"].strip():
            raise ValueError(f"excepción {indice}: motivo debe ser texto no vacío")
        salida.append(dict(elemento))
    return salida


def _tamanos(valor: str | None) -> list[tuple[float, float]]:
    if not valor:
        return []
    salida: list[tuple[float, float]] = []
    for trozo in valor.split(","):
        trozo = trozo.strip().lower().replace("×", "x")
        if not trozo:
            continue
        ancho, alto = trozo.split("x")
        salida.append((float(ancho), float(alto)))
    return salida


CASOS_TELEFONO_POSITIVOS = [
    "+1 202 555 0143",
    "202 555 0100",
    "202.555.0111",
    "+1 303-555-0124",
    "202 555 0135",
    "202-555-0198",
]
CASOS_TELEFONO_NEGATIVOS = [
    "2024-07-19",
    "19.07.2024",
    "07/19/2024",
    "2024-07-19 10:30",
    "1.234,56",
    "12 000",
    "1234 5678",
    "3.1416",
]
CASOS_CORREO = ["persona.de.prueba@example.com", "nombre.apellido+etiqueta@sub.dominio.es"]
CASOS_URL = ["https://example.com/porfolio", "www.ejemplo.org/ruta?x=1"]


def autoprueba() -> int:
    """Autoprueba de los patrones de datos personales, con casos conocidos."""
    fallos: list[str] = []
    for caso in CASOS_TELEFONO_POSITIVOS:
        candidatos = [c for c in RE_TELEFONO.findall(caso) if _es_telefono(c)]
        if not candidatos:
            fallos.append(f"teléfono positivo no detectado: {caso}")
    for caso in CASOS_TELEFONO_NEGATIVOS:
        candidatos = [c for c in RE_TELEFONO.findall(caso) if _es_telefono(c)]
        if candidatos:
            fallos.append(f"falso teléfono en «{caso}»: {candidatos}")
    for caso in CASOS_CORREO:
        if not RE_EMAIL.findall(caso):
            fallos.append(f"correo no detectado: {caso}")
    for caso in CASOS_URL:
        encontrados = [_limpiar(c) for c in RE_URL.findall(caso)]
        if not encontrados:
            fallos.append(f"URL no detectada: {caso}")
    print("# Autoprueba de patrones")
    print()
    print(f"- teléfonos positivos: {len(CASOS_TELEFONO_POSITIVOS)}; negativos (fechas y cifras): {len(CASOS_TELEFONO_NEGATIVOS)}")
    print(f"- correos: {len(CASOS_CORREO)}; URL: {len(CASOS_URL)}")
    if fallos:
        print()
        for fallo in fallos:
            print(f"- [FALLO] {fallo}")
        return 1
    print()
    print("- [ok] todos los casos se comportan como se espera")
    return 0


def analizar(args: argparse.Namespace) -> tuple[list[Resultado], pymupdf.Document]:
    ruta = Path(args.pdf)
    doc = pymupdf.open(str(ruta))
    config = getattr(args, "_configuracion", None) or configuracion.cargar_configuracion(args.config)
    excepciones = getattr(args, "_excepciones", None)
    if excepciones is None:
        excepciones = _leer_excepciones(Path(args.excepciones) if args.excepciones else None)
    fuentes = _recoger_fuentes(doc)
    resultados: list[Resultado] = [
        comprobar_paginas(doc, args.paginas, args.paginas_min, args.paginas_max),
        comprobar_tamanos(doc, _tamanos(args.tamano), args.tolerancia),
    ]
    resultados.extend(
        comprobar_fuentes(doc, fuentes, configuracion.ficheros_fuente(config), configuracion.caracteres_requeridos(config))
    )
    resultados.append(comprobar_imagenes(doc, args.ppi_objetivo, args.ppi_minimo, args.copias_trabajo))
    resultados.append(comprobar_tamano_archivo(ruta, args.max_mb))
    resultados.append(comprobar_metadatos(doc, args.exigir_metadatos))
    if args.anonimo:
        resultados.append(comprobar_anonimato(doc, _leer_nombres(Path(args.nombres) if args.nombres else None)))
    resultados.append(
        comprobar_medida(
            _bloques_texto(doc),
            minimo=args.cpl_min,
            maximo=args.cpl_max,
            duro_min=args.cpl_duro_min,
            duro_max=args.cpl_duro_max,
            excepciones=excepciones,
        )
    )
    resultados.append(comprobar_fuera_de_caja(doc, args.margen_seguro, args.tolerancia))
    return resultados, doc


def construir_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="control_pdf",
        description="Control de calidad de un PDF editorial (páginas, fuentes, imágenes, medida, caja, metadatos).",
    )
    p.add_argument(
        "--config",
        default=None,
        help=(
            "configuración del proyecto; sin esta opción se usa maquetacion/config.md si existe y, "
            "si no, los valores predeterminados. Una ruta explícita que no exista es un error. "
            "Las fuentes para la cobertura salen de `carpeta_fuentes` y de `sistema`; no hay "
            "opción --fuentes"
        ),
    )
    p.add_argument("pdf", nargs="?", help="PDF a comprobar (no hace falta con --autoprueba)")
    p.add_argument("--paginas", type=int, default=None, help="número de páginas esperado (exacto)")
    p.add_argument("--paginas-min", type=int, default=None, help="mínimo de páginas aceptado")
    p.add_argument("--paginas-max", type=int, default=None, help="máximo de páginas aceptado")
    p.add_argument("--tamano", default=None, help="tamaño de corte esperado en mm, p. ej. «210x297»; admite lista con comas")
    p.add_argument(
        "--tolerancia",
        default=0.5,
        type=float,
        help="tolerancia en mm para el tamaño de página y la comparación de cajas (por defecto 0.5); no exime de la franja de seguridad",
    )
    p.add_argument(
        "--excepciones",
        default=None,
        help=(
            "YAML o JSON con excepciones por bloque del control heurístico medida; se intenta JSON y, "
            "si no lo es, YAML"
        ),
    )
    p.add_argument("--ppi-objetivo", type=float, default=300.0, help="ppp objetivo de las imágenes colocadas (por defecto 300)")
    p.add_argument("--ppi-minimo", type=float, default=200.0, help="mínimo duro de ppp para las imágenes (por defecto 200)")
    p.add_argument(
        "--copias-trabajo",
        action="store_true",
        help="las imágenes son copias de trabajo reducidas: la resolución no se juzga; se informa del lado corto que necesitará cada archivo final",
    )
    p.add_argument("--max-mb", type=float, default=None, help="límite de peso en MB decimales (1 MB = 1 000 000 bytes)")
    p.add_argument(
        "--exigir-metadatos",
        action="store_true",
        help="falla si falta el título o el creador del PDF; sin esta opción, solo avisa",
    )
    p.add_argument(
        "--anonimo",
        action="store_true",
        help=(
            "busca nombres, correo, URL y teléfono en texto visible, metadatos, XMP (texto y atributos), "
            "anotaciones, enlaces, formularios y contenido de adjuntos. Los nombres y el texto se comparan "
            "sin diacríticos, sin formas de compatibilidad y sin invisibles, con espacios/saltos/guiones/"
            "puntuación colapsados, así que «Ana López» coincide con «ANA LOPEZ». Los adjuntos se leen en "
            "UTF-8, UTF-16, UTF-32, Latin-1 y sin bytes NUL; los PDF adjuntos se abren hasta 3 niveles. "
            "Cualquier adjunto deja aviso como mínimo; un dato personal es fallo. No se revisa texto "
            "dentro de imágenes ni contenido comprimido o cifrado de adjuntos."
        ),
    )
    p.add_argument("--nombres", default=None, help="fichero de nombres personales, uno por línea")
    p.add_argument(
        "--cpl-min",
        type=int,
        default=45,
        help="mínimo del tramo objetivo de la mediana cpl por bloque (por defecto 45); por debajo del objetivo y por encima de --cpl-duro-min hay aviso",
    )
    p.add_argument(
        "--cpl-max",
        type=int,
        default=75,
        help="máximo del tramo objetivo de la mediana cpl por bloque (por defecto 75); por encima del objetivo y por debajo de --cpl-duro-max hay aviso",
    )
    p.add_argument("--cpl-duro-min", type=int, default=40, help="límite duro inferior de la mediana (por defecto 40); por debajo es fallo heurístico")
    p.add_argument("--cpl-duro-max", type=int, default=85, help="límite duro superior de la mediana (por defecto 85); por encima es fallo heurístico")
    p.add_argument("--margen-seguro", type=float, default=3.0, help="área segura desde el corte, en mm (por defecto 3)")
    p.add_argument("--json", default=None, help="escribir el informe JSON en esta ruta")
    p.add_argument("--md", default=None, help="escribir el informe Markdown en esta ruta")
    p.add_argument("--json-breve", action="store_true", help="omitir los datos completos en el JSON")
    p.add_argument(
        "--autoprueba",
        action="store_true",
        help="comprueba los patrones de teléfono, correo y URL con casos conocidos y termina",
    )
    return p


def main(argv: Sequence[str] | None = None) -> int:
    p = construir_parser()
    args = p.parse_args(argv)
    if args.autoprueba:
        return autoprueba()
    if not args.pdf:
        p.error("falta el PDF a comprobar (o use --autoprueba)")
    ruta = Path(args.pdf)
    if not ruta.is_file():
        p.error(f"no existe el PDF: {ruta}")
    if args.tamano:
        try:
            _tamanos(args.tamano)
        except Exception:
            p.error("--tamano debe tener la forma 210x297 (mm)")
    if args.nombres and not Path(args.nombres).is_file():
        p.error(f"no existe el fichero de nombres: {args.nombres}")
    ruta_excepciones = Path(args.excepciones) if args.excepciones else None
    if ruta_excepciones and not ruta_excepciones.is_file():
        p.error(f"no existe el fichero de excepciones: {ruta_excepciones}")
    try:
        args._configuracion = configuracion.cargar_configuracion(args.config)
        args._excepciones = _leer_excepciones(ruta_excepciones)
    except (OSError, ValueError) as exc:
        p.error(f"configuración o excepciones no válidas: {exc}")
    try:
        resultados, doc = analizar(args)
    except Exception as exc:  # PDF corrupto o ilegible
        sys.stderr.write(f"control_pdf: no se pudo analizar {ruta}: {exc}\n")
        return 1
    md = informe_markdown(ruta, resultados)
    datos = informe_json(ruta, resultados)
    if args.json_breve:
        for r in datos["resultados"]:
            r["datos"] = {}
    if args.md:
        Path(args.md).write_text(md, encoding="utf-8")
    if args.json:
        Path(args.json).write_text(json.dumps(datos, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(md)
    doc.close()
    return 1 if datos["resumen"]["fallo"] or datos["resumen"]["fallo heurístico"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
