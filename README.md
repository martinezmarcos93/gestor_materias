# Gestor de Materias — herramienta de estudio

App de escritorio (Windows) para organizar la bibliografia y el cronograma de
cualquier carrera universitaria, aplicar OCR a los escaneos de mala calidad
del campus, y analizar los textos con Claude (usando la propia cuenta de
Claude Pro del usuario, sin API key ni costos adicionales).

Es agnostica a la carrera: se configura desde cero (nombre de la carrera,
si se cursa por cuatrimestres/trimestres/semestres/anual, materias,
periodos), no asume ninguna estructura particular.

## Funciones (MVP)

- Modelo configurable: Carrera -> Periodo (cuatrimestre/trimestre/etc.) ->
  Materia -> Documentos, con alta/baja/edicion en cada nivel.
- Importar PDFs por materia, con OCR automatico (Tesseract) cuando el PDF
  no tiene capa de texto (escaneos de mala calidad).
- Cronograma por materia: parciales, recuperatorios, trabajos practicos,
  entregas, con vista global de "Proximos eventos" de todas las materias.
- Busqueda de texto completo sobre toda la bibliografia cargada.
- Analisis con IA (Claude, via [Claude Code](https://claude.com/claude-code)):
  resumen, preguntas de estudio, analisis de fuente, consultas libres sobre
  el texto. Usa la sesion de Claude Code ya logueada — no requiere una API
  key aparte ni tiene costo adicional sobre el plan Pro/Max.

## Requisitos

- Windows 10/11
- Python 3.11 o superior
- [Tesseract OCR](https://github.com/UB-Mannheim/tesseract/wiki) instalado
  (via `winget install --id UB-Mannheim.TesseractOCR -e`)
- [Node.js](https://nodejs.org) (para instalar Claude Code)
- Claude Code instalado y logueado con una cuenta Claude Pro o Max:
  ```powershell
  npm install -g @anthropic-ai/claude-code
  claude login
  ```

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

1. La primera vez, la app pide crear una carrera (nombre y si se cursa por
   cuatrimestres, trimestres, semestres o es anual).
2. Crear un periodo (ej: "1er Cuatrimestre 2026") y dentro las materias.
3. Importar los PDFs de cada materia, y cargar el cronograma (parciales,
   entregas, etc.) desde la pestana "Cronograma de la materia".
4. Seleccionar un documento para leer el texto extraido o pedirle a Claude
   un resumen, preguntas de estudio o un analisis de la fuente.
5. Usar "Verificar conexion IA" en la barra de herramientas para confirmar
   que Claude Code esta instalado y logueado correctamente.

## Estructura del proyecto

```
main.py              punto de entrada de la app
src/
  db.py               capa de datos (SQLite + busqueda full-text)
                       carreras -> periodos -> materias -> documentos/eventos
  ocr.py              extraccion de texto + OCR con Tesseract
  ai.py               integracion con Claude via Claude Code (subproceso)
  workers.py          tareas en segundo plano (importacion, IA, chequeo de conexion)
  main_window.py      interfaz (PySide6)
scripts/
  descargar_tessdata.py   descarga los modelos de idioma de Tesseract
tests/
  test_pipeline.py    prueba end-to-end del pipeline OCR + DB + cronograma + IA
```

La carpeta `data/` (bibliografia importada y base de datos) es local y no se
sube al repositorio: es material de catedra de uso personal.

## Pendiente / proximos pasos

- Extraccion automatica de autor/metadata desde el PDF.
- Linea de tiempo generada a partir de fechas mencionadas en el texto.
- Exportar fichas de lectura a Word/Markdown.
- Correccion post-OCR asistida por IA para mejorar el reconocimiento.
- Notificaciones o recordatorios de eventos proximos del cronograma.
