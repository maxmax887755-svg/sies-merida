"""Orquestador del ciclo completo SIES-Merida (v2: clima real + alertas SMS demo)."""
from datetime import datetime

from src.actuator import ActuadorAutonomo
from src.alertas import SistemaAlertas
from src.apis_reales import APIsReales
from src.digital_twin import DigitalTwinManglar
from src.edge_ai import EdgeAnomalyDetector
from src.logger_config import configurar_logger
from src.reporte import generar_reporte_html
from src.sensor_simulator import SensorNode
from src.tokenization import TokenizadorEcosistemico
from src.visualization import graficar_series_temporales

NODOS_YUCATAN = [
    ("Progreso", 21.2833, -89.6667),
    ("Chelem", 21.2667, -89.7333),
    ("Chicxulub", 21.2833, -89.6000),
]
NODO_DERRAME = "Progreso"
FOCO_DERRAME_KM = (2.5, 1.5)      # centro del dominio 5 x 3 km (deja espacio a la deriva)
MASA_DERRAME_KG = 2000.0
HECTAREAS_PROTEGIDAS = 25.0
LECTURAS_NORMALES = 5
LECTURAS_ANOMALAS = 3
VENTANA = 3                        # ultimas lecturas evaluadas por nodo
CONFIRMACION_MIN = 2               # anomalias requeridas dentro de la ventana

_componentes = None


def obtener_componentes():
    """Inicializa (una sola vez) detector, actuador, tokenizador, nodos, clima y alertas."""
    global _componentes
    if _componentes is None:
        _componentes = {
            "detector": EdgeAnomalyDetector(),
            "actuador": ActuadorAutonomo(),
            "tokenizador": TokenizadorEcosistemico(),
            "nodos": [SensorNode(nombre, lat, lon) for nombre, lat, lon in NODOS_YUCATAN],
            "apis": APIsReales(),
            "alertas": SistemaAlertas(),
        }
    return _componentes


def ejecutar_ciclo_completo(inyectar_anomalia=True, masa_kg=MASA_DERRAME_KG):
    log = configurar_logger("SIES.main")
    comp = obtener_componentes()
    detector, actuador, tokenizador = comp["detector"], comp["actuador"], comp["tokenizador"]
    apis = comp["apis"]
    log.info("Ciclo iniciado (derrame=%s, masa=%.0f kg)", inyectar_anomalia, masa_kg)

    # 0) Clima real
    clima = apis.clima_actual()
    if "error" not in clima:
        log.info("Clima real en Progreso: %sC, viento %s km/h",
                 clima["temperatura_c"], clima["viento_kmh"])
    else:
        log.warning("Clima real no disponible; el gemelo usa el viento por defecto")

    twin = DigitalTwinManglar()
    viento = None
    if "error" not in clima:
        viento = apis.viento_para_gemelo(clima)
        twin.vx = viento["vx"]
        twin.vy = viento["vy"]
        log.info("Deriva aplicada al gemelo: vx=%.3f vy=%.3f km/h (%s)",
                 viento["vx"], viento["vy"], viento["fuente"])

    if inyectar_anomalia:
        twin.inyectar_derrame(FOCO_DERRAME_KM[0], FOCO_DERRAME_KM[1], masa_kg)
        log.info("Derrame de %.0f kg inyectado en %s", masa_kg, NODO_DERRAME)

    # 1) Monitoreo de nodos
    lecturas, nodos_res = [], []
    for nodo in comp["nodos"]:
        ls = nodo.ejecutar_ciclo(LECTURAS_NORMALES)
        if inyectar_anomalia and nodo.node_id == NODO_DERRAME:
            ls += nodo.ejecutar_ciclo(LECTURAS_ANOMALAS, inyectar_anomalia=True)
        lecturas.extend(ls)
        preds = [detector.predecir(l) for l in ls[-VENTANA:]]
        n_anom = sum(1 for p in preds if p["es_anomalia"])
        peor = max(preds, key=lambda p: p["error_reconstruccion"])
        nodos_res.append({
            "node_id": nodo.node_id,
            "lat": nodo.lat,
            "lon": nodo.lon,
            "anomalias_en_ventana": n_anom,
            "anomalia_confirmada": bool(n_anom >= CONFIRMACION_MIN),
            "error_maximo": peor["error_reconstruccion"],
            "umbral": peor["umbral"],
        })
        log.info("Nodo %-10s anomalias %d/%d | error max %.3f",
                 nodo.node_id, n_anom, len(preds), peor["error_reconstruccion"])

    # 2) Deteccion
    afectados = [n for n in nodos_res if n["anomalia_confirmada"]]
    anomalia = bool(afectados)
    referencia = max(afectados or nodos_res, key=lambda n: n["error_maximo"])
    deteccion = {
        "es_anomalia": anomalia,
        "error_reconstruccion": referencia["error_maximo"],
        "umbral": referencia["umbral"],
        "node_id": referencia["node_id"],
    }
    nodo_afectado = referencia["node_id"] if anomalia else None
    log.info("Anomalia detectada: %s", anomalia)

    # 3) Gemelo digital
    impacto = twin.predecir_impacto(pasos=30)
    barrera = twin.recomendar_barrera()
    ruta_heatmap = twin.visualizar()
    log.info("Gemelo digital: conc. max %.1f kg, %d celdas afectadas",
             impacto["concentracion_maxima"], impacto["celdas_afectadas"])

    # 4) Actuador
    accion = actuador.decidir(deteccion, impacto["concentracion_maxima"], barrera)

    # 4b) Alertas SMS (modo demo)
    alertas_info = None
    if anomalia and accion["accion"] != "ninguna":
        n = comp["alertas"].alertar_autoridades(
            ubicacion=nodo_afectado or NODO_DERRAME,
            accion=accion["accion"],
            masa_kg=masa_kg,
        )
        alertas_info = {"destinatarios": n, "modo": "demo"}
        log.info("Alertas SMS enviadas a %d destinatarios (demo)", n)

    # 5) Token
    token = None
    if anomalia:
        token = tokenizador.emitir_token(HECTAREAS_PROTEGIDAS, "Manglar de Progreso", accion["accion"])
        log.info("Token emitido: %s (USD %.2f)", token["token_id"], token["valor_usd"])

    resultado = {
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "inyectar_anomalia": bool(inyectar_anomalia),
        "masa_kg": float(masa_kg),
        "anomalia": anomalia,
        "nodo_afectado": nodo_afectado,
        "nodos": nodos_res,
        "deteccion": deteccion,
        "impacto": impacto,
        "barrera": barrera,
        "accion": accion,
        "token": token,
        "clima": clima,
        "viento": viento,
        "alertas": alertas_info,
    }

    # 6) Reporte y graficas
    ruta_reporte = generar_reporte_html(resultado, ruta_heatmap)
    ruta_series = graficar_series_temporales(lecturas)
    resultado["archivos"] = {"heatmap": ruta_heatmap, "reporte": ruta_reporte, "series": ruta_series}
    log.info("Reporte: %s", ruta_reporte)
    return resultado


def main():
    log = configurar_logger("SIES.main")
    log.info("SIES-Merida v2 | InnovaFest Merida 2026")
    resultado = ejecutar_ciclo_completo(inyectar_anomalia=True, masa_kg=MASA_DERRAME_KG)
    log.info("Resumen: anomalia=%s | accion=%s | token=%s | alertas=%s",
             resultado["anomalia"], resultado["accion"]["accion"],
             resultado["token"]["token_id"] if resultado["token"] else "-",
             resultado["alertas"]["destinatarios"] if resultado["alertas"] else 0)
    log.info("Archivos en evidencia/: gemelo_digital.png, series_temporales.png, reporte.html")


if __name__ == "__main__":
    main()
