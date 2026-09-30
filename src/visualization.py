"""Graficas de series temporales de los sensores."""
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from src.config import EVIDENCIA_DIR
from src.sensor_simulator import SensorNode

PANELES = [
    ("turbidez", "Turbidez (NTU)"),
    ("salinidad", "Salinidad (PSU)"),
    ("oxigeno", "Oxigeno disuelto (mg/L)"),
    ("temperatura", "Temperatura (C)"),
]


def graficar_series_temporales(lecturas, ruta=None):
    ruta = str(ruta or EVIDENCIA_DIR / "series_temporales.png")
    por_nodo = {}
    for lectura in lecturas:
        por_nodo.setdefault(lectura["node_id"], []).append(lectura)

    fig, axes = plt.subplots(2, 2, figsize=(12, 7))
    for ax, (clave, titulo) in zip(axes.flat, PANELES):
        for nodo, ls in por_nodo.items():
            ax.plot(range(1, len(ls) + 1), [l[clave] for l in ls], marker="o", label=nodo)
        ax.axhline(SensorNode.BASE[clave], color="gray", linestyle="--", linewidth=1)
        ax.set_title(titulo)
        ax.set_xlabel("Lectura")
        ax.grid(alpha=0.3)
    axes[0, 0].legend(fontsize=8)
    fig.suptitle("SIES-Merida - Series temporales de sensores")
    fig.tight_layout()
    fig.savefig(ruta, dpi=130)
    plt.close(fig)
    return ruta
