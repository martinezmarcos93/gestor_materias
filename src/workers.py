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

                texto, ocr_aplicado, metadata = ocr.extraer_texto_pdf(destino, progreso_cb=cb)

                titulo = origen.stem
                nombre_generico = titulo.strip().lower() in ("", "documento", "download", "scan", "untitled")
                if metadata.get("titulo") and (nombre_generico or titulo.isdigit()):
                    titulo = metadata["titulo"]

                doc_id = db.agregar_documento(
                    self.materia_id, titulo, self.tipo, destino, texto, ocr_aplicado,
                    autor=metadata.get("autor"),
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

    def __init__(self, accion, texto, modelo, pregunta=None, contexto_catedra=None, titulo=None, autor=None):
        super().__init__()
        self.accion = accion
        self.texto = texto
        self.modelo = modelo
        self.pregunta = pregunta
        self.contexto_catedra = contexto_catedra
        self.titulo = titulo
        self.autor = autor

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
            elif self.accion == "cita":
                resultado = ai.generar_cita(self.titulo, self.autor, self.texto, self.modelo)
            else:
                raise ValueError(f"Accion desconocida: {self.accion}")
            self.resultado.emit(resultado)
        except Exception as exc:
            self.error.emit(str(exc))


class CorreccionOCRWorker(QThread):
    progreso = Signal(int, int)
    resultado = Signal(str)
    error = Signal(str)

    def __init__(self, texto, modelo):
        super().__init__()
        self.texto = texto
        self.modelo = modelo

    def run(self):
        try:
            corregido = ai.corregir_ocr(
                self.texto, self.modelo, progreso_cb=lambda a, t: self.progreso.emit(a, t)
            )
            self.resultado.emit(corregido)
        except Exception as exc:
            self.error.emit(str(exc))


class ConsultaCorpusWorker(QThread):
    resultado = Signal(str)
    error = Signal(str)

    def __init__(self, pregunta, documentos, modelo):
        super().__init__()
        self.pregunta = pregunta
        self.documentos = documentos
        self.modelo = modelo

    def run(self):
        try:
            resultado = ai.consulta_corpus(self.pregunta, self.documentos, self.modelo)
            self.resultado.emit(resultado)
        except Exception as exc:
            self.error.emit(str(exc))


class ComparacionWorker(QThread):
    resultado = Signal(str)
    error = Signal(str)

    def __init__(self, titulo_a, texto_a, titulo_b, texto_b, modelo, contexto_catedra=None):
        super().__init__()
        self.titulo_a = titulo_a
        self.texto_a = texto_a
        self.titulo_b = titulo_b
        self.texto_b = texto_b
        self.modelo = modelo
        self.contexto_catedra = contexto_catedra

    def run(self):
        try:
            resultado = ai.comparar_textos(
                self.titulo_a, self.texto_a, self.titulo_b, self.texto_b,
                self.modelo, contexto_catedra=self.contexto_catedra,
            )
            self.resultado.emit(resultado)
        except Exception as exc:
            self.error.emit(str(exc))


class LineaTiempoWorker(QThread):
    resultado = Signal(list)
    error = Signal(str)

    def __init__(self, texto, modelo):
        super().__init__()
        self.texto = texto
        self.modelo = modelo

    def run(self):
        try:
            eventos = ai.extraer_linea_tiempo(self.texto, self.modelo)
            self.resultado.emit(eventos)
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
