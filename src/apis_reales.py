"""Clima real (Open-Meteo) para alimentar el gemelo digital."""
import math
from datetime import datetime

from src.logger_config import configurar_logger

logger = configurar_logger("SIES.apis_reales")


class APIsReales:
    # El gemelo trabaja en km/h y modela la deriva de la mancha, no el viento en si:
    # se usa ~3% de la velocidad del viento, limitada para que la mancha permanezca
    # dentro del dominio de 5 x 3 km durante la simulacion.
    FACTOR_DERIVA = 0.03
    DERIVA_MAX_KMH = 0.2

    def __init__(self, lat=21.2833, lon=-89.6667):
        self.lat = lat
        self.lon = lon

    def clima_actual(self):
        try:
            import httpx
            url = (
                f"https://api.open-meteo.com/v1/forecast?"
                f"latitude={self.lat}&longitude={self.lon}"
                f"&current=temperature_2m,wind_speed_10m,wind_direction_10m,"
                f"precipitation,relative_humidity_2m"
            )
            r = httpx.get(url, timeout=10)
            r.raise_for_status()
            data = r.json()["current"]
            return {
                "temperatura_c": data["temperature_2m"],
                "viento_kmh": data["wind_speed_10m"],
                "viento_direccion": data["wind_direction_10m"],
                "precipitacion_mm": data["precipitation"],
                "humedad_pct": data["relative_humidity_2m"],
                "fuente": "Open-Meteo (real)",
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Error clima: {e}")
            return {"error": str(e)}

    def viento_para_gemelo(self, clima=None):
        """Velocidad de deriva (km/h) para el gemelo: x = este, y = norte."""
        clima = clima or self.clima_actual()
        if "error" in clima:
            return {"vx": 0.15, "vy": 0.05, "fuente": "valores por defecto (sin clima real)"}
        deriva = min(clima["viento_kmh"] * self.FACTOR_DERIVA, self.DERIVA_MAX_KMH)
        # La direccion meteorologica indica de DONDE sopla; la mancha va hacia el lado opuesto.
        hacia = math.radians((clima["viento_direccion"] + 180.0) % 360.0)
        return {
            "vx": round(deriva * math.sin(hacia), 4),
            "vy": round(deriva * math.cos(hacia), 4),
            "deriva_kmh": round(deriva, 4),
            "fuente": "Open-Meteo real"
        }
