import pytest

from apps.scheduling.domain.teacher_assignment import AsignacionInvalida, validar_asignacion


def test_curso_academico_en_seccion_academica_es_valido():
    validar_asignacion(
        course_type="academico", section_type="academica", teacher_role_name="Docente"
    )


def test_curso_taller_en_seccion_taller_es_valido():
    validar_asignacion(course_type="taller", section_type="taller", teacher_role_name="Tallerista")


def test_curso_academico_en_seccion_taller_es_invalido():
    with pytest.raises(AsignacionInvalida):
        validar_asignacion(
            course_type="academico", section_type="taller", teacher_role_name="Docente"
        )


def test_curso_taller_en_seccion_academica_es_invalido():
    with pytest.raises(AsignacionInvalida):
        validar_asignacion(
            course_type="taller", section_type="academica", teacher_role_name="Tallerista"
        )


def test_tallerista_no_puede_dar_un_curso_academico():
    with pytest.raises(AsignacionInvalida):
        validar_asignacion(
            course_type="academico", section_type="academica", teacher_role_name="Tallerista"
        )


def test_docente_no_puede_dar_un_taller():
    with pytest.raises(AsignacionInvalida):
        validar_asignacion(course_type="taller", section_type="taller", teacher_role_name="Docente")


def test_docente_con_seccion_a_cargo_puede_dar_un_curso_academico():
    validar_asignacion(
        course_type="academico",
        section_type="academica",
        teacher_role_name="Docente con sección a cargo",
    )
