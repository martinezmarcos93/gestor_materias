import io
import os
from pathlib import Path

import pymupdf as fitz
import pytesseract
from PIL import Image

BASE_DIR = Path(__file__).resolve().parent.parent
TESSDATA_DIR = BASE_DIR / "tessdata"
TESSERACT_EXE = Path(r"C:\Program Files\Tesseract-OCR\tesseract.exe")

if TESSERACT_EXE.exists():
    pytesseract.pytesseract.tesseract_cmd = str(TESSERACT_EXE)

# Se setea por variable de entorno en vez de pasar --tessdata-dir en la config:
# pytesseract/tesseract en Windows rompe el quoting de rutas con espacios y
# backslashes cuando se pasa como argumento de config.
os.environ["TESSDATA_PREFIX"] = str(TESSDATA_DIR)

UMBRAL_CHARS_PAGINA = 20
IDIOMAS = "spa+eng"

# Valores de metadata de PDF que en realidad son ruido de la app que genero
# el archivo, no un autor/titulo real.
_METADATA_RUIDO = ("microsoft", "word", "acrobat", "adobe", "libreoffice", "openoffice", "pdf")


def _limpiar_metadata(valor):
    valor = (valor or "").strip()
    if not valor:
        return None
    if any(ruido in valor.lower() for ruido in _METADATA_RUIDO):
        return None
    return valor


def extraer_texto_pdf(ruta_pdf, dpi=300, progreso_cb=None):
    """Extrae texto de un PDF. Usa la capa de texto nativa si existe;
    si una pagina no tiene texto (escaneo), la pasa por OCR.
    Devuelve (texto_completo, ocr_aplicado: bool, metadata: dict)."""
    doc = fitz.open(str(ruta_pdf))
    partes = []
    ocr_aplicado = False
    total = len(doc)

    metadata_pdf = doc.metadata or {}
    metadata = {
        "autor": _limpiar_metadata(metadata_pdf.get("author")),
        "titulo": _limpiar_metadata(metadata_pdf.get("title")),
    }

    for i, page in enumerate(doc):
        texto = page.get_text().strip()
        if len(texto) < UMBRAL_CHARS_PAGINA:
            pix = page.get_pixmap(dpi=dpi)
            img = Image.open(io.BytesIO(pix.tobytes("png")))
            texto = pytesseract.image_to_string(img, lang=IDIOMAS).strip()
            ocr_aplicado = True
        partes.append(texto)
        if progreso_cb:
            progreso_cb(i + 1, total)

    doc.close()
    texto_completo = "\n\n--- pagina siguiente ---\n\n".join(partes)
    return texto_completo, ocr_aplicado, metadata
