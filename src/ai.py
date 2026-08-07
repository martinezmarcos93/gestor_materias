import json
import shutil
import subprocess

MODELOS = ["sonnet", "opus", "haiku"]
MODELO_DEFAULT = "sonnet"
LIMITE_CHARS = 15000
TIMEOUT_DEFAULT = 180

SISTEMA = (
    "Sos un asistente de estudio para un estudiante universitario. Respondes siempre "
    "en espanol, de forma clara y academica, basandote en el texto que se te da."
)

# Sin herramientas: cada consulta es texto-a-texto, sin tocar archivos ni la red.
HERRAMIENTAS_DESHABILITADAS = "Bash,Edit,Write,Read,WebSearch,WebFetch,NotebookEdit,Glob,Grep,Task"


class ClaudeCodeNoDisponible(Exception):
    pass


class ClaudeCodeError(Exception):
    pass


def esta_instalado():
    return shutil.which("claude") is not None


def verificar_conexion(timeout=30):
    """Corre una consulta minima para confirmar instalacion + sesion activa.
    Devuelve (ok: bool, mensaje: str)."""
    if not esta_instalado():
        return False, (
            "No se encontro el comando 'claude'. Instala Claude Code con:\n"
            "npm install -g @anthropic-ai/claude-code\n"
            "y despues ejecuta 'claude login' una vez."
        )
    try:
        resultado = _ejecutar(
            "Respondes unicamente con la palabra: listo", modelo="haiku", timeout=timeout
        )
        return True, f"Conectado correctamente. Respuesta de prueba: {resultado!r}"
    except ClaudeCodeError as exc:
        return False, str(exc)


def _ejecutar(prompt, modelo=MODELO_DEFAULT, system_prompt=SISTEMA, timeout=TIMEOUT_DEFAULT):
    ruta_claude = shutil.which("claude")
    if not ruta_claude:
        raise ClaudeCodeNoDisponible(
            "No se encontro el comando 'claude'. Instala Claude Code y ejecuta 'claude login'."
        )

    comando = [
        ruta_claude,
        "-p",
        prompt,
        "--output-format",
        "json",
        "--model",
        modelo,
        "--system-prompt",
        system_prompt,
        "--disallowedTools",
        HERRAMIENTAS_DESHABILITADAS,
    ]

    try:
        proceso = subprocess.run(
            comando,
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=timeout,
        )
    except subprocess.TimeoutExpired:
        raise ClaudeCodeError("La consulta a Claude tardo demasiado y se cancelo.")
    except OSError as exc:
        raise ClaudeCodeError(f"No se pudo ejecutar Claude Code: {exc}")

    if proceso.returncode != 0:
        detalle = (proceso.stderr or proceso.stdout or "").strip()[:500]
        raise ClaudeCodeError(f"Claude Code fallo (codigo {proceso.returncode}): {detalle}")

    try:
        data = json.loads(proceso.stdout)
    except json.JSONDecodeError:
        raise ClaudeCodeError(f"Respuesta inesperada de Claude Code: {proceso.stdout[:300]}")

    if data.get("is_error") or data.get("subtype") != "success":
        raise ClaudeCodeError(data.get("result") or "Error desconocido al consultar a Claude.")

    return data.get("result", "").strip()


def resumir(texto, modelo=MODELO_DEFAULT):
    prompt = (
        "Resumi el siguiente texto de bibliografia academica, identificando la tesis "
        "principal, los argumentos secundarios y las conclusiones, en no mas de 300 "
        f"palabras.\n\nTEXTO:\n{texto[:LIMITE_CHARS]}"
    )
    return _ejecutar(prompt, modelo)


def preguntas_de_estudio(texto, modelo=MODELO_DEFAULT):
    prompt = (
        "A partir del siguiente texto de bibliografia de una materia, genera 8 "
        "preguntas de estudio que podrian aparecer en un parcial, de dificultad "
        f"variada. Numeralas.\n\nTEXTO:\n{texto[:LIMITE_CHARS]}"
    )
    return _ejecutar(prompt, modelo)


def analizar_fuente(texto, modelo=MODELO_DEFAULT):
    prompt = (
        "Analiza el siguiente texto como fuente academica, indicando en secciones "
        "claras: 1) tipo de fuente (primaria o secundaria) y por que, 2) corriente o "
        "postura teorica si es identificable, 3) posibles sesgos o limitaciones, "
        f"4) conceptos clave que introduce.\n\nTEXTO:\n{texto[:LIMITE_CHARS]}"
    )
    return _ejecutar(prompt, modelo)


def consulta_libre(texto, pregunta, modelo=MODELO_DEFAULT):
    prompt = (
        f"Tenes el siguiente fragmento de bibliografia:\n\n{texto[:LIMITE_CHARS]}\n\n"
        f"Respondes esta consulta del estudiante, basandote en el texto anterior: {pregunta}"
    )
    return _ejecutar(prompt, modelo)
