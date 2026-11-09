"""Utilidades comunes de las pruebas: rutas del repo, ejecución y materiales.

Todo lo que necesitan las pruebas se genera en un directorio temporal: no se
lee ningún archivo de fuera del repositorio. Las fuentes se construyen con
fontTools para no depender de fuentes instaladas en la máquina.
"""

from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

import pymupdf

REPO = Path(__file__).resolve().parent.parent
SCRIPTS = REPO / "skills" / "maquetacion-editorial" / "scripts"
CONTROL = SCRIPTS / "control_pdf.py"
CONTACTOS = SCRIPTS / "hoja_contactos.py"
CATALOGO = SCRIPTS / "catalogo_fuentes.py"
LIBRERIA = REPO / "skills" / "maquetacion-editorial" / "typst" / "editorial.typ"
FIXTURES = Path(__file__).resolve().parent / "fixtures"


def ejecutar(comando, cwd: Path, env=None, stdout=None):
    """Ejecuta un comando sin dejar `__pycache__` en el árbol."""
    entorno = os.environ.copy()
    entorno["PYTHONDONTWRITEBYTECODE"] = "1"
    if env:
        entorno.update(env)
    return subprocess.run(
        comando,
        cwd=cwd,
        env=entorno,
        stdout=subprocess.PIPE if stdout is None else stdout,
        stderr=subprocess.PIPE,
        check=False,
    )


def crear_config(raiz: Path, *, idioma="es", sistema=False, carpeta="null", campos="", caracteres="{}") -> Path:
    destino = raiz / "maquetacion" / "config.md"
    destino.parent.mkdir(parents=True, exist_ok=True)
    idiomas = "[es, en]" if idioma == "es-en" else f"[{idioma}]"
    texto = (
        "---\n"
        f"carpeta_fuentes: {carpeta}\n"
        f"sistema: {'sí' if sistema else 'no'}\n"
        f"idiomas: {idiomas}\n"
        "preferidas: []\n"
        "evitar: []\n"
        "licencias: {}\n"
        f"caracteres_extra: {caracteres}\n"
        'version: "_v01"\n'
        "nombres_sin_acentos_ni_espacios: sí\n"
        f"{campos}"
        "---\n"
    )
    destino.write_text(texto, encoding="utf-8")
    return destino


def carpeta_config(ruta: Path) -> str:
    """Valor de `carpeta_fuentes` para una ruta, tal como lo escribe la config."""
    return json.dumps(str(ruta).replace("\\", "/"))


def informe(ruta: Path) -> dict:
    return json.loads(ruta.read_text(encoding="utf-8"))


def resultado(datos: dict, ident: str) -> dict:
    return next(r for r in datos["resultados"] if r["id"] == ident)


def escribir_pdf_texto(ruta: Path, textos: list[tuple[int, str]]) -> None:
    doc = pymupdf.open()
    for _ in textos:
        doc.new_page(width=595, height=842)
    for indice, texto in enumerate(textos):
        pagina, contenido = texto
        doc[pagina - 1].insert_text((72, 72), contenido, fontsize=12)
    doc.save(ruta)
    doc.close()


def pdf_vacio(ruta: Path) -> Path:
    doc = pymupdf.open()
    doc.new_page(width=595, height=842)
    doc.save(ruta)
    doc.close()
    return ruta


def pdf_con_corte(ruta: Path, dibujar) -> None:
    """Una página con TrimBox interior de 9 pt y BleedBox = MediaBox.

    Sin margen de corte declarado no hay sangre posible: hace falta un corte
    más pequeño que el sangrado para que un dibujo pueda cruzarlo.
    """
    doc = pymupdf.open()
    pagina = doc.new_page(width=595, height=842)
    doc.xref_set_key(pagina.xref, "TrimBox", "[9 9 586 833]")
    dibujar(pagina)
    doc.save(ruta)
    doc.close()


UPM = 2048

# Todo el juego que exigen los idiomas de las pruebas, más ASCII: así una
# fuente sintética puede ser apta para texto sin depender de fuente alguna.
_CARACTERES = set(chr(codigo) for codigo in range(0x20, 0x7F)) | set("¡«»¿ÁÉÍÑÓÚÜáéíñóúü–—‘’“”…")


def _caja(x0: int, y0: int, x1: int, y1: int):
    from fontTools.pens.ttGlyphPen import TTGlyphPen

    lapiz = TTGlyphPen(None)
    lapiz.moveTo((x0, y0))
    lapiz.lineTo((x0, y1))
    lapiz.lineTo((x1, y1))
    lapiz.lineTo((x1, y0))
    lapiz.closePath()
    return lapiz.glyph()


def construir_fuente(destino: Path, *, familia: str = "Prueba", estilo: str = "Regular", fs_type: int = 0) -> Path:
    """Construye una TrueType mínima, con cifras, ñ y acentos, en `destino`.

    El dibujo es una caja por glifo: basta para medir cobertura, cmap, OS/2,
    métricas y clases de cifras. Las alturas de x y de mayúscula quedan
    declaradas en OS/2 para que el catálogo no tenga que tomarlas del contorno
    salvo que la prueba ponga esos campos a cero.
    """
    from fontTools import agl
    from fontTools.fontBuilder import FontBuilder

    glifos = {".notdef": _caja(50, 0, 550, 700)}
    avances = {".notdef": 600}
    cmap: dict[int, str] = {}
    for caracter in sorted(_CARACTERES):
        codigo = ord(caracter)
        nombre = "space" if caracter == " " else agl.UV2AGL.get(codigo, f"uni{codigo:04X}")
        if nombre in glifos:
            continue
        glifos[nombre] = _caja(100, 0, 700, 1200)
        avances[nombre] = 1000
        cmap[codigo] = nombre
    for digito in "0123456789":
        nombre = agl.UV2AGL[ord(digito)]
        glifos[nombre] = _caja(100, 0, 700, 1400 if digito == "0" else 1200)
    glifos["x"] = _caja(100, 0, 700, 1024)
    glifos["H"] = _caja(100, 0, 700, 1536)

    constructor = FontBuilder(UPM, isTTF=True)
    constructor.setupGlyphOrder([".notdef"] + [nombre for nombre in glifos if nombre != ".notdef"])
    constructor.setupCharacterMap(cmap)
    constructor.setupGlyf(glifos)
    constructor.setupHorizontalMetrics({nombre: (avances[nombre], 100) for nombre in constructor.font.getGlyphOrder()})
    constructor.setupHorizontalHeader(ascent=1600, descent=-400)
    constructor.setupNameTable(
        {
            "familyName": familia,
            "styleName": estilo,
            "typographicFamily": familia,
            "typographicSubfamily": estilo,
            "fullName": f"{familia} {estilo}",
            "psName": f"{familia}-{estilo}",
        }
    )
    constructor.setupOS2(
        sTypoAscender=1600,
        sTypoDescender=-400,
        usWinAscent=1600,
        usWinDescent=400,
        sxHeight=1024,
        sCapHeight=1536,
        fsType=fs_type,
        achVendID="TEST",
    )
    constructor.setupPost()
    destino.parent.mkdir(parents=True, exist_ok=True)
    constructor.save(str(destino))
    return destino


def bloqueador(tmp_path: Path, nombre: str, modulo: str) -> dict:
    """Entorno que hace que un módulo no se pueda importar en un subproceso."""
    carpeta = tmp_path / nombre
    carpeta.mkdir()
    clase = "Missing" + modulo.replace(".", "")
    (carpeta / "sitecustomize.py").write_text(
        "import sys\n"
        f"class {clase}:\n"
        "    def find_spec(self, fullname, path=None, target=None):\n"
        f"        if fullname == {modulo!r} or fullname.startswith({modulo!r} + '.'):\n"
        f"            raise ModuleNotFoundError('No module named {modulo}')\n"
        f"sys.meta_path.insert(0, {clase}())\n",
        encoding="utf-8",
    )
    entorno = os.environ.copy()
    entorno["PYTHONPATH"] = str(carpeta) + os.pathsep + entorno.get("PYTHONPATH", "")
    return entorno


def construir_fuentes(raiz: Path) -> Path:
    """Tres caras de dos familias: una preferida y otra con Regular y cursiva."""
    construir_fuente(raiz / "prueba" / "Prueba-Regular.ttf")
    construir_fuente(raiz / "otra" / "Otra-Regular.ttf", familia="Otra")
    construir_fuente(raiz / "otra" / "Otra-Italic.ttf", familia="Otra", estilo="Italic")
    return raiz
