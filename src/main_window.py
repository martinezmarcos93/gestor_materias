from datetime import date

from PySide6.QtCore import QDate, Qt
from PySide6.QtGui import QAction
from PySide6.QtWidgets import (
    QComboBox,
    QDateEdit,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QHeaderView,
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
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QTextEdit,
    QToolBar,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)

from . import ai, config, db, exportador
from .workers import AIWorker, ConexionIAWorker, ImportWorker, ProgramaWorker

ROL_TIPO = Qt.UserRole
ROL_ID = Qt.UserRole + 1


def sugerir_nombre_periodo(tipo_periodo, existentes_en_anio):
    n = existentes_en_anio
    ordinales = {0: "1er", 1: "2do", 2: "3er", 3: "4to"}
    ordinal = ordinales.get(n, f"{n + 1}to")
    if tipo_periodo == "anual":
        return "Ciclo anual" if n == 0 else f"Ciclo anual {n + 1}"
    return f"{ordinal} {tipo_periodo.capitalize()}"


class CarreraDialog(QDialog):
    def __init__(self, parent=None, nombre="", tipo_periodo="cuatrimestre"):
        super().__init__(parent)
        self.setWindowTitle("Carrera")
        layout = QFormLayout(self)

        self.nombre_edit = QLineEdit(nombre)
        self.tipo_combo = QComboBox()
        self.tipo_combo.addItems(db.TIPOS_PERIODO)
        self.tipo_combo.setCurrentText(tipo_periodo)

        layout.addRow("Nombre de la carrera:", self.nombre_edit)
        layout.addRow("Se divide en:", self.tipo_combo)

        botones = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        botones.accepted.connect(self.accept)
        botones.rejected.connect(self.reject)
        layout.addRow(botones)

    def datos(self):
        return self.nombre_edit.text().strip(), self.tipo_combo.currentText()


class PeriodoDialog(QDialog):
    def __init__(self, parent=None, tipo_periodo="cuatrimestre", nombre="", anio=None, existentes_en_anio=0):
        super().__init__(parent)
        self.setWindowTitle("Periodo")
        layout = QFormLayout(self)

        anio = anio or date.today().year
        self.nombre_edit = QLineEdit(nombre or sugerir_nombre_periodo(tipo_periodo, existentes_en_anio))
        self.anio_spin = QSpinBox()
        self.anio_spin.setRange(2000, 2100)
        self.anio_spin.setValue(anio)

        layout.addRow("Nombre del periodo:", self.nombre_edit)
        layout.addRow("Anio:", self.anio_spin)

        botones = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        botones.accepted.connect(self.accept)
        botones.rejected.connect(self.reject)
        layout.addRow(botones)

    def datos(self):
        return self.nombre_edit.text().strip(), self.anio_spin.value()


class MateriaDialog(QDialog):
    def __init__(self, parent=None, nombre=""):
        super().__init__(parent)
        self.setWindowTitle("Materia")
        layout = QFormLayout(self)

        self.nombre_edit = QLineEdit(nombre)
        layout.addRow("Nombre de la materia:", self.nombre_edit)

        botones = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        botones.accepted.connect(self.accept)
        botones.rejected.connect(self.reject)
        layout.addRow(botones)

    def datos(self):
        return self.nombre_edit.text().strip()


class DocumentoDialog(QDialog):
    def __init__(self, parent=None, titulo="", tipo="texto", autor=""):
        super().__init__(parent)
        self.setWindowTitle("Documento")
        layout = QFormLayout(self)

        self.titulo_edit = QLineEdit(titulo)
        self.tipo_combo = QComboBox()
        self.tipo_combo.addItems(db.TIPOS_DOCUMENTO)
        self.tipo_combo.setCurrentText(tipo)
        self.autor_edit = QLineEdit(autor or "")

        layout.addRow("Titulo:", self.titulo_edit)
        layout.addRow("Tipo:", self.tipo_combo)
        layout.addRow("Autor:", self.autor_edit)

        botones = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        botones.accepted.connect(self.accept)
        botones.rejected.connect(self.reject)
        layout.addRow(botones)

    def datos(self):
        return self.titulo_edit.text().strip(), self.tipo_combo.currentText(), self.autor_edit.text().strip()


class EventoDialog(QDialog):
    def __init__(self, parent=None, titulo="", fecha=None, tipo="parcial", descripcion=""):
        super().__init__(parent)
        self.setWindowTitle("Evento del cronograma")
        layout = QFormLayout(self)

        self.titulo_edit = QLineEdit(titulo)
        self.fecha_edit = QDateEdit()
        self.fecha_edit.setCalendarPopup(True)
        self.fecha_edit.setDate(fecha or QDate.currentDate())
        self.tipo_combo = QComboBox()
        self.tipo_combo.addItems(db.TIPOS_EVENTO)
        self.tipo_combo.setCurrentText(tipo)
        self.descripcion_edit = QLineEdit(descripcion or "")

        layout.addRow("Titulo:", self.titulo_edit)
        layout.addRow("Fecha:", self.fecha_edit)
        layout.addRow("Tipo:", self.tipo_combo)
        layout.addRow("Descripcion:", self.descripcion_edit)

        botones = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        botones.accepted.connect(self.accept)
        botones.rejected.connect(self.reject)
        layout.addRow(botones)

    def datos(self):
        return (
            self.titulo_edit.text().strip(),
            self.fecha_edit.date().toString("yyyy-MM-dd"),
            self.tipo_combo.currentText(),
            self.descripcion_edit.text().strip(),
        )


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Gestor de Materias - Herramienta de estudio")
        self.resize(1300, 780)

        db.init_db()

        self.doc_actual = None
        self.materia_actual_id = None
        self.import_worker = None
        self.ai_worker = None
        self.conexion_worker = None
        self.programa_worker = None
        self.ia_accion_actual = None
        self.ia_pregunta_actual = None
        self.ia_modelo_actual = None

        self._crear_toolbar()
        self._crear_layout_central()
        self._recargar_arbol()
        self._recargar_proximos_eventos()

        if not db.listar_carreras():
            self._nueva_carrera()

    # ---------- construccion de UI ----------

    def _crear_toolbar(self):
        toolbar = QToolBar("Principal")
        self.addToolBar(toolbar)

        acciones = [
            ("Nueva carrera", self._nueva_carrera),
            ("Nuevo periodo", self._nuevo_periodo),
            ("Nueva materia", self._nueva_materia),
            ("Importar documentos...", self._importar_documentos),
            ("Nuevo evento", self._nuevo_evento),
            (None, None),
            ("Editar", self._editar_seleccion),
            ("Eliminar", self._eliminar_seleccion),
            (None, None),
            ("Verificar conexion IA", self._verificar_conexion_ia),
        ]
        for texto, callback in acciones:
            if texto is None:
                toolbar.addSeparator()
                continue
            accion = QAction(texto, self)
            accion.triggered.connect(callback)
            toolbar.addAction(accion)

    def _crear_layout_central(self):
        splitter = QSplitter(Qt.Horizontal)

        # --- panel izquierdo: arbol + busqueda + proximos eventos ---
        panel_izq = QTabWidget()

        self.arbol = QTreeWidget()
        self.arbol.setHeaderLabels(["Carrera / Periodo / Materia / Documento"])
        self.arbol.itemSelectionChanged.connect(self._seleccion_cambiada)
        panel_izq.addTab(self.arbol, "Materias")

        panel_izq.addTab(self._crear_panel_busqueda(), "Busqueda")
        panel_izq.addTab(self._crear_panel_proximos(), "Proximos eventos")

        splitter.addWidget(panel_izq)

        # --- panel derecho: texto + cronograma + analisis IA ---
        panel_der = QTabWidget()

        self.texto_view = QPlainTextEdit()
        self.texto_view.setReadOnly(True)
        panel_der.addTab(self.texto_view, "Texto")

        panel_der.addTab(self._crear_panel_programa(), "Programa")
        panel_der.addTab(self._crear_panel_cronograma(), "Cronograma de la materia")
        panel_der.addTab(self._crear_panel_ia(), "Analisis IA")

        splitter.addWidget(panel_der)
        splitter.setSizes([380, 920])

        self.setCentralWidget(splitter)

    def _crear_panel_busqueda(self):
        panel = QWidget()
        layout = QVBoxLayout(panel)
        fila = QHBoxLayout()
        self.busqueda_edit = QLineEdit()
        self.busqueda_edit.setPlaceholderText("Buscar en toda la bibliografia...")
        self.busqueda_edit.returnPressed.connect(self._buscar)
        boton_buscar = QPushButton("Buscar")
        boton_buscar.clicked.connect(self._buscar)
        fila.addWidget(self.busqueda_edit)
        fila.addWidget(boton_buscar)
        layout.addLayout(fila)

        self.resultados_lista = QListWidget()
        self.resultados_lista.itemDoubleClicked.connect(self._abrir_resultado_busqueda)
        layout.addWidget(self.resultados_lista)
        return panel

    def _crear_panel_proximos(self):
        panel = QWidget()
        layout = QVBoxLayout(panel)
        boton_refrescar = QPushButton("Actualizar")
        boton_refrescar.clicked.connect(self._recargar_proximos_eventos)
        layout.addWidget(boton_refrescar)
        self.proximos_lista = QListWidget()
        layout.addWidget(self.proximos_lista)
        return panel

    def _crear_panel_cronograma(self):
        panel = QWidget()
        layout = QVBoxLayout(panel)

        self.cronograma_label = QLabel("Selecciona una materia para ver su cronograma.")
        layout.addWidget(self.cronograma_label)

        self.cronograma_tabla = QTableWidget(0, 4)
        self.cronograma_tabla.setHorizontalHeaderLabels(["Fecha", "Tipo", "Titulo", "Descripcion"])
        self.cronograma_tabla.horizontalHeader().setSectionResizeMode(3, QHeaderView.Stretch)
        self.cronograma_tabla.setSelectionBehavior(QTableWidget.SelectRows)
        self.cronograma_tabla.setEditTriggers(QTableWidget.NoEditTriggers)
        layout.addWidget(self.cronograma_tabla)

        fila_botones = QHBoxLayout()
        boton_agregar = QPushButton("Agregar evento")
        boton_agregar.clicked.connect(self._nuevo_evento)
        boton_editar = QPushButton("Editar evento")
        boton_editar.clicked.connect(self._editar_evento_seleccionado)
        boton_eliminar = QPushButton("Eliminar evento")
        boton_eliminar.clicked.connect(self._eliminar_evento_seleccionado)
        fila_botones.addWidget(boton_agregar)
        fila_botones.addWidget(boton_editar)
        fila_botones.addWidget(boton_eliminar)
        layout.addLayout(fila_botones)

        return panel

    def _crear_panel_programa(self):
        panel = QWidget()
        layout = QVBoxLayout(panel)

        self.programa_label = QLabel("Selecciona una materia para ver su programa.")
        layout.addWidget(self.programa_label)

        self.boton_analizar_programa = QPushButton("Analizar programa con IA")
        self.boton_analizar_programa.clicked.connect(self._analizar_programa)
        self.boton_analizar_programa.setEnabled(False)
        layout.addWidget(self.boton_analizar_programa)

        layout.addWidget(QLabel("Ejes tematicos:"))
        self.programa_ejes = QPlainTextEdit()
        self.programa_ejes.setReadOnly(True)
        self.programa_ejes.setMaximumHeight(110)
        layout.addWidget(self.programa_ejes)

        layout.addWidget(QLabel("Perspectiva / enfoque de la catedra:"))
        self.programa_perspectiva = QPlainTextEdit()
        self.programa_perspectiva.setReadOnly(True)
        self.programa_perspectiva.setMaximumHeight(90)
        layout.addWidget(self.programa_perspectiva)

        fila_biblio = QHBoxLayout()
        col_obligatoria = QVBoxLayout()
        col_obligatoria.addWidget(QLabel("Bibliografia obligatoria:"))
        self.programa_obligatoria = QPlainTextEdit()
        self.programa_obligatoria.setReadOnly(True)
        col_obligatoria.addWidget(self.programa_obligatoria)
        col_opcional = QVBoxLayout()
        col_opcional.addWidget(QLabel("Bibliografia opcional:"))
        self.programa_opcional = QPlainTextEdit()
        self.programa_opcional.setReadOnly(True)
        col_opcional.addWidget(self.programa_opcional)
        fila_biblio.addLayout(col_obligatoria)
        fila_biblio.addLayout(col_opcional)
        layout.addLayout(fila_biblio)

        return panel

    def _crear_panel_ia(self):
        panel = QWidget()
        layout = QVBoxLayout(panel)

        fila_modelo = QHBoxLayout()
        fila_modelo.addWidget(QLabel("Modelo (Claude Code, cuenta Pro):"))
        self.modelo_combo = QComboBox()
        self.modelo_combo.addItems(ai.MODELOS)
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

        fila_exportar = QHBoxLayout()
        self.carpeta_exportacion_label = QLabel(self._texto_carpeta_exportacion())
        self.boton_elegir_carpeta = QPushButton("Elegir carpeta (vault Obsidian)...")
        self.boton_elegir_carpeta.clicked.connect(self._elegir_carpeta_exportacion)
        self.boton_exportar_md = QPushButton("Exportar a Markdown")
        self.boton_exportar_md.clicked.connect(self._exportar_markdown)
        self.boton_exportar_md.setEnabled(False)
        fila_exportar.addWidget(self.carpeta_exportacion_label, stretch=1)
        fila_exportar.addWidget(self.boton_elegir_carpeta)
        fila_exportar.addWidget(self.boton_exportar_md)
        layout.addLayout(fila_exportar)

        self._botones_ia = [
            self.boton_resumir,
            self.boton_preguntas,
            self.boton_fuente,
            self.boton_consultar,
        ]

        return panel

    def _texto_carpeta_exportacion(self):
        carpeta = config.obtener_carpeta_exportacion()
        return f"Carpeta de exportacion: {carpeta}" if carpeta else "Carpeta de exportacion: (no configurada)"

    # ---------- arbol: construccion y navegacion ----------

    def _recargar_arbol(self):
        item_previo = self._seleccion_actual()
        self.arbol.clear()
        for carrera in db.listar_carreras():
            item_carrera = QTreeWidgetItem([f"{carrera['nombre']} ({carrera['tipo_periodo']})"])
            item_carrera.setData(0, ROL_TIPO, "carrera")
            item_carrera.setData(0, ROL_ID, carrera["id"])

            for periodo in db.listar_periodos(carrera["id"]):
                item_periodo = QTreeWidgetItem([f"{periodo['nombre']} {periodo['anio']}"])
                item_periodo.setData(0, ROL_TIPO, "periodo")
                item_periodo.setData(0, ROL_ID, periodo["id"])

                for materia in db.listar_materias(periodo["id"]):
                    marca_programa = "" if materia["programa_doc_id"] else " (sin programa)"
                    item_materia = QTreeWidgetItem([f"{materia['nombre']}{marca_programa}"])
                    item_materia.setData(0, ROL_TIPO, "materia")
                    item_materia.setData(0, ROL_ID, materia["id"])

                    for doc in db.listar_documentos(materia["id"]):
                        marca_ocr = " [OCR]" if doc["ocr_aplicado"] else ""
                        item_doc = QTreeWidgetItem([f"[{doc['tipo']}] {doc['titulo']}{marca_ocr}"])
                        item_doc.setData(0, ROL_TIPO, "documento")
                        item_doc.setData(0, ROL_ID, doc["id"])
                        item_materia.addChild(item_doc)

                    item_periodo.addChild(item_materia)

                item_carrera.addChild(item_periodo)

            self.arbol.addTopLevelItem(item_carrera)
        self.arbol.expandAll()

        if item_previo:
            self._reseleccionar(*item_previo)

    def _seleccion_actual(self):
        item = self.arbol.currentItem()
        if item is None:
            return None
        return item.data(0, ROL_TIPO), item.data(0, ROL_ID)

    def _reseleccionar(self, tipo, id_buscado):
        pila = [self.arbol.topLevelItem(i) for i in range(self.arbol.topLevelItemCount())]
        while pila:
            item = pila.pop()
            if item.data(0, ROL_TIPO) == tipo and item.data(0, ROL_ID) == id_buscado:
                self.arbol.setCurrentItem(item)
                return
            pila.extend(item.child(i) for i in range(item.childCount()))

    def _ancestro_id(self, tipo_buscado):
        """Busca hacia arriba desde la seleccion actual el id del ancestro (o si mismo) del tipo pedido."""
        item = self.arbol.currentItem()
        while item is not None:
            if item.data(0, ROL_TIPO) == tipo_buscado:
                return item.data(0, ROL_ID)
            item = item.parent()
        return None

    # ---------- CRUD: carreras ----------

    def _nueva_carrera(self):
        dialogo = CarreraDialog(self)
        if dialogo.exec() == QDialog.Accepted:
            nombre, tipo_periodo = dialogo.datos()
            if not nombre:
                QMessageBox.warning(self, "Falta el nombre", "Ingresa el nombre de la carrera.")
                return
            db.crear_carrera(nombre, tipo_periodo)
            self._recargar_arbol()

    # ---------- CRUD: periodos ----------

    def _nuevo_periodo(self):
        carrera_id = self._ancestro_id("carrera")
        if carrera_id is None:
            QMessageBox.information(self, "Elegi una carrera", "Selecciona una carrera antes de agregar un periodo.")
            return
        carrera = db.obtener_carrera(carrera_id)
        anio = date.today().year
        existentes = [p for p in db.listar_periodos(carrera_id) if p["anio"] == anio]
        dialogo = PeriodoDialog(
            self, tipo_periodo=carrera["tipo_periodo"], anio=anio, existentes_en_anio=len(existentes)
        )
        if dialogo.exec() == QDialog.Accepted:
            nombre, anio = dialogo.datos()
            if not nombre:
                QMessageBox.warning(self, "Falta el nombre", "Ingresa el nombre del periodo.")
                return
            orden = len([p for p in db.listar_periodos(carrera_id) if p["anio"] == anio])
            db.crear_periodo(carrera_id, nombre, anio, orden)
            self._recargar_arbol()

    # ---------- CRUD: materias ----------

    def _nueva_materia(self):
        periodo_id = self._ancestro_id("periodo")
        if periodo_id is None:
            QMessageBox.information(self, "Elegi un periodo", "Selecciona un periodo antes de agregar una materia.")
            return
        dialogo = MateriaDialog(self)
        if dialogo.exec() == QDialog.Accepted:
            nombre = dialogo.datos()
            if not nombre:
                QMessageBox.warning(self, "Falta el nombre", "Ingresa el nombre de la materia.")
                return
            db.crear_materia(periodo_id, nombre)
            self._recargar_arbol()

    # ---------- documentos: importar ----------

    def _importar_documentos(self):
        materia_id = self._ancestro_id("materia")
        if materia_id is None:
            QMessageBox.information(self, "Elegi una materia", "Selecciona una materia antes de importar.")
            return

        rutas, _ = QFileDialog.getOpenFileNames(self, "Seleccionar PDFs", "", "Archivos PDF (*.pdf)")
        if not rutas:
            return

        tipo, ok = QInputDialog.getItem(
            self, "Tipo de documento", "Estos archivos son:", db.TIPOS_DOCUMENTO, 0, False
        )
        if not ok:
            return

        self.progreso = QProgressDialog("Importando...", "Cancelar", 0, len(rutas), self)
        self.progreso.setWindowModality(Qt.WindowModal)
        self.progreso.show()

        self.import_worker = ImportWorker(materia_id, rutas, tipo)
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

    # ---------- editar / eliminar generico ----------

    def _editar_seleccion(self):
        seleccion = self._seleccion_actual()
        if seleccion is None:
            QMessageBox.information(self, "Elegi un elemento", "Selecciona algo en el arbol para editar.")
            return
        tipo, elemento_id = seleccion

        if tipo == "carrera":
            carrera = db.obtener_carrera(elemento_id)
            dialogo = CarreraDialog(self, carrera["nombre"], carrera["tipo_periodo"])
            if dialogo.exec() == QDialog.Accepted:
                nombre, tipo_periodo = dialogo.datos()
                db.actualizar_carrera(elemento_id, nombre, tipo_periodo)
                self._recargar_arbol()

        elif tipo == "periodo":
            periodo = db.obtener_periodo(elemento_id)
            dialogo = PeriodoDialog(self, nombre=periodo["nombre"], anio=periodo["anio"])
            if dialogo.exec() == QDialog.Accepted:
                nombre, anio = dialogo.datos()
                db.actualizar_periodo(elemento_id, nombre, anio, periodo["orden"])
                self._recargar_arbol()

        elif tipo == "materia":
            materia = db.obtener_materia(elemento_id)
            dialogo = MateriaDialog(self, materia["nombre"])
            if dialogo.exec() == QDialog.Accepted:
                nombre = dialogo.datos()
                db.actualizar_materia(elemento_id, nombre)
                self._recargar_arbol()

        elif tipo == "documento":
            doc = db.obtener_documento(elemento_id)
            dialogo = DocumentoDialog(self, doc["titulo"], doc["tipo"], doc["autor"])
            if dialogo.exec() == QDialog.Accepted:
                titulo, tipo_doc, autor = dialogo.datos()
                db.actualizar_documento(elemento_id, titulo, tipo_doc, autor)
                if tipo_doc == "programa":
                    db.marcar_como_programa(doc["materia_id"], elemento_id)
                self._recargar_arbol()
                self._cargar_programa()

    def _eliminar_seleccion(self):
        seleccion = self._seleccion_actual()
        if seleccion is None:
            return
        tipo, elemento_id = seleccion

        mensajes = {
            "carrera": "Eliminar esta carrera, todos sus periodos, materias y documentos?",
            "periodo": "Eliminar este periodo, sus materias y documentos?",
            "materia": "Eliminar esta materia y todos sus documentos y eventos?",
            "documento": "Eliminar este documento del archivo?",
        }
        if not self._confirmar(mensajes.get(tipo, "Eliminar el elemento seleccionado?")):
            return

        if tipo == "carrera":
            db.eliminar_carrera(elemento_id)
        elif tipo == "periodo":
            db.eliminar_periodo(elemento_id)
        elif tipo == "materia":
            db.eliminar_materia(elemento_id)
        elif tipo == "documento":
            db.eliminar_documento(elemento_id)

        self._recargar_arbol()
        self._recargar_proximos_eventos()

    def _confirmar(self, mensaje):
        return (
            QMessageBox.question(self, "Confirmar", mensaje, QMessageBox.Yes | QMessageBox.No)
            == QMessageBox.Yes
        )

    # ---------- seleccion y carga de contenido ----------

    def _seleccion_cambiada(self):
        seleccion = self._seleccion_actual()
        if seleccion is None:
            return
        tipo, elemento_id = seleccion

        if tipo == "documento":
            self._cargar_documento(elemento_id)
            self.materia_actual_id = self._ancestro_id("materia")
        elif tipo == "materia":
            self.doc_actual = None
            self.texto_view.setPlainText("")
            self.materia_actual_id = elemento_id
        else:
            self.doc_actual = None
            self.texto_view.setPlainText("")
            self.materia_actual_id = None

        self._cargar_cronograma()
        self._cargar_programa()

    def _cargar_documento(self, doc_id):
        doc = db.obtener_documento(doc_id)
        self.doc_actual = doc
        self.texto_view.setPlainText(doc["texto"] or "(sin texto extraido)")
        self.ia_resultado.clear()
        self.boton_exportar_md.setEnabled(False)
        self.ia_accion_actual = None

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
        self._reseleccionar("documento", doc_id)

    # ---------- cronograma ----------

    def _cargar_cronograma(self):
        self.cronograma_tabla.setRowCount(0)
        if self.materia_actual_id is None:
            self.cronograma_label.setText("Selecciona una materia para ver su cronograma.")
            return

        materia = db.obtener_materia(self.materia_actual_id)
        eventos = db.listar_eventos(self.materia_actual_id)
        self.cronograma_label.setText(f"Cronograma de: {materia['nombre']} ({len(eventos)} eventos)")

        self.cronograma_tabla.setRowCount(len(eventos))
        for fila, evento in enumerate(eventos):
            self.cronograma_tabla.setItem(fila, 0, QTableWidgetItem(evento["fecha"] or ""))
            self.cronograma_tabla.setItem(fila, 1, QTableWidgetItem(evento["tipo"]))
            self.cronograma_tabla.setItem(fila, 2, QTableWidgetItem(evento["titulo"]))
            self.cronograma_tabla.setItem(fila, 3, QTableWidgetItem(evento["descripcion"] or ""))
            self.cronograma_tabla.item(fila, 0).setData(Qt.UserRole, evento["id"])

    def _evento_seleccionado_id(self):
        fila = self.cronograma_tabla.currentRow()
        if fila < 0:
            return None
        item = self.cronograma_tabla.item(fila, 0)
        return item.data(Qt.UserRole) if item else None

    def _nuevo_evento(self):
        materia_id = self._ancestro_id("materia") or self.materia_actual_id
        if materia_id is None:
            QMessageBox.information(self, "Elegi una materia", "Selecciona una materia antes de agregar un evento.")
            return
        dialogo = EventoDialog(self)
        if dialogo.exec() == QDialog.Accepted:
            titulo, fecha, tipo, descripcion = dialogo.datos()
            if not titulo:
                QMessageBox.warning(self, "Falta el titulo", "Ingresa el titulo del evento.")
                return
            db.crear_evento(materia_id, titulo, fecha, tipo, descripcion)
            self.materia_actual_id = materia_id
            self._cargar_cronograma()
            self._recargar_proximos_eventos()

    def _editar_evento_seleccionado(self):
        evento_id = self._evento_seleccionado_id()
        if evento_id is None:
            QMessageBox.information(self, "Elegi un evento", "Selecciona un evento en la tabla.")
            return
        evento = db.obtener_evento(evento_id)
        fecha_qt = QDate.fromString(evento["fecha"], "yyyy-MM-dd") if evento["fecha"] else QDate.currentDate()
        dialogo = EventoDialog(self, evento["titulo"], fecha_qt, evento["tipo"], evento["descripcion"])
        if dialogo.exec() == QDialog.Accepted:
            titulo, fecha, tipo, descripcion = dialogo.datos()
            db.actualizar_evento(evento_id, titulo, fecha, tipo, descripcion)
            self._cargar_cronograma()
            self._recargar_proximos_eventos()

    def _eliminar_evento_seleccionado(self):
        evento_id = self._evento_seleccionado_id()
        if evento_id is None:
            return
        if self._confirmar("Eliminar este evento del cronograma?"):
            db.eliminar_evento(evento_id)
            self._cargar_cronograma()
            self._recargar_proximos_eventos()

    def _recargar_proximos_eventos(self):
        self.proximos_lista.clear()
        for evento in db.listar_eventos_proximos():
            texto = f"{evento['fecha']} - [{evento['materia']}] {evento['tipo']}: {evento['titulo']}"
            item = QListWidgetItem(texto)
            item.setData(Qt.UserRole, evento["materia_id"])
            self.proximos_lista.addItem(item)

    # ---------- programa de la materia ----------

    def _cargar_programa(self):
        campos = (self.programa_ejes, self.programa_perspectiva, self.programa_obligatoria, self.programa_opcional)
        if self.materia_actual_id is None:
            self.programa_label.setText("Selecciona una materia para ver su programa.")
            self.boton_analizar_programa.setEnabled(False)
            for campo in campos:
                campo.setPlainText("")
            return

        materia = db.obtener_materia(self.materia_actual_id)
        if not materia["programa_doc_id"]:
            self.programa_label.setText(
                f"{materia['nombre']}: todavia no hay un documento marcado como 'programa'. "
                "Importa o edita un documento y elegi el tipo 'programa'."
            )
            self.boton_analizar_programa.setEnabled(False)
        else:
            doc_programa = db.obtener_documento(materia["programa_doc_id"])
            nombre_doc = doc_programa["titulo"] if doc_programa else "(documento eliminado)"
            self.programa_label.setText(f"Programa de {materia['nombre']}: {nombre_doc}")
            self.boton_analizar_programa.setEnabled(doc_programa is not None)

        self.programa_ejes.setPlainText(materia["ejes_tematicos"] or "(sin analizar todavia)")
        self.programa_perspectiva.setPlainText(materia["perspectiva"] or "(sin analizar todavia)")
        self.programa_obligatoria.setPlainText(materia["bibliografia_obligatoria"] or "(sin analizar todavia)")
        self.programa_opcional.setPlainText(materia["bibliografia_opcional"] or "(sin analizar todavia)")

    def _analizar_programa(self):
        materia = db.obtener_materia(self.materia_actual_id)
        if not materia or not materia["programa_doc_id"]:
            return
        doc_programa = db.obtener_documento(materia["programa_doc_id"])
        texto = (doc_programa["texto"] or "") if doc_programa else ""
        if not texto.strip():
            QMessageBox.information(self, "Sin texto", "El documento marcado como programa no tiene texto extraido.")
            return

        modelo = self.modelo_combo.currentText() or ai.MODELO_DEFAULT
        self.boton_analizar_programa.setEnabled(False)
        self.programa_label.setText("Analizando el programa con Claude, espera unos segundos...")

        self.programa_worker = ProgramaWorker(texto, modelo)
        self.programa_worker.resultado.connect(self._programa_analizado)
        self.programa_worker.error.connect(self._programa_error)
        self.programa_worker.start()

    def _programa_analizado(self, datos):
        db.guardar_analisis_programa(
            self.materia_actual_id,
            datos["ejes_tematicos"],
            datos["perspectiva"],
            datos["bibliografia_obligatoria"],
            datos["bibliografia_opcional"],
        )
        self._cargar_programa()

    def _programa_error(self, mensaje):
        QMessageBox.warning(self, "Error al analizar el programa", mensaje)
        self._cargar_programa()

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

        materia = db.obtener_materia(self.doc_actual["materia_id"])
        contexto_catedra = materia["perspectiva"] if materia and materia["perspectiva"] else None

        for boton in self._botones_ia:
            boton.setEnabled(False)
        self.boton_exportar_md.setEnabled(False)
        self.ia_estado.setText(f"Consultando a Claude ({modelo})...")
        self.ia_resultado.clear()

        self.ia_accion_actual = accion
        self.ia_pregunta_actual = pregunta
        self.ia_modelo_actual = modelo

        self.ai_worker = AIWorker(accion, texto, modelo, pregunta, contexto_catedra=contexto_catedra)
        self.ai_worker.resultado.connect(self._ia_resultado_listo)
        self.ai_worker.error.connect(self._ia_error)
        self.ai_worker.start()

    def _ia_resultado_listo(self, resultado):
        self.ia_resultado.setPlainText(resultado)
        self.ia_estado.setText("Listo.")
        for boton in self._botones_ia:
            boton.setEnabled(True)
        self.boton_exportar_md.setEnabled(True)

    def _ia_error(self, mensaje):
        self.ia_estado.setText("Error al consultar a Claude.")
        QMessageBox.warning(self, "Error de IA", mensaje)
        for boton in self._botones_ia:
            boton.setEnabled(True)

    def _elegir_carpeta_exportacion(self):
        carpeta_actual = config.obtener_carpeta_exportacion() or ""
        carpeta = QFileDialog.getExistingDirectory(self, "Elegir carpeta de exportacion (vault de Obsidian)", carpeta_actual)
        if carpeta:
            config.guardar_carpeta_exportacion(carpeta)
            self.carpeta_exportacion_label.setText(self._texto_carpeta_exportacion())

    def _exportar_markdown(self):
        if self.doc_actual is None or not self.ia_resultado.toPlainText().strip():
            QMessageBox.information(self, "Nada para exportar", "Primero genera un analisis con la IA.")
            return

        carpeta = config.obtener_carpeta_exportacion()
        if not carpeta:
            self._elegir_carpeta_exportacion()
            carpeta = config.obtener_carpeta_exportacion()
            if not carpeta:
                return

        materia = db.obtener_materia(self.doc_actual["materia_id"])
        periodo = db.obtener_periodo(materia["periodo_id"])
        carrera = db.obtener_carrera(periodo["carrera_id"])

        try:
            ruta_final = exportador.exportar_markdown(
                carpeta,
                carrera,
                periodo,
                materia,
                self.doc_actual,
                self.ia_accion_actual,
                self.ia_resultado.toPlainText(),
                self.ia_modelo_actual,
                pregunta=self.ia_pregunta_actual,
            )
        except OSError as exc:
            QMessageBox.warning(self, "Error al exportar", str(exc))
            return

        QMessageBox.information(self, "Exportado", f"Nota guardada en:\n{ruta_final}")

    def _verificar_conexion_ia(self):
        self.ia_estado.setText("Verificando conexion con Claude Code...")
        self.conexion_worker = ConexionIAWorker()
        self.conexion_worker.resultado.connect(self._conexion_ia_resultado)
        self.conexion_worker.start()

    def _conexion_ia_resultado(self, ok, mensaje):
        self.ia_estado.setText("")
        if ok:
            QMessageBox.information(self, "Conexion OK", mensaje)
        else:
            QMessageBox.warning(self, "Conexion fallida", mensaje)
