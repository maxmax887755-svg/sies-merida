"""Tokenizacion de creditos de carbono azul."""
import hashlib
from datetime import datetime


class TokenizadorEcosistemico:
    FACTOR_CAPTURA_TON_HA = 5.0
    PRECIO_USD_TON = 20.0
    DISTRIBUCION = {"comunidad": 0.60, "infraestructura": 0.30, "emergencia": 0.10}

    def calcular_creditos(self, hectareas):
        if hectareas < 0:
            raise ValueError("hectareas debe ser >= 0")
        toneladas = hectareas * self.FACTOR_CAPTURA_TON_HA
        return {
            "hectareas": float(hectareas),
            "toneladas_co2": float(toneladas),
            "valor_usd": float(toneladas * self.PRECIO_USD_TON),
        }

    def distribuir(self, valor_usd):
        return {k: round(valor_usd * p, 2) for k, p in self.DISTRIBUCION.items()}

    def emitir_token(self, hectareas, ecosistema="Manglar de Progreso", evento="proteccion"):
        creditos = self.calcular_creditos(hectareas)
        ts = datetime.now().isoformat()
        carga = "%s|%s|%s|%s|%s" % (ecosistema, evento, creditos["hectareas"],
                                    creditos["toneladas_co2"], ts)
        token_id = hashlib.sha256(carga.encode("utf-8")).hexdigest()[:16]
        token = {"token_id": token_id, "ecosistema": ecosistema, "evento": evento, "timestamp": ts}
        token.update(creditos)
        token["distribucion"] = self.distribuir(creditos["valor_usd"])
        return token
