import shutil
from pathlib import Path

from PySide6.QtCore import QThread, Signal

from . import ai, db, ocr


class ImportWorker(QThread):
    progreso = Signal(int, int, str)
    documento_importado = Signal(int, str)
    error = Signal(str, str)
    terminado = Signal()

    def __init__(self, materia_id, materia_nombre, rutas_pdf, tipo):
        super().__init__()
        self.materia_id = materia_id
        self.materia_nombre = materia_nombre
        self.rutas_pdf = rutas_pdf
        self.tipo = tipo

    def run(self):
        destino_dir = db.ARCHIVOS_DIR / self._slug(self.materia_nombre)
        destino_dir.mkdir(parents=True, exist_ok=True)

        for idx, ruta in enumerate(self.rutas_pdf, start=1):
            origen = Path(ruta)
            try:
                self.progreso.emit(idx, len(self.rutas_pdf), f"Copiando {origen.name}...")
                destino = destino_dir / origen.name
                if not destino.exists():
                    shutil.copy2(origen, destino)

                def cb(pagina, total, nombre=origen.name):
                    self.progreso.emit(
                        idx, len(self.rutas_pdf), f"OCR {nombre}: pagina {pagina}/{total}"
                    )

                texto, ocr_aplicado = ocr.extraer_texto_pdf(destino, progreso_cb=cb)

                titulo = origen.stem
                doc_id = db.agregar_documento(
                    self.materia_id, titulo, self.tipo, destino, texto, ocr_aplicado
                )
                self.documento_importado.emit(doc_id, titulo)
            except Exception as exc:
                self.error.emit(origen.name, str(exc))

        self.terminado.emit()

    @staticmethod
    def _slug(nombre):
        return "".join(c if c.isalnum() or c in " -_" else "_" for c in nombre).strip()


class AIWorker(QThread):
    resultado = Signal(str)
    error = Signal(str)

    def __init__(self, accion, texto, modelo, pregunta=None):
        super().__init__()
        self.accion = accion
        self.texto = texto
        self.modelo = modelo
        self.pregunta = pregunta

    def run(self):
        try:
            if self.accion == "resumir":
                resultado = ai.resumir(self.texto, self.modelo)
            elif self.accion == "preguntas":
                resultado = ai.preguntas_de_estudio(self.texto, self.modelo)
            elif self.accion == "fuente":
                resultado = ai.analizar_fuente(self.texto, self.modelo)
            elif self.accion == "consulta":
                resultado = ai.consulta_libre(self.texto, self.pregunta, self.modelo)
            else:
                raise ValueError(f"Accion desconocida: {self.accion}")
            self.resultado.emit(resultado)
        except Exception as exc:
            self.error.emit(str(exc))
