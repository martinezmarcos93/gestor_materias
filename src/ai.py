import json
import re
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


def _con_contexto_catedra(prompt_base, contexto_catedra):
    if not contexto_catedra:
        return prompt_base
    return (
        "Contexto: la catedra de esta materia tiene la siguiente perspectiva/enfoque "
        f"(segun su programa) - tenela en cuenta en tu analisis, ya que un mismo texto "
        f"puede leerse distinto segun el enfoque de la catedra:\n{contexto_catedra}\n\n"
        + prompt_base
    )


def resumir(texto, modelo=MODELO_DEFAULT, contexto_catedra=None):
    prompt = _con_contexto_catedra(
        "Resumi el siguiente texto de bibliografia academica, identificando la tesis "
        "principal, los argumentos secundarios y las conclusiones, en no mas de 300 "
        f"palabras.\n\nTEXTO:\n{texto[:LIMITE_CHARS]}",
        contexto_catedra,
    )
    return _ejecutar(prompt, modelo)


def preguntas_de_estudio(texto, modelo=MODELO_DEFAULT, contexto_catedra=None):
    prompt = _con_contexto_catedra(
        "A partir del siguiente texto de bibliografia de una materia, genera 8 "
        "preguntas de estudio que podrian aparecer en un parcial, de dificultad "
        f"variada. Numeralas.\n\nTEXTO:\n{texto[:LIMITE_CHARS]}",
        contexto_catedra,
    )
    return _ejecutar(prompt, modelo)


def analizar_fuente(texto, modelo=MODELO_DEFAULT, contexto_catedra=None):
    prompt = _con_contexto_catedra(
        "Analiza el siguiente texto como fuente academica, indicando en secciones "
        "claras: 1) tipo de fuente (primaria o secundaria) y por que, 2) corriente o "
        "postura teorica si es identificable, 3) posibles sesgos o limitaciones, "
        f"4) conceptos clave que introduce.\n\nTEXTO:\n{texto[:LIMITE_CHARS]}",
        contexto_catedra,
    )
    return _ejecutar(prompt, modelo)


def consulta_libre(texto, pregunta, modelo=MODELO_DEFAULT, contexto_catedra=None):
    prompt = _con_contexto_catedra(
        f"Tenes el siguiente fragmento de bibliografia:\n\n{texto[:LIMITE_CHARS]}\n\n"
        f"Respondes esta consulta del estudiante, basandote en el texto anterior: {pregunta}",
        contexto_catedra,
    )
    return _ejecutar(prompt, modelo)


def analizar_programa(texto, modelo=MODELO_DEFAULT):
    """Extrae del programa/syllabus los ejes tematicos, la perspectiva de la
    catedra, y la bibliografia obligatoria/opcional, como texto estructurado."""
    prompt = (
        "A partir del siguiente programa (syllabus) de una materia universitaria, "
        "extrae la informacion pedida y respondes UNICAMENTE con un objeto JSON "
        "valido, sin texto adicional antes o despues, sin bloques de codigo "
        "markdown, con exactamente esta forma:\n"
        '{"ejes_tematicos": "...", "perspectiva": "...", '
        '"bibliografia_obligatoria": "...", "bibliografia_opcional": "..."}\n\n'
        "Cada valor es un string (no una lista): para los ejes o la bibliografia, "
        "separa cada item con un salto de linea dentro del mismo string, incluyendo "
        "autor cuando este disponible. Para 'perspectiva', describe en un parrafo "
        "breve el enfoque, corriente teorica o linea de la catedra si se puede "
        "identificar en el programa. Si una seccion no esta presente, deja el "
        "valor como string vacio.\n\n"
        f"PROGRAMA:\n{texto[:LIMITE_CHARS]}"
    )
    salida = _ejecutar(prompt, modelo)
    return _parsear_json_programa(salida)


def _parsear_json_programa(salida):
    texto = salida.strip()
    if texto.startswith("```"):
        texto = re.sub(r"^```(json)?", "", texto).rstrip("`").strip()
    try:
        datos = json.loads(texto)
    except json.JSONDecodeError:
        coincidencia = re.search(r"\{.*\}", texto, re.DOTALL)
        if not coincidencia:
            raise ClaudeCodeError(f"No se pudo interpretar la respuesta como JSON: {salida[:300]}")
        datos = json.loads(coincidencia.group(0))
    return {
        "ejes_tematicos": datos.get("ejes_tematicos") or "",
        "perspectiva": datos.get("perspectiva") or "",
        "bibliografia_obligatoria": datos.get("bibliografia_obligatoria") or "",
        "bibliografia_opcional": datos.get("bibliografia_opcional") or "",
    }
