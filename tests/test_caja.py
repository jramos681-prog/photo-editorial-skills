"""Caja, franja de seguridad, sangre, imágenes y límites del PDF."""

from __future__ import annotations

import sys

import pymupdf
from PIL import Image

from soporte import CONTROL, crear_config, ejecutar, escribir_pdf_texto, informe, pdf_con_corte, pdf_vacio, resultado


def _control(tmp_path, config, pdf, *extra):
    json_salida = tmp_path / f"{pdf.stem}.json"
    ejecutar([sys.executable, str(CONTROL), "--config", str(config), str(pdf), *extra, "--json", str(json_salida)], tmp_path)
    return informe(json_salida)


def test_vector_en_la_franja_de_seguridad(tmp_path):
    config = crear_config(tmp_path / "base", idioma="es-en")
    pdf = tmp_path / "vector-seguridad.pdf"
    doc = pymupdf.open()
    pagina = doc.new_page(width=595, height=842)
    pagina.draw_rect(pymupdf.Rect(3, 3, 6, 6), color=(0, 0, 0), width=1)
    doc.save(pdf)
    doc.close()
    caja = resultado(_control(tmp_path, config, pdf), "caja")
    assert caja["estado"] == "fallo"
    assert any(i["tipo"].startswith("dibujo en la franja de seguridad") for i in caja["datos"]["incidencias"]), caja
    assert "texto: dentro del corte" in caja["detalle"] and "área segura" in caja["detalle"]


def test_texto_en_la_franja_y_fuera_del_corte(tmp_path):
    config = crear_config(tmp_path / "base", idioma="es-en")

    texto_borde = tmp_path / "texto-borde.pdf"
    pdf_con_corte(texto_borde, lambda p: p.insert_text((10.0, 60), "Texto en la franja", fontsize=10))
    caja_texto = resultado(_control(tmp_path, config, texto_borde), "caja")
    assert caja_texto["estado"] == "fallo"
    assert any(i["tipo"] == "texto en la franja de seguridad" for i in caja_texto["datos"]["incidencias"]), caja_texto

    texto_cruzado = tmp_path / "texto-cruzado.pdf"
    pdf_con_corte(texto_cruzado, lambda p: p.insert_text((-20, 60), "Texto que cruza el corte", fontsize=10))
    caja_cruzado = resultado(_control(tmp_path, config, texto_cruzado), "caja")
    assert caja_cruzado["estado"] == "fallo", caja_cruzado

    texto_justo = tmp_path / "texto-justo.pdf"
    pdf_con_corte(texto_justo, lambda p: p.insert_text((8.5, 60), "Texto 1 pt fuera del corte", fontsize=10))
    caja_justo = resultado(_control(tmp_path, config, texto_justo, "--margen-seguro", "0"), "caja")
    assert caja_justo["estado"] == "fallo"
    assert any(i["tipo"] == "texto fuera del corte" for i in caja_justo["datos"]["incidencias"]), caja_justo


def test_sangre_solo_en_los_bordes_alcanzados(tmp_path):
    config = crear_config(tmp_path / "base", idioma="es-en")

    sangre_pdf = tmp_path / "vector-sangre.pdf"
    pdf_con_corte(sangre_pdf, lambda p: p.draw_rect(pymupdf.Rect(0, 100, 40, 140), color=(0, 0, 0), width=1))
    caja_sangre = resultado(_control(tmp_path, config, sangre_pdf), "caja")
    assert caja_sangre["estado"] == "ok", caja_sangre

    roza_pdf = tmp_path / "vector-roza.pdf"
    pdf_con_corte(roza_pdf, lambda p: p.draw_rect(pymupdf.Rect(9, 300, 40, 340), color=(0, 0, 0), width=1))
    caja_roza = resultado(_control(tmp_path, config, roza_pdf), "caja")
    assert caja_roza["estado"] == "ok", caja_roza

    dentro_pdf = tmp_path / "vector-dentro.pdf"
    pdf_con_corte(dentro_pdf, lambda p: p.draw_rect(pymupdf.Rect(10, 300, 41, 340), color=(0, 0, 0), width=1))
    caja_dentro = resultado(_control(tmp_path, config, dentro_pdf), "caja")
    assert caja_dentro["estado"] == "fallo", caja_dentro

    filete_pdf = tmp_path / "filete-superior.pdf"
    pdf_con_corte(
        filete_pdf,
        lambda p: p.draw_line((0, 9 + 72 / 25.4), (595, 9 + 72 / 25.4), color=(0, 0, 0), width=0.5),
    )
    caja_filete = resultado(_control(tmp_path, config, filete_pdf), "caja")
    assert caja_filete["estado"] == "fallo"
    assert any(
        i["tipo"].startswith("dibujo en la franja de seguridad") and "superior" in i["tipo"]
        for i in caja_filete["datos"]["incidencias"]
    ), caja_filete

    fondo_pdf = tmp_path / "fondo-pagina.pdf"
    pdf_con_corte(fondo_pdf, lambda p: p.draw_rect(p.rect, color=None, fill=(0.8, 0.8, 0.8)))
    caja_fondo = resultado(_control(tmp_path, config, fondo_pdf), "caja")
    assert caja_fondo["estado"] == "ok", caja_fondo


def test_ppi_de_imagen_girada(tmp_path):
    config = crear_config(tmp_path / "base", idioma="es-en")
    imagen = tmp_path / "imagen-300ppp-giro45.pdf"
    png = tmp_path / "imagen.png"
    Image.new("RGB", (1000, 1000), "white").save(png)
    origen = pymupdf.open()
    pagina_origen = origen.new_page(width=1000, height=1000)
    pagina_origen.insert_image(pymupdf.Rect(0, 0, 1000, 1000), filename=str(png))
    destino = pymupdf.open()
    pagina_destino = destino.new_page(width=500, height=500)
    pagina_destino.show_pdf_page(pymupdf.Rect(80, 80, 419.41125497, 419.41125497), origen, 0, rotate=45)
    destino.save(imagen)
    origen.close()
    destino.close()
    resultado_imagen = resultado(_control(tmp_path, config, imagen), "imagenes")
    ppi = resultado_imagen["datos"]["imagenes"][0]["ppi"]
    assert ppi is not None and abs(ppi - 300) < 0.1, ppi
    assert not resultado_imagen["datos"]["imagenes"][0]["transformacion_no_soportada"]


def test_limite_de_peso_decimal(tmp_path):
    config = crear_config(tmp_path / "base", idioma="es-en")
    grande = tmp_path / "1020000-bytes.pdf"
    doc = pymupdf.open()
    doc.new_page(width=595, height=842)
    doc.save(grande)
    doc.close()
    with grande.open("ab") as fichero:
        fichero.write(b" " * (1_020_000 - grande.stat().st_size))
    archivo = resultado(_control(tmp_path, config, grande, "--max-mb", "1"), "archivo")
    assert archivo["estado"] == "fallo" and archivo["datos"]["bytes"] == 1_020_000 and archivo["datos"]["mb"] == 1.02, archivo
    assert "1.020 MB decimales" in archivo["detalle"] and "1,020,000 bytes" in archivo["detalle"], archivo["detalle"]


def test_excepciones_por_bloque(tmp_path):
    config = crear_config(tmp_path / "base", idioma="es-en")
    medida_pdf = tmp_path / "medida-excepciones.pdf"
    escribir_pdf_texto(
        medida_pdf,
        [
            (1, "CITA DE PRUEBA - TEXTO CORTO\nEsta segunda linea queda corta\nY la tercera tambien muy corta"),
            (2, "PROSA SIN EXCEPCION DE PRUEBA\nOtra linea que tambien es corta\nUna tercera frase fuera de rango"),
        ],
    )
    excepciones = tmp_path / "excepciones.yaml"
    excepciones.write_text(
        "- pagina: 1\n  control: medida\n  bloque: CITA DE PRUEBA\n  tipo: cita\n  motivo: cita reproducible de prueba\n",
        encoding="utf-8",
    )
    json_medida = tmp_path / "medida.json"
    prueba = ejecutar(
        [sys.executable, str(CONTROL), "--config", str(config), str(medida_pdf), "--excepciones", str(excepciones), "--json", str(json_medida)],
        tmp_path,
    )
    med = resultado(informe(json_medida), "medida")
    juicios = {(b["pagina"], b["juicio"]) for b in med["datos"]["bloques"]}
    assert (1, "excepción declarada") in juicios and (2, "fallo heurístico") in juicios, juicios
    assert med["estado"] == "fallo heurístico" and prueba.returncode == 1
    salida = prueba.stdout.decode("utf-8").lower()
    assert "excepción declarada" in salida and "fallo heurístico" in salida


def test_excepcion_en_control_duro(tmp_path):
    config = crear_config(tmp_path / "base", idioma="es-en")
    pdf = tmp_path / "vector.pdf"
    doc = pymupdf.open()
    pagina = doc.new_page(width=595, height=842)
    pagina.draw_rect(pymupdf.Rect(3, 3, 6, 6), color=(0, 0, 0), width=1)
    doc.save(pdf)
    doc.close()
    invalida = tmp_path / "excepcion-dura.json"
    invalida.write_text(
        '[{"pagina": 1, "control": "caja", "bloque": 1, "tipo": "otro", "motivo": "prueba"}]',
        encoding="utf-8",
    )
    rechazo = ejecutar(
        [sys.executable, str(CONTROL), "--config", str(config), str(pdf), "--excepciones", str(invalida)],
        tmp_path,
    )
    assert rechazo.returncode == 2 and "solo se permiten excepciones del control" in rechazo.stderr.decode("utf-8").lower(), rechazo.stderr.decode(errors="replace")


def test_metadatos_exigidos(tmp_path):
    config = crear_config(tmp_path / "base", idioma="es-en")
    pdf = pdf_vacio(tmp_path / "pagina.pdf")
    meta = resultado(_control(tmp_path, config, pdf), "metadatos")
    assert meta["estado"] == "aviso", meta
    json_duro = tmp_path / "meta-duro.json"
    exigido = ejecutar(
        [sys.executable, str(CONTROL), "--config", str(config), str(pdf), "--exigir-metadatos", "--json", str(json_duro)],
        tmp_path,
    )
    meta_duro = resultado(informe(json_duro), "metadatos")
    assert meta_duro["estado"] == "fallo" and exigido.returncode == 1, meta_duro


def test_medida_heuristica(tmp_path):
    config = crear_config(tmp_path / "base", idioma="es-en")

    def pdf_medida(ruta, largos):
        doc = pymupdf.open()
        pagina = doc.new_page(width=595, height=842)
        pagina.insert_textbox(pymupdf.Rect(72, 72, 523, 420), "\n".join("x" * n for n in largos), fontsize=9)
        doc.save(ruta)
        doc.close()

    casos = (
        ("mediana-42", [42] * 5, "aviso"),
        ("mediana-81", [81] * 5, "aviso"),
        ("mediana-38", [38] * 5, "fallo heurístico"),
        ("mediana-60", [60] * 5, "ok"),
        ("lineas-extremas", [60] * 9 + [95], "aviso"),
    )
    for nombre, largos, esperado in casos:
        ruta = tmp_path / f"{nombre}.pdf"
        pdf_medida(ruta, largos)
        medido = resultado(_control(tmp_path, config, ruta), "medida")
        assert medido["estado"] == esperado, f"{nombre}: {medido['estado']} en vez de {esperado} · {medido['detalle']}"
