"""Dashboard Streamlit.  Ejecutar: streamlit run dashboard/app.py (con la API activa)."""
from pathlib import Path

import requests
import streamlit as st
import streamlit.components.v1 as components

BASE_DIR = Path(__file__).resolve().parent.parent

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
