# -*- coding: utf-8 -*-
"""Actualiza un proyecto SIES-Merida existente a la v2.

Anade: mapa interactivo (Folium), clima real (Open-Meteo) y alertas SMS en modo demo.
Sobrescribe: src/main.py y dashboard/app.py (se guarda copia .bak_v1).
Anade 3 dependencias a requirements.txt.

Uso:  python actualizar_v2.py
Puede guardarse dentro de la carpeta del proyecto o junto a la carpeta SIES-Merida.
"""
import os
import shutil

AQUI = os.path.dirname(os.path.abspath(__file__))

# ------------------------------------------------------------------ archivos NUEVOS
nuevos = {}

nuevos["dashboard/__init__.py"] = ""

nuevos["dashboard/mapa.py"] = r'''import folium
import streamlit as st
from streamlit_folium import st_folium

NODOS_YUCATAN = [
    {"id": "BOYA-PROGRESO-01", "nombre": "Progreso", "lat": 21.2833, "lon": -89.6667},
    {"id": "BOYA-CHELEM-02", "nombre": "Chelem", "lat": 21.2667, "lon": -89.7333},
    {"id": "BOYA-CHICXULUB-03", "nombre": "Chicxulub Puerto", "lat": 21.2833, "lon": -89.6000},
]


def crear_mapa():
    m = folium.Map(location=[21.28, -89.66], zoom_start=12, tiles="CartoDB dark_matter")
    folium.Rectangle(
        bounds=[[21.25, -89.75], [21.30, -89.58]],
        color="#4ade80", fill=True, fill_opacity=0.15,
        popup="Reserva Estatal Ciénegas y Manglares"
    ).add_to(m)
    for nodo in NODOS_YUCATAN:
        folium.Marker(
            [nodo["lat"], nodo["lon"]],
            popup=f"<b>{nodo['nombre']}</b><br>Boya Edge AI",
            tooltip=nodo["nombre"],
            icon=folium.Icon(color="green", icon="tint", prefix="fa")
        ).add_to(m)
    return m


def render_mapa():
    st.subheader("🗺️ Mapa de Nodos en Tiempo Real")
    st.caption("Reserva Estatal Ciénegas y Manglares — Costa Norte de Yucatán")
    st_folium(crear_mapa(), width=None, height=500, returned_objects=[])
'''

nuevos["src/apis_reales.py"] = r'''"""Clima real (Open-Meteo) para alimentar el gemelo digital."""
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
'''

nuevos["src/alertas.py"] = r'''"""Alertas SMS en modo demo (no se envia nada real)."""
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
'''

# ------------------------------------------------------------------ archivos SOBRESCRITOS
reemplazos = {}

reemplazos["src/main.py"] = r'''"""Orquestador del ciclo completo SIES-Merida (v2: clima real + alertas SMS demo)."""
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
'''

reemplazos["dashboard/app.py"] = r'''"""Dashboard Streamlit.  Ejecutar: streamlit run dashboard/app.py (con la API activa)."""
import sys
from pathlib import Path

import requests
import streamlit as st
import streamlit.components.v1 as components

BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from dashboard.mapa import render_mapa

st.set_page_config(page_title="SIES-Merida", layout="wide")
st.title("SIES-Merida | InnovaFest Merida 2026")
st.caption("Sistema Inteligente de Ecosistemas Sostenibles - monitoreo del manglar de Progreso, Yucatan")

with st.sidebar:
    st.header("Control")
    api_url = st.text_input("URL de la API", "http://localhost:8000")
    simular = st.checkbox("Simular derrame", value=True)
    masa = st.slider("Masa del derrame (kg)", 10, 1000, 500, disabled=not simular)
    ejecutar = st.button("Ejecutar ciclo", type="primary")

# Metricas de la API
st.subheader("Estado del sistema")
try:
    est = requests.get(api_url + "/api/estado", timeout=10).json()
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Ciclos ejecutados", est["ciclos_ejecutados"])
    c2.metric("Anomalias detectadas", est["anomalias_detectadas"])
    c3.metric("Tokens emitidos", est["tokens_emitidos"])
    c4.metric("Valor acumulado (USD)", "%.2f" % est["valor_usd_acumulado"])
except Exception:
    st.error("No se pudo conectar con la API. Inicia: uvicorn src.api:app")

st.divider()
render_mapa()
st.divider()

if ejecutar:
    with st.spinner("Ejecutando ciclo (la primera vez entrena el modelo)..."):
        try:
            resp = requests.post(
                api_url + "/api/ciclo-completo",
                json={"inyectar_anomalia": simular, "masa_kg": float(masa)},
                timeout=300,
            )
            resp.raise_for_status()
            st.session_state["resultado"] = resp.json()
        except Exception as exc:
            st.error("Error al ejecutar el ciclo: %s" % exc)

res = st.session_state.get("resultado")
if res:
    st.subheader("Resultados del ultimo ciclo")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Anomalia", "SI" if res["anomalia"] else "NO")
    c2.metric("Accion", res["accion"]["accion"])
    c3.metric("Conc. maxima (kg)", "%.1f" % res["impacto"]["concentracion_maxima"])
    c4.metric("Token", res["token"]["token_id"] if res["token"] else "-")

    clima = res.get("clima") or {}
    c1, c2, c3, c4 = st.columns(4)
    if "error" not in clima and clima:
        c1.metric("Temperatura (C)", clima["temperatura_c"])
        c2.metric("Viento (km/h)", clima["viento_kmh"])
        c3.metric("Humedad (%)", clima["humedad_pct"])
    else:
        c1.metric("Clima real", "No disponible")
    alertas = res.get("alertas")
    c4.metric("Alertas SMS (demo)", alertas["destinatarios"] if alertas else 0)

    if res.get("barrera"):
        st.info("Barrera recomendada: %s" % res["barrera"])

    col_a, col_b = st.columns(2)
    heatmap = Path(res["archivos"]["heatmap"])
    series = Path(res["archivos"]["series"])
    if heatmap.exists():
        col_a.image(str(heatmap), caption="Gemelo digital")
    if series.exists():
        col_b.image(str(series), caption="Series temporales")

    with st.expander("Reporte HTML"):
        try:
            html = requests.get(api_url + "/api/reporte", timeout=10).text
            components.html(html, height=900, scrolling=True)
        except Exception:
            st.warning("No se pudo cargar el reporte.")
    with st.expander("Respuesta completa (JSON)"):
        st.json(res)
'''

DEPENDENCIAS_NUEVAS = [
    "folium==0.17.0",
    "streamlit-folium==0.21.0",
    "httpx==0.27.2",
]

ARCHIVOS_REQUERIDOS = [
    "requirements.txt",
    "src/main.py",
    "src/edge_ai.py",
    "src/digital_twin.py",
    "dashboard/app.py",
]


def ruta(base, rel):
    return os.path.join(base, *rel.split("/"))


def encontrar_proyecto():
    candidatos = [
        AQUI,
        os.path.join(AQUI, "SIES-Merida"),
        os.path.join(AQUI, "SIES-Merida-V2"),
    ]
    for c in candidatos:
        if all(os.path.isfile(ruta(c, r)) for r in ARCHIVOS_REQUERIDOS):
            return c
    return None


def escribir(base, rel, contenido):
    destino = ruta(base, rel)
    os.makedirs(os.path.dirname(destino), exist_ok=True)
    with open(destino, "w", encoding="utf-8", newline="\n") as f:
        f.write(contenido)


def actualizar():
    base = encontrar_proyecto()
    if base is None:
        print("ERROR: no se encontro el proyecto SIES-Merida.")
        print("Guarda este script dentro de la carpeta del proyecto (la que contiene src/ y")
        print("requirements.txt) o junto a la carpeta SIES-Merida, y vuelve a ejecutarlo.")
        return 1

    print("Proyecto encontrado en:", base)
    resumen = []

    # 1) Archivos nuevos
    for rel, contenido in nuevos.items():
        existia = os.path.exists(ruta(base, rel))
        escribir(base, rel, contenido)
        resumen.append(("%s %s" % ("actualizado" if existia else "creado    ", rel)))

    # 2) Sobrescribir con copia de respaldo
    for rel, contenido in reemplazos.items():
        destino = ruta(base, rel)
        respaldo = destino + ".bak_v1"
        if os.path.exists(destino) and not os.path.exists(respaldo):
            shutil.copy2(destino, respaldo)
        escribir(base, rel, contenido)
        resumen.append("sobrescrito %s (respaldo: %s)" % (rel, os.path.basename(respaldo)))

    # 3) requirements.txt
    req = ruta(base, "requirements.txt")
    with open(req, "r", encoding="utf-8") as f:
        texto = f.read()
    existentes = {l.strip().split("==")[0].lower() for l in texto.splitlines() if l.strip()}
    anadidas = [d for d in DEPENDENCIAS_NUEVAS if d.split("==")[0].lower() not in existentes]
    if anadidas:
        if texto and not texto.endswith("\n"):
            texto += "\n"
        texto += "\n".join(anadidas) + "\n"
        with open(req, "w", encoding="utf-8", newline="\n") as f:
            f.write(texto)
    resumen.append("requirements.txt: +%d dependencia(s) %s" % (len(anadidas), anadidas))

    print("\nResumen de cambios:")
    for linea in resumen:
        print("  -", linea)
    print("\nAhora ejecuta (con el venv activado, dentro de la carpeta del proyecto):")
    print("  pip install -r requirements.txt")
    print("  python -m src.main")
    print("\nDashboard (dos terminales):")
    print("  uvicorn src.api:app --reload")
    print("  streamlit run dashboard/app.py")
    return 0


if __name__ == "__main__":
    raise SystemExit(actualizar())
