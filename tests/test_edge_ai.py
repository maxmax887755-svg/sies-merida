import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest

from src.edge_ai import EdgeAnomalyDetector
from src.sensor_simulator import SensorNode


@pytest.fixture(scope="module")
def detector():
    return EdgeAnomalyDetector()


def test_modelo_carga(detector):
    assert detector.modelo is not None
    assert detector.umbral > 0
    assert os.path.exists(detector.model_path)
    assert os.path.exists(detector.scaler_path)
    recargado = EdgeAnomalyDetector()
    assert recargado.umbral == pytest.approx(detector.umbral)


def test_lectura_normal_no_es_anomalia(detector):
    lectura = dict(SensorNode.BASE)
    lectura["node_id"] = "test"
    resultado = detector.predecir(lectura)
    assert resultado["es_anomalia"] is False
    assert resultado["error_reconstruccion"] < resultado["umbral"]


def test_derrame_es_anomalia(detector):
    nodo = SensorNode("test", 21.2833, -89.6667, seed=1)
    resultado = detector.predecir(nodo.leer(inyectar_anomalia=True))
    assert resultado["es_anomalia"] is True
    assert resultado["error_reconstruccion"] > resultado["umbral"]
    assert resultado["node_id"] == "test"
