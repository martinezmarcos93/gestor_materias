"""Prueba end-to-end del pipeline sin depender de la interfaz grafica.
Genera un PDF escaneado simulado (imagen sin capa de texto), lo procesa con
OCR, lo guarda en la base y consulta al modelo local de IA."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import shutil

from PIL import Image, ImageDraw, ImageFont

from src import ai, db, exportador, ocr

TEXTO_PRUEBA = (
    "La Revolucion de Mayo de 1810 marco el inicio del proceso independentista "
    "en el Rio de la Plata. Segun Tulio Halperin Donghi, este proceso no puede "
    "entenderse sin considerar la crisis del orden colonial espanol."
)


def generar_pdf_escaneado(ruta_pdf):
    img = Image.new("RGB", (1600, 900), color="white")
    dibujo = ImageDraw.Draw(img)
    try:
        fuente = ImageFont.truetype("arial.ttf", 28)
    except Exception:
        fuente = ImageFont.load_default()

    lineas = []
    palabras = TEXTO_PRUEBA.split()
    linea_actual = ""
    for palabra in palabras:
        if len(linea_actual) + len(palabra) < 55:
            linea_actual += palabra + " "
        else:
            lineas.append(linea_actual)
            linea_actual = palabra + " "
    lineas.append(linea_actual)

    y = 60
    for linea in lineas:
        dibujo.text((60, y), linea, fill="black", font=fuente)
        y += 45

    img.save(ruta_pdf, "PDF")


def main():
    ruta_pdf = Path(__file__).resolve().parent / "test_scan.pdf"
    print("1) Generando PDF escaneado simulado (sin capa de texto)...")
    generar_pdf_escaneado(ruta_pdf)

    print("2) Corriendo pipeline de OCR...")
    texto, ocr_aplicado = ocr.extraer_texto_pdf(ruta_pdf)
    print(f"   OCR aplicado: {ocr_aplicado}")
    print(f"   Texto extraido:\n   {texto!r}\n")
    assert ocr_aplicado, "Deberia haber usado OCR (la imagen no tiene capa de texto)"
    assert "Revolucion" in texto or "Revoluci" in texto, "El OCR no reconocio el texto esperado"

    print("3) Probando base de datos (carrera > periodo > materia > documento + busqueda FTS)...")
    db.init_db()
    carrera_id = db.crear_carrera("Carrera de prueba", "cuatrimestre")
    periodo_id = db.crear_periodo(carrera_id, "1er Cuatrimestre", 2026, 0)
    materia_id = db.crear_materia(periodo_id, "Historia Argentina I - TEST")
    doc_id = db.agregar_documento(
        materia_id, "Apunte de prueba", "texto", ruta_pdf, texto, ocr_aplicado
    )
    db.crear_evento(materia_id, "Parcial de prueba", "2026-09-01", "parcial", "Unidades 1 y 2")
    resultados = db.buscar("Revolucion OR Revoluci*")
    print(f"   Resultados de busqueda: {len(resultados)}")
    assert any(r["id"] == doc_id for r in resultados), "El documento deberia aparecer en la busqueda"
    eventos = db.listar_eventos(materia_id)
    assert len(eventos) == 1, "El evento del cronograma deberia haberse guardado"

    print("4) Probando IA (Claude Code, cuenta Pro)...")
    resumen = None
    if not ai.esta_instalado():
        print("   Claude Code no esta instalado en esta maquina: se omite el paso de IA.")
    else:
        resumen = ai.resumir(texto, modelo="haiku")
        print(f"   Resumen generado:\n   {resumen}\n")

    print("5) Probando exportacion a Markdown (Obsidian)...")
    carpeta_vault = Path(__file__).resolve().parent / "vault_test"
    doc = db.obtener_documento(doc_id)
    periodo = db.obtener_periodo(periodo_id)
    carrera = db.obtener_carrera(carrera_id)
    ruta_md = exportador.exportar_markdown(
        carpeta_vault, carrera, periodo, db.obtener_materia(materia_id), doc,
        "resumir", resumen or texto, "haiku",
    )
    assert ruta_md.exists(), "La nota exportada deberia existir en disco"
    contenido_md = ruta_md.read_text(encoding="utf-8")
    assert "materia:" in contenido_md and "[[Historia Argentina I - TEST]]" in contenido_md
    print(f"   Nota exportada en: {ruta_md}")

    print("6) Limpiando datos de prueba...")
    db.eliminar_carrera(carrera_id)
    ruta_pdf.unlink(missing_ok=True)
    shutil.rmtree(carpeta_vault, ignore_errors=True)

    print("\nTODO OK: el pipeline de OCR + DB + cronograma + IA + exportacion funciona de punta a punta.")


if __name__ == "__main__":
    main()
