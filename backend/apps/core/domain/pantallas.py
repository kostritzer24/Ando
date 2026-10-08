"""RNF-07: el registro de accesos guarda la ruta técnica de cada petición
(`/api/v1/grades/...`). Dirección necesita leer qué pantalla consultó la
familia, así que la ruta se traduce a su nombre en el portal."""

# Se evalúa en orden: la primera coincidencia por prefijo gana.
_PANTALLAS = [
    ("/api/v1/auth/me", "Inicio de sesión"),
    ("/api/v1/calendar/weekly", "Calendario de la semana"),
    ("/api/v1/schedule", "Horario"),
    ("/api/v1/calendar-events", "Calendario"),
    ("/api/v1/grades", "Notas"),
    ("/api/v1/report-cards", "Boletines"),
    ("/api/v1/activities", "Notas"),
    ("/api/v1/attendance", "Asistencia"),
    ("/api/v1/justifications", "Justificaciones"),
    ("/api/v1/payments", "Pagos"),
    ("/api/v1/solvency", "Solvencia"),
    ("/api/v1/documents", "Documentos"),
    ("/api/v1/announcements", "Avisos"),
    ("/api/v1/messages", "Buzón"),
    ("/api/v1/conduct-reports", "Reportes de conducta"),
    ("/api/v1/conduct-rule-articles", "Código de convivencia"),
    ("/api/v1/students", "Estudiantes"),
    ("/api/v1/enrollments", "Estudiantes"),
    ("/api/v1/guardians", "Encargados"),
    ("/api/v1/reports", "Reportes"),
    ("/api/v1/audit-log", "Bitácora de cambios"),
    ("/api/v1/access-log", "Registro de accesos"),
    ("/api/v1/users", "Usuarios"),
    ("/api/v1/roles", "Usuarios"),
]


def nombre_de_pantalla(ruta: str) -> str:
    """`/api/v1/grades/?page_size=200` → `Notas`. Una ruta desconocida se
    devuelve tal cual: mejor mostrarla cruda que esconderla."""
    for prefijo, nombre in _PANTALLAS:
        if ruta.startswith(prefijo):
            return nombre
    return ruta
