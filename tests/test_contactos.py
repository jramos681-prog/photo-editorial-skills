"""Hoja de contactos: salida, dependencias y fuente de los rótulos."""

from __future__ import annotations

import os
import re
import sys

from soporte import CONTACTOS, SCRIPTS, bloqueador, carpeta_config, construir_fuentes, crear_config, ejecutar, pdf_vacio


def test_hoja_de_contactos_en_ingles_y_cp1252(tmp_path):
    config = crear_config(tmp_path / "contactos", idioma="en", sistema=False)
    pdf = pdf_vacio(tmp_path / "contactos" / "una-pagina.pdf")
    salida = tmp_path / "contactos" / "hojas"
    stdout_path = tmp_path / "contactos" / "stdout.bin"
    entorno = os.environ.copy()
    entorno["PYTHONIOENCODING"] = "cp1252"
    with stdout_path.open("wb") as fichero:
        contacto = ejecutar(
            [sys.executable, str(CONTACTOS), str(pdf), "--config", str(config), "--modo", "paginas", "--salida", str(salida)],
            tmp_path,
            env=entorno,
            stdout=fichero,
        )
    stdout_utf8 = stdout_path.read_bytes().decode("utf-8")
    assert contacto.returncode == 0 and "→" in stdout_utf8, contacto.stderr.decode(errors="replace")
    assert list(salida.glob("*.png")), "hoja_contactos.py no generó PNG en inglés"
    assert "modo paginas" in stdout_utf8

    pliegos = ejecutar(
        [sys.executable, str(CONTACTOS), str(pdf), "--config", str(config), "--salida", str(tmp_path / "hojas-pliegos")],
        tmp_path,
    )
    assert pliegos.returncode == 0 and "modo pliegos" in pliegos.stdout.decode("utf-8")


def test_hoja_de_contactos_sin_pillow(tmp_path):
    config = crear_config(tmp_path / "contactos", idioma="en", sistema=False)
    pdf = pdf_vacio(tmp_path / "una-pagina.pdf")
    entorno = bloqueador(tmp_path, "bloquea-pillow", "PIL")
    sin_pillow = ejecutar(
        [sys.executable, str(CONTACTOS), str(pdf), "--config", str(config)],
        tmp_path,
        env=entorno,
    )
    assert sin_pillow.returncode == 2 and b"falta Pillow" in sin_pillow.stderr, sin_pillow.stderr.decode(errors="replace")


def test_fuente_de_los_rotulos(tmp_path):
    fuentes = construir_fuentes(tmp_path / "fuentes")
    config_preferida = crear_config(
        tmp_path / "rotulos",
        idioma="es",
        sistema=False,
        carpeta=carpeta_config(fuentes),
        campos="preferidas: [Prueba]\n",
    )
    config_propia = crear_config(
        tmp_path / "rotulos-propia",
        idioma="es",
        sistema=False,
        carpeta=carpeta_config(fuentes / "otra"),
    )
    codigo = (
        f"import sys; sys.path.insert(0, {str(SCRIPTS)!r}); import configuracion, hoja_contactos; "
        f"c1 = configuracion.cargar_configuracion({str(config_preferida)!r}); "
        f"c2 = configuracion.cargar_configuracion({str(config_propia)!r}); "
        "l1 = hoja_contactos.fuente(12, c1, 'pliego 0123-'); "
        "l2 = hoja_contactos.fuente(12, c2, 'pliego 0123-'); "
        "print('PREFERIDA=' + getattr(l1, 'path', '')); "
        "print('PROPIA=' + getattr(l2, 'path', ''))"
    )
    rotulos = ejecutar([sys.executable, "-B", "-c", codigo], tmp_path)
    assert rotulos.returncode == 0, rotulos.stderr.decode(errors="replace")
    assert b"not enough data in post.stringData" not in rotulos.stderr, rotulos.stderr.decode(errors="replace")
    salida = rotulos.stdout.decode("utf-8", errors="replace")
    preferida = re.search(r"PREFERIDA=(.+)", salida)
    propia = re.search(r"PROPIA=(.+)", salida)
    assert preferida is not None and preferida.group(1).strip().endswith("Prueba-Regular.ttf"), salida
    assert propia is not None and propia.group(1).strip().endswith("Otra-Regular.ttf"), salida

    entorno_ft = bloqueador(tmp_path, "bloquea-fonttools", "fontTools")
    sin_ft = ejecutar([sys.executable, "-B", "-c", codigo], tmp_path, env=entorno_ft)
    assert sin_ft.returncode == 0, sin_ft.stderr.decode(errors="replace")
    assert "falta fontTools" in sin_ft.stderr.decode("utf-8", errors="replace")
