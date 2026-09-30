"""Generacion del reporte HTML."""
import base64
from datetime import datetime
from pathlib import Path

from jinja2 import Environment

from src.config import EVIDENCIA_DIR

PLANTILLA = """<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="utf-8">
<title>SIES-Merida - Reporte</title>
<style>
body { margin: 0; padding: 32px; background: #0f2438; color: #e6eef5; font-family: "Segoe UI", Arial, sans-serif; }
h1 { color: #4ade80; margin-bottom: 4px; }
h2 { color: #4ade80; margin-top: 32px; }
.sub { color: #94a9bd; margin-bottom: 24px; }
.cards { display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 16px; }
.card { background: #16344f; border-left: 4px solid #4ade80; border-radius: 8px; padding: 16px; }
.label { color: #94a9bd; font-size: 13px; text-transform: uppercase; letter-spacing: 1px; }
.valor { font-size: 24px; font-weight: 600; margin-top: 6px; word-break: break-word; }
.ok { color: #4ade80; }
.alerta { color: #f87171; }
table { width: 100%; border-collapse: collapse; background: #16344f; border-radius: 8px; overflow: hidden; }
th, td { padding: 10px 14px; text-align: left; border-bottom: 1px solid #0f2438; }
th { color: #4ade80; }
img { max-width: 100%; border-radius: 8px; border: 1px solid #244a6b; }
</style>
</head>
<body>
<h1>SIES-Merida</h1>
<div class="sub">InnovaFest Merida 2026 - Reporte generado {{ generado }}</div>

<div class="cards">
  <div class="card"><div class="label">Estado</div>
    <div class="valor {{ 'alerta' if r.anomalia else 'ok' }}">{{ 'ANOMALIA DETECTADA' if r.anomalia else 'Sin anomalias' }}</div></div>
  <div class="card"><div class="label">Nodo afectado</div><div class="valor">{{ r.nodo_afectado or '-' }}</div></div>
  <div class="card"><div class="label">Error / umbral</div>
    <div class="valor">{{ '%.3f' | format(r.deteccion.error_reconstruccion) }} / {{ '%.3f' | format(r.deteccion.umbral) }}</div></div>
  <div class="card"><div class="label">Concentracion maxima</div>
    <div class="valor">{{ '%.1f' | format(r.impacto.concentracion_maxima) }} kg</div></div>
  <div class="card"><div class="label">Celdas afectadas</div><div class="valor">{{ r.impacto.celdas_afectadas }}</div></div>
  <div class="card"><div class="label">Accion del actuador</div><div class="valor">{{ r.accion.accion }}</div></div>
</div>

<h2>Gemelo digital</h2>
{% if heatmap_b64 %}
<img alt="Gemelo digital" src="data:image/png;base64,{{ heatmap_b64 }}">
{% else %}
<p>Sin imagen disponible.</p>
{% endif %}
{% if r.barrera %}
<p>Barrera recomendada: x = {{ r.barrera.x_km }} km, y = {{ r.barrera.y_km }} km, radio = {{ r.barrera.radio_km }} km.</p>
{% endif %}

<h2>Nodos monitoreados</h2>
<table>
  <tr><th>Nodo</th><th>Lat</th><th>Lon</th><th>Anomalias (ventana)</th><th>Error max.</th><th>Estado</th></tr>
  {% for n in r.nodos %}
  <tr><td>{{ n.node_id }}</td><td>{{ n.lat }}</td><td>{{ n.lon }}</td><td>{{ n.anomalias_en_ventana }}</td>
      <td>{{ '%.3f' | format(n.error_maximo) }}</td>
      <td class="{{ 'alerta' if n.anomalia_confirmada else 'ok' }}">{{ 'ANOMALIA' if n.anomalia_confirmada else 'Normal' }}</td></tr>
  {% endfor %}
</table>

<h2>Token de resiliencia</h2>
{% if r.token %}
<div class="cards">
  <div class="card"><div class="label">Token ID</div><div class="valor">{{ r.token.token_id }}</div></div>
  <div class="card"><div class="label">CO2 (ton)</div><div class="valor">{{ r.token.toneladas_co2 }}</div></div>
  <div class="card"><div class="label">Valor (USD)</div><div class="valor">${{ '%.2f' | format(r.token.valor_usd) }}</div></div>
  <div class="card"><div class="label">Comunidad 60%</div><div class="valor">${{ '%.2f' | format(r.token.distribucion.comunidad) }}</div></div>
  <div class="card"><div class="label">Infraestructura 30%</div><div class="valor">${{ '%.2f' | format(r.token.distribucion.infraestructura) }}</div></div>
  <div class="card"><div class="label">Emergencia 10%</div><div class="valor">${{ '%.2f' | format(r.token.distribucion.emergencia) }}</div></div>
</div>
{% else %}
<p>No se emitio token en este ciclo.</p>
{% endif %}
</body>
</html>
"""


def generar_reporte_html(resultado, ruta_heatmap=None, ruta=None):
    ruta = Path(ruta or EVIDENCIA_DIR / "reporte.html")
    ruta_heatmap = Path(ruta_heatmap or EVIDENCIA_DIR / "gemelo_digital.png")
    heatmap_b64 = ""
    if ruta_heatmap.exists():
        heatmap_b64 = base64.b64encode(ruta_heatmap.read_bytes()).decode("ascii")
    plantilla = Environment(autoescape=True).from_string(PLANTILLA)
    html = plantilla.render(
        r=resultado,
        heatmap_b64=heatmap_b64,
        generado=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    )
    ruta.write_text(html, encoding="utf-8")
    return str(ruta)
