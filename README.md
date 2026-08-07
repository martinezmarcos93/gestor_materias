# Archivo Historiografico — herramienta de estudio

App de escritorio (Windows) para organizar la bibliografia de la carrera de
Historia, aplicar OCR a los escaneos de mala calidad del campus, y analizar
los textos con un modelo de IA que corre 100% local (sin depender de ninguna
API externa ni enviar datos a internet).

## Funciones (MVP)

- Importar PDFs por materia/cuatrimestre, con OCR automatico cuando el PDF
  no tiene capa de texto (escaneos).
- Busqueda de texto completo sobre toda la bibliografia cargada.
- Analisis con IA local (via [Ollama](https://ollama.com)): resumen, preguntas
  de estudio, analisis de fuente historiografica, consultas libres sobre el texto.

## Requisitos

- Windows 10/11
- Python 3.11 o superior
- [Tesseract OCR](https://github.com/UB-Mannheim/tesseract/wiki) instalado
  (via `winget install --id UB-Mannheim.TesseractOCR -e`)
- [Ollama](https://ollama.com) instalado, con al menos un modelo descargado,
  por ejemplo: `ollama pull mistral:7b`

## Instalacion

```powershell
py -3 -m venv venv
venv\Scripts\python.exe -m pip install -r requirements.txt
venv\Scripts\python.exe scripts\descargar_tessdata.py
```

## Uso

```powershell
venv\Scripts\python.exe main.py
```

1. Crear una materia (nombre, anio, cuatrimestre).
2. Importar los PDFs de esa materia.
3. Seleccionar un documento para leer el texto extraido o pedirle a la IA
   un resumen, preguntas de estudio o un analisis de la fuente.

## Estructura del proyecto

```
main.py              punto de entrada de la app
src/
  db.py               capa de datos (SQLite + busqueda full-text)
  ocr.py              extraccion de texto + OCR con Tesseract
  ai.py               integracion con modelos locales de Ollama
  workers.py          tareas en segundo plano (import y consultas a IA)
  main_window.py       interfaz (PySide6)
scripts/
  descargar_tessdata.py   descarga los modelos de idioma de Tesseract
tests/
  test_pipeline.py    prueba end-to-end del pipeline OCR + DB + IA
```

La carpeta `data/` (bibliografia importada y base de datos) es local y no se
sube al repositorio: es material de catedra de uso personal.

## Pendiente / proximos pasos

- Extraccion automatica de autor/metadata desde el PDF.
- Linea de tiempo generada a partir de fechas mencionadas en el texto.
- Exportar fichas de lectura a Word/Markdown.
- Correccion post-OCR asistida por IA para mejorar el reconocimiento.
