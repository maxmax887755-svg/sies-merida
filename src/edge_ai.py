"""IA en el borde: autoencoder para deteccion de anomalias."""
import os
import pickle

import numpy as np
import torch
from sklearn.preprocessing import StandardScaler
from torch import nn

from src.config import MODEL_PATH, SCALER_PATH
from src.logger_config import configurar_logger
from src.sensor_simulator import SensorNode

VARIABLES = SensorNode.VARIABLES
log = configurar_logger("SIES.edge_ai")


class Autoencoder(nn.Module):
    def __init__(self):
        super().__init__()
        self.encoder = nn.Sequential(nn.Linear(4, 8), nn.ReLU(), nn.Linear(8, 3), nn.ReLU())
        self.decoder = nn.Sequential(nn.Linear(3, 8), nn.ReLU(), nn.Linear(8, 4))

    def forward(self, x):
        return self.decoder(self.encoder(x))


class EdgeAnomalyDetector:
    def __init__(self, model_path=MODEL_PATH, scaler_path=SCALER_PATH, seed=42):
        self.model_path = str(model_path)
        self.scaler_path = str(scaler_path)
        self.seed = seed
        self.modelo = None
        self.scaler = None
        self.umbral = None
        if not self._cargar():
            self.entrenar()

    def _datos_sinteticos(self, n):
        rng = np.random.default_rng(self.seed)
        cols = [rng.normal(SensorNode.BASE[v], SensorNode.RUIDO[v], n) for v in VARIABLES]
        return np.column_stack(cols).astype(np.float32)

    def _errores(self, X):
        with torch.no_grad():
            t = torch.from_numpy(np.ascontiguousarray(X, dtype=np.float32))
            rec = self.modelo(t)
            return ((rec - t) ** 2).mean(dim=1).numpy()

    def entrenar(self, n_muestras=2000, epocas=300):
        log.info("Entrenando autoencoder con %d muestras sinteticas (seed %d)", n_muestras, self.seed)
        torch.manual_seed(self.seed)
        datos = self._datos_sinteticos(n_muestras)
        self.scaler = StandardScaler().fit(datos)
        X = self.scaler.transform(datos).astype(np.float32)
        tensor = torch.from_numpy(X)

        self.modelo = Autoencoder()
        opt = torch.optim.Adam(self.modelo.parameters(), lr=5e-3)
        perdida = nn.MSELoss()
        self.modelo.train()
        for _ in range(epocas):
            opt.zero_grad()
            loss = perdida(self.modelo(tensor), tensor)
            loss.backward()
            opt.step()
        self.modelo.eval()

        err = self._errores(X)
        self.umbral = float(err.mean() + 2 * err.std())
        self._guardar()
        log.info("Modelo entrenado. Umbral de anomalia = %.4f", self.umbral)

    def _guardar(self):
        os.makedirs(os.path.dirname(self.model_path), exist_ok=True)
        torch.save({"state_dict": self.modelo.state_dict(), "umbral": self.umbral}, self.model_path)
        with open(self.scaler_path, "wb") as f:
            pickle.dump(self.scaler, f)

    def _cargar(self):
        if not (os.path.exists(self.model_path) and os.path.exists(self.scaler_path)):
            return False
        try:
            ckpt = torch.load(self.model_path, map_location="cpu", weights_only=True)
            modelo = Autoencoder()
            modelo.load_state_dict(ckpt["state_dict"])
            modelo.eval()
            with open(self.scaler_path, "rb") as f:
                scaler = pickle.load(f)
            self.modelo, self.scaler, self.umbral = modelo, scaler, float(ckpt["umbral"])
            log.info("Modelo cargado desde %s", self.model_path)
            return True
        except Exception as exc:
            log.warning("No se pudo cargar el modelo (%s). Se reentrenara.", exc)
            return False

    def predecir(self, lectura):
        x = np.array([[lectura[v] for v in VARIABLES]], dtype=np.float32)
        xs = self.scaler.transform(x).astype(np.float32)
        error = float(self._errores(xs)[0])
        return {
            "es_anomalia": bool(error > self.umbral),
            "error_reconstruccion": error,
            "umbral": float(self.umbral),
            "node_id": lectura.get("node_id"),
        }
