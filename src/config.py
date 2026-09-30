"""Configuracion global: variables de entorno y rutas absolutas."""
import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

APP_ENV = os.getenv("APP_ENV", "development")
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

_modelo = os.getenv("MODEL_PATH", "models/edge_model.pth")
MODEL_PATH = _modelo if os.path.isabs(_modelo) else str(BASE_DIR / _modelo)
SCALER_PATH = os.path.splitext(MODEL_PATH)[0] + "_scaler.pkl"

MODELS_DIR = BASE_DIR / "models"
EVIDENCIA_DIR = BASE_DIR / "evidencia"

MODELS_DIR.mkdir(parents=True, exist_ok=True)
EVIDENCIA_DIR.mkdir(parents=True, exist_ok=True)
