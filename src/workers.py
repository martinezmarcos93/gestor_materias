import shutil
from pathlib import Path

from PySide6.QtCore import QThread, Signal

from . import ai, db, ocr


class ImportWorker(QThread):
    progreso = Signal(int, int, str)
    documento_importado = Signal(int, str)
    error = Signal(str, str)
    terminado = Signal()

    def __init__(self, materia_id, rutas_pdf, tipo):
        super().__init__()
        self.materia_id = materia_id
        self.rutas_pdf = rutas_pdf
        self.tipo = tipo

    def run(self):
        destino_dir = db.ruta_materia(self.materia_id)

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
                if self.tipo == "programa":
                    db.marcar_como_programa(self.materia_id, doc_id)
                self.documento_importado.emit(doc_id, titulo)
            except Exception as exc:
                self.error.emit(origen.name, str(exc))

        self.terminado.emit()


class AIWorker(QThread):
    resultado = Signal(str)
    error = Signal(str)

    def __init__(self, accion, texto, modelo, pregunta=None, contexto_catedra=None):
        super().__init__()
        self.accion = accion
        self.texto = texto
        self.modelo = modelo
        self.pregunta = pregunta
        self.contexto_catedra = contexto_catedra

    def run(self):
        try:
            if self.accion == "resumir":
                resultado = ai.resumir(self.texto, self.modelo, contexto_catedra=self.contexto_catedra)
            elif self.accion == "preguntas":
                resultado = ai.preguntas_de_estudio(
                    self.texto, self.modelo, contexto_catedra=self.contexto_catedra
                )
            elif self.accion == "fuente":
                resultado = ai.analizar_fuente(
                    self.texto, self.modelo, contexto_catedra=self.contexto_catedra
                )
            elif self.accion == "consulta":
                resultado = ai.consulta_libre(
                    self.texto, self.pregunta, self.modelo, contexto_catedra=self.contexto_catedra
                )
            else:
                raise ValueError(f"Accion desconocida: {self.accion}")
            self.resultado.emit(resultado)
        except Exception as exc:
            self.error.emit(str(exc))


class ProgramaWorker(QThread):
    resultado = Signal(dict)
    error = Signal(str)

    def __init__(self, texto, modelo):
        super().__init__()
        self.texto = texto
        self.modelo = modelo

    def run(self):
        try:
            datos = ai.analizar_programa(self.texto, self.modelo)
            self.resultado.emit(datos)
        except Exception as exc:
            self.error.emit(str(exc))


class ConexionIAWorker(QThread):
    resultado = Signal(bool, str)

    def run(self):
        ok, mensaje = ai.verificar_conexion()
        self.resultado.emit(ok, mensaje)
