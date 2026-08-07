import json
import re
import shutil
import subprocess

MODELOS = ["sonnet", "opus", "haiku"]
MODELO_DEFAULT = "sonnet"
LIMITE_CHARS = 15000
LIMITE_CHARS_CORPUS = 60000
TIMEOUT_DEFAULT = 180
TIMEOUT_CORPUS = 300

SISTEMA = (
    "Sos un asistente de estudio para un estudiante universitario. Respondes siempre "
    "en espanol, de forma clara y academica, basandote en el texto que se te da."
)

# Sin herramientas: cada consulta es texto-a-texto, sin tocar archivos ni la red.
HERRAMIENTAS_DESHABILITADAS = "Bash,Edit,Write,Read,WebSearch,WebFetch,NotebookEdit,Glob,Grep,Task"


class ClaudeCodeError(Exception):
    """Error generico al consultar a Claude Code."""


class ClaudeCodeNoInstalado(ClaudeCodeError):
    pass


class ClaudeCodeNoLogueado(ClaudeCodeError):
    pass


class ClaudeCodeTimeout(ClaudeCodeError):
    pass


class ClaudeCodeLimiteAlcanzado(ClaudeCodeError):
    pass


ClaudeCodeNoDisponible = ClaudeCodeNoInstalado  # alias, nombre anterior

_PISTAS_NO_LOGUEADO = (
    "login", "log in", "authent", "credential", "not logged", "unauthorized", "api key",
)
_PISTAS_LIMITE = (
    "rate limit", "rate_limit", "429", "overloaded", "quota", "usage limit", "too many requests",
)


def _clasificar_error(mensaje):
    """Heuristico best-effort sobre el texto de error/stderr de Claude Code,
    ya que el CLI no expone codigos de error tipados. Ante la duda, cae en
    ClaudeCodeError generico con el mensaje original intacto."""
    texto_low = mensaje.lower()
    if any(p in texto_low for p in _PISTAS_LIMITE):
        return ClaudeCodeLimiteAlcanzado(
            f"Se alcanzo un limite de uso de la cuenta Claude. Proba de nuevo en unos "
            f"minutos.\nDetalle: {mensaje}"
        )
    if any(p in texto_low for p in _PISTAS_NO_LOGUEADO):
        return ClaudeCodeNoLogueado(
            f"Claude Code no esta logueado o la sesion vencio. Ejecuta 'claude login' "
            f"en una terminal.\nDetalle: {mensaje}"
        )
    return ClaudeCodeError(mensaje)


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
        raise ClaudeCodeNoInstalado(
            "No se encontro el comando 'claude'. Instala Claude Code con "
            "'npm install -g @anthropic-ai/claude-code' y despues ejecuta 'claude login'."
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
        raise ClaudeCodeTimeout(
            f"La consulta a Claude tardo mas de {timeout} segundos y se cancelo. "
            "Si el texto es muy largo, proba con el modelo 'haiku' (mas rapido)."
        )
    except OSError as exc:
        raise ClaudeCodeError(f"No se pudo ejecutar Claude Code: {exc}")

    if proceso.returncode != 0:
        detalle = (proceso.stderr or proceso.stdout or "").strip()[:500]
        raise _clasificar_error(detalle or f"Claude Code fallo (codigo {proceso.returncode}).")

    try:
        data = json.loads(proceso.stdout)
    except json.JSONDecodeError:
        raise ClaudeCodeError(f"Respuesta inesperada de Claude Code: {proceso.stdout[:300]}")

    if data.get("is_error") or data.get("subtype") != "success":
        raise _clasificar_error(data.get("result") or "Error desconocido al consultar a Claude.")

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


def corregir_ocr(texto, modelo=MODELO_DEFAULT, progreso_cb=None):
    """Corrige errores de reconocimiento de OCR en un texto largo, procesando
    pagina por pagina (usando el separador que deja ocr.py) para no perder
    contenido por el limite de caracteres de una sola consulta."""
    partes = texto.split("\n\n--- pagina siguiente ---\n\n")
    corregidas = []
    for i, parte in enumerate(partes):
        if not parte.strip():
            corregidas.append(parte)
        else:
            prompt = (
                "El siguiente texto fue extraido con OCR y puede tener errores de "
                "reconocimiento de caracteres (letras confundidas, palabras cortadas, "
                "espacios de mas o de menos). Corregi UNICAMENTE los errores evidentes "
                "de OCR, sin resumir, sin parafrasear, sin agregar ni quitar contenido, "
                "sin traducir. Mantene el mismo idioma y la estructura del texto. "
                "Respondes unicamente con el texto corregido, sin comentarios ni "
                f"explicaciones adicionales.\n\nTEXTO:\n{parte[:LIMITE_CHARS]}"
            )
            corregidas.append(_ejecutar(prompt, modelo))
        if progreso_cb:
            progreso_cb(i + 1, len(partes))
    return "\n\n--- pagina siguiente ---\n\n".join(corregidas)


def generar_cita(titulo, autor, texto, modelo=MODELO_DEFAULT):
    """Genera una cita bibliografica en APA y Chicago con los datos
    disponibles, infiriendo del propio texto lo que falte y marcando
    claramente que datos fueron inferidos vs. conocidos."""
    prompt = (
        "Con la informacion disponible, genera una cita bibliografica en "
        "formato APA (7ma edicion) y otra en formato Chicago (autor-fecha), "
        "para el siguiente documento academico. Si falta algun dato (autor, "
        "anio, editorial, etc.), intenta inferirlo del contenido del texto; "
        "si no es posible, dejalo como [dato no disponible]. Aclara "
        "brevemente que datos fueron inferidos y cuales son los conocidos.\n\n"
        f"Titulo conocido: {titulo or '(desconocido)'}\n"
        f"Autor conocido: {autor or '(desconocido)'}\n\n"
        f"Primeras lineas del documento (para inferir datos faltantes):\n{texto[:3000]}"
    )
    return _ejecutar(prompt, modelo)


def consulta_corpus(pregunta, documentos, modelo=MODELO_DEFAULT):
    """Responde una consulta usando varios documentos como contexto combinado
    (tipo 'segundo cerebro' sobre toda una materia), citando de que documento
    sale cada idea cuando sea relevante. 'documentos' es una lista de dicts
    o sqlite3.Row con 'titulo' y 'texto'."""
    bloques = []
    presupuesto = LIMITE_CHARS_CORPUS
    for doc in documentos:
        texto = (doc["texto"] or "").strip()
        if not texto or presupuesto <= 0:
            continue
        fragmento = texto[:presupuesto]
        bloques.append(f"--- {doc['titulo']} ---\n{fragmento}")
        presupuesto -= len(fragmento)

    contexto = "\n\n".join(bloques)
    prompt = (
        "Tenes acceso a varios textos de bibliografia de una misma materia, "
        "delimitados por '--- titulo ---'. Respondes la siguiente consulta del "
        "estudiante basandote en el conjunto de estos textos, indicando de que "
        "documento sale cada idea cuando sea relevante. Si la respuesta no esta "
        "en ninguno de los textos, decilo explicitamente en vez de inventar.\n\n"
        f"TEXTOS:\n{contexto}\n\n"
        f"CONSULTA: {pregunta}"
    )
    return _ejecutar(prompt, modelo, timeout=TIMEOUT_CORPUS)


def comparar_textos(titulo_a, texto_a, titulo_b, texto_b, modelo=MODELO_DEFAULT, contexto_catedra=None):
    """Compara dos textos identificando coincidencias, complementariedades y
    contradicciones o debates entre sus posturas."""
    mitad = LIMITE_CHARS_CORPUS // 2
    prompt = _con_contexto_catedra(
        "Compara los siguientes dos textos academicos. Indica en secciones "
        "claras: 1) de que trata cada uno brevemente, 2) puntos en los que "
        "coinciden o se complementan, 3) contradicciones, tensiones o debates "
        "entre sus posturas (si los hay), 4) que aporta cada uno que el otro no "
        "tiene.\n\n"
        f"--- {titulo_a} ---\n{texto_a[:mitad]}\n\n"
        f"--- {titulo_b} ---\n{texto_b[:mitad]}",
        contexto_catedra,
    )
    return _ejecutar(prompt, modelo, timeout=TIMEOUT_CORPUS)


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


def _extraer_json(salida):
    """Parsea la salida de Claude como JSON, tolerando bloques de codigo
    markdown o texto extra alrededor del objeto/lista."""
    texto = salida.strip()
    if texto.startswith("```"):
        texto = re.sub(r"^```(json)?", "", texto).rstrip("`").strip()
    try:
        return json.loads(texto)
    except json.JSONDecodeError:
        coincidencia = re.search(r"[\{\[].*[\}\]]", texto, re.DOTALL)
        if not coincidencia:
            raise ClaudeCodeError(f"No se pudo interpretar la respuesta como JSON: {salida[:300]}")
        return json.loads(coincidencia.group(0))


def _parsear_json_programa(salida):
    datos = _extraer_json(salida)
    return {
        "ejes_tematicos": datos.get("ejes_tematicos") or "",
        "perspectiva": datos.get("perspectiva") or "",
        "bibliografia_obligatoria": datos.get("bibliografia_obligatoria") or "",
        "bibliografia_opcional": datos.get("bibliografia_opcional") or "",
    }


def extraer_linea_tiempo(texto, modelo=MODELO_DEFAULT):
    """Identifica fechas/periodos mencionados en el texto y el hecho asociado,
    en orden cronologico. Devuelve una lista de {"fecha": str, "descripcion": str}."""
    prompt = (
        "A partir del siguiente texto, identifica las fechas o periodos "
        "historicos mencionados y el hecho o evento asociado a cada uno. "
        "Respondes UNICAMENTE con un objeto JSON valido, sin texto adicional "
        "ni bloques de codigo markdown, con esta forma exacta:\n"
        '{"eventos": [{"fecha": "...", "descripcion": "..."}]}\n\n'
        "Ordena los eventos cronologicamente. La fecha puede ser un anio, un "
        "rango, o una referencia aproximada tal como aparece en el texto (por "
        "ejemplo '1810', '1880-1916', 'fines del siglo XIX'). Si el texto no "
        "menciona fechas especificas, devolve una lista vacia.\n\n"
        f"TEXTO:\n{texto[:LIMITE_CHARS]}"
    )
    salida = _ejecutar(prompt, modelo)
    datos = _extraer_json(salida)
    eventos = datos.get("eventos", []) if isinstance(datos, dict) else []
    return [
        {"fecha": str(e.get("fecha", "")).strip(), "descripcion": str(e.get("descripcion", "")).strip()}
        for e in eventos
        if isinstance(e, dict) and (e.get("fecha") or e.get("descripcion"))
    ]
