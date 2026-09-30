import pytest

from apps.accounts.domain.gestion_usuarios import CambioNoPermitido, validar_cambio_propio


def test_rf01_no_se_puede_desactivar_la_propia_cuenta():
    with pytest.raises(CambioNoPermitido):
        validar_cambio_propio(es_la_misma_cuenta=True, desactiva=True, cambia_rol=False)


def test_rf01_no_se_puede_cambiar_el_propio_rol():
    with pytest.raises(CambioNoPermitido):
        validar_cambio_propio(es_la_misma_cuenta=True, desactiva=False, cambia_rol=True)


def test_rf01_la_propia_cuenta_puede_cambiar_nombre_y_correo():
    validar_cambio_propio(es_la_misma_cuenta=True, desactiva=False, cambia_rol=False)


def test_rf01_otra_cuenta_se_puede_desactivar_y_cambiar_de_rol():
    validar_cambio_propio(es_la_misma_cuenta=False, desactiva=True, cambia_rol=True)
