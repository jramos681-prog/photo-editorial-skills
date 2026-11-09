"""Configuración de los scripts: lector YAML, rutas y errores de entrada."""

from __future__ import annotations

import sys

import pytest

from soporte import CATALOGO, CONTROL, CONTACTOS, LIBRERIA, SCRIPTS, bloqueador, ejecutar, pdf_vacio


def test_autoprueba_de_control_pdf(tmp_path):
    prueba = ejecutar([sys.executable, str(CONTROL), "--autoprueba"], tmp_path)
    assert prueba.returncode == 0, prueba.stderr.decode(errors="replace")
    assert b"todos los casos se comportan como se espera" in prueba.stdout


def test_lector_yaml_minimo(tmp_path):
    muestra_yaml = (
        "carpeta_fuentes: null\nsistema: sí\nidiomas: [es, en]\npreferidas: []\n"
        "licencias: {}\ncaracteres_extra: {}\n"
    )
    excepcion_yaml = "- pagina: 1\n  control: medida\n  bloque: CITA\n  tipo: cita\n  motivo: test\n"
    codigo = (
        f"import sys; sys.path.insert(0, {str(SCRIPTS)!r}); import configuracion; "
        f"cfg=configuracion._yaml_minimo({muestra_yaml!r}); "
        f"ex=configuracion._yaml_minimo({excepcion_yaml!r}); "
        "assert cfg['sistema'] is True and cfg['idiomas']==['es','en']; "
        "assert ex[0]['bloque']=='CITA' and ex[0]['tipo']=='cita'; print('fallback YAML: OK')"
    )
    fallback = ejecutar([sys.executable, "-B", "-c", codigo], tmp_path)
    assert fallback.returncode == 0 and b"fallback YAML: OK" in fallback.stdout, fallback.stderr.decode(errors="replace")


def test_limites_del_lector_minimo(tmp_path):
    codigo = (
        f"import sys; sys.path.insert(0, {str(SCRIPTS)!r}); import configuracion as c; "
        "assert c._yaml_minimo('evitar:\\n- Calibri\\n') == {'evitar': ['Calibri']}; "
        "assert c._yaml_minimo('\"Otra: Fam\": nota\\n') == {'Otra: Fam': 'nota'}; "
        "assert c._yaml_minimo('carpeta_fuentes: fuentes/#x\\n') == {'carpeta_fuentes': 'fuentes/#x'}; "
        "assert c._yaml_minimo('carpeta_fuentes: fuentes/  # nota\\n') == {'carpeta_fuentes': 'fuentes/'}; "
        "print('yaml minimo: OK')"
    )
    limites = ejecutar([sys.executable, "-B", "-c", codigo], tmp_path)
    assert limites.returncode == 0, limites.stderr.decode(errors="replace")


def test_conjunto_de_caracteres(tmp_path):
    codigo = (
        f"import sys; sys.path.insert(0, {str(SCRIPTS)!r}); import configuracion as c; "
        "cfg = dict(c.VALORES_POR_DEFECTO); cfg['caracteres_extra'] = {'ro': 'ș ț Ș Ț'}; "
        "conjunto = c.caracteres_requeridos(cfg); "
        "assert ' ' not in conjunto, conjunto; "
        "assert all(v in conjunto for v in 'șțȘȚáéíóúüÁÉÍÓÚÜñÑ¿¡«»'), conjunto; "
        "assert c.caracteres_requeridos({'idiomas': ['en'], 'caracteres_extra': {}}) == ''.join(sorted('‘’“”–—…')); "
        "print('caracteres: OK')"
    )
    caracteres = ejecutar([sys.executable, "-B", "-c", codigo], tmp_path)
    assert caracteres.returncode == 0, caracteres.stderr.decode(errors="replace")


def test_deteccion_de_plataforma(tmp_path):
    codigo = (
        f"import os, pathlib, sys, tempfile; sys.path.insert(0, {str(SCRIPTS)!r}); import configuracion as c; "
        "datos = pathlib.Path(tempfile.mkdtemp()); (datos / 'fonts').mkdir(); "
        "os.environ['XDG_DATA_HOME'] = str(datos); sys.platform = 'linux'; "
        "rutas = [str(r) for r in c.raices_fuentes_sistema()]; "
        "assert str(datos / 'fonts') in rutas, rutas; "
        "assert all(pathlib.Path(r).is_dir() for r in rutas), rutas; print('plataformas: OK')"
    )
    plataformas = ejecutar([sys.executable, "-B", "-c", codigo], tmp_path)
    assert plataformas.returncode == 0, plataformas.stderr.decode(errors="replace")


def test_config_explicita_ausente(tmp_path):
    pdf = pdf_vacio(tmp_path / "pagina.pdf")
    inexistente = tmp_path / "no-existe" / "maquetacion" / "config.md"
    for comando in (
        [sys.executable, str(CONTROL), str(pdf)],
        [sys.executable, str(CONTACTOS), str(pdf)],
        [sys.executable, str(CATALOGO)],
    ):
        rechazo = ejecutar([*comando, "--config", str(inexistente)], tmp_path)
        assert rechazo.returncode == 2, rechazo.stderr.decode(errors="replace")
        assert "no existe el archivo de configuración" in rechazo.stderr.decode("utf-8", errors="replace")


def test_config_por_defecto(tmp_path):
    pdf = pdf_vacio(tmp_path / "pagina.pdf")
    sin_config = tmp_path / "sin-config"
    sin_config.mkdir()
    for comando in (
        [sys.executable, str(CONTROL), str(pdf)],
        [sys.executable, str(CONTACTOS), str(pdf)],
        [sys.executable, str(CATALOGO)],
    ):
        explicita = ejecutar([*comando, "--config", "maquetacion/config.md"], sin_config)
        assert explicita.returncode == 2
        assert "no existe el archivo de configuración" in explicita.stderr.decode("utf-8", errors="replace")
        implicita = ejecutar(comando, sin_config)
        assert implicita.returncode in (0, 1), implicita.stderr.decode(errors="replace")
        assert "no existe el archivo de configuración" not in implicita.stderr.decode("utf-8", errors="replace")


def test_yaml_roto(tmp_path):
    pdf = pdf_vacio(tmp_path / "pagina.pdf")
    config_rota = tmp_path / "rota" / "maquetacion" / "config.md"
    config_rota.parent.mkdir(parents=True)
    config_rota.write_text("---\nidiomas: [es\nsistema:\tno\n---\n", encoding="utf-8")
    for comando in (
        [sys.executable, str(CONTROL), str(pdf)],
        [sys.executable, str(CONTACTOS), str(pdf)],
        [sys.executable, str(CATALOGO)],
    ):
        roto = ejecutar([*comando, "--config", str(config_rota)], tmp_path)
        assert roto.returncode == 2, roto.stderr.decode(errors="replace")
        assert b"Traceback" not in roto.stderr


def test_excepciones_json_o_yaml(tmp_path):
    from soporte import crear_config

    pdf = pdf_vacio(tmp_path / "pagina.pdf")
    config = crear_config(tmp_path / "base", idioma="es-en")
    exc_flow = tmp_path / "excepciones-flow.yaml"
    exc_flow.write_text("[{pagina: 1, control: medida, bloque: 1, tipo: cita, motivo: prueba}]\n", encoding="utf-8")
    flow = ejecutar(
        [sys.executable, str(CONTROL), "--config", str(config), str(pdf), "--excepciones", str(exc_flow)],
        tmp_path,
    )
    assert flow.returncode == 0, flow.stderr.decode(errors="replace")
    exc_rota = tmp_path / "excepciones-rotas.yaml"
    exc_rota.write_text("[1\n", encoding="utf-8")
    rotas = ejecutar(
        [sys.executable, str(CONTROL), "--config", str(config), str(pdf), "--excepciones", str(exc_rota)],
        tmp_path,
    )
    assert rotas.returncode == 2 and b"no es JSON ni YAML" in rotas.stderr


def test_sin_pyyaml(tmp_path):
    from soporte import crear_config

    pdf = pdf_vacio(tmp_path / "pagina.pdf")
    config = crear_config(tmp_path / "base", idioma="es-en")
    exc_flow = tmp_path / "excepciones-flow.yaml"
    exc_flow.write_text("[{pagina: 1, control: medida, bloque: 1, tipo: cita, motivo: prueba}]\n", encoding="utf-8")
    entorno_yaml = bloqueador(tmp_path, "bloquea-yaml", "yaml")
    flow_sin_yaml = ejecutar(
        [sys.executable, "-B", str(CONTROL), "--config", str(config), str(pdf), "--excepciones", str(exc_flow)],
        tmp_path,
        env=entorno_yaml,
    )
    assert flow_sin_yaml.returncode == 0, flow_sin_yaml.stderr.decode(errors="replace")
    config_tab = tmp_path / "tab" / "maquetacion" / "config.md"
    config_tab.parent.mkdir(parents=True)
    config_tab.write_text("---\nsistema:\tno\n---\n", encoding="utf-8")
    tab_sin_yaml = ejecutar(
        [sys.executable, "-B", str(CATALOGO), "--config", str(config_tab)],
        tmp_path,
        env=entorno_yaml,
    )
    assert tab_sin_yaml.returncode == 2 and b"Traceback" not in tab_sin_yaml.stderr


@pytest.mark.parametrize(
    "ruta",
    [CONTROL, CONTACTOS, CATALOGO, SCRIPTS / "configuracion.py", LIBRERIA],
    ids=lambda ruta: ruta.name,
)
def test_finales_de_linea_lf(ruta):
    contenido = ruta.read_bytes()
    assert contenido.count(b"\r\n") == 0, f"{ruta.name} tiene finales de línea CRLF"
    assert contenido.endswith(b"\n") and not contenido.endswith(b"\n\n"), f"{ruta.name} no termina en un único salto de línea"
