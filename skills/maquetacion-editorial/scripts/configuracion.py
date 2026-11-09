"""Carga centralizada de maquetacion/config.md para los scripts editoriales."""
from __future__ import annotations

import json
import os
import re
import subprocess
from pathlib import Path
from typing import Any

IDIOMAS = {
    "es": {"caracteres": "ñÑ¿¡«»–—…’áéíóúüÁÉÍÓÚÜ", "pliego": "pliego", "pagina": "pág."},
    "en": {"caracteres": "‘’“”…–—", "pliego": "spread", "pagina": "p."},
}
VALORES_POR_DEFECTO: dict[str, Any] = {
    "carpeta_fuentes": "fuentes/",
    "sistema": True,
    "idiomas": ["es", "en"],
    "preferidas": [],
    "evitar": [],
    "licencias": {},
    "caracteres_extra": {},
    "version": "_v01",
    "nombres_sin_acentos_ni_espacios": True,
}


def _comentario_fuera_de_comillas(linea: str) -> str:
    """Quita el comentario `#`, que en YAML empieza la línea o sigue a un espacio.

    Un `#` pegado a un valor (`carpeta_fuentes: fuentes/#x`) es parte del valor,
    igual que en PyYAML.
    """
    comilla: str | None = None
    escapado = False
    for indice, caracter in enumerate(linea):
        if escapado:
            escapado = False
        elif caracter == "\\" and comilla:
            escapado = True
        elif caracter in "\"'":
            if comilla == caracter:
                comilla = None
            elif comilla is None:
                comilla = caracter
        elif caracter == "#" and comilla is None:
            if indice == 0 or linea[indice - 1].isspace():
                return linea[:indice]
    return linea


def _partir_clave(contenido: str) -> tuple[str, str, str]:
    """Separa «clave: valor» por los dos puntos que quedan fuera de comillas."""
    comilla: str | None = None
    escapado = False
    for indice, caracter in enumerate(contenido):
        if escapado:
            escapado = False
        elif caracter == "\\" and comilla:
            escapado = True
        elif caracter in "\"'":
            if comilla == caracter:
                comilla = None
            elif comilla is None:
                comilla = caracter
        elif caracter == ":" and comilla is None:
            return contenido[:indice], ":", contenido[indice + 1:]
    return contenido, "", ""


def _trozos_inline(texto: str) -> list[str]:
    partes: list[str] = []
    inicio = 0
    profundidad = 0
    comilla: str | None = None
    escapado = False
    for indice, caracter in enumerate(texto):
        if escapado:
            escapado = False
        elif caracter == "\\" and comilla:
            escapado = True
        elif caracter in "\"'":
            if comilla == caracter:
                comilla = None
            elif comilla is None:
                comilla = caracter
        elif comilla is None:
            if caracter in "[{":
                profundidad += 1
            elif caracter in "]}":
                profundidad -= 1
            elif caracter == "," and profundidad == 0:
                partes.append(texto[inicio:indice].strip())
                inicio = indice + 1
    partes.append(texto[inicio:].strip())
    return [parte for parte in partes if parte]


def _escalar(texto: str) -> Any:
    texto = texto.strip()
    if not texto:
        return None
    if texto.startswith("[") and texto.endswith("]"):
        interior = texto[1:-1].strip()
        return [_escalar(x) for x in _trozos_inline(interior)] if interior else []
    if texto.startswith("{") and texto.endswith("}"):
        interior = texto[1:-1].strip()
        salida: dict[str, Any] = {}
        for par in _trozos_inline(interior):
            clave, separador, valor = par.partition(":")
            if not separador:
                raise ValueError(f"entrada YAML no válida: {par}")
            salida[str(_escalar(clave))] = _escalar(valor)
        return salida
    if texto[0:1] in ("\"", "'") and texto[-1:] == texto[0]:
        if texto[0] == "\"":
            try:
                return json.loads(texto)
            except json.JSONDecodeError:
                return bytes(texto[1:-1], "utf-8").decode("unicode_escape")
        return texto[1:-1].replace("''", "'")
    bajo = texto.casefold()
    if bajo in ("sí", "si", "yes", "true", "on"):
        return True
    if bajo in ("no", "false", "off"):
        return False
    if bajo in ("null", "~"):
        return None
    if re.fullmatch(r"[-+]?\d+", texto):
        return int(texto)
    if re.fullmatch(r"[-+]?(?:\d+\.\d*|\.\d+)", texto):
        return float(texto)
    return texto


def _rechazar_tabulador(linea: str) -> None:
    """Rechaza un tabulador fuera de comillas, como hace PyYAML.

    El tabulador no sirve para indentar ni para separar una clave de su valor;
    aceptarlo en el lector mínimo daría configuraciones válidas con un analizador
    y no válidas con el otro.
    """
    comilla: str | None = None
    escapado = False
    for caracter in linea:
        if escapado:
            escapado = False
        elif caracter == "\\" and comilla:
            escapado = True
        elif caracter in "\"'":
            if comilla == caracter:
                comilla = None
            elif comilla is None:
                comilla = caracter
        elif caracter == "\t" and comilla is None:
            raise ValueError("tabulador no válido en YAML: use espacios como separador")


def _yaml_minimo(texto: str) -> Any:
    """Lee el subconjunto de YAML usado por config.md y las excepciones.

    Admite mapas y listas por indentación, las listas con el guion al mismo
    nivel que su clave, listas y mapas en línea (`[a, b]`, `{c: v}`), escalares
    entre comillas y los booleanos `sí`/`no`. Un archivo que empieza por `[` o
    `{` se lee entero como valor en flujo. No admite anclas ni alias,
    etiquetas, bloques escalares (`|`, `>`), varias líneas por valor, claves
    repetidas, fusiones (`<<`) ni tabuladores como separadores: para esos casos
    hace falta PyYAML.
    """
    filas: list[tuple[int, str]] = []
    for linea in texto.splitlines():
        limpia = _comentario_fuera_de_comillas(linea).rstrip()
        if not limpia.strip() or limpia.lstrip().startswith("---") or limpia.lstrip().startswith("..."):
            continue
        _rechazar_tabulador(limpia)
        indentacion = len(limpia) - len(limpia.lstrip(" "))
        filas.append((indentacion, limpia.strip()))

    if not filas:
        return {}
    if filas[0][1][0] in "[{":
        return _escalar(" ".join(fila for _, fila in filas))

    def bloque(indice: int, indentacion: int) -> tuple[Any, int]:
        es_lista = indice < len(filas) and filas[indice][0] == indentacion and filas[indice][1].startswith("-")
        resultado: Any = [] if es_lista else {}
        while indice < len(filas) and filas[indice][0] == indentacion:
            contenido = filas[indice][1]
            if es_lista:
                if not contenido.startswith("-"):
                    break
                resto = contenido[1:].strip()
                indice += 1
                if not resto:
                    if indice < len(filas) and filas[indice][0] > indentacion:
                        valor, indice = bloque(indice, filas[indice][0])
                    else:
                        valor = None
                    resultado.append(valor)
                    continue
                clave, separador, valor_txt = _partir_clave(resto)
                if separador and re.fullmatch(r"[A-Za-z0-9_-]+", clave.strip()):
                    elemento: dict[str, Any] = {}
                    if valor_txt.strip():
                        elemento[clave.strip()] = _escalar(valor_txt)
                    elif indice < len(filas) and filas[indice][0] > indentacion:
                        valor, indice = bloque(indice, filas[indice][0])
                        elemento[clave.strip()] = valor
                    else:
                        elemento[clave.strip()] = None
                    while indice < len(filas) and filas[indice][0] > indentacion:
                        siguiente_indent = filas[indice][0]
                        siguientes, indice = bloque(indice, siguiente_indent)
                        if not isinstance(siguientes, dict):
                            raise ValueError("estructura YAML de lista no válida")
                        elemento.update(siguientes)
                    resultado.append(elemento)
                else:
                    resultado.append(_escalar(resto))
            else:
                clave, separador, valor_txt = _partir_clave(contenido)
                if not separador or not clave.strip():
                    raise ValueError(f"entrada YAML no válida: {contenido}")
                indice += 1
                if valor_txt.strip():
                    valor = _escalar(valor_txt)
                elif indice < len(filas) and (
                    filas[indice][0] > indentacion
                    or (filas[indice][0] == indentacion and filas[indice][1].startswith("-"))
                ):
                    # El guion al mismo nivel que su clave sigue siendo su lista.
                    valor, indice = bloque(indice, filas[indice][0])
                else:
                    valor = None
                resultado[str(_escalar(clave.strip()))] = valor
                if indice < len(filas) and filas[indice][0] < indentacion:
                    break
        return resultado, indice

    if not filas:
        return {}
    resultado, indice = bloque(0, filas[0][0])
    if indice != len(filas):
        raise ValueError("estructura YAML no compatible con el analizador mínimo")
    return resultado


def leer_yaml(texto: str) -> Any:
    """Analiza YAML con PyYAML si está instalado, y usa el lector mínimo si no.

    Los errores de sintaxis de PyYAML se convierten en `ValueError`: así todos
    los scripts informan de una configuración no válida con código 2, en vez de
    terminar con una traza que se confunde con un fallo de control.
    """
    try:
        import yaml  # type: ignore
    except ImportError:
        return _yaml_minimo(texto)
    try:
        return yaml.safe_load(texto)
    except yaml.YAMLError as exc:
        raise ValueError(f"YAML no válido: {exc}") from exc


def _cabecera(texto: str) -> str:
    lineas = texto.splitlines()
    if not lineas or lineas[0].strip() != "---":
        raise ValueError("la configuración debe comenzar con una cabecera YAML entre ---")
    for indice in range(1, len(lineas)):
        if lineas[indice].strip() == "---":
            return "\n".join(lineas[1:indice])
    raise ValueError("la cabecera YAML no tiene cierre ---")


def _normalizar_configuracion(dato: Any, base: Path) -> dict[str, Any]:
    if dato is None:
        dato = {}
    if not isinstance(dato, dict):
        raise ValueError("la cabecera de configuración debe ser un mapa YAML")
    desconocidas = sorted(set(dato) - set(VALORES_POR_DEFECTO))
    if desconocidas:
        raise ValueError("campos de configuración desconocidos: " + ", ".join(map(str, desconocidas)))
    config = {**VALORES_POR_DEFECTO, **dato}
    carpeta = config["carpeta_fuentes"]
    if carpeta is not None and not isinstance(carpeta, str):
        raise ValueError("carpeta_fuentes debe ser una ruta o null")
    config["sistema"] = _booleano(config["sistema"], "sistema")
    config["nombres_sin_acentos_ni_espacios"] = _booleano(
        config["nombres_sin_acentos_ni_espacios"], "nombres_sin_acentos_ni_espacios"
    )
    if not isinstance(config["idiomas"], list) or not config["idiomas"] or not all(isinstance(x, str) for x in config["idiomas"]):
        raise ValueError("idiomas debe ser una lista no vacía de códigos")
    desconocidos = sorted(set(config["idiomas"]) - set(IDIOMAS))
    if desconocidos:
        raise ValueError("idiomas sin datos de caracteres y rótulos: " + ", ".join(desconocidos))
    for campo in ("preferidas", "evitar"):
        if not isinstance(config[campo], list) or not all(isinstance(x, str) for x in config[campo]):
            raise ValueError(f"{campo} debe ser una lista de nombres de familia")
    for campo in ("licencias", "caracteres_extra"):
        if not isinstance(config[campo], dict) or not all(isinstance(k, str) for k in config[campo]):
            raise ValueError(f"{campo} debe ser un mapa")
    if not all(isinstance(v, str) for v in config["licencias"].values()):
        raise ValueError("licencias debe asignar una nota de texto a cada familia")
    if not all(isinstance(v, str) for v in config["caracteres_extra"].values()):
        raise ValueError("caracteres_extra debe asignar texto a cada código de idioma")
    if not isinstance(config["version"], str):
        raise ValueError("version debe ser texto")
    config["carpeta_fuentes_en_config"] = "carpeta_fuentes" in dato
    config["directorio_proyecto"] = str(base)
    return config


def _booleano(valor: Any, campo: str) -> bool:
    if isinstance(valor, bool):
        return valor
    if isinstance(valor, str):
        normal = valor.casefold()
        if normal in ("sí", "si", "yes", "true", "on"):
            return True
        if normal in ("no", "false", "off"):
            return False
    raise ValueError(f"{campo} debe ser sí o no")


RUTA_CONFIG_POR_DEFECTO = Path("maquetacion") / "config.md"


def cargar_configuracion(ruta: str | Path | None = None) -> dict[str, Any]:
    """Carga maquetacion/config.md o los valores de nivel 0 si no se indica.

    Los valores por defecto solo se aplican cuando no se indica ninguna ruta.
    Una ruta explícita —aunque sea la de por defecto— se respeta: si no existe,
    es un error. Ignorarla cambia `idiomas` o `carpeta_fuentes` sin avisar.
    """
    explicita = ruta is not None
    destino = Path(ruta) if explicita else Path.cwd() / RUTA_CONFIG_POR_DEFECTO
    if not destino.is_file():
        if explicita:
            raise ValueError(f"no existe el archivo de configuración: {destino}")
        return _normalizar_configuracion({}, Path.cwd())
    destino = destino.expanduser().resolve()
    base = destino.parent.parent if destino.parent.name.lower() == "maquetacion" else destino.parent
    dato = leer_yaml(_cabecera(destino.read_text(encoding="utf-8-sig")))
    return _normalizar_configuracion(dato, base)


def caracteres_requeridos(config: dict[str, Any]) -> str:
    """Conjunto de caracteres del idioma, más los adicionales de la configuración.

    Se exige el conjunto completo de cada idioma configurado, no solo los
    caracteres que el texto acaba usando: una fuente que no pueda componer «¿»,
    «ñ» o «á» no sirve para un encargo en español aunque ese encargo concreto no
    llegue a escribirlos, porque cualquier corrección futura volvería a fallar.

    Se comparan signos, no espacios: los espacios que aparezcan en
    `caracteres_extra` se ignoran, porque un espacio no es un glifo que haya que
    exigir a la fuente.
    """
    caracteres = set()
    for idioma in config["idiomas"]:
        caracteres.update(IDIOMAS[idioma]["caracteres"])
    for extra in config["caracteres_extra"].values():
        caracteres.update(extra)
    caracteres = {caracter for caracter in caracteres if not caracter.isspace()}
    return "".join(sorted(caracteres))


def rotulos(idioma: str) -> dict[str, str]:
    """Rótulos de las hojas de contactos para español o inglés."""
    return IDIOMAS[idioma]


def carpeta_fuentes(config: dict[str, Any]) -> Path | None:
    """Resuelve carpeta_fuentes respecto de la raíz del encargo."""
    valor = config.get("carpeta_fuentes")
    if not valor:
        return None
    ruta = Path(valor).expanduser()
    if not ruta.is_absolute():
        ruta = Path(config["directorio_proyecto"]) / ruta
    return ruta


def raices_fuentes_sistema() -> list[Path]:
    """Directorios de fuentes instaladas, según Windows, macOS o Linux.

    La plataforma se consulta siempre con `sys.platform`, sin mezclar
    comprobaciones. En Linux se incluye `XDG_DATA_HOME` (o su valor por defecto,
    `~/.local/share`) y, en macOS, la carpeta de red que el sistema también
    consulta.
    """
    import sys

    home = Path.home()
    if sys.platform.startswith("win"):
        windows = Path(os.environ.get("WINDIR", r"C:\Windows"))
        local = Path(os.environ.get("LOCALAPPDATA", str(home / "AppData" / "Local")))
        rutas = [windows / "Fonts", local / "Microsoft" / "Windows" / "Fonts"]
    elif sys.platform == "darwin":
        rutas = [
            Path("/System/Library/Fonts"),
            Path("/Library/Fonts"),
            Path("/Network/Library/Fonts"),
            home / "Library" / "Fonts",
        ]
    else:
        datos = Path(os.environ.get("XDG_DATA_HOME", str(home / ".local" / "share")))
        rutas = [
            Path("/usr/share/fonts"),
            Path("/usr/local/share/fonts"),
            datos / "fonts",
            home / ".fonts",
        ]
    return [ruta for ruta in rutas if ruta.exists()]


def ficheros_fuente(config: dict[str, Any], incluir_sistema: bool | None = None) -> list[Path]:
    """Inventaría fuentes de la carpeta propia y, si procede, del sistema."""
    extensiones = {".ttf", ".otf", ".ttc"}
    raices: list[Path] = []
    propia = carpeta_fuentes(config)
    if propia and propia.exists():
        raices.append(propia)
    usar_sistema = config["sistema"] if incluir_sistema is None else incluir_sistema
    if usar_sistema:
        raices.extend(raices_fuentes_sistema())
    rutas: set[Path] = set()
    for raiz in raices:
        if raiz.is_file() and raiz.suffix.lower() in extensiones:
            rutas.add(raiz)
        elif raiz.is_dir():
            rutas.update(p for p in raiz.rglob("*") if p.is_file() and p.suffix.lower() in extensiones)
    return sorted(rutas, key=lambda p: str(p).casefold())


def inventario_typst(config: dict[str, Any], incluir_sistema: bool = False) -> dict[str, list[Path | None]]:
    """Obtiene familias vistas por Typst y sus ficheros (None representa fuente embebida)."""
    propia = carpeta_fuentes(config)
    comando = ["typst", "fonts", "--variants"]
    if not incluir_sistema:
        comando.append("--ignore-system-fonts")
    if propia and propia.is_dir():
        comando.extend(["--font-path", str(propia)])
    try:
        ejecucion = subprocess.run(comando, capture_output=True, text=True, encoding="utf-8", errors="replace", check=True)
    except (OSError, subprocess.CalledProcessError):
        return {}
    resultado: dict[str, list[Path | None]] = {}
    familia: str | None = None
    for linea in ejecucion.stdout.splitlines():
        if not linea[:1].isspace() and linea.strip():
            familia = linea.strip()
            resultado.setdefault(familia, [])
        elif familia and "(Embedded)" in linea:
            resultado[familia].append(None)
        elif familia and re.search(r"\.(?:ttf|otf|ttc)(?:\s|$)", linea, re.IGNORECASE):
            texto_ruta = re.sub(r"^[\s├└│─┬┤┴]+", "", linea).strip()
            texto_ruta = re.sub(r"\s+\((?:Variable|TrueType)\).*?$", "", texto_ruta)
            texto_ruta = re.sub(r"\s+Style:.*$", "", texto_ruta)
            ruta = Path(texto_ruta)
            if ruta.is_file():
                resultado[familia].append(ruta)
    return resultado
