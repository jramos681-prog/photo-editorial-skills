"""Fuentes del PDF: incrustación, cobertura y subconjuntos."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pymupdf

from soporte import (
    CONTROL,
    SCRIPTS,
    bloqueador,
    construir_fuente,
    crear_config,
    ejecutar,
    escribir_pdf_texto,
    informe,
    resultado,
)


def _compilar_typst(carpeta: Path, fuente: str) -> Path:
    salida = carpeta / f"{Path(fuente).stem}.pdf"
    compila = ejecutar(["typst", "compile", "--root", str(carpeta), str(carpeta / fuente), str(salida)], carpeta)
    assert compila.returncode == 0, compila.stderr.decode(errors="replace")
    return salida


def test_fuente_sin_incrustar(tmp_path):
    config = crear_config(tmp_path / "base", idioma="es-en")
    pdf = tmp_path / "base14.pdf"
    escribir_pdf_texto(pdf, [(1, "Texto con Helvetica")])
    json_salida = tmp_path / "base14.json"
    ejecutar([sys.executable, str(CONTROL), "--config", str(config), str(pdf), "--json", str(json_salida)], tmp_path)
    fuentes = resultado(informe(json_salida), "fuentes")
    assert fuentes["estado"] == "fallo" and "sin incrustar" in fuentes["detalle"], fuentes


def test_cobertura_sin_programa_medible(tmp_path):
    config = crear_config(tmp_path / "base", idioma="es-en")
    pdf = tmp_path / "base14.pdf"
    escribir_pdf_texto(pdf, [(1, "Texto con Helvetica")])
    json_salida = tmp_path / "base14-cobertura.json"
    ejecutar([sys.executable, str(CONTROL), "--config", str(config), str(pdf), "--json", str(json_salida)], tmp_path)
    cobertura = resultado(informe(json_salida), "cobertura")
    assert cobertura["estado"] == "no-aplica", cobertura
    assert "medir 1 fuente usada" in cobertura["detalle"]
    assert "medir 1 la fuente" not in cobertura["detalle"]


def test_cobertura_de_los_subconjuntos_de_typst(tmp_path):
    carpeta = tmp_path / "typst-cata"
    carpeta.mkdir()
    (carpeta / "cata.typ").write_text(
        '#set page(width: 120mm, height: 70mm)\nHola, señor López: «¿qué tal?»\n',
        encoding="utf-8",
    )
    cata = _compilar_typst(carpeta, "cata.typ")
    config_cata = crear_config(tmp_path / "typst-cata-cfg", idioma="es-en", sistema=True, carpeta="null")
    json_cata = tmp_path / "cata.json"
    salida_cata = ejecutar(
        [sys.executable, str(CONTROL), "--config", str(config_cata), str(cata), "--json", str(json_cata)],
        tmp_path,
    )
    cobertura = resultado(informe(json_cata), "cobertura")
    formatos = cobertura["datos"]["formatos_incrustados"]
    assert formatos and set(formatos.values()) == {"cid"}, formatos
    assert cobertura["estado"] == "ok", f"{cobertura['estado']} · {cobertura['detalle']}"
    assert "TTLibError" not in salida_cata.stdout.decode("utf-8", errors="replace")
    assert "TTLibError" not in cobertura["detalle"]
    assert "cubre los caracteres usados" in cobertura["detalle"]
    assert "el juego completo no se puede comprobar en un subconjunto" in cobertura["detalle"]

    nombres_cata = tmp_path / "nombres-cata.txt"
    nombres_cata.write_text("Senor Lopez\n", encoding="utf-8")
    json_cata_anon = tmp_path / "cata-anon.json"
    cata_anon = ejecutar(
        [
            sys.executable,
            str(CONTROL),
            "--config",
            str(config_cata),
            str(cata),
            "--anonimo",
            "--nombres",
            str(nombres_cata),
            "--json",
            str(json_cata_anon),
        ],
        tmp_path,
    )
    anon_cata = resultado(informe(json_cata_anon), "anonimato")
    assert anon_cata["estado"] == "fallo"
    assert any(h["tipo"] == "nombre" and h["canal"] == "texto" for h in anon_cata["datos"]["hallazgos"]), anon_cata["datos"]["hallazgos"]
    assert not [h for h in anon_cata["datos"]["hallazgos"] if h["canal"] == "xmp"], anon_cata["datos"]["hallazgos"]
    assert "TTLibError" not in cata_anon.stdout.decode("utf-8", errors="replace")

    (carpeta / "completo.typ").write_text(
        "#set page(width: 180mm, height: 90mm, margin: 5mm)\n#set text(size: 11pt)\n¡«»¿ÁÉÍÑÓÚÜáéíñóúü–—‘’“”…\n",
        encoding="utf-8",
    )
    completo = _compilar_typst(carpeta, "completo.typ")
    config_completo = crear_config(tmp_path / "typst-completo-cfg", idioma="es-en", sistema=False, carpeta="null")
    json_completo = tmp_path / "completo.json"
    ejecutar(
        [sys.executable, str(CONTROL), "--config", str(config_completo), str(completo), "--json", str(json_completo)],
        tmp_path,
    )
    cobertura_completo = resultado(informe(json_completo), "cobertura")
    assert cobertura_completo["estado"] == "ok", f"{cobertura_completo['estado']} · {cobertura_completo['detalle']}"
    assert any(
        "programa incrustado en el PDF (cid)" in v["origen"] for v in cobertura_completo["datos"]["verificadas"]
    ), cobertura_completo["datos"]["verificadas"]


def test_cobertura_sin_fonttools(tmp_path):
    carpeta = tmp_path / "typst-cata"
    carpeta.mkdir()
    (carpeta / "cata.typ").write_text(
        '#set page(width: 120mm, height: 70mm)\nHola, señor López: «¿qué tal?»\n',
        encoding="utf-8",
    )
    cata = _compilar_typst(carpeta, "cata.typ")
    config_cata = crear_config(tmp_path / "typst-cata-cfg", idioma="es-en", sistema=True, carpeta="null")
    entorno_ft = bloqueador(tmp_path, "bloquea-fonttools", "fontTools")
    json_salida = tmp_path / "sin-fonttools.json"
    ejecutar(
        [sys.executable, str(CONTROL), "--config", str(config_cata), str(cata), "--json", str(json_salida)],
        tmp_path,
        env=entorno_ft,
    )
    cobertura = resultado(informe(json_salida), "cobertura")
    assert cobertura["estado"] == "ok", cobertura
    assert "el juego completo no se puede comprobar en un subconjunto" in cobertura["detalle"]


def test_cobertura_de_una_fuente_propia(tmp_path):
    fuentes = tmp_path / "fuentes-propias"
    fuente = construir_fuente(fuentes / "Prueba-Regular.ttf")
    pdf = tmp_path / "fuente-propia.pdf"
    doc = pymupdf.open()
    pagina = doc.new_page(width=595, height=842)
    pagina.insert_font(fontname="F0", fontfile=str(fuente))
    pagina.insert_text((72, 72), "Texto de prueba con ñ y á", fontname="F0", fontsize=12)
    doc.save(pdf)
    doc.close()
    config = crear_config(
        tmp_path / "hueco",
        idioma="es",
        carpeta=json.dumps(str(fuentes).replace("\\", "/")),
        caracteres='{es: "😀"}',
    )
    json_hueco = tmp_path / "hueco.json"
    ejecutar([sys.executable, str(CONTROL), "--config", str(config), str(pdf), "--json", str(json_hueco)], tmp_path)
    cobertura = resultado(informe(json_hueco), "cobertura")
    assert cobertura["estado"] == "aviso", cobertura
    assert "😀" in cobertura["detalle"]
    assert "no usados aquí" in cobertura["detalle"]
    assert "sirve para títulos y rótulos, no para texto corrido" in cobertura["detalle"]

    codigo = (
        f"import sys; sys.path.insert(0, {str(SCRIPTS)!r}); import control_pdf as c, pymupdf; from pathlib import Path; "
        "doc = pymupdf.open(); doc.new_page(); requerido = chr(0x1F600); "
        f"f = c.FuentePDF(basefont='Prueba Regular', clave=c._clave_fuente('Prueba Regular'), ext='ttf', tipo='Type0', xref=0, incrustada=True, caracteres={{requerido}}); "
        f"res = [r for r in c.comprobar_fuentes(doc, {{f.clave: f}}, [Path({str(fuente)!r})], requerido) if r.id == 'cobertura'][0]; "
        "print(res.estado + '|' + res.detalle); "
        "assert res.estado == 'fallo' and requerido in res.detalle; print('usado: OK')"
    )
    usado = ejecutar([sys.executable, "-B", "-c", codigo], tmp_path)
    assert usado.returncode == 0 and b"usado: OK" in usado.stdout, usado.stderr.decode(errors="replace")


def test_subconjunto_truetype_sin_cmap(tmp_path):
    carpeta = tmp_path / "typst-mono"
    carpeta.mkdir()
    (carpeta / "mono.typ").write_text(
        "#set page(width: 180mm, height: 90mm, margin: 5mm)\n"
        '#set text(font: "DejaVu Sans Mono", size: 11pt)\n'
        "¡«»¿ÁÉÍÑÓÚÜáéíñóúü–—‘’“”…\n",
        encoding="utf-8",
    )
    mono = _compilar_typst(carpeta, "mono.typ")
    config = crear_config(tmp_path / "mono-cfg", idioma="es-en", sistema=False, carpeta="null")
    json_mono = tmp_path / "mono.json"
    ejecutar([sys.executable, str(CONTROL), "--config", str(config), str(mono), "--json", str(json_mono)], tmp_path)
    cobertura = resultado(informe(json_mono), "cobertura")
    formatos = cobertura["datos"]["formatos_incrustados"]
    assert formatos and set(formatos.values()) == {"ttf"}, formatos
    assert cobertura["estado"] == "ok" and "no trae tabla cmap" not in cobertura["detalle"], cobertura
