# Estado de implementacion (corte por limite de tokens)

Este documento existe porque la sesion se corto por limite de tokens en medio
de una tanda grande de funcionalidades ("implementa todo, desde lo menos
complejo a lo mas complejo"). Registra que quedo terminado, que quedo a
medias, y que falta, para retomar sin perder contexto.

## Terminado y probado (funciona end-to-end)

1. **Manejo de errores de Claude Code mas especifico** (`src/ai.py`):
   `ClaudeCodeNoInstalado`, `ClaudeCodeNoLogueado`, `ClaudeCodeTimeout`,
   `ClaudeCodeLimiteAlcanzado`, con clasificacion heuristica del mensaje de
   error (best-effort, ya que el CLI no expone codigos tipados).
2. **Aviso de proximos eventos al abrir la app** (7 dias): `_avisar_eventos_proximos`
   en `main_window.py`, usando `db.listar_eventos_proximos(dias=7)`.
3. **Extraccion automatica de autor/metadata del PDF**: `ocr.py` lee
   `doc.metadata` de PyMuPDF (autor/titulo), filtrando ruido tipico
   (Microsoft, Adobe, etc.). `workers.py` lo usa para prellenar el autor y,
   si el nombre de archivo es generico, el titulo.
4. **Correccion post-OCR asistida por IA**: `ai.corregir_ocr()` (procesa
   pagina por pagina), `CorreccionOCRWorker`, boton "Corregir OCR con IA..."
   en la pestana Texto, con dialogo de revision antes de guardar
   (`db.actualizar_texto_documento`).
5. **Exportar cronograma a .ics**: `src/calendario.py` (`generar_ics`, sin
   dependencias nuevas), `db.listar_todos_los_eventos()`, boton en la
   toolbar. Importable directo en Google Calendar/Outlook/Apple Calendar.
   Sustituye la sync en vivo con Google/Outlook, que requeriria credenciales
   OAuth que no puedo generar yo.
6. **Generador de citas APA/Chicago**: `ai.generar_cita()`, boton "Generar
   cita (APA/Chicago)" en el panel de Analisis IA. Sustituye integracion con
   Zotero (no confirmado que Lautaro lo use).
7. **Linea de tiempo de fechas mencionadas en un texto**: `ai.extraer_linea_tiempo()`
   (JSON estructurado), `LineaTiempoWorker`, nueva pestana "Linea de tiempo"
   con boton de extraccion. No se persiste en DB (se recalcula al pedirla).
8. **Busqueda global tipo "segundo cerebro"**: `ai.consulta_corpus()` (usa
   hasta ~60000 caracteres combinando todos los documentos con texto de la
   materia actual), `ConsultaCorpusWorker`, boton "Preguntar a toda la
   materia" junto al campo de consulta existente.

Se agrego tambien `_extraer_json()` generico en `ai.py` (refactor de lo que
antes era especifico de `analizar_programa`, ahora reusado por
`extraer_linea_tiempo`).

## A medias (backend listo, falta UI)

9. **Deteccion de contradicciones/debates entre dos textos**:
   - `ai.comparar_textos(titulo_a, texto_a, titulo_b, texto_b, modelo, contexto_catedra)` -
     ya escrito en `ai.py`, no probado todavia con una llamada real.
   - `ComparacionWorker` en `workers.py` - ya escrito.
   - **Falta**: el panel/pestana en `main_window.py` (dos QComboBox para elegir
     documentos A y B de la materia actual, boton "Comparar", area de
     resultado). Nada de esto esta conectado a la interfaz todavia.

## No empezado

10. **Mapa conceptual automatico (Mermaid)**: extraer conceptos clave de un
    documento con IA y generar un diagrama Mermaid (embebible en la nota
    exportada a Markdown/Obsidian, que ya soporta Mermaid nativamente).
11. **Exportar preguntas de estudio como flashcards (Anki CSV)**: generar
    pares pregunta/respuesta con IA y exportar a CSV (formato que Anki
    importa nativamente, sin necesidad de la libreria `genanki`).
12. **Modo oscuro / tema visual**: hoja de estilos QSS + toggle en la
    toolbar.
13. **Onboarding guiado mejorado**: wizard de primera ejecucion con opcion
    de cargar datos de ejemplo.
14. **Estadisticas y gamificacion ligera**: rachas, cantidad de analisis
    generados, materias mas activas.
15. **Planificador automatico de estudio**: dificultad por documento (1-5),
    horas disponibles por dia, generar plan respetando el cronograma. Es el
    de mayor complejidad de toda la lista (nuevo modelo de datos + logica de
    scheduling).
16. **Exportar/importar paquete de materia (.gdm)**: zip con DB+PDFs+config
    de una materia para compartir con companeros, con logica de
    importacion/merge.
17. **Dashboard visual con widgets**: pestana inicial con resumen (proximos
    eventos, progreso, accesos rapidos).

## Bloqueados / requieren una decision externa (no implementables por mi)

- **Sync en vivo con Google Calendar/Outlook**: necesita credenciales OAuth
  de una app registrada en Google Cloud / Azure — las tiene que crear un
  humano con cuenta ahi. El `.ics` (item 5) es el sustituto ya implementado.
- **Sync con Zotero**: no esta confirmado que Lautaro lo use. La generacion
  de citas (item 6) cubre buena parte de la necesidad sin esa dependencia.

## Para retomar

El repo esta commiteado y pusheado con los items 1-8 completos y probados,
y el backend de 9 escrito pero sin UI. El proximo paso logico es:
1. Terminar la UI de comparacion de textos (item 9) — es rapido, el backend
   ya existe.
2. Seguir con 10-17 en el mismo orden (menor a mayor complejidad).

Antes de programar, resetear `data/` (esta vacio en este commit, como
siempre antes de subir).
