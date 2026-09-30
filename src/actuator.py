"""Actuador autonomo: decide la respuesta ante una anomalia."""
from datetime import datetime

from src.logger_config import configurar_logger

log = configurar_logger("SIES.actuator")


class ActuadorAutonomo:
    UMBRAL_CONCENTRACION_KG = 50.0
    DURACION_FLUSHING_MIN = 15

    def decidir(self, deteccion, concentracion_maxima, barrera=None):
        if not deteccion.get("es_anomalia", False):
            accion = {
                "accion": "ninguna",
                "descripcion": "Sin anomalia: monitoreo continuo.",
                "parametros": {},
            }
        elif concentracion_maxima > self.UMBRAL_CONCENTRACION_KG:
            parametros = dict(barrera) if barrera else {}
            accion = {
                "accion": "desplegar_barrera_absorbente",
                "descripcion": "Concentracion critica: se despliega barrera absorbente.",
                "parametros": parametros,
            }
        else:
            accion = {
                "accion": "activar_bomba_flushing",
                "descripcion": "Concentracion moderada: flushing de %d min." % self.DURACION_FLUSHING_MIN,
                "parametros": {"duracion_min": self.DURACION_FLUSHING_MIN},
            }
        accion["concentracion_maxima"] = float(concentracion_maxima)
        accion["timestamp"] = datetime.now().isoformat(timespec="seconds")
        log.info("Accion: %s (conc. max %.1f kg)", accion["accion"], concentracion_maxima)
        return accion
