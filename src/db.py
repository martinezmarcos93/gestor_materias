import sqlite3
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "data" / "biblioteca.db"
ARCHIVOS_DIR = BASE_DIR / "data" / "materias"

SCHEMA = """
CREATE TABLE IF NOT EXISTS materias (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre TEXT NOT NULL,
    anio INTEGER,
    cuatrimestre INTEGER,
    UNIQUE(nombre, anio, cuatrimestre)
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


def crear_materia(nombre, anio, cuatrimestre):
    conn = get_conn()
    cur = conn.execute(
        "INSERT OR IGNORE INTO materias (nombre, anio, cuatrimestre) VALUES (?, ?, ?)",
        (nombre, anio, cuatrimestre),
    )
    conn.commit()
    if cur.lastrowid:
        materia_id = cur.lastrowid
    else:
        row = conn.execute(
            "SELECT id FROM materias WHERE nombre=? AND anio=? AND cuatrimestre=?",
            (nombre, anio, cuatrimestre),
        ).fetchone()
        materia_id = row["id"]
    conn.close()
    return materia_id


def listar_materias():
    conn = get_conn()
    rows = conn.execute(
        "SELECT * FROM materias ORDER BY anio DESC, cuatrimestre DESC, nombre ASC"
    ).fetchall()
    conn.close()
    return rows


def eliminar_materia(materia_id):
    conn = get_conn()
    conn.execute("DELETE FROM materias WHERE id=?", (materia_id,))
    conn.commit()
    conn.close()


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


def renombrar_documento(doc_id, nuevo_titulo):
    conn = get_conn()
    conn.execute("UPDATE documentos SET titulo=? WHERE id=?", (nuevo_titulo, doc_id))
    conn.commit()
    conn.close()


def eliminar_documento(doc_id):
    conn = get_conn()
    conn.execute("DELETE FROM documentos WHERE id=?", (doc_id,))
    conn.commit()
    conn.close()


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
