import re
from datetime import datetime
from pathlib import Path

TITULOS_ACCION = {
    "resumir": "Resumen",
    "preguntas": "Preguntas de estudio",
    "fuente": "Analisis de fuente",
    "consulta": "Consulta",
}


def sanitizar_nombre_archivo(nombre):
    limpio = re.sub(r'[<>:"/\\|?*]', "_", nombre).strip()
    return limpio or "sin_nombre"


def exportar_markdown(carpeta_base, carrera, periodo, materia, documento, accion, contenido, modelo, pregunta=None):
    """Guarda un analisis de IA como nota .md con front-matter, lista para usar
    en una vault de Obsidian (o cualquier otra herramienta basada en Markdown)."""
    carpeta_destino = (
        Path(carpeta_base)
        / sanitizar_nombre_archivo(carrera["nombre"])
        / sanitizar_nombre_archivo(f"{periodo['nombre']} {periodo['anio']}")
        / sanitizar_nombre_archivo(materia["nombre"])
    )
    carpeta_destino.mkdir(parents=True, exist_ok=True)

    etiqueta_accion = TITULOS_ACCION.get(accion, accion)
    ahora = datetime.now()
    nombre_archivo = (
        sanitizar_nombre_archivo(f"{etiqueta_accion} - {documento['titulo']} - {ahora.strftime('%Y%m%d-%H%M%S')}")
        + ".md"
    )
    ruta_final = carpeta_destino / nombre_archivo

    tag_materia = sanitizar_nombre_archivo(materia["nombre"]).lower().replace(" ", "-")
    tags = ["gestor-materias", accion, tag_materia]

    frontmatter = (
        "---\n"
        f'titulo: "{etiqueta_accion} - {documento["titulo"]}"\n'
        f'materia: "{materia["nombre"]}"\n'
        f'periodo: "{periodo["nombre"]} {periodo["anio"]}"\n'
        f'carrera: "{carrera["nombre"]}"\n'
        f"tipo_analisis: {accion}\n"
        f'documento_fuente: "{documento["titulo"]}"\n'
        f"modelo: {modelo}\n"
        f"fecha: {ahora.strftime('%Y-%m-%d')}\n"
        f"tags: [{', '.join(tags)}]\n"
        "---\n\n"
    )

    cuerpo = f"# {etiqueta_accion}: {documento['titulo']}\n\n"
    if pregunta:
        cuerpo += f"**Pregunta:** {pregunta}\n\n"
    cuerpo += contenido.strip() + "\n\n"
    cuerpo += (
        "---\n"
        f"Materia: [[{materia['nombre']}]]\n"
        f"Documento fuente: {documento['titulo']} ({documento['tipo']})\n"
    )

    ruta_final.write_text(frontmatter + cuerpo, encoding="utf-8")
    return ruta_final
