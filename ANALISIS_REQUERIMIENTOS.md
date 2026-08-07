# Analisis de la conversacion con Lautaro (dueño del proyecto)

Nota: Lautaro aclaro que esto es parcial — dijo que va a mandar una lista mas
completa de funcionalidades cuando lo piense con calma, en base a las materias
que ya curso. Esto es lo que se puede extraer de lo ya conversado.

## 1. El concepto central: "el programa" de la materia

Esto es, con diferencia, el requerimiento mas fuerte y repetido del chat:

> "cada materia - SI O SI- tiene un programa presentado a principio del
> cuatrimestre... y siempre la materia esta resumida en ese programa. da los
> ejes de como se da la materia y da los textos obligatorios/opcionales...
> es decir en cada materia PARA MI lo principal es adjuntarle el programa"

> "lo importante es que el programa tenga archivados los textos, los ejes de
> la materia, la perspectiva que dice en el programa, entendes? entonces ya
> sabes bien en que hacen hincapie"

**Lectura funcional:** el "programa" (syllabus) no es un documento mas de la
bibliografia — es el documento fundacional de cada materia, del cual se
desprende:
- Los **ejes tematicos** (unidades/bloques en que se organiza la cursada).
- La **perspectiva/enfoque** de la catedra (que corriente, que enfasis).
- La lista de **bibliografia obligatoria** y **opcional**.

**Ejemplo concreto que dio Lautaro** (ilustra por que esto importa en la
practica, no es un capricho academico abstracto):

> "me anote a otra catedra, y es la catedra mas progre que hay, y enfatiza
> mucho con textos y autores criticos de occidente, y critica mucho a
> europa y la forma de concebir la historia"

Esto muestra que la "perspectiva" de la catedra puede ser fuertemente
ideologica/teorica (en este caso, una lectura critica/decolonial de la
historiografia europea), y que **el mismo texto puede necesitar un analisis
distinto segun la catedra que lo asigna**. Un analisis generico de IA que
ignore esto (por ejemplo, uno que dé por sentada una perspectiva eurocentrica
"neutral") le seria poco util o hasta contraproducente para esa materia
puntual. Refuerza que la perspectiva del programa no es metadata decorativa:
deberia condicionar activamente como la IA analiza los textos de esa materia.

Esto sugiere:
- Tratar "Programa" como un tipo de documento distinguido (no uno mas del
  monton), posiblemente unico por materia y destacado en el arbol/UI.
- Usar IA para *extraer* del programa: ejes, perspectiva, y la lista de
  bibliografia obligatoria/opcional — y despues cruzar esa lista contra los
  documentos ya cargados (que falta subir, que ya esta).
- Cuando se analiza cualquier texto de esa materia con IA, dar como contexto
  la perspectiva/enfasis del programa, para que el analisis este orientado a
  "lo que la catedra pide", no un analisis generico.

## 2. El framing del producto: "asesor academico"

> "la plataforma deberia ser algo asi como un asesor academico"

No es (solo) un archivo/biblioteca pasiva. La expectativa es que la
herramienta actue con cierta proactividad: guiar, priorizar, recordar — no
solo guardar y buscar.

## 3. Mezcla real de tipos de material (matiza el riesgo de OCR)

> "no todos los textos para estudiar son con escaneado, algunos son los
> textos en pdf o en texto"
> "quiza la mitad son escaneados"
> "como no debe leer todos los textos de una, sino capaz dos o tres a la
> semana, no habria problemas con el tema de ocr y esperar"

**Lectura funcional:** la lentitud del OCR (~10 min en PDFs largos) no es un
bloqueante critico porque el uso real es incremental (2-3 textos por semana,
no una carga masiva de golpe). No hace falta optimizar el OCR con urgencia;
si hace falta, es baja prioridad frente a lo del programa.

## 4. Confirmacion de la integracion con Claude Code

> "y funciona con tu cuenta de claude" / "tenes que tener descargado y
> logueado claudecode" — confirmado y probado por Marcos subiendo un
> documento escaneado real.

Sin cambios pendientes aca; ya validado en la practica.

## 5. Detalles esteticos

El chat **no tiene pedidos esteticos explicitos** todavia — Lautaro no
comento nada sobre colores, layout o estilo visual. Es un vacio real, no
"no hay nada que hacer": cuando mande su lista completa, probablemente
incluya esto. Por ahora no hay base para inventar preferencias visuales.

## Propuesta de proximo paso concreto

De todo lo anterior, lo unico con suficiente especificidad para implementar
ya es **(1) el Programa como documento eje de la materia** con extraccion
asistida por IA de ejes/perspectiva/bibliografia obligatoria-opcional. El
resto (asesor proactivo, esteticos) son direcciones a tener en cuenta pero
sin especificacion suficiente todavia — esperan la lista completa de
Lautaro.
