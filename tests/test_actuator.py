import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.actuator import ActuadorAutonomo


def test_sin_anomalia_no_actua():
    accion = ActuadorAutonomo().decidir({"es_anomalia": False}, 0.0)
    assert accion["accion"] == "ninguna"


def test_con_anomalia_barrera_o_bomba():
    actuador = ActuadorAutonomo()
    barrera = {"x_km": 2.0, "y_km": 1.6, "radio_km": 0.5}
    critica = actuador.decidir({"es_anomalia": True}, 200.0, barrera)
    assert critica["accion"] == "desplegar_barrera_absorbente"
    assert critica["parametros"]["x_km"] == 2.0
    moderada = actuador.decidir({"es_anomalia": True}, 10.0, barrera)
    assert moderada["accion"] == "activar_bomba_flushing"
    assert moderada["parametros"]["duracion_min"] == 15
    assert critica["accion"] in ("desplegar_barrera_absorbente", "activar_bomba_flushing")
