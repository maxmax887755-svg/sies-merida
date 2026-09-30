"""Simulador de nodos sensores con valores base de la costa de Yucatan."""
import random
from datetime import datetime


class SensorNode:
    VARIABLES = ("turbidez", "salinidad", "oxigeno", "temperatura")
    BASE = {"turbidez": 6.5, "salinidad": 35.5, "oxigeno": 6.8, "temperatura": 28.5}
    RUIDO = {"turbidez": 0.4, "salinidad": 0.5, "oxigeno": 0.25, "temperatura": 0.3}

    def __init__(self, node_id, lat, lon, seed=None):
        self.node_id = node_id
        self.lat = lat
        self.lon = lon
        self._rng = random.Random(seed)

    def leer(self, inyectar_anomalia=False):
        """Una lectura. Con inyectar_anomalia=True simula un derrame."""
        valores = {v: self._rng.gauss(self.BASE[v], self.RUIDO[v]) for v in self.VARIABLES}
        if inyectar_anomalia:
            valores["turbidez"] *= self._rng.uniform(3.5, 5.0)
            valores["salinidad"] -= self._rng.uniform(5.0, 8.0)
            valores["oxigeno"] *= self._rng.uniform(0.3, 0.5)
            valores["temperatura"] += self._rng.uniform(1.5, 3.0)
        lectura = {
            "node_id": self.node_id,
            "lat": self.lat,
            "lon": self.lon,
            "timestamp": datetime.now().isoformat(timespec="seconds"),
        }
        for v in self.VARIABLES:
            lectura[v] = round(max(valores[v], 0.0), 3)
        lectura["anomalia_inyectada"] = bool(inyectar_anomalia)
        return lectura

    def ejecutar_ciclo(self, n_lecturas=5, inyectar_anomalia=False):
        """Retorna una lista de lecturas consecutivas del nodo."""
        return [self.leer(inyectar_anomalia) for _ in range(n_lecturas)]
