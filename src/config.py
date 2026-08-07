import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
CONFIG_PATH = BASE_DIR / "data" / "config.json"


def _leer():
    if CONFIG_PATH.exists():
        try:
            return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return {}
    return {}


def _guardar(datos):
    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    CONFIG_PATH.write_text(json.dumps(datos, ensure_ascii=False, indent=2), encoding="utf-8")


def obtener_carpeta_exportacion():
    return _leer().get("carpeta_exportacion")


def guardar_carpeta_exportacion(ruta):
    datos = _leer()
    datos["carpeta_exportacion"] = str(ruta)
    _guardar(datos)
