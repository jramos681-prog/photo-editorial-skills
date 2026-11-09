#!/usr/bin/env python3
"""Hoja de contactos de un PDF para revisión visual.

Renderiza cada página a PNG sin reescalarla, y monta hojas según la unidad de
lectura. Hay dos unidades y el modo las separa:

- `--modo pliegos` (por defecto): la unidad es el pliego, es decir, dos páginas
  contiguas del PDF pegadas como doble página, con la cubierta (página 1) sola.
- `--modo paginas`: la unidad es la página del PDF, cada una suelta.

En ambos casos una celda de la hoja es una unidad de lectura y el rótulo indica
qué página o páginas del PDF contiene; el resumen final informa del modo usado.
Los rótulos siguen el primer idioma de maquetacion/config.md y la tipografía se
resuelve entre las fuentes configuradas para el proyecto y las instaladas en el
sistema, empezando por la carpeta propia y por las familias `preferidas`.

`--por-hoja` distribuye las celdas entre hojas numeradas; `--columnas`, márgenes
y separación controlan su rejilla. La salida de consola se fuerza a UTF-8 para
que los rótulos y el resumen no dependan de la página de códigos del terminal.

Uso:
    python hoja_contactos.py documento.pdf --config maquetacion/config.md --modo pliegos

Código de salida: 0 correcto, 1 fallo de lectura, 2 uso o configuración no válida.
"""

from __future__ import annotations

import argparse
import logging
import math
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

import configuracion

try:
    import pymupdf
except ImportError:  # pragma: no cover - dependencia del entorno
    sys.stderr.write("hoja_contactos: falta PyMuPDF (import pymupdf)\n")
    raise SystemExit(2)

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:  # pragma: no cover - dependencia del entorno
    sys.stderr.write("hoja_contactos: falta Pillow; instálalo para generar PNG\n")
    raise SystemExit(2)

MM_A_PX = 25.4  # referencia: los márgenes se dan en mm y se convierten con los ppp


@dataclass
class Celda:
    """Una imagen de la hoja y su etiqueta."""

    imagen: Image.Image
    etiqueta: str


def renderizar_pagina(pagina: pymupdf.Page, ppi: int) -> Image.Image:
    """Una página del PDF como imagen RGB a los ppp indicados."""
    pix = pagina.get_pixmap(dpi=ppi, colorspace=pymupdf.csRGB, alpha=False)
    return Image.frombytes("RGB", (pix.width, pix.height), pix.samples)


def iterar_paginas(doc: pymupdf.Document, ppi: int):
    """Genera (número de página base 1, imagen) de una en una, sin acumular."""
    for pagina in doc:
        yield pagina.number + 1, renderizar_pagina(pagina, ppi)


def iterar_grupos(paginas, modo: str):
    """Genera grupos de (número, imagen) según el modo, consumiendo el iterador.

    En modo pliegos la primera página va sola (cubierta) y después se emparejan
    2–3, 4–5…; una última página impar queda sola.
    """
    if modo == "paginas":
        for numero, imagen in paginas:
            yield [(numero, imagen)]
        return
    pendiente: tuple[int, Image.Image] | None = None
    for numero, imagen in paginas:
        if numero == 1:
            yield [(numero, imagen)]
            continue
        if pendiente is None:
            pendiente = (numero, imagen)
        else:
            yield [pendiente, (numero, imagen)]
            pendiente = None
    if pendiente is not None:
        yield [pendiente]


def _clave(texto: str) -> str:
    return re.sub(r"\s+", " ", texto.casefold()).strip()


def _orden_rutas(config: dict) -> list[Path]:
    """Fuentes candidatas: primero la carpeta propia y, dentro de cada grupo, orden alfabético."""
    propia = configuracion.carpeta_fuentes(config)

    def orden(ruta: Path) -> tuple[int, str]:
        en_propia = propia is not None and ruta.is_relative_to(propia)
        return (0 if en_propia else 1, str(ruta).casefold())

    return sorted(configuracion.ficheros_fuente(config), key=orden)


def _letra_respaldo(tamano: int) -> ImageFont.ImageFont:
    try:
        return ImageFont.load_default(size=tamano)
    except TypeError:  # Pillow antiguo
        return ImageFont.load_default()


def fuente(tamano: int, config: dict, texto: str) -> ImageFont.ImageFont:
    """Fuente de los rótulos: mandan la carpeta propia y las familias `preferidas`.

    Entre las caras que cubren los caracteres de los rótulos se prefiere Regular
    antes que cursivas y decorativas, y la carpeta propia antes que el sistema.
    Sin `fontTools` no se puede comprobar la cobertura: se avisa por stderr y se
    toma la primera cara que Pillow pueda abrir, empezando por la carpeta propia.
    """
    logging.getLogger("fontTools").setLevel(logging.ERROR)
    requeridos = set(map(ord, texto))
    try:
        from fontTools.ttLib import TTCollection, TTFont
    except ImportError:
        TTCollection = TTFont = None
    propia = configuracion.carpeta_fuentes(config)
    rutas = _orden_rutas(config)
    if TTFont is None:
        sys.stderr.write(
            "hoja_contactos: falta fontTools; no se puede comprobar que la fuente de los rótulos "
            "cubra los caracteres. Se usa la primera fuente que Pillow abra, empezando por la "
            "carpeta propia.\n"
        )
        for ruta in rutas:
            try:
                return ImageFont.truetype(str(ruta), tamano)
            except Exception:
                continue
        return _letra_respaldo(tamano)
    preferidas = {_clave(nombre) for nombre in config["preferidas"]}
    candidatos: list[tuple[tuple[int, int, int, str, int], Path, int]] = []
    for ruta in rutas:
        coleccion = None
        try:
            if ruta.suffix.lower() == ".ttc":
                # Las caras comparten el lector de la colección: hay que mantenerla viva.
                coleccion = TTCollection(str(ruta), lazy=True)
                caras = list(coleccion.fonts)
            else:
                caras = [TTFont(str(ruta), lazy=True)]
        except Exception:
            continue
        en_propia = 0 if propia is not None and ruta.is_relative_to(propia) else 1
        try:
            for indice, fuente_tt in enumerate(caras):
                try:
                    cmap = fuente_tt.getBestCmap() or {}
                except Exception:
                    continue
                if not requeridos.issubset(cmap):
                    continue
                nombres: dict[int, str] = {}
                for ident in (1, 16, 17, 2):
                    try:
                        valor = fuente_tt["name"].getDebugName(ident)
                    except Exception:
                        valor = None
                    if valor:
                        nombres.setdefault(ident, valor)
                familia = nombres.get(16) or nombres.get(1) or ruta.stem
                subfamilia = (nombres.get(17) or nombres.get(2) or "").casefold()
                if subfamilia in ("regular", "book", "roman"):
                    prioridad = 0
                elif "italic" in subfamilia or "oblique" in subfamilia:
                    prioridad = 2
                else:
                    prioridad = 1
                clave_orden = (
                    0 if _clave(familia) in preferidas else 1,
                    en_propia,
                    prioridad,
                    str(ruta).casefold(),
                    indice,
                )
                candidatos.append((clave_orden, ruta, indice))
        finally:
            if coleccion is not None:
                try:
                    coleccion.close()
                except Exception:
                    pass
            else:
                for fuente_tt in caras:
                    try:
                        fuente_tt.close()
                    except Exception:
                        pass
    for _orden, ruta, indice in sorted(candidatos, key=lambda candidato: candidato[0]):
        try:
            return ImageFont.truetype(str(ruta), tamano, index=indice)
        except Exception:
            continue
    return _letra_respaldo(tamano)


def _px(mm: float, ppi: float) -> int:
    return max(0, int(round(mm / MM_A_PX * ppi)))


def montar_hoja(
    celdas: list[Celda],
    columnas: int,
    ppi: float,
    margen_mm: float,
    separacion_mm: float,
    alto_etiqueta_px: int,
    letra: ImageFont.ImageFont,
) -> Image.Image:
    """Compone una hoja con las celdas en rejilla, con etiqueta bajo cada una."""
    if not celdas:
        return Image.new("RGB", (1, 1), "white")
    ancho_celda = max(c.imagen.width for c in celdas)
    alto_celda = max(c.imagen.height for c in celdas)
    margen = _px(margen_mm, ppi)
    separacion = _px(separacion_mm, ppi)
    filas = math.ceil(len(celdas) / columnas)
    ancho = margen * 2 + columnas * ancho_celda + (columnas - 1) * separacion
    alto = margen * 2 + filas * (alto_celda + alto_etiqueta_px) + (filas - 1) * separacion
    hoja = Image.new("RGB", (ancho, alto), "white")
    dibujo = ImageDraw.Draw(hoja)
    for indice, celda in enumerate(celdas):
        col = indice % columnas
        fila = indice // columnas
        x = margen + col * (ancho_celda + separacion)
        y = margen + fila * (alto_celda + alto_etiqueta_px + separacion)
        dx = x + (ancho_celda - celda.imagen.width) // 2
        hoja.paste(celda.imagen, (dx, y))
        dibujo.rectangle(
            [dx, y, dx + celda.imagen.width - 1, y + celda.imagen.height - 1],
            outline=(190, 190, 190),
        )
        dibujo.text((x, y + alto_celda + 2), celda.etiqueta, fill=(90, 90, 90), font=letra)
    return hoja


def main(argv: Sequence[str] | None = None) -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass
    p = argparse.ArgumentParser(
        prog="hoja_contactos",
        description="Renderiza un PDF a PNG y monta hojas de contactos por pliegos o por páginas.",
    )
    p.add_argument("pdf", help="PDF de entrada")
    p.add_argument(
        "--config",
        default=None,
        help=(
            "configuración del proyecto; sin esta opción se usa maquetacion/config.md si existe y, "
            "si no, los valores predeterminados. Una ruta explícita que no exista es un error"
        ),
    )
    p.add_argument("--salida", default="contactos", help="directorio de salida (se crea si falta)")
    p.add_argument("--ppi", type=int, default=96, help="resolución de render en ppp, entero (por defecto 96)")
    p.add_argument(
        "--modo",
        choices=("pliegos", "paginas"),
        default="pliegos",
        help=(
            "unidad de lectura de cada celda: pliegos (doble página, con la cubierta sola; por "
            "defecto) o paginas (cada página del PDF suelta). Se informa del modo usado."
        ),
    )
    p.add_argument("--columnas", type=int, default=2, help="celdas por fila (por defecto 2)")
    p.add_argument(
        "--por-hoja",
        type=int,
        default=4,
        help="celdas por hoja (4 por defecto); las celdas sobrantes van a hojas numeradas",
    )
    p.add_argument("--margen-mm", type=float, default=8.0, help="margen de la hoja en mm (por defecto 8)")
    p.add_argument("--separacion-mm", type=float, default=6.0, help="separación entre celdas en mm (por defecto 6)")
    p.add_argument("--prefijo", default=None, help="prefijo de los PNG (por defecto, el nombre del PDF)")
    args = p.parse_args(argv)

    try:
        config = configuracion.cargar_configuracion(args.config)
        rotulos = configuracion.rotulos(config["idiomas"][0])
    except (OSError, ValueError) as exc:
        p.error(f"configuración no válida: {exc}")
    ruta = Path(args.pdf)
    if not ruta.is_file():
        p.error(f"no existe el PDF: {ruta}")
    if args.ppi <= 0 or args.columnas <= 0:
        p.error("--ppi y --columnas deben ser positivos")
    try:
        doc = pymupdf.open(str(ruta))
    except Exception as exc:
        sys.stderr.write(f"hoja_contactos: no se pudo abrir {ruta}: {exc}\n")
        return 1
    if doc.page_count == 0:
        sys.stderr.write(f"hoja_contactos: {ruta} no tiene páginas\n")
        doc.close()
        return 1

    salida = Path(args.salida)
    salida.mkdir(parents=True, exist_ok=True)
    prefijo = args.prefijo or ruta.stem
    por_hoja = max(1, args.por_hoja)
    alto_etiqueta = max(14, int(args.ppi * 0.22))
    etiqueta_base = rotulos["pliego"] + " " if args.modo == "pliegos" else rotulos["pagina"] + " "
    letra = fuente(max(10, int(alto_etiqueta * 0.7)), config, etiqueta_base + "0123456789-")

    escritas: list[Path] = []
    celda_actual: list[Celda] = []
    celdas_totales = 0
    paginas_totales = 0

    def volcar() -> None:
        """Escribe la hoja con las celdas acumuladas y vacía el lote."""
        nonlocal celda_actual
        if not celda_actual:
            return
        hoja = montar_hoja(
            celda_actual, args.columnas, args.ppi, args.margen_mm, args.separacion_mm, alto_etiqueta, letra
        )
        destino = salida / f"{prefijo}-contactos-{len(escritas) + 1:02d}.png"
        hoja.save(destino)
        escritas.append(destino)
        celda_actual = []

    for grupo in iterar_grupos(iterar_paginas(doc, args.ppi), args.modo):
        paginas_totales += len(grupo)
        celdas_totales += 1
        celda_actual.append(Celda(imagen=_emparejar(grupo), etiqueta=etiqueta_base + _rotulo(grupo)))
        if len(celda_actual) >= por_hoja:
            volcar()
    volcar()

    for destino in escritas:
        print(f"{destino}  ({_tamano(destino)})")
    paginas_txt = f"{paginas_totales} página" if paginas_totales == 1 else f"{paginas_totales} páginas"
    hojas_txt = f"{len(escritas)} hoja" if len(escritas) == 1 else f"{len(escritas)} hojas"
    print(
        f"{paginas_txt} → {celdas_totales} celdas → {hojas_txt} "
        f"({por_hoja} por hoja, modo {args.modo}) a {args.ppi:g} ppp"
    )
    doc.close()
    return 0


def _emparejar(grupo: list[tuple[int, Image.Image]]) -> Image.Image:
    """Dos páginas contiguas como un pliego: izquierda y derecha separadas."""
    if len(grupo) == 1:
        return grupo[0][1]
    izquierda, derecha = grupo[0][1], grupo[1][1]
    alto = max(izquierda.height, derecha.height)
    ancho = izquierda.width + derecha.width
    pliego = Image.new("RGB", (ancho, alto), "white")
    pliego.paste(izquierda, (0, 0))
    pliego.paste(derecha, (izquierda.width, 0))
    return pliego


def _rotulo(grupo: list[tuple[int, Image.Image]]) -> str:
    return "-".join(str(n) for n, _ in grupo)


def _tamano(ruta: Path) -> str:
    kb = ruta.stat().st_size / 1024
    return f"{kb:.0f} kB"


if __name__ == "__main__":
    raise SystemExit(main())
