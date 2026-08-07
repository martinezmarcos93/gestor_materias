import shutil
import sqlite3
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "data" / "biblioteca.db"
ARCHIVOS_DIR = BASE_DIR / "data" / "documentos"

TIPOS_PERIODO = ["cuatrimestre", "trimestre", "semestre", "anual", "bimestre"]
TIPOS_DOCUMENTO = ["texto", "consigna", "parcial", "fuente primaria"]
TIPOS_EVENTO = ["parcial", "recuperatorio", "trabajo practico", "entrega", "clase", "otro"]

SCHEMA = """
CREATE TABLE IF NOT EXISTS carreras (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre TEXT NOT NULL UNIQUE,
    tipo_periodo TEXT NOT NULL DEFAULT 'cuatrimestre'
);

CREATE TABLE IF NOT EXISTS periodos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    carrera_id INTEGER NOT NULL REFERENCES carreras(id) ON DELETE CASCADE,
    nombre TEXT NOT NULL,
    anio INTEGER NOT NULL,
    orden INTEGER DEFAULT 0,
    UNIQUE(carrera_id, nombre, anio)
);

CREATE TABLE IF NOT EXISTS materias (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    periodo_id INTEGER NOT NULL REFERENCES periodos(id) ON DELETE CASCADE,
    nombre TEXT NOT NULL,
    UNIQUE(periodo_id, nombre)
);

CREATE TABLE IF NOT EXISTS documentos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    materia_id INTEGER NOT NULL REFERENCES materias(id) ON DELETE CASCADE,
    titulo TEXT NOT NULL,
    autor TEXT,
    tipo TEXT DEFAULT 'texto',
    ruta_archivo TEXT NOT NULL,
    texto TEXT,
    ocr_aplicado INTEGER DEFAULT 0,
    fecha_agregado TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS eventos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    materia_id INTEGER NOT NULL REFERENCES materias(id) ON DELETE CASCADE,
    titulo TEXT NOT NULL,
    fecha TEXT,
    tipo TEXT DEFAULT 'otro',
    descripcion TEXT
);

CREATE VIRTUAL TABLE IF NOT EXISTS documentos_fts USING fts5(
    titulo, texto, content='documentos', content_rowid='id'
);

CREATE TRIGGER IF NOT EXISTS documentos_ai AFTER INSERT ON documentos BEGIN
    INSERT INTO documentos_fts(rowid, titulo, texto) VALUES (new.id, new.titulo, new.texto);
END;

CREATE TRIGGER IF NOT EXISTS documentos_ad AFTER DELETE ON documentos BEGIN
    INSERT INTO documentos_fts(documentos_fts, rowid, titulo, texto) VALUES ('delete', old.id, old.titulo, old.texto);
END;

CREATE TRIGGER IF NOT EXISTS documentos_au AFTER UPDATE ON documentos BEGIN
    INSERT INTO documentos_fts(documentos_fts, rowid, titulo, texto) VALUES ('delete', old.id, old.titulo, old.texto);
    INSERT INTO documentos_fts(rowid, titulo, texto) VALUES (new.id, new.titulo, new.texto);
END;
"""


def get_conn():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    conn = get_conn()
    conn.executescript(SCHEMA)
    conn.commit()
    conn.close()


# ---------- carreras ----------

def crear_carrera(nombre, tipo_periodo):
    conn = get_conn()
    cur = conn.execute(
        "INSERT INTO carreras (nombre, tipo_periodo) VALUES (?, ?)", (nombre, tipo_periodo)
    )
    conn.commit()
    carrera_id = cur.lastrowid
    conn.close()
    return carrera_id


def listar_carreras():
    conn = get_conn()
    rows = conn.execute("SELECT * FROM carreras ORDER BY nombre").fetchall()
    conn.close()
    return rows


def obtener_carrera(carrera_id):
    conn = get_conn()
    row = conn.execute("SELECT * FROM carreras WHERE id=?", (carrera_id,)).fetchone()
    conn.close()
    return row


def actualizar_carrera(carrera_id, nombre, tipo_periodo):
    conn = get_conn()
    conn.execute(
        "UPDATE carreras SET nombre=?, tipo_periodo=? WHERE id=?",
        (nombre, tipo_periodo, carrera_id),
    )
    conn.commit()
    conn.close()


def eliminar_carrera(carrera_id):
    materia_ids = [
        m["id"]
        for periodo in listar_periodos(carrera_id)
        for m in listar_materias(periodo["id"])
    ]
    conn = get_conn()
    conn.execute("DELETE FROM carreras WHERE id=?", (carrera_id,))
    conn.commit()
    conn.close()
    for materia_id in materia_ids:
        shutil.rmtree(ARCHIVOS_DIR / str(materia_id), ignore_errors=True)


# ---------- periodos ----------

def crear_periodo(carrera_id, nombre, anio, orden=0):
    conn = get_conn()
    cur = conn.execute(
        "INSERT INTO periodos (carrera_id, nombre, anio, orden) VALUES (?, ?, ?, ?)",
        (carrera_id, nombre, anio, orden),
    )
    conn.commit()
    periodo_id = cur.lastrowid
    conn.close()
    return periodo_id


def listar_periodos(carrera_id):
    conn = get_conn()
    rows = conn.execute(
        "SELECT * FROM periodos WHERE carrera_id=? ORDER BY anio DESC, orden DESC, nombre",
        (carrera_id,),
    ).fetchall()
    conn.close()
    return rows


def obtener_periodo(periodo_id):
    conn = get_conn()
    row = conn.execute("SELECT * FROM periodos WHERE id=?", (periodo_id,)).fetchone()
    conn.close()
    return row


def actualizar_periodo(periodo_id, nombre, anio, orden=0):
    conn = get_conn()
    conn.execute(
        "UPDATE periodos SET nombre=?, anio=?, orden=? WHERE id=?",
        (nombre, anio, orden, periodo_id),
    )
    conn.commit()
    conn.close()


def eliminar_periodo(periodo_id):
    materia_ids = [m["id"] for m in listar_materias(periodo_id)]
    conn = get_conn()
    conn.execute("DELETE FROM periodos WHERE id=?", (periodo_id,))
    conn.commit()
    conn.close()
    for materia_id in materia_ids:
        shutil.rmtree(ARCHIVOS_DIR / str(materia_id), ignore_errors=True)


# ---------- materias ----------

def crear_materia(periodo_id, nombre):
    conn = get_conn()
    cur = conn.execute(
        "INSERT INTO materias (periodo_id, nombre) VALUES (?, ?)", (periodo_id, nombre)
    )
    conn.commit()
    materia_id = cur.lastrowid
    conn.close()
    return materia_id


def listar_materias(periodo_id):
    conn = get_conn()
    rows = conn.execute(
        "SELECT * FROM materias WHERE periodo_id=? ORDER BY nombre", (periodo_id,)
    ).fetchall()
    conn.close()
    return rows


def obtener_materia(materia_id):
    conn = get_conn()
    row = conn.execute("SELECT * FROM materias WHERE id=?", (materia_id,)).fetchone()
    conn.close()
    return row


def actualizar_materia(materia_id, nombre):
    conn = get_conn()
    conn.execute("UPDATE materias SET nombre=? WHERE id=?", (nombre, materia_id))
    conn.commit()
    conn.close()


def eliminar_materia(materia_id):
    conn = get_conn()
    conn.execute("DELETE FROM materias WHERE id=?", (materia_id,))
    conn.commit()
    conn.close()
    shutil.rmtree(ARCHIVOS_DIR / str(materia_id), ignore_errors=True)


def ruta_materia(materia_id):
    """Ruta donde se guardan los PDFs de una materia, por id (agnostico al nombre)."""
    ruta = ARCHIVOS_DIR / str(materia_id)
    ruta.mkdir(parents=True, exist_ok=True)
    return ruta


# ---------- documentos ----------

def agregar_documento(materia_id, titulo, tipo, ruta_archivo, texto, ocr_aplicado, autor=None):
    conn = get_conn()
    cur = conn.execute(
        """INSERT INTO documentos (materia_id, titulo, autor, tipo, ruta_archivo, texto, ocr_aplicado)
           VALUES (?, ?, ?, ?, ?, ?, ?)""",
        (materia_id, titulo, autor, tipo, str(ruta_archivo), texto, int(ocr_aplicado)),
    )
    conn.commit()
    doc_id = cur.lastrowid
    conn.close()
    return doc_id


def listar_documentos(materia_id):
    conn = get_conn()
    rows = conn.execute(
        "SELECT * FROM documentos WHERE materia_id=? ORDER BY tipo, titulo", (materia_id,)
    ).fetchall()
    conn.close()
    return rows


def obtener_documento(doc_id):
    conn = get_conn()
    row = conn.execute("SELECT * FROM documentos WHERE id=?", (doc_id,)).fetchone()
    conn.close()
    return row


def actualizar_documento(doc_id, titulo, tipo, autor=None):
    conn = get_conn()
    conn.execute(
        "UPDATE documentos SET titulo=?, tipo=?, autor=? WHERE id=?",
        (titulo, tipo, autor, doc_id),
    )
    conn.commit()
    conn.close()


def eliminar_documento(doc_id):
    doc = obtener_documento(doc_id)
    conn = get_conn()
    conn.execute("DELETE FROM documentos WHERE id=?", (doc_id,))
    conn.commit()
    conn.close()
    if doc:
        Path(doc["ruta_archivo"]).unlink(missing_ok=True)


# ---------- eventos (cronograma) ----------

def crear_evento(materia_id, titulo, fecha, tipo, descripcion=None):
    conn = get_conn()
    cur = conn.execute(
        "INSERT INTO eventos (materia_id, titulo, fecha, tipo, descripcion) VALUES (?, ?, ?, ?, ?)",
        (materia_id, titulo, fecha, tipo, descripcion),
    )
    conn.commit()
    evento_id = cur.lastrowid
    conn.close()
    return evento_id


def listar_eventos(materia_id):
    conn = get_conn()
    rows = conn.execute(
        "SELECT * FROM eventos WHERE materia_id=? ORDER BY fecha", (materia_id,)
    ).fetchall()
    conn.close()
    return rows


def listar_eventos_proximos(limite=20):
    """Cronograma global: proximos eventos de todas las materias, con contexto."""
    conn = get_conn()
    rows = conn.execute(
        """SELECT e.*, m.nombre AS materia, m.id AS materia_id
           FROM eventos e
           JOIN materias m ON m.id = e.materia_id
           WHERE date(e.fecha) >= date('now')
           ORDER BY e.fecha
           LIMIT ?""",
        (limite,),
    ).fetchall()
    conn.close()
    return rows


def obtener_evento(evento_id):
    conn = get_conn()
    row = conn.execute("SELECT * FROM eventos WHERE id=?", (evento_id,)).fetchone()
    conn.close()
    return row


def actualizar_evento(evento_id, titulo, fecha, tipo, descripcion=None):
    conn = get_conn()
    conn.execute(
        "UPDATE eventos SET titulo=?, fecha=?, tipo=?, descripcion=? WHERE id=?",
        (titulo, fecha, tipo, descripcion, evento_id),
    )
    conn.commit()
    conn.close()


def eliminar_evento(evento_id):
    conn = get_conn()
    conn.execute("DELETE FROM eventos WHERE id=?", (evento_id,))
    conn.commit()
    conn.close()


# ---------- busqueda ----------

def buscar(consulta):
    conn = get_conn()
    rows = conn.execute(
        """SELECT d.id, d.titulo, d.tipo, m.nombre AS materia, m.id AS materia_id,
                  snippet(documentos_fts, 1, '[', ']', '...', 10) AS extracto
           FROM documentos_fts
           JOIN documentos d ON d.id = documentos_fts.rowid
           JOIN materias m ON m.id = d.materia_id
           WHERE documentos_fts MATCH ?
           ORDER BY rank
           LIMIT 50""",
        (consulta,),
    ).fetchall()
    conn.close()
    return rows
