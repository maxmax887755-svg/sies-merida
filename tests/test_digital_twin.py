import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest

from src.digital_twin import DigitalTwinManglar


def test_inyeccion():
    twin = DigitalTwinManglar()
    twin.inyectar_derrame(1.0, 1.5, 500)
    assert twin.concentracion.sum() == pytest.approx(500)
    assert twin.concentracion.max() == pytest.approx(500)
    assert twin.foco == (1.0, 1.5)


def test_simulacion():
    twin = DigitalTwinManglar()
    twin.inyectar_derrame(1.0, 1.5, 500)
    impacto = twin.predecir_impacto(pasos=10)
    assert impacto["concentracion_maxima"] == pytest.approx(500)
    assert impacto["concentracion_maxima_final"] < 500
    assert 400 < impacto["masa_final_kg"] <= 500 + 1e-6
    assert impacto["centroide_x_km"] > 1.05  # la mancha avanza con la corriente


def test_recomendacion():
    twin = DigitalTwinManglar()
    twin.inyectar_derrame(1.0, 1.5, 500)
    barrera = twin.recomendar_barrera()
    assert barrera is not None
    assert 0 <= barrera["x_km"] <= DigitalTwinManglar.ANCHO_KM
    assert 0 <= barrera["y_km"] <= DigitalTwinManglar.ALTO_KM
    assert barrera["radio_km"] > 0
