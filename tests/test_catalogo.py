"""Catálogo de fuentes: grupos, recursos OpenType, métricas y huella."""

from __future__ import annotations

import re
import shutil
import sys

from fontTools.ttLib import TTFont
from fontTools.feaLib.builder import addOpenTypeFeaturesFromString

from soporte import CATALOGO, bloqueador, carpeta_config, construir_fuente, crear_config, ejecutar

CONTEO = r"Familias aptas para texto: (\d+); solo para títulos y rótulos: (\d+); no aptas: (\d+)\."


def _catalogo(tmp_path, config, *extra):
    salida = ejecutar([sys.executable, str(CATALOGO), "--config", str(config), *extra], tmp_path)
    texto = (config.parent.parent / "maquetacion" / "catalogo.md").read_text(encoding="utf-8")
    return salida, texto


def _catalogo_de_una_fuente(tmp_path, etiqueta, fuente, config_extra=""):
    carpeta = tmp_path / f"fuentes-{etiqueta}"
    carpeta.mkdir()
    fuente.save(carpeta / f"Prueba-{etiqueta}.ttf")
    fuente.close()
    config = crear_config(
        tmp_path / f"catalogo-{etiqueta}",
        idioma="es",
        sistema=False,
        carpeta=carpeta_config(carpeta),
        campos=config_extra,
    )
    salida, texto = _catalogo(tmp_path, config)
    assert salida.returncode == 0, salida.stderr.decode(errors="replace")
    return texto


def test_catalogo_con_fuente_propia(tmp_path):
    fuentes = tmp_path / "fuentes"
    construir_fuente(fuentes / "Prueba-Regular.ttf")
    config = crear_config(
        tmp_path / "catalogo",
        idioma="es-en",
        sistema=True,
        carpeta=carpeta_config(fuentes),
        campos="preferidas: [Prueba]\nevitar: [Inexistente]\nlicencias:\n  Prueba: Nota de licencia de prueba\n",
    )
    salida, texto = _catalogo(tmp_path, config)
    assert salida.returncode == 0, salida.stderr.decode(errors="replace")
    assert (config.parent.parent / "maquetacion" / "catalogo.md").is_file()
    conteos = re.search(CONTEO, salida.stdout.decode("utf-8"))
    assert conteos is not None, salida.stdout.decode(errors="replace")
    assert "## Aptas para texto (" in texto
    assert "## Solo para títulos y rótulos (" in texto
    assert "## No aptas (" in texto
    assert "fsType" in texto
    assert "**Prueba**" in texto


def test_catalogo_solo_con_fuentes_de_typst(tmp_path):
    config = crear_config(
        tmp_path / "catalogo-typst",
        idioma="es-en",
        sistema=False,
        carpeta="null",
        campos="preferidas: [Arial]\nevitar: [Calibri]\nlicencias:\n  Arial: Nota de prueba\n",
    )
    salida, texto = _catalogo(tmp_path, config)
    assert salida.returncode == 0, salida.stderr.decode(errors="replace")
    conteos = re.search(CONTEO, salida.stdout.decode("utf-8"))
    assert conteos is not None and int(conteos.group(1)) > 0, texto
    aptas = texto.split("## Aptas para texto", 1)[1].split("## Solo para títulos y rótulos", 1)[0]
    assert "incluida en Typst (OFL); cobertura no medida" in aptas
    assert re.search(r"Huella: `[0-9a-f]{16}`", texto) is not None
    assert "nombres que no aparecen en el inventario: Arial" in texto
    assert "nombres que no aparecen en el inventario: Calibri" in texto


def test_catalogo_sin_fonttools(tmp_path):
    config = crear_config(tmp_path / "catalogo-typst", idioma="es-en", sistema=False, carpeta="null")
    entorno = bloqueador(tmp_path, "bloquea-fonttools", "fontTools")
    salida = ejecutar([sys.executable, str(CATALOGO), "--config", str(config)], tmp_path, env=entorno)
    assert salida.returncode == 2
    assert "falta fontTools: sin él no se puede medir cmap ni OS/2.fsType" in salida.stderr.decode("utf-8", errors="replace")


def test_catalogo_avisa_de_la_carpeta_ausente(tmp_path):
    ausente = crear_config(
        tmp_path / "catalogo-ausente",
        idioma="es",
        sistema=False,
        carpeta=carpeta_config(tmp_path / "carpeta-que-no-existe"),
    )
    salida, texto = _catalogo(tmp_path, ausente)
    assert salida.returncode == 0, salida.stderr.decode(errors="replace")
    assert "la carpeta propia de fuentes no existe" in texto
    assert "la carpeta propia de fuentes no existe" in salida.stderr.decode("utf-8", errors="replace")

    defecto = tmp_path / "catalogo-defecto"
    defecto.mkdir()
    sin_config = ejecutar([sys.executable, str(CATALOGO)], defecto)
    assert sin_config.returncode == 0, sin_config.stderr.decode(errors="replace")
    texto_defecto = (defecto / "maquetacion" / "catalogo.md").read_text(encoding="utf-8")
    assert "la carpeta propia de fuentes no existe" not in sin_config.stderr.decode("utf-8", errors="replace")
    assert "la carpeta propia de fuentes no existe" not in texto_defecto

    escrita = crear_config(tmp_path / "catalogo-carpeta-defecto", idioma="es", sistema=False, carpeta="fuentes/")
    con_defecto = ejecutar([sys.executable, str(CATALOGO), "--config", str(escrita)], tmp_path)
    assert con_defecto.returncode == 0
    assert "la carpeta propia de fuentes no existe" in con_defecto.stderr.decode("utf-8", errors="replace")


def test_catalogo_fuente_no_incrustable_y_sin_ene(tmp_path):
    base = construir_fuente(tmp_path / "base" / "Prueba-Regular.ttf")

    carpeta_no = tmp_path / "fuentes-no-incrustable"
    carpeta_no.mkdir()
    fuente = TTFont(str(base))
    fuente["OS/2"].fsType = 0x0002
    fuente.save(carpeta_no / "Prueba-NoIncrustable.ttf")
    fuente.close()
    config_no = crear_config(tmp_path / "catalogo-no-incrustable", idioma="es", sistema=False, carpeta=carpeta_config(carpeta_no))
    salida, texto = _catalogo(tmp_path, config_no)
    assert salida.returncode == 0, salida.stderr.decode(errors="replace")
    seccion_no = texto.split("## No aptas", 1)[1].split("## Avisos", 1)[0]
    assert "OS/2.fsType no permite incrustar" in seccion_no and "**Prueba**" in seccion_no, seccion_no

    carpeta_sin = tmp_path / "fuentes-sin-ene"
    carpeta_sin.mkdir()
    fuente = TTFont(str(base))
    for tabla in fuente["cmap"].tables:
        tabla.cmap.pop(0x00F1, None)
    fuente.save(carpeta_sin / "Prueba-SinEne.ttf")
    fuente.close()
    config_sin = crear_config(tmp_path / "catalogo-sin-ene", idioma="es", sistema=False, carpeta=carpeta_config(carpeta_sin))
    salida, texto = _catalogo(tmp_path, config_sin)
    assert salida.returncode == 0, salida.stderr.decode(errors="replace")
    seccion_titulos = texto.split("## Solo para títulos y rótulos", 1)[1].split("## No aptas", 1)[0]
    assert "faltan: ñ" in seccion_titulos and "**Prueba**" in seccion_titulos, seccion_titulos


def test_catalogo_recursos_opentype(tmp_path):
    base = construir_fuente(tmp_path / "base" / "Prueba-Regular.ttf")

    fuente_versalitas = TTFont(str(base))
    addOpenTypeFeaturesFromString(
        fuente_versalitas,
        "feature smcp { sub a by A; } smcp;\n"
        "feature c2sc { sub A by a; } c2sc;\n"
        "feature onum { sub zero by one; } onum;\n",
    )
    texto_versalitas = _catalogo_de_una_fuente(tmp_path, "versalitas", fuente_versalitas)
    assert "VC (smcp+c2sc)" in texto_versalitas and "alt.: onum" in texto_versalitas, texto_versalitas

    texto_sin = _catalogo_de_una_fuente(tmp_path, "sin-recursos", TTFont(str(base)))
    assert "VC (smcp)" not in texto_sin and "sin VC" in texto_sin and "alt.: ninguna" in texto_sin, texto_sin

    fuente_antiguas = TTFont(str(base))
    glifos = fuente_antiguas["glyf"]
    for nombre in ("three", "five", "seven", "nine"):
        glifos[nombre].coordinates.translate((0, -300))
        glifos[nombre].recalcBounds(glifos)
    glifos["zero"].coordinates.translate((0, -400))
    glifos["zero"].recalcBounds(glifos)
    mapa = fuente_antiguas.getBestCmap()
    for digito in "0123456789":
        _, lateral = fuente_antiguas["hmtx"][mapa[ord(digito)]]
        fuente_antiguas["hmtx"][mapa[ord(digito)]] = (1000, lateral)
    texto_antiguas = _catalogo_de_una_fuente(tmp_path, "antiguas", fuente_antiguas)
    assert "cifras: ant., tab." in texto_antiguas, texto_antiguas
    assert "cifras: alin." not in texto_antiguas, texto_antiguas


def test_catalogo_metricas_y_contorno(tmp_path):
    base = construir_fuente(tmp_path / "base" / "Prueba-Regular.ttf")

    fuente = TTFont(str(base))
    upm = fuente["head"].unitsPerEm
    fuente["OS/2"].sxHeight = 1024
    fuente["OS/2"].sCapHeight = 1536
    for nombre in fuente.getGlyphOrder():
        _, lateral = fuente["hmtx"][nombre]
        fuente["hmtx"][nombre] = (1000, lateral)
    texto = _catalogo_de_una_fuente(tmp_path, "metricas", fuente)
    avance_esperado = 1000 / upm * 10 * 25.4 / 72
    texto_avance = "av.: " + f"{avance_esperado:.4f}".replace(".", ",") + " mm/car"
    assert "x: 0,500; M: 0,750" in texto and texto_avance in texto, texto

    linea = next(linea for linea in texto.splitlines() if linea.startswith("- **Prueba**"))
    avance = float(re.search(r"av\.: ([\d,]+) mm/car", linea).group(1).replace(",", "."))
    cpl = float(re.search(r"CPL: ([\d,]+)", linea).group(1).replace(",", "."))
    assert abs(cpl - 140.0 / avance) <= 0.05, linea

    contorno = TTFont(str(base))
    contorno["OS/2"].sxHeight = 0
    contorno["OS/2"].sCapHeight = 0
    texto_contorno = _catalogo_de_una_fuente(tmp_path, "contorno", contorno)
    assert "(alturas del contorno)" in texto_contorno, texto_contorno


def test_catalogo_huella(tmp_path):
    base = construir_fuente(tmp_path / "base" / "Prueba-Regular.ttf")
    carpeta = tmp_path / "fuentes-huella"
    carpeta.mkdir()
    fuente_huella = carpeta / base.name
    shutil.copy2(base, fuente_huella)

    def huella(nombre: str) -> str:
        config = crear_config(tmp_path / nombre, idioma="es", sistema=False, carpeta=carpeta_config(carpeta))
        salida, texto = _catalogo(tmp_path, config)
        assert salida.returncode == 0, salida.stderr.decode(errors="replace")
        encontrada = re.search(r"Huella: `([0-9a-f]{16})`", texto)
        assert encontrada is not None, f"El catálogo {nombre} no lleva huella"
        return encontrada.group(1)

    huella_uno = huella("huella-uno")
    tamano = fuente_huella.stat().st_size
    contenido = bytearray(fuente_huella.read_bytes())
    contenido[len(contenido) // 2] ^= 0xFF
    fuente_huella.write_bytes(bytes(contenido))
    assert fuente_huella.stat().st_size == tamano
    huella_dos = huella("huella-dos")
    assert huella_uno != huella_dos, "La huella no cambia al cambiar el contenido de una fuente del mismo tamaño"


def test_catalogo_del_sistema_compacto(tmp_path):
    config = crear_config(tmp_path / "catalogo-sistema", idioma="es-en", sistema=True, carpeta="null")
    salida, texto = _catalogo(tmp_path, config)
    assert salida.returncode == 0, salida.stderr.decode(errors="replace")
    entradas = [linea for linea in texto.splitlines() if linea.startswith("- **")]
    assert entradas, "El catálogo no lista familias aptas"
    assert max(len(linea) for linea in entradas) <= 300, "Una entrada del catálogo no cabe en una línea legible"
    assert len(texto) < 20000, f"El catálogo no es compacto: {len(texto)} caracteres"
