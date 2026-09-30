"""Alertas SMS en modo demo (no se envia nada real)."""
from datetime import datetime

from src.logger_config import configurar_logger

logger = configurar_logger("SIES.alertas")


class SistemaAlertas:
    def __init__(self):
        self.alertas_enviadas = []
        logger.info("Sistema de alertas en MODO DEMO")

    def enviar_alerta(self, telefono, ubicacion, accion, masa_kg):
        mensaje = (
            f"SIES-Mérida ALERTA\n"
            f"Derrame detectado en {ubicacion}\n"
            f"Masa: {masa_kg} kg\n"
            f"Acción: {accion}\n"
            f"Hora: {datetime.now().strftime('%H:%M:%S')}"
        )
        alerta = {
            "telefono": telefono,
            "ubicacion": ubicacion,
            "accion": accion,
            "mensaje": mensaje,
            "timestamp": datetime.now().isoformat(),
            "estado": "simulado"
        }
        logger.warning(f"[DEMO SMS] {telefono}: {mensaje[:50].replace(chr(10), ' ')}...")
        self.alertas_enviadas.append(alerta)
        return alerta

    def alertar_autoridades(self, ubicacion, accion, masa_kg):
        destinatarios = [
            "+529991234567",
            "+529991234568",
            "+529991234569",
        ]
        for tel in destinatarios:
            self.enviar_alerta(tel, ubicacion, accion, masa_kg)
        return len(destinatarios)
