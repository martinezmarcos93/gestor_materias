from datetime import date

from PySide6.QtCore import Qt
from PySide6.QtGui import QAction
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMessageBox,
    QPlainTextEdit,
    QProgressDialog,
    QPushButton,
    QSpinBox,
    QSplitter,
    QTabWidget,
    QTextEdit,
    QToolBar,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)

from . import ai, db
from .workers import AIWorker, ImportWorker

ROL_MATERIA = Qt.UserRole
ROL_DOCUMENTO = Qt.UserRole + 1
CUATRIMESTRES = {"1er cuatrimestre": 1, "2do cuatrimestre": 2, "Anual": 0}
CUATRIMESTRES_INV = {v: k for k, v in CUATRIMESTRES.items()}
TIPOS_DOCUMENTO = ["texto", "consigna", "parcial", "fuente primaria"]


class NuevaMateriaDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Nueva materia")
        layout = QFormLayout(self)

        self.nombre_edit = QLineEdit()
        self.anio_spin = QSpinBox()
        self.anio_spin.setRange(2000, 2100)
        self.anio_spin.setValue(date.today().year)
        self.cuatrimestre_combo = QComboBox()
        self.cuatrimestre_combo.addItems(list(CUATRIMESTRES.keys()))

        layout.addRow("Nombre:", self.nombre_edit)
        layout.addRow("Anio:", self.anio_spin)
        layout.addRow("Periodo:", self.cuatrimestre_combo)

        botones = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        botones.accepted.connect(self.accept)
        botones.rejected.connect(self.reject)
        layout.addRow(botones)

    def datos(self):
        return (
            self.nombre_edit.text().strip(),
            self.anio_spin.value(),
            CUATRIMESTRES[self.cuatrimestre_combo.currentText()],
        )


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Archivo Historiografico - Herramienta de estudio")
        self.resize(1200, 750)

        db.init_db()

        self.doc_actual = None
        self.import_worker = None
        self.ai_worker = None

        self._crear_toolbar()
        self._crear_layout_central()
        self._recargar_arbol()

    # ---------- construccion de UI ----------

    def _crear_toolbar(self):
        toolbar = QToolBar("Principal")
        self.addToolBar(toolbar)

        accion_materia = QAction("Nueva materia", self)
        accion_materia.triggered.connect(self._nueva_materia)
        toolbar.addAction(accion_materia)

        accion_importar = QAction("Importar PDFs...", self)
        accion_importar.triggered.connect(self._importar_pdfs)
        toolbar.addAction(accion_importar)

        accion_renombrar = QAction("Renombrar documento", self)
        accion_renombrar.triggered.connect(self._renombrar_documento)
        toolbar.addAction(accion_renombrar)

        accion_eliminar = QAction("Eliminar", self)
        accion_eliminar.triggered.connect(self._eliminar_seleccion)
        toolbar.addAction(accion_eliminar)

    def _crear_layout_central(self):
        splitter = QSplitter(Qt.Horizontal)

        # --- panel izquierdo: materias + busqueda ---
        panel_izq = QTabWidget()

        self.arbol = QTreeWidget()
        self.arbol.setHeaderLabels(["Materias y documentos"])
        self.arbol.itemSelectionChanged.connect(self._seleccion_cambiada)
        panel_izq.addTab(self.arbol, "Materias")

        panel_busqueda = QWidget()
        layout_busqueda = QVBoxLayout(panel_busqueda)
        fila_busqueda = QHBoxLayout()
        self.busqueda_edit = QLineEdit()
        self.busqueda_edit.setPlaceholderText("Buscar en toda la bibliografia...")
        self.busqueda_edit.returnPressed.connect(self._buscar)
        boton_buscar = QPushButton("Buscar")
        boton_buscar.clicked.connect(self._buscar)
        fila_busqueda.addWidget(self.busqueda_edit)
        fila_busqueda.addWidget(boton_buscar)
        layout_busqueda.addLayout(fila_busqueda)

        self.resultados_lista = QListWidget()
        self.resultados_lista.itemDoubleClicked.connect(self._abrir_resultado_busqueda)
        layout_busqueda.addWidget(self.resultados_lista)
        panel_izq.addTab(panel_busqueda, "Busqueda")

        splitter.addWidget(panel_izq)

        # --- panel derecho: texto + analisis IA ---
        panel_der = QTabWidget()

        self.texto_view = QPlainTextEdit()
        self.texto_view.setReadOnly(True)
        panel_der.addTab(self.texto_view, "Texto")

        panel_der.addTab(self._crear_panel_ia(), "Analisis IA")

        splitter.addWidget(panel_der)
        splitter.setSizes([350, 850])

        self.setCentralWidget(splitter)

    def _crear_panel_ia(self):
        panel = QWidget()
        layout = QVBoxLayout(panel)

        fila_modelo = QHBoxLayout()
        fila_modelo.addWidget(QLabel("Modelo local (Ollama):"))
        self.modelo_combo = QComboBox()
        modelos = ai.modelos_disponibles()
        self.modelo_combo.addItems(modelos)
        if ai.MODELO_DEFAULT in modelos:
            self.modelo_combo.setCurrentText(ai.MODELO_DEFAULT)
        fila_modelo.addWidget(self.modelo_combo)
        fila_modelo.addStretch()
        layout.addLayout(fila_modelo)

        fila_botones = QHBoxLayout()
        self.boton_resumir = QPushButton("Resumir")
        self.boton_resumir.clicked.connect(lambda: self._ejecutar_ia("resumir"))
        self.boton_preguntas = QPushButton("Preguntas de estudio")
        self.boton_preguntas.clicked.connect(lambda: self._ejecutar_ia("preguntas"))
        self.boton_fuente = QPushButton("Analizar como fuente")
        self.boton_fuente.clicked.connect(lambda: self._ejecutar_ia("fuente"))
        fila_botones.addWidget(self.boton_resumir)
        fila_botones.addWidget(self.boton_preguntas)
        fila_botones.addWidget(self.boton_fuente)
        layout.addLayout(fila_botones)

        fila_consulta = QHBoxLayout()
        self.consulta_edit = QLineEdit()
        self.consulta_edit.setPlaceholderText("Preguntale algo puntual sobre este texto...")
        self.consulta_edit.returnPressed.connect(lambda: self._ejecutar_ia("consulta"))
        self.boton_consultar = QPushButton("Preguntar")
        self.boton_consultar.clicked.connect(lambda: self._ejecutar_ia("consulta"))
        fila_consulta.addWidget(self.consulta_edit)
        fila_consulta.addWidget(self.boton_consultar)
        layout.addLayout(fila_consulta)

        self.ia_estado = QLabel("")
        layout.addWidget(self.ia_estado)

        self.ia_resultado = QTextEdit()
        self.ia_resultado.setReadOnly(True)
        layout.addWidget(self.ia_resultado)

        self._botones_ia = [
            self.boton_resumir,
            self.boton_preguntas,
            self.boton_fuente,
            self.boton_consultar,
        ]

        return panel

    # ---------- materias y documentos ----------

    def _recargar_arbol(self):
        self.arbol.clear()
        for materia in db.listar_materias():
            periodo = CUATRIMESTRES_INV.get(materia["cuatrimestre"], "")
            item_materia = QTreeWidgetItem([f"{materia['nombre']} ({materia['anio']} - {periodo})"])
            item_materia.setData(0, ROL_MATERIA, materia["id"])
            for doc in db.listar_documentos(materia["id"]):
                marca_ocr = " [OCR]" if doc["ocr_aplicado"] else ""
                item_doc = QTreeWidgetItem([f"[{doc['tipo']}] {doc['titulo']}{marca_ocr}"])
                item_doc.setData(0, ROL_DOCUMENTO, doc["id"])
                item_materia.addChild(item_doc)
            self.arbol.addTopLevelItem(item_materia)
        self.arbol.expandAll()

    def _nueva_materia(self):
        dialogo = NuevaMateriaDialog(self)
        if dialogo.exec() == QDialog.Accepted:
            nombre, anio, cuatrimestre = dialogo.datos()
            if not nombre:
                QMessageBox.warning(self, "Falta el nombre", "Ingresa el nombre de la materia.")
                return
            db.crear_materia(nombre, anio, cuatrimestre)
            self._recargar_arbol()

    def _materia_seleccionada_id(self):
        item = self.arbol.currentItem()
        if item is None:
            return None
        materia_id = item.data(0, ROL_MATERIA)
        if materia_id is not None:
            return materia_id
        if item.parent() is not None:
            return item.parent().data(0, ROL_MATERIA)
        return None

    def _importar_pdfs(self):
        materia_id = self._materia_seleccionada_id()
        if materia_id is None:
            QMessageBox.information(
                self, "Elegi una materia", "Selecciona (o crea) una materia antes de importar."
            )
            return

        rutas, _ = QFileDialog.getOpenFileNames(
            self, "Seleccionar PDFs", "", "Archivos PDF (*.pdf)"
        )
        if not rutas:
            return

        tipo, ok = QInputDialog.getItem(
            self, "Tipo de documento", "Estos archivos son:", TIPOS_DOCUMENTO, 0, False
        )
        if not ok:
            return

        conn_row = next(m for m in db.listar_materias() if m["id"] == materia_id)

        self.progreso = QProgressDialog("Importando...", "Cancelar", 0, len(rutas), self)
        self.progreso.setWindowModality(Qt.WindowModal)
        self.progreso.show()

        self.import_worker = ImportWorker(materia_id, conn_row["nombre"], rutas, tipo)
        self.import_worker.progreso.connect(self._progreso_importacion)
        self.import_worker.documento_importado.connect(lambda *_: self._recargar_arbol())
        self.import_worker.error.connect(self._error_importacion)
        self.import_worker.terminado.connect(self._importacion_terminada)
        self.import_worker.start()

    def _progreso_importacion(self, actual, total, mensaje):
        self.progreso.setMaximum(total)
        self.progreso.setValue(actual - 1)
        self.progreso.setLabelText(mensaje)

    def _error_importacion(self, nombre_archivo, mensaje):
        QMessageBox.warning(self, f"Error con {nombre_archivo}", mensaje)

    def _importacion_terminada(self):
        self.progreso.setValue(self.progreso.maximum())
        self._recargar_arbol()

    def _renombrar_documento(self):
        item = self.arbol.currentItem()
        if item is None or item.data(0, ROL_DOCUMENTO) is None:
            QMessageBox.information(self, "Elegi un documento", "Selecciona un documento en el arbol.")
            return
        doc_id = item.data(0, ROL_DOCUMENTO)
        doc = db.obtener_documento(doc_id)
        nuevo_titulo, ok = QInputDialog.getText(self, "Renombrar", "Nuevo titulo:", text=doc["titulo"])
        if ok and nuevo_titulo.strip():
            db.renombrar_documento(doc_id, nuevo_titulo.strip())
            self._recargar_arbol()

    def _eliminar_seleccion(self):
        item = self.arbol.currentItem()
        if item is None:
            return
        doc_id = item.data(0, ROL_DOCUMENTO)
        materia_id = item.data(0, ROL_MATERIA)
        if doc_id is not None:
            if self._confirmar("Eliminar este documento del archivo?"):
                db.eliminar_documento(doc_id)
        elif materia_id is not None:
            if self._confirmar("Eliminar esta materia y todos sus documentos?"):
                db.eliminar_materia(materia_id)
        self._recargar_arbol()

    def _confirmar(self, mensaje):
        return (
            QMessageBox.question(self, "Confirmar", mensaje, QMessageBox.Yes | QMessageBox.No)
            == QMessageBox.Yes
        )

    def _seleccion_cambiada(self):
        item = self.arbol.currentItem()
        if item is None:
            return
        doc_id = item.data(0, ROL_DOCUMENTO)
        if doc_id is None:
            self.texto_view.setPlainText("")
            self.doc_actual = None
            return
        self._cargar_documento(doc_id)

    def _cargar_documento(self, doc_id):
        doc = db.obtener_documento(doc_id)
        self.doc_actual = doc
        self.texto_view.setPlainText(doc["texto"] or "(sin texto extraido)")
        self.ia_resultado.clear()

    # ---------- busqueda ----------

    def _buscar(self):
        consulta = self.busqueda_edit.text().strip()
        if not consulta:
            return
        self.resultados_lista.clear()
        try:
            resultados = db.buscar(consulta)
        except Exception as exc:
            QMessageBox.warning(self, "Busqueda invalida", str(exc))
            return
        for fila in resultados:
            texto_item = f"[{fila['materia']}] {fila['titulo']} ({fila['tipo']})\n{fila['extracto']}"
            item = QListWidgetItem(texto_item)
            item.setData(Qt.UserRole, fila["id"])
            self.resultados_lista.addItem(item)

    def _abrir_resultado_busqueda(self, item):
        doc_id = item.data(Qt.UserRole)
        self._cargar_documento(doc_id)

    # ---------- panel IA ----------

    def _ejecutar_ia(self, accion):
        if self.doc_actual is None:
            QMessageBox.information(self, "Elegi un documento", "Selecciona un documento primero.")
            return
        texto = self.doc_actual["texto"] or ""
        if not texto.strip():
            QMessageBox.information(self, "Sin texto", "Este documento no tiene texto extraido.")
            return

        pregunta = None
        if accion == "consulta":
            pregunta = self.consulta_edit.text().strip()
            if not pregunta:
                return

        modelo = self.modelo_combo.currentText() or ai.MODELO_DEFAULT

        for boton in self._botones_ia:
            boton.setEnabled(False)
        self.ia_estado.setText(f"Consultando modelo local ({modelo})...")
        self.ia_resultado.clear()

        self.ai_worker = AIWorker(accion, texto, modelo, pregunta)
        self.ai_worker.resultado.connect(self._ia_resultado_listo)
        self.ai_worker.error.connect(self._ia_error)
        self.ai_worker.start()

    def _ia_resultado_listo(self, resultado):
        self.ia_resultado.setPlainText(resultado)
        self.ia_estado.setText("Listo.")
        for boton in self._botones_ia:
            boton.setEnabled(True)

    def _ia_error(self, mensaje):
        self.ia_estado.setText("Error al consultar el modelo.")
        QMessageBox.warning(
            self,
            "Error de IA local",
            f"No se pudo completar la consulta a Ollama:\n{mensaje}\n\n"
            "Verifica que Ollama este corriendo (ollama serve) y que el modelo este descargado.",
        )
        for boton in self._botones_ia:
            boton.setEnabled(True)
