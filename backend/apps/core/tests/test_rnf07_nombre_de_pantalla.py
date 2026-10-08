from apps.core.domain.pantallas import nombre_de_pantalla


def test_rnf07_la_ruta_tecnica_se_muestra_como_el_nombre_de_la_pantalla():
    assert nombre_de_pantalla("/api/v1/grades/?page_size=200") == "Notas"
    assert nombre_de_pantalla("/api/v1/calendar/weekly/") == "Calendario de la semana"
    assert nombre_de_pantalla("/api/v1/auth/me/") == "Inicio de sesión"


def test_rnf07_una_ruta_desconocida_se_devuelve_tal_cual():
    assert nombre_de_pantalla("/api/v1/algo-nuevo/") == "/api/v1/algo-nuevo/"
