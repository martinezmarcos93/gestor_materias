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
- **Programa de la materia como documento eje**: cada materia puede tener un
  documento marcado como "programa" (el syllabus). Con un click, Claude
  extrae del programa los ejes tematicos, la bibliografia obligatoria/
  opcional, y la **perspectiva o enfoque de la catedra** — y esa perspectiva
  se usa automaticamente como contexto en cualquier analisis de IA sobre los
  textos de esa materia (un mismo texto puede leerse distinto segun el
  enfoque de la catedra que lo asigna).
- Importar PDFs por materia, con OCR automatico (Tesseract) cuando el PDF
  no tiene capa de texto (escaneos de mala calidad).
- Cronograma por materia: parciales, recuperatorios, trabajos practicos,
  entregas, con vista global de "Proximos eventos" de todas las materias.
- Busqueda de texto completo sobre toda la bibliografia cargada.
- Analisis con IA (Claude, via [Claude Code](https://claude.com/claude-code)):
  resumen, preguntas de estudio, analisis de fuente, consultas libres sobre
  el texto — todos informados por la perspectiva de la catedra si el
  programa ya fue analizado. Usa la sesion de Claude Code ya logueada — no
  requiere una API key aparte ni tiene costo adicional sobre el plan Pro/Max.
- Exportar cualquier analisis de IA como nota Markdown con front-matter,
  a una carpeta configurable (por ejemplo, una vault de Obsidian).

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
3. Importar el programa de la materia primero, con tipo **"programa"** (o
   editar un documento ya importado y cambiarle el tipo). En la pestana
   "Programa", apretar "Analizar programa con IA" para extraer ejes,
   perspectiva y bibliografia.
4. Importar el resto de los PDFs de cada materia, y cargar el cronograma
   (parciales, entregas, etc.) desde la pestana "Cronograma de la materia".
5. Seleccionar un documento para leer el texto extraido o pedirle a Claude
   un resumen, preguntas de estudio o un analisis de la fuente — si el
   programa ya fue analizado, el enfoque de la catedra se aplica solo.
6. Usar "Verificar conexion IA" en la barra de herramientas para confirmar
   que Claude Code esta instalado y logueado correctamente.

## Estructura del proyecto

```
main.py              punto de entrada de la app
src/
  db.py               capa de datos (SQLite + busqueda full-text)
                       carreras -> periodos -> materias -> documentos/eventos
  ocr.py              extraccion de texto + OCR con Tesseract
  ai.py               integracion con Claude via Claude Code (subproceso),
                       incluye analizar_programa() para el programa/syllabus
  workers.py          tareas en segundo plano (importacion, IA, programa, conexion)
  exportador.py       exporta analisis de IA a notas Markdown (Obsidian)
  config.py           preferencias locales (carpeta de exportacion)
  main_window.py      interfaz (PySide6)
scripts/
  descargar_tessdata.py   descarga los modelos de idioma de Tesseract
tests/
  test_pipeline.py    prueba end-to-end del pipeline OCR + DB + cronograma + IA
  test_programa.py    prueba end-to-end de extraccion de programa + contexto de catedra
```

La carpeta `data/` (bibliografia importada y base de datos) es local y no se
sube al repositorio: es material de catedra de uso personal.

## Pendiente / proximos pasos

- Cruzar la bibliografia obligatoria/opcional extraida del programa contra
  los documentos ya importados (que falta subir, que ya esta).
- Extraccion automatica de autor/metadata desde el PDF.
- Linea de tiempo generada a partir de fechas mencionadas en el texto.
- Correccion post-OCR asistida por IA para mejorar el reconocimiento.
- Notificaciones o recordatorios de eventos proximos del cronograma.
- Lista completa de funcionalidades pendiente de parte de Lautaro (dueño
  del proyecto), en base a su experiencia en materias ya cursadas.
