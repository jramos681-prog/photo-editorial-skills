"""Biblioteca Typst: proyectos externos, margen, cuerpo y API pública."""

from __future__ import annotations

import re
import shutil
from pathlib import Path

import pymupdf
from PIL import Image

from soporte import FIXTURES, LIBRERIA, REPO, ejecutar


def _compilar(etiqueta: str, raiz: Path, fuente: Path, salida: Path) -> None:
    resultado = ejecutar(["typst", "compile", "--root", str(raiz), str(fuente), str(salida)], raiz)
    assert resultado.returncode == 0, f"{etiqueta}: {resultado.stderr.decode(errors='replace')}"


def _preparar(raiz: Path, fixture: str, imagen: Path) -> Path:
    (raiz / "typst").mkdir(parents=True)
    (raiz / "images").mkdir()
    shutil.copy2(LIBRERIA, raiz / "typst" / "editorial.typ")
    shutil.copy2(imagen, raiz / "images" / imagen.name)
    (raiz / "main.typ").write_text((FIXTURES / fixture).read_text(encoding="utf-8"), encoding="utf-8")
    return raiz


def test_typst_instalado():
    assert shutil.which("typst"), "Typst no está instalado o no está en PATH"


def test_proyecto_externo_minimo(tmp_path):
    imagen = tmp_path / "foto.png"
    Image.new("RGB", (1200, 800), (80, 120, 160)).save(imagen)
    raiz = _preparar(tmp_path / "minimo", "minimo.typ", imagen)
    _compilar("Proyecto externo mínimo", raiz, raiz / "main.typ", raiz / "main.pdf")
    assert (raiz / "main.pdf").is_file()


def test_margen(tmp_path):
    imagen = tmp_path / "2-a-1.png"
    Image.new("RGB", (2000, 1000), (150, 90, 60)).save(imagen)
    raiz = _preparar(tmp_path / "margen", "margen.typ", imagen)
    salida = raiz / "margen.pdf"
    _compilar("Margen", raiz, raiz / "main.typ", salida)
    document = pymupdf.open(salida)
    rects = document[0].get_image_rects(document[0].get_images()[0][0])
    factor = 25.4 / 72
    cajas = [tuple(round(valor * factor, 3) for valor in (rect.x0, rect.y0, rect.width, rect.height)) for rect in rects]
    document.close()
    assert cajas == [(10.0, 10.0, 80.0, 40.0)], cajas


def test_beli_bryag_con_imagenes_sinteticas(tmp_path):
    raiz = tmp_path / "beli"
    origen = REPO / "examples" / "beli-bryag"
    destino = raiz / "examples" / "beli-bryag"
    destino.mkdir(parents=True)
    for nombre in ("beli_bryag.typ", "contenido.typ"):
        shutil.copy2(origen / nombre, destino / nombre)
    # El ejemplo conserva su import relativo; en el temporal se resuelve a esta copia.
    staged = raiz / "examples" / ".claude" / "skills" / "maquetacion-editorial" / "typst" / "editorial.typ"
    staged.parent.mkdir(parents=True)
    shutil.copy2(LIBRERIA, staged)

    content = (origen / "contenido.typ").read_text(encoding="utf-8")
    paths = dict(re.findall(r'\b(E\d{2}):\s*"(/[^\"]+\.jpg)"', content.split("#let R = (", 1)[0]))
    ratios_text = content.split("#let R = (", 1)[1].split(")", 1)[0]
    ratios = {clave: float(valor) for clave, valor in re.findall(r"\b(E\d{2}):\s*([0-9.]+)", ratios_text)}
    assert paths.keys() == ratios.keys(), (paths.keys(), ratios.keys())
    for clave, relativa in paths.items():
        alto = 1000
        ancho = round(ratios[clave] * alto)
        ruta = raiz / relativa.lstrip("/")
        ruta.parent.mkdir(parents=True, exist_ok=True)
        Image.new("RGB", (ancho, alto), (60 + len(clave), 110, 140)).save(ruta, format="JPEG", quality=85)

    _compilar("Beli Bryag con imágenes sintéticas", raiz, destino / "beli_bryag.typ", raiz / "beli.pdf")
    assert (raiz / "beli.pdf").is_file()


def test_cuerpo_sobre_la_caja_de_la_imagen(tmp_path):
    raiz = tmp_path / "cuerpo"
    (raiz / "typst").mkdir(parents=True)
    (raiz / "images").mkdir()
    shutil.copy2(LIBRERIA, raiz / "typst" / "editorial.typ")
    Image.new("RGB", (2000, 1000), (30, 60, 90)).save(raiz / "images" / "foto.png")
    reticula = (
        '#import "typst/editorial.typ": reticula, foto\n'
        "#set page(width: 100mm, height: 100mm, margin: 0pt)\n"
        "#let r = reticula(ancho: 100mm, alto: 100mm, columnas: 1, filas: 1, canal_h: 0mm, canal_v: 0mm)\n"
    )
    (raiz / "cuerpo.typ").write_text(
        reticula
        + '#foto("/images/foto.png", r, margen: 10mm, alinear: bottom + left, '
        'texto_sobre_foto: "autorizado", cuerpo: [CUERPO])\n',
        encoding="utf-8",
    )
    cuerpo_pdf = raiz / "cuerpo.pdf"
    _compilar("Cuerpo sobre la caja de la imagen", raiz, raiz / "cuerpo.typ", cuerpo_pdf)
    document = pymupdf.open(cuerpo_pdf)
    cajas = document[0].search_for("CUERPO")
    imagenes = document[0].get_image_rects(document[0].get_images()[0][0])
    document.close()
    assert cajas, "No se encontró el cuerpo sobre la fotografía"
    assert imagenes, "No se encontró la imagen colocada"
    factor = 25.4 / 72
    izquierda = round(cajas[0].x0 * factor, 1)
    arriba = round(cajas[0].y0 * factor, 1)
    derecha = round(cajas[0].x1 * factor, 1)
    abajo = round(cajas[0].y1 * factor, 1)
    imagen = [round(valor * factor, 1) for valor in (imagenes[0].x0, imagenes[0].y0, imagenes[0].x1, imagenes[0].y1)]
    # Foto 2:1 en un campo cuadrado de 80 mm: 80×40 mm, abajo a la izquierda
    # del área libre, es decir, en (10, 50)–(90, 90) mm.
    assert 9 <= izquierda <= 11 and 48 <= arriba <= 52, (izquierda, arriba)
    assert (
        imagen[0] - 1 <= izquierda
        and imagen[1] - 1 <= arriba
        and derecha <= imagen[2] + 1
        and abajo <= imagen[3] + 1
    ), (izquierda, arriba, derecha, abajo, imagen)

    for etiqueta, fuente, esperado in (
        ("margen negativo", reticula + '#foto("/images/foto.png", r, margen: -10mm)\n', "margen debe ser mayor o igual que 0pt"),
        ("cuerpo sin autorización", reticula + '#foto("/images/foto.png", r, cuerpo: [CUERPO])\n', 'texto_sobre_foto: "autorizado"'),
        ("ruta relativa", reticula + '#foto("images/foto.png", r)\n', "searched at"),
    ):
        (raiz / "main.typ").write_text(fuente, encoding="utf-8")
        fallo = ejecutar(
            ["typst", "compile", "--root", str(raiz), str(raiz / "main.typ"), str(raiz / "fallo.pdf")],
            raiz,
        )
        assert fallo.returncode != 0, f"{etiqueta}: Typst compiló cuando debía fallar"
        stderr = fallo.stderr.decode(errors="replace")
        assert esperado in stderr, f"{etiqueta}: mensaje inesperado: {stderr.strip()}"
        if etiqueta == "cuerpo sin autorización":
            assert "foto:" in stderr, "El mensaje de cuerpo perdió el prefijo foto:"


def test_api_publica_en_la_cabecera():
    texto = LIBRERIA.read_text(encoding="utf-8")
    cabecera = "\n".join(texto.splitlines()[:80])
    publicas = [
        nombre
        for nombre in re.findall(r"^#let ([a-zA-Z_][a-zA-Z0-9_]*)", texto, re.MULTILINE)
        if not nombre.startswith("_")
    ]
    faltan = [nombre for nombre in publicas if f"{nombre}(" not in cabecera]
    assert not faltan, f"El índice de la cabecera no cubre: {faltan}"
    assert "avance lo mide el catálogo de fuentes" in texto, "No se dice de dónde sale el avance"
    assert "searched at …\\typst\\images" in cabecera, "La cabecera no advierte de las rutas relativas"
