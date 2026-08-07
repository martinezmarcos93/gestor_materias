import requests

OLLAMA_URL = "http://localhost:11434/api/generate"
OLLAMA_TAGS_URL = "http://localhost:11434/api/tags"
MODELO_DEFAULT = "mistral:7b"
LIMITE_CHARS = 12000


def modelos_disponibles():
    try:
        resp = requests.get(OLLAMA_TAGS_URL, timeout=5)
        resp.raise_for_status()
        return [m["name"] for m in resp.json().get("models", [])]
    except Exception:
        return [MODELO_DEFAULT]


def _generar(prompt, modelo=MODELO_DEFAULT, timeout=300):
    resp = requests.post(
        OLLAMA_URL,
        json={"model": modelo, "prompt": prompt, "stream": False},
        timeout=timeout,
    )
    resp.raise_for_status()
    return resp.json()["response"].strip()


def resumir(texto, modelo=MODELO_DEFAULT):
    prompt = (
        "Sos un asistente de estudio para un estudiante de Historia en la universidad. "
        "Resumi el siguiente texto en espanol, identificando la tesis principal, "
        "los argumentos secundarios y las conclusiones, en no mas de 300 palabras.\n\n"
        f"TEXTO:\n{texto[:LIMITE_CHARS]}"
    )
    return _generar(prompt, modelo)


def preguntas_de_estudio(texto, modelo=MODELO_DEFAULT):
    prompt = (
        "A partir del siguiente texto de bibliografia de una materia de Historia, "
        "genera 8 preguntas de estudio que podrian aparecer en un parcial, de "
        "dificultad variada, en espanol. Numeralas.\n\n"
        f"TEXTO:\n{texto[:LIMITE_CHARS]}"
    )
    return _generar(prompt, modelo)


def analizar_fuente(texto, modelo=MODELO_DEFAULT):
    prompt = (
        "Sos un asistente de analisis historiografico. Analiza el siguiente texto "
        "indicando en secciones claras: 1) tipo de fuente (primaria o secundaria) "
        "y por que, 2) corriente o postura historiografica si es identificable, "
        "3) posibles sesgos o limitaciones, 4) conceptos clave que introduce. "
        "Respondes en espanol.\n\n"
        f"TEXTO:\n{texto[:LIMITE_CHARS]}"
    )
    return _generar(prompt, modelo)


def consulta_libre(texto, pregunta, modelo=MODELO_DEFAULT):
    prompt = (
        "Tenes el siguiente fragmento de bibliografia de Historia:\n\n"
        f"{texto[:LIMITE_CHARS]}\n\n"
        f"Respondes esta consulta del estudiante, basandote en el texto anterior: {pregunta}"
    )
    return _generar(prompt, modelo)
