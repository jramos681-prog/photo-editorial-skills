"""Anonimato: nombres, XMP, teléfonos y canales secundarios del PDF."""

from __future__ import annotations

import sys

import pymupdf

from soporte import CONTROL, SCRIPTS, crear_config, ejecutar, escribir_pdf_texto, informe, resultado


def _xmp_documento(ruta, xmp: str) -> None:
    doc = pymupdf.open()
    doc.new_page(width=595, height=842)
    doc.set_xml_metadata(xmp)
    doc.save(ruta)
    doc.close()


def test_nombre_partido_por_salto_y_guion(tmp_path):
    config = crear_config(tmp_path / "base", idioma="es-en")
    nombres = tmp_path / "nombres.txt"
    nombres.write_text("Ada Lovelace\n", encoding="utf-8")
    pdf = tmp_path / "nombres-partidos.pdf"
    escribir_pdf_texto(pdf, [(1, "Ada\nLovelace"), (2, "Ada-Lovelace")])
    json_nombres = tmp_path / "nombres.json"
    ejecutar(
        [sys.executable, str(CONTROL), "--config", str(config), str(pdf), "--anonimo", "--nombres", str(nombres), "--json", str(json_nombres)],
        tmp_path,
    )
    hallazgos = resultado(informe(json_nombres), "anonimato")["datos"]["hallazgos"]
    ubicaciones = [h["ubicacion"] for h in hallazgos if h["tipo"] == "nombre" and h["valor"] == "Ada Lovelace"]
    assert "pág. 1" in ubicaciones and "pág. 2" in ubicaciones, ubicaciones


def test_nombre_en_atributo_xmp(tmp_path):
    config = crear_config(tmp_path / "base", idioma="es-en")
    nombre_xmp = tmp_path / "nombre-xmp.txt"
    nombre_xmp.write_text("Morgan Example\n", encoding="utf-8")
    pdf = tmp_path / "xmp-atributo.pdf"
    _xmp_documento(
        pdf,
        '<x:xmpmeta xmlns:x="adobe:ns:meta/" x:xmptk="tool">'
        '<rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#">'
        '<rdf:Description rdf:about="" xmlns:dc="http://purl.org/dc/elements/1.1/" '
        'dc:creator="Morgan Example"/>'
        "</rdf:RDF></x:xmpmeta>",
    )
    json_xmp = tmp_path / "xmp.json"
    ejecutar(
        [sys.executable, str(CONTROL), "--config", str(config), str(pdf), "--anonimo", "--nombres", str(nombre_xmp), "--json", str(json_xmp)],
        tmp_path,
    )
    hallazgos = resultado(informe(json_xmp), "anonimato")["datos"]["hallazgos"]
    assert any(h["canal"] == "xmp" and h["valor"] == "Morgan Example" for h in hallazgos), hallazgos


def test_nombre_repartido_en_dos_valores_xmp(tmp_path):
    config = crear_config(tmp_path / "base", idioma="es-en")
    nombre_xmp = tmp_path / "nombre-xmp.txt"
    nombre_xmp.write_text("Morgan Example\n", encoding="utf-8")
    pdf = tmp_path / "xmp-partido.pdf"
    _xmp_documento(
        pdf,
        '<x:xmpmeta xmlns:x="adobe:ns:meta/">'
        '<rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#">'
        '<rdf:Description rdf:about="" xmlns:dc="http://purl.org/dc/elements/1.1/">'
        "<dc:creator><rdf:Seq><rdf:li>Morgan</rdf:li><rdf:li>Example</rdf:li></rdf:Seq></dc:creator>"
        "</rdf:Description></rdf:RDF></x:xmpmeta>",
    )
    json_partido = tmp_path / "xmp-partido.json"
    ejecutar(
        [sys.executable, str(CONTROL), "--config", str(config), str(pdf), "--anonimo", "--nombres", str(nombre_xmp), "--json", str(json_partido)],
        tmp_path,
    )
    anon_partido = resultado(informe(json_partido), "anonimato")
    assert any(
        h["canal"] == "xmp" and h["tipo"] == "nombre" and h["valor"] == "Morgan Example"
        for h in anon_partido["datos"]["hallazgos"]
    ), anon_partido["datos"]["hallazgos"]


def test_xmp_con_prefijo_sin_declarar(tmp_path):
    config = crear_config(tmp_path / "base", idioma="es-en")
    nombre_xmp = tmp_path / "nombre-xmp.txt"
    nombre_xmp.write_text("Morgan Example\n", encoding="utf-8")
    pdf = tmp_path / "xmp-prefijo.pdf"
    _xmp_documento(
        pdf,
        '<x:xmpmeta xmlns:x="adobe:ns:meta/">'
        '<rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#">'
        '<rdf:Description dc:creator="Morgan Example"/>'
        "</rdf:RDF></x:xmpmeta>",
    )
    json_prefijo = tmp_path / "xmp-prefijo.json"
    ejecutar(
        [sys.executable, str(CONTROL), "--config", str(config), str(pdf), "--anonimo", "--nombres", str(nombre_xmp), "--json", str(json_prefijo)],
        tmp_path,
    )
    anon_prefijo = resultado(informe(json_prefijo), "anonimato")
    assert anon_prefijo["estado"] == "fallo"
    assert any(h["canal"] == "xmp" and h["valor"] == "Morgan Example" for h in anon_prefijo["datos"]["hallazgos"]), anon_prefijo
    assert any("barrió como texto" in valor["motivo"] for valor in anon_prefijo["datos"]["no_revisados"]), anon_prefijo["datos"]["no_revisados"]


def test_xmp_mal_formado(tmp_path):
    config = crear_config(tmp_path / "base", idioma="es-en")
    nombre_xmp = tmp_path / "nombre-xmp.txt"
    nombre_xmp.write_text("Morgan Example\n", encoding="utf-8")
    pdf = tmp_path / "xmp-roto.pdf"
    _xmp_documento(
        pdf,
        '<x:xmpmeta xmlns:x="adobe:ns:meta/">'
        '<rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#">'
        '<rdf:Description><dc:creator xmlns:dc="http://purl.org/dc/elements/1.1/">'
        "<rdf:Seq><rdf:li>Morgan Example</rdf:li></rdf:Seq></dc:creator></rdf:Description></rdf:RDF>",
    )
    json_xmp = tmp_path / "xmp-roto.json"
    ejecutar(
        [sys.executable, str(CONTROL), "--config", str(config), str(pdf), "--anonimo", "--nombres", str(nombre_xmp), "--json", str(json_xmp)],
        tmp_path,
    )
    anonimato = resultado(informe(json_xmp), "anonimato")
    assert anonimato["estado"] == "fallo", anonimato
    assert any(valor["elemento"] == "XMP" and "barrió como texto" in valor["motivo"] for valor in anonimato["datos"]["no_revisados"]), anonimato["datos"]["no_revisados"]


def test_normalizacion_de_identidad(tmp_path):
    codigo = (
        f"import sys; sys.path.insert(0, {str(SCRIPTS)!r}); import control_pdf as c; "
        "casos = [('Lopez', 'Lo\\u200bpez'), ('Lopez', 'Lo\\u00adpez'), ('Lopez', 'Ｌｏｐｅｚ'), "
        "('Ana Lopez', 'Ana Lo\\u0301pez'), ('ANA LOPEZ', 'Ana López')]; "
        "assert all(c._normalizar_identidad(a) == c._normalizar_identidad(b) for a, b in casos); "
        "print('identidad: OK')"
    )
    identidad = ejecutar([sys.executable, "-B", "-c", codigo], tmp_path)
    assert identidad.returncode == 0, identidad.stderr.decode(errors="replace")


def test_xmp_con_fecha_y_telefono(tmp_path):
    config = crear_config(tmp_path / "base", idioma="es-en")
    nombre_xmp = tmp_path / "nombre-xmp.txt"
    nombre_xmp.write_text("Morgan Example\n", encoding="utf-8")

    pdf_fechas = tmp_path / "xmp-fechas.pdf"
    _xmp_documento(
        pdf_fechas,
        '<x:xmpmeta xmlns:x="adobe:ns:meta/">'
        '<rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#">'
        '<rdf:Description rdf:about="" xmlns:xmp="http://ns.adobe.com/xap/1.0/">'
        "<xmp:CreateDate>2024-05-17</xmp:CreateDate>"
        "<xmp:Label>00</xmp:Label>"
        '<xmp:Rating dc:format="image/tiff" xmlns:dc="http://purl.org/dc/elements/1.1/">5</xmp:Rating>'
        "</rdf:Description></rdf:RDF></x:xmpmeta>",
    )
    json_fechas = tmp_path / "xmp-fechas.json"
    ejecutar(
        [sys.executable, str(CONTROL), "--config", str(config), str(pdf_fechas), "--anonimo", "--nombres", str(nombre_xmp), "--json", str(json_fechas)],
        tmp_path,
    )
    anon_fechas = resultado(informe(json_fechas), "anonimato")
    telefonos = [h for h in anon_fechas["datos"]["hallazgos"] if h["tipo"] == "telefono"]
    assert not telefonos, telefonos

    pdf_telefono = tmp_path / "xmp-telefono.pdf"
    _xmp_documento(
        pdf_telefono,
        '<x:xmpmeta xmlns:x="adobe:ns:meta/">'
        '<rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#">'
        '<rdf:Description rdf:about=""><xmp:Label xmlns:xmp="http://ns.adobe.com/xap/1.0/">202 555 0143</xmp:Label>'
        "</rdf:Description></rdf:RDF></x:xmpmeta>",
    )
    json_telefono = tmp_path / "xmp-telefono.json"
    ejecutar(
        [sys.executable, str(CONTROL), "--config", str(config), str(pdf_telefono), "--anonimo", "--nombres", str(nombre_xmp), "--json", str(json_telefono)],
        tmp_path,
    )
    anon_telefono = resultado(informe(json_telefono), "anonimato")
    assert any(h["tipo"] == "telefono" and h["canal"] == "xmp" for h in anon_telefono["datos"]["hallazgos"]), anon_telefono["datos"]["hallazgos"]

    pdf_fecha_telefono = tmp_path / "fecha-telefono.pdf"
    escribir_pdf_texto(pdf_fecha_telefono, [(1, "Fecha 17.05.2024 600 123 456")])
    json_fecha_telefono = tmp_path / "fecha-telefono.json"
    ejecutar(
        [sys.executable, str(CONTROL), "--config", str(config), str(pdf_fecha_telefono), "--anonimo", "--nombres", str(nombre_xmp), "--json", str(json_fecha_telefono)],
        tmp_path,
    )
    anon_fecha_telefono = resultado(informe(json_fecha_telefono), "anonimato")
    assert any(
        h["tipo"] == "telefono" and h["canal"] == "texto" and "600 123 456" in h["valor"]
        for h in anon_fecha_telefono["datos"]["hallazgos"]
    ), anon_fecha_telefono["datos"]["hallazgos"]


def test_canales_del_anonimato(tmp_path):
    config = crear_config(tmp_path / "base", idioma="es-en")
    nombre_xmp = tmp_path / "nombre-xmp.txt"
    nombre_xmp.write_text("Morgan Example\n", encoding="utf-8")

    canales_pdf = tmp_path / "canales.pdf"
    doc = pymupdf.open()
    pagina = doc.new_page(width=595, height=842)
    pagina.add_text_annot(pymupdf.Point(72, 72), "Morgan Example")
    pagina.add_file_annot(
        pymupdf.Point(72, 200),
        b"Contacto: persona.de.prueba@example.com\n",
        "nota.txt",
        ufilename="nota.txt",
        desc="adjunto de prueba",
    )
    doc.embfile_add(
        "datos.txt",
        b"Telefono: 202 555 0143\n",
        filename="datos.txt",
        ufilename="datos.txt",
        desc="adjunto incrustado",
    )
    pagina.insert_link(
        {"kind": pymupdf.LINK_URI, "from": pymupdf.Rect(72, 300, 200, 320), "uri": "https://example.com/privado"}
    )
    campo = pymupdf.Widget()
    campo.field_name = "contacto"
    campo.field_value = "Morgan Example"
    campo.rect = pymupdf.Rect(72, 400, 300, 420)
    campo.field_type = pymupdf.PDF_WIDGET_TYPE_TEXT
    pagina.add_widget(campo)
    doc.save(canales_pdf)
    doc.close()
    json_canales = tmp_path / "canales.json"
    ejecutar(
        [sys.executable, str(CONTROL), "--config", str(config), str(canales_pdf), "--anonimo", "--nombres", str(nombre_xmp), "--json", str(json_canales)],
        tmp_path,
    )
    anon_canales = resultado(informe(json_canales), "anonimato")
    canales_vistos = {h["canal"] for h in anon_canales["datos"]["hallazgos"]}
    assert anon_canales["estado"] == "fallo", anon_canales
    assert {"anotaciones", "enlaces", "formularios", "adjuntos-contenido"} <= canales_vistos, sorted(canales_vistos)
    assert any(adjunto["origen"] == "anotación" for adjunto in anon_canales["datos"]["adjuntos"])

    limpio_pdf = tmp_path / "canales-limpio.pdf"
    doc = pymupdf.open()
    pagina = doc.new_page(width=595, height=842)
    pagina.add_text_annot(pymupdf.Point(72, 72), "revisar composición")
    campo = pymupdf.Widget()
    campo.field_name = "version"
    campo.field_value = "1"
    campo.rect = pymupdf.Rect(72, 400, 300, 420)
    campo.field_type = pymupdf.PDF_WIDGET_TYPE_TEXT
    pagina.add_widget(campo)
    doc.embfile_add("nota.txt", b"Sin datos personales\n", filename="nota.txt", ufilename="nota.txt")
    doc.save(limpio_pdf)
    doc.close()
    json_limpio = tmp_path / "canales-limpio.json"
    ejecutar(
        [sys.executable, str(CONTROL), "--config", str(config), str(limpio_pdf), "--anonimo", "--nombres", str(nombre_xmp), "--json", str(json_limpio)],
        tmp_path,
    )
    anon_limpio = resultado(informe(json_limpio), "anonimato")
    assert anon_limpio["estado"] == "aviso" and not anon_limpio["datos"]["hallazgos"], anon_limpio
