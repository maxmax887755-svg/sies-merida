"""Gemelo digital del manglar: adveccion-difusion 2D de un derrame."""
import math

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from src.config import EVIDENCIA_DIR


class DigitalTwinManglar:
    ANCHO_KM = 5.0
    ALTO_KM = 3.0
    NX = 50
    NY = 50

    def __init__(self, vx=0.15, vy=0.05, difusion=0.01, dt_paso_h=0.5):
        # Velocidades en km/h, difusion en km2/h, dt_paso en horas.
        self.vx = vx
        self.vy = vy
        self.D = difusion
        self.dt_paso = dt_paso_h
        self.dx = self.ANCHO_KM / self.NX
        self.dy = self.ALTO_KM / self.NY
        self.concentracion = np.zeros((self.NY, self.NX))  # kg por celda
        xs = (np.arange(self.NX) + 0.5) * self.dx
        ys = (np.arange(self.NY) + 0.5) * self.dy
        self._XX, self._YY = np.meshgrid(xs, ys)
        self.foco = None
        self.mapa_prediccion = None
        self.barrera = None
        self.ultimo_impacto = None

    # ------------------------------------------------------------ fisica
    def _dt_estable(self):
        """Paso maximo estable (upwind + difusion explicita)."""
        tasa = (abs(self.vx) / self.dx + abs(self.vy) / self.dy
                + 2 * self.D * (1 / self.dx ** 2 + 1 / self.dy ** 2))
        return 0.9 / tasa

    def _paso(self, c, dt):
        p = np.pad(c, 1)  # cero fuera del dominio (frontera abierta)
        izq, der = p[1:-1, :-2], p[1:-1, 2:]
        abajo, arriba = p[:-2, 1:-1], p[2:, 1:-1]
        vxp, vxn = max(self.vx, 0.0), min(self.vx, 0.0)
        vyp, vyn = max(self.vy, 0.0), min(self.vy, 0.0)
        adv = (vxp * (c - izq) + vxn * (der - c)) / self.dx \
            + (vyp * (c - abajo) + vyn * (arriba - c)) / self.dy
        dif = self.D * ((der - 2 * c + izq) / self.dx ** 2 + (arriba - 2 * c + abajo) / self.dy ** 2)
        return np.maximum(c + dt * (dif - adv), 0.0)

    # ------------------------------------------------------------ API
    def inyectar_derrame(self, x_km, y_km, masa_kg):
        i = int(np.clip(x_km / self.dx, 0, self.NX - 1))
        j = int(np.clip(y_km / self.dy, 0, self.NY - 1))
        self.concentracion[j, i] += masa_kg
        self.foco = (float(x_km), float(y_km))
        self.mapa_prediccion = None
        self.barrera = None

    def predecir_impacto(self, pasos=30):
        c = self.concentracion.copy()
        n_sub = max(1, math.ceil(self.dt_paso / self._dt_estable()))
        dt = self.dt_paso / n_sub
        pico = float(c.max())
        for _ in range(pasos):
            for _ in range(n_sub):
                c = self._paso(c, dt)
            pico = max(pico, float(c.max()))
        self.mapa_prediccion = c
        masa = float(c.sum())
        if masa > 1e-9:
            cx = float((c * self._XX).sum() / masa)
            cy = float((c * self._YY).sum() / masa)
        else:
            cx = cy = None
        self.ultimo_impacto = {
            "pasos": int(pasos),
            "horas_simuladas": float(pasos * self.dt_paso),
            "subpasos_por_paso": int(n_sub),
            "concentracion_maxima": pico,
            "concentracion_maxima_final": float(c.max()),
            "masa_inicial_kg": float(self.concentracion.sum()),
            "masa_final_kg": masa,
            "celdas_afectadas": int((c > 1.0).sum()),
            "centroide_x_km": cx,
            "centroide_y_km": cy,
        }
        return self.ultimo_impacto

    def recomendar_barrera(self):
        """Barrera aguas abajo del centroide de la mancha prevista."""
        if self.mapa_prediccion is None:
            self.predecir_impacto()
        c = self.mapa_prediccion
        masa = float(c.sum())
        if masa <= 1e-9:
            self.barrera = None
            return None
        cx = float((c * self._XX).sum() / masa)
        cy = float((c * self._YY).sum() / masa)
        varianza = float((c * ((self._XX - cx) ** 2 + (self._YY - cy) ** 2)).sum() / masa)
        sigma = math.sqrt(varianza)
        norma = math.hypot(self.vx, self.vy) or 1.0
        ux, uy = self.vx / norma, self.vy / norma
        radio = float(min(max(1.5 * sigma, 0.3), 1.0))
        x = float(np.clip(cx + ux * 0.5, radio * 0.5, self.ANCHO_KM - radio * 0.5))
        y = float(np.clip(cy + uy * 0.5, radio * 0.5, self.ALTO_KM - radio * 0.5))
        self.barrera = {"x_km": round(x, 3), "y_km": round(y, 3), "radio_km": round(radio, 3)}
        return self.barrera

    def visualizar(self, ruta=None):
        ruta = str(ruta or EVIDENCIA_DIR / "gemelo_digital.png")
        datos = self.mapa_prediccion if self.mapa_prediccion is not None else self.concentracion
        fig, ax = plt.subplots(figsize=(9, 5.8))
        im = ax.imshow(datos, origin="lower", extent=[0, self.ANCHO_KM, 0, self.ALTO_KM],
                       cmap="hot_r", vmin=0, vmax=max(float(datos.max()), 1.0), aspect="equal")
        plt.colorbar(im, ax=ax, label="Concentracion (kg/celda)", fraction=0.046, pad=0.04)
        if self.foco is not None:
            ax.scatter([self.foco[0]], [self.foco[1]], marker="*", s=380, c="cyan",
                       edgecolors="black", linewidths=1.2, zorder=5, label="Foco del derrame")
        if self.barrera is not None:
            ax.add_patch(plt.Circle((self.barrera["x_km"], self.barrera["y_km"]),
                                    self.barrera["radio_km"], fill=False, edgecolor="blue",
                                    linewidth=3, zorder=5, label="Barrera recomendada"))
        ax.set_xlabel("x (km)")
        ax.set_ylabel("y (km)")
        ax.set_title("Gemelo digital - prediccion de dispersion del derrame")
        if self.foco is not None or self.barrera is not None:
            ax.legend(loc="upper right")
        fig.tight_layout()
        fig.savefig(ruta, dpi=140)
        plt.close(fig)
        return ruta
