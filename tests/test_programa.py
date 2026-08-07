"""Prueba manual del flujo de Programa: extraccion con IA a partir de un
programa simulado, guardado en la materia, y uso como contexto de catedra
en un analisis posterior. No se ejecuta en CI automatico: requiere Claude
Code instalado y logueado."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from src import ai, db

PROGRAMA_SIMULADO = """
Programa de Historia Social Latinoamericana - Catedra: Dra. Fernandez

Fundamentacion: la materia adopta una perspectiva critica y decolonial,
cuestionando la historiografia eurocentrica tradicional y poniendo enfasis
en autores criticos de Occidente y en las voces subalternas de America
Latina.

Ejes tematicos:
Unidad 1: La conquista y sus relatos oficiales vs. las voces subalternas.
Unidad 2: Independencias latinoamericanas desde una mirada descolonial.
Unidad 3: Neocolonialismo economico en el siglo XX.

Bibliografia obligatoria:
- Quijano, Anibal: "Colonialidad del poder, eurocentrismo y America Latina"
- Dussel, Enrique: "1492: el encubrimiento del Otro"

Bibliografia optativa:
- Said, Edward: "Orientalismo" (capitulos seleccionados)
"""

TEXTO_A_ANALIZAR = (
    "La llegada de Colon a America fue presentada tradicionalmente como un "
    "'descubrimiento' civilizatorio que trajo progreso a tierras vacias de "
    "historia."
)


def main():
    if not ai.esta_instalado():
        print("Claude Code no esta instalado en esta maquina: no se puede correr esta prueba.")
        return

    db.init_db()
    print("1) Creando carrera/periodo/materia/documento 'programa' de prueba...")
    carrera_id = db.crear_carrera("Carrera Programa Test", "cuatrimestre")
    periodo_id = db.crear_periodo(carrera_id, "1er Cuatrimestre", 2026, 0)
    materia_id = db.crear_materia(periodo_id, "Historia Social Latinoamericana")
    doc_programa_id = db.agregar_documento(
        materia_id, "Programa de la materia", "programa", "programa.pdf", PROGRAMA_SIMULADO, False
    )
    db.marcar_como_programa(materia_id, doc_programa_id)

    print("2) Extrayendo ejes/perspectiva/bibliografia del programa con Claude...")
    datos = ai.analizar_programa(PROGRAMA_SIMULADO, modelo="sonnet")
    print(f"   Ejes tematicos:\n   {datos['ejes_tematicos']}\n")
    print(f"   Perspectiva:\n   {datos['perspectiva']}\n")
    print(f"   Bibliografia obligatoria:\n   {datos['bibliografia_obligatoria']}\n")
    print(f"   Bibliografia opcional:\n   {datos['bibliografia_opcional']}\n")

    assert datos["perspectiva"].strip(), "Deberia haber extraido una perspectiva"
    assert "quijano" in datos["bibliografia_obligatoria"].lower() or "dussel" in datos["bibliografia_obligatoria"].lower()

    db.guardar_analisis_programa(
        materia_id, datos["ejes_tematicos"], datos["perspectiva"],
        datos["bibliografia_obligatoria"], datos["bibliografia_opcional"],
    )
    materia_guardada = db.obtener_materia(materia_id)
    assert materia_guardada["perspectiva"] == datos["perspectiva"]

    print("3) Analizando un texto de la materia CON el contexto de catedra...")
    doc_texto_id = db.agregar_documento(
        materia_id, "Fragmento sobre la conquista", "texto", "fragmento.pdf", TEXTO_A_ANALIZAR, False
    )
    resumen_con_contexto = ai.resumir(
        TEXTO_A_ANALIZAR, modelo="sonnet", contexto_catedra=materia_guardada["perspectiva"]
    )
    print(f"   Resumen (con contexto de catedra):\n   {resumen_con_contexto}\n")

    print("4) Limpiando datos de prueba...")
    db.eliminar_carrera(carrera_id)

    print("\nTODO OK: extraccion de programa + contexto de catedra funcionan de punta a punta.")


if __name__ == "__main__":
    main()
