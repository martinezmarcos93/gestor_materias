"""Descarga los modelos de idioma de Tesseract (espanol e ingles) a la
carpeta tessdata/ del proyecto, sin tocar la instalacion global de Tesseract.
Correr una sola vez despues de clonar el repo:

    venv\\Scripts\\python.exe scripts\\descargar_tessdata.py
"""

import urllib.request
from pathlib import Path

TESSDATA_DIR = Path(__file__).resolve().parent.parent / "tessdata"
BASE_URL = "https://github.com/tesseract-ocr/tessdata_fast/raw/main/{}.traineddata"
IDIOMAS = ["spa", "eng"]


def main():
    TESSDATA_DIR.mkdir(parents=True, exist_ok=True)
    for idioma in IDIOMAS:
        destino = TESSDATA_DIR / f"{idioma}.traineddata"
        if destino.exists():
            print(f"Ya existe: {destino.name}")
            continue
        url = BASE_URL.format(idioma)
        print(f"Descargando {idioma}.traineddata...")
        urllib.request.urlretrieve(url, destino)
        print(f"  -> guardado en {destino}")

    print("\nListo. Si la descarga falla por SSL/certificados, descarga los")
    print("archivos manualmente desde https://github.com/tesseract-ocr/tessdata_fast")
    print(f"y colocalos en: {TESSDATA_DIR}")


if __name__ == "__main__":
    main()
