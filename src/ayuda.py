TEXTO_AYUDA = """
# Guia de uso - Gestor de Materias

## Que es esto

Una app para organizar la bibliografia y el cronograma de tu carrera, y
analizar los textos con Claude (usando tu propia cuenta Pro/Max, sin costo
adicional). Funciona para cualquier carrera: vos la configuras desde cero.

## Primeros pasos

1. **Crear una carrera**: boton "Nueva carrera" en la barra de herramientas.
   Elegis el nombre y si se cursa por cuatrimestres, trimestres, semestres,
   o es anual.
2. **Crear un periodo**: seleccioná la carrera y apretá "Nuevo periodo"
   (ej: "1er Cuatrimestre 2026").
3. **Crear una materia**: seleccioná el periodo y apretá "Nueva materia".
4. **Importar el programa de la materia primero**: seleccioná la materia y
   apretá "Importar documentos...". Cuando te pregunte el tipo, elegi
   **"programa"**. Esto es lo mas importante: de ahi sale todo lo demas.

## El Programa de la materia

En la pestana **"Programa"** (arriba a la derecha), con la materia
seleccionada:

- Si ya importaste un documento tipo "programa", aparece el boton
  **"Analizar programa con IA"**. Al apretarlo, Claude lee el programa y
  extrae:
  - Los **ejes tematicos** (unidades de la materia).
  - La **perspectiva o enfoque de la catedra** (que corriente, que enfasis).
  - La **bibliografia obligatoria** y **opcional**, marcando con ✓ cuales
    ya estan importadas en la app y con ✗ cuales todavia faltan subir.
- Una vez analizado, la perspectiva de la catedra se usa **automaticamente**
  como contexto en cualquier analisis de IA que hagas sobre los textos de
  esa materia. No hace falta repetirlo cada vez.

Si un documento no quedo marcado como "programa" por error, lo podes
arreglar: seleccionalo en el arbol, apreta "Editar", y cambia el tipo a
"programa".

## Importar el resto de los textos

Segui importando PDFs con "Importar documentos...", eligiendo el tipo que
corresponda: texto, consigna, parcial, fuente primaria. Si el PDF es un
escaneo de mala calidad, la app le aplica OCR automaticamente (puede tardar
varios minutos en documentos largos — es normal, se ve el progreso en una
barra).

## Estado de lectura

Al abrir un documento (pestana "Texto"), arriba hay un selector de estado:
**Pendiente / En proceso / Leido**. El arbol de la izquierda muestra un
contador de progreso por materia (ej: "[2/5 leidos]"), para que veas de un
vistazo cuanto te falta.

## Cronograma

En la pestana **"Cronograma de la materia"** podes cargar parciales,
recuperatorios, trabajos practicos y entregas, con fecha y descripcion.
La pestana **"Proximos eventos"** (panel izquierdo) muestra, de todas las
materias juntas, lo que se viene.

## Analisis con IA

Con un documento seleccionado, en la pestana **"Analisis IA"**:

- **Resumir**: tesis principal, argumentos, conclusiones.
- **Preguntas de estudio**: 8 preguntas tipo parcial sobre el texto.
- **Analizar como fuente**: tipo de fuente, corriente teorica, sesgos,
  conceptos clave.
- **Preguntar**: escribi cualquier consulta puntual sobre el texto.

Arriba podes elegir el modelo (Sonnet por defecto; Opus para analisis mas
profundos pero mas lento; Haiku para respuestas rapidas y simples).

## Exportar a Markdown / Obsidian

Despues de generar un analisis, el boton **"Exportar a Markdown"** lo
guarda como nota `.md` con toda la informacion (materia, tipo, fecha, tags)
en una carpeta que vos elegis — puede ser directamente tu vault de
Obsidian. La primera vez te va a pedir elegir esa carpeta.

## Busqueda

En la pestana **"Busqueda"** (panel izquierdo) buscas texto en toda tu
bibliografia cargada, sin importar en que materia este.

## Preguntas frecuentes

**¿Esto tiene algun costo?**
No, mientras tengas Claude Code instalado y logueado con tu cuenta Pro o
Max. La app no usa una API key separada ni factura por su cuenta.

**"Claude no responde" o da error de conexion**
Usa el boton **"Verificar conexion IA"** en la barra de herramientas. Si
falla, asegurate de:
1. Tener Claude Code instalado (`npm install -g @anthropic-ai/claude-code`).
2. Haber corrido `claude login` al menos una vez en esta PC.
3. Tener conexion a internet.

**El OCR tarda mucho**
Es normal en PDFs largos y escaneados (puede tardar varios minutos). No
hace falta esperarlo de una: importa el documento y seguí con otra cosa,
se termina solo en segundo plano.

**¿Mis PDFs o mis textos se suben a algun servidor mio o de terceros?**
Los PDFs y la base de datos quedan en tu PC (carpeta `data/`). Al usar el
Analisis IA, el texto del documento se envia a Claude (Anthropic) para
procesarlo, igual que si lo pegaras en el chat de Claude directamente.

**¿Sirve para otra carrera que no sea Historia?**
Si. La app es agnostica: vos definis la carrera, como se divide en
periodos, y las materias. No asume ninguna estructura particular.

**Borre un documento por error**
Al borrar un documento se elimina tambien el archivo PDF de la carpeta
`data/`, no hay forma de recuperarlo desde la app — fijate si todavia
tenes el PDF original en otro lado para volver a importarlo.
"""
