"""RF-19/RF-20: generar y cargar la plantilla de calificaciones. Cada
celda ya calificada (RN-05/RN-07: el punteo real nunca se sobreescribe,
y una plantilla recargada se trata como solicitud de modificación) se
clasifica como "crear" o "modificacion" antes de guardar nada."""

import io

from openpyxl import Workbook, load_workbook
from openpyxl.utils import get_column_letter

from apps.students.models import Enrollment

from ..domain.template import CeldaPlantillaInvalida, validar_codigo, validar_punteo
from ..models import Activity, Grade
from .grade import registrar_punteo
from .grade_change_request import solicitar_modificacion

ACCION_CREAR = "crear"
ACCION_MODIFICACION = "modificacion"
ACCION_SIN_CAMBIO = "sin_cambio"


class UnidadSinActividades(Exception):
    pass


def _actividades_de(assignment, unit) -> list[Activity]:
    actividades = list(
        Activity.objects.filter(assignment=assignment, unit=unit, is_active=True).order_by(
            "due_date", "id"
        )
    )
    if not actividades:
        raise UnidadSinActividades(
            "Esta unidad todavía no tiene actividades definidas para esta asignación."
        )
    return actividades


def generar_plantilla(*, assignment, unit) -> bytes:
    actividades = _actividades_de(assignment, unit)

    libro = Workbook()
    hoja = libro.active
    hoja.title = "Calificaciones"
    encabezados = ["Código", "Nombre"] + [f"{a.name} (máx {a.max_score})" for a in actividades]
    hoja.append(encabezados)

    inscripciones = (
        Enrollment.objects.filter(
            section=assignment.section, cycle=assignment.cycle, is_active=True
        )
        .select_related("student")
        .order_by("student__internal_code")
    )
    for inscripcion in inscripciones:
        fila = [inscripcion.student.internal_code, inscripcion.student.nombre_completo()]
        fila += ["" for _ in actividades]
        hoja.append(fila)

    for columna in range(1, len(encabezados) + 1):
        hoja.column_dimensions[get_column_letter(columna)].width = 24

    buffer = io.BytesIO()
    libro.save(buffer)
    return buffer.getvalue()


def validar_y_clasificar_plantilla(*, assignment, unit, archivo):
    """Devuelve `(filas_validas, errores)`. `filas_validas` es una lista
    de `(enrollment, [{"activity", "punteo", "accion"}, ...])`. Nunca
    guarda nada — sirve tanto para la vista previa como para la carga."""
    actividades = _actividades_de(assignment, unit)

    inscripciones = {
        inscripcion.student.internal_code: inscripcion
        for inscripcion in Enrollment.objects.filter(
            section=assignment.section, cycle=assignment.cycle, is_active=True
        ).select_related("student")
    }

    libro = load_workbook(archivo, data_only=True, read_only=True)
    hoja = libro.active

    errores = []
    filas_validas = []

    for numero, fila in enumerate(hoja.iter_rows(min_row=2, values_only=True), start=2):
        if not fila or fila[0] in (None, ""):
            continue
        codigo = str(fila[0]).strip()

        try:
            validar_codigo(
                numero_fila=numero, internal_code=codigo, codigos_esperados=set(inscripciones)
            )
        except CeldaPlantillaInvalida as exc:
            errores.append(str(exc))
            continue

        inscripcion = inscripciones[codigo]
        celdas = []
        fila_tiene_error = False

        for indice, actividad in enumerate(actividades):
            columna = 2 + indice
            valor = fila[columna] if len(fila) > columna else None
            if valor in (None, ""):
                continue

            try:
                punteo = validar_punteo(
                    numero_fila=numero,
                    nombre_actividad=actividad.name,
                    valor=valor,
                    max_score=actividad.max_score,
                )
            except CeldaPlantillaInvalida as exc:
                errores.append(str(exc))
                fila_tiene_error = True
                continue

            grade_existente = Grade.objects.filter(
                enrollment=inscripcion, activity=actividad, is_active=True
            ).first()
            if grade_existente is None:
                accion = ACCION_CREAR
            elif grade_existente.current_score == punteo:
                accion = ACCION_SIN_CAMBIO
            else:
                accion = ACCION_MODIFICACION

            celdas.append({"activity": actividad, "punteo": punteo, "accion": accion})

        if not fila_tiene_error:
            filas_validas.append((inscripcion, celdas))

    if errores:
        return [], errores
    return filas_validas, []


def aplicar_plantilla(*, filas_validas, recorded_by) -> dict:
    """Solo se llama después de que `validar_y_clasificar_plantilla` no
    encontró errores."""
    creados = 0
    solicitudes = 0
    for inscripcion, celdas in filas_validas:
        for celda in celdas:
            if celda["accion"] == ACCION_CREAR:
                registrar_punteo(
                    enrollment=inscripcion,
                    activity=celda["activity"],
                    raw_score=celda["punteo"],
                    recorded_by=recorded_by,
                    source=Grade.ORIGEN_PLANTILLA,
                )
                creados += 1
            elif celda["accion"] == ACCION_MODIFICACION:
                grade = Grade.objects.get(
                    enrollment=inscripcion, activity=celda["activity"], is_active=True
                )
                solicitar_modificacion(
                    grade=grade,
                    requested_score=celda["punteo"],
                    reason="Cargado de nuevo por plantilla (RN-07).",
                    requested_by=recorded_by,
                )
                solicitudes += 1
    return {"creados": creados, "solicitudes_de_modificacion": solicitudes}
