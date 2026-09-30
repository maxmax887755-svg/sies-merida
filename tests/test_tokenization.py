import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest

from src.tokenization import TokenizadorEcosistemico


def test_creditos():
    c = TokenizadorEcosistemico().calcular_creditos(10)
    assert c["toneladas_co2"] == pytest.approx(50)
    assert c["valor_usd"] == pytest.approx(1000)


def test_emision():
    token = TokenizadorEcosistemico().emitir_token(10)
    assert len(token["token_id"]) == 16
    int(token["token_id"], 16)  # debe ser hexadecimal
    assert token["valor_usd"] == pytest.approx(1000)


def test_distribucion_60_30_10():
    d = TokenizadorEcosistemico().distribuir(1000)
    assert d["comunidad"] == pytest.approx(600)
    assert d["infraestructura"] == pytest.approx(300)
    assert d["emergencia"] == pytest.approx(100)
    assert sum(d.values()) == pytest.approx(1000)
