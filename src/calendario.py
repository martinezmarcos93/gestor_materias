from datetime import datetime, timezone


def _escapar(texto):
    texto = texto or ""
    texto = texto.replace("\\", "\\\\").replace(";", "\\;").replace(",", "\\,")
    return texto.replace("\n", "\\n")


def generar_ics(eventos):
    """Genera el contenido de un archivo .ics (iCalendar) a partir de filas de
    eventos con materia, tipo, titulo, fecha (YYYY-MM-DD) y descripcion."""
    ahora = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    lineas = ["BEGIN:VCALENDAR", "VERSION:2.0", "PRODID:-//Gestor de Materias//ES", "CALSCALE:GREGORIAN"]

    for evento in eventos:
        fecha = (evento["fecha"] or "").replace("-", "")
        if not fecha:
            continue
        resumen = f"[{evento['materia']}] {evento['tipo']}: {evento['titulo']}"
        lineas.append("BEGIN:VEVENT")
        lineas.append(f"UID:evento-{evento['id']}@gestor-materias")
        lineas.append(f"DTSTAMP:{ahora}")
        lineas.append(f"DTSTART;VALUE=DATE:{fecha}")
        lineas.append(f"SUMMARY:{_escapar(resumen)}")
        if evento["descripcion"]:
            lineas.append(f"DESCRIPTION:{_escapar(evento['descripcion'])}")
        lineas.append(f"CATEGORIES:{_escapar(evento['tipo'])}")
        lineas.append("END:VEVENT")

    lineas.append("END:VCALENDAR")
    return "\r\n".join(lineas) + "\r\n"
