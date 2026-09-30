import folium
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
