# -*- coding: utf-8 -*-
"""Parche v2.1 para SIES-Merida: foco del derrame segun el viento y conteo de celdas afectadas.

Uso (dentro de la carpeta del proyecto):  python parche_v2_1.py
"""
import os
import shutil

AQUI = os.path.dirname(os.path.abspath(__file__))

CAMBIOS = {
    "src/main.py": [(
        """        twin.inyectar_derrame(FOCO_DERRAME_KM[0], FOCO_DERRAME_KM[1], masa_kg)
""",
        """        # Foco en el lado de donde sopla el viento, para que la mancha quede dentro del dominio
        foco_x = 4.0 if twin.vx < 0 else 1.0
        foco_y = 2.2 if twin.vy < 0 else 0.8
        twin.inyectar_derrame(foco_x, foco_y, masa_kg)
""")],
    "src/digital_twin.py": [
        ("""        pico = float(c.max())
        for _ in range(pasos):
            for _ in range(n_sub):
                c = self._paso(c, dt)
            pico = max(pico, float(c.max()))
""",
         """        pico = float(c.max())
        alcanzadas = c > 0.1  # celdas que superan 0.1 kg en algun momento de la simulacion
        for _ in range(pasos):
            for _ in range(n_sub):
                c = self._paso(c, dt)
            pico = max(pico, float(c.max()))
            alcanzadas |= (c > 0.1)
"""),
        ("""            "celdas_afectadas": int((c > 1.0).sum()),
""",
         """            "celdas_afectadas": int(alcanzadas.sum()),
"""),
    ],
}


def main():
    for rel, reemplazos in CAMBIOS.items():
        ruta = os.path.join(AQUI, *rel.split("/"))
        if not os.path.isfile(ruta):
            print("ERROR: no se encontro", rel, "- ejecuta el parche dentro de la carpeta del proyecto.")
            return 1
        with open(ruta, "r", encoding="utf-8") as f:
            texto = f.read()
        for viejo, nuevo in reemplazos:
            if nuevo in texto:
                print("Ya aplicado:", rel)
                continue
            if viejo not in texto:
                print("ERROR: no se reconocio el codigo esperado en", rel, "- no se modifico nada.")
                return 1
            texto = texto.replace(viejo, nuevo, 1)
        respaldo = ruta + ".bak_v2"
        if not os.path.exists(respaldo):
            shutil.copy2(ruta, respaldo)
        with open(ruta, "w", encoding="utf-8", newline="\n") as f:
            f.write(texto)
        print("Parchado:", rel)
    print("\nListo. Ejecuta: python -m src.main")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
