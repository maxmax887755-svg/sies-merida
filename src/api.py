"""API REST de SIES-Merida.  Ejecutar: uvicorn src.api:app --reload"""
import os
import threading
from datetime import datetime
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field

from src.config import APP_ENV, EVIDENCIA_DIR, MODEL_PATH
from src.main import ejecutar_ciclo_completo

app = FastAPI(title="SIES-Merida API", version="1.0.0")
_lock = threading.Lock()

estado = {
    "inicio": datetime.now().isoformat(timespec="seconds"),
    "ciclos_ejecutados": 0,
    "ultimo_ciclo": None,
    "ultima_accion": None,
    "anomalias_detectadas": 0,
    "tokens_emitidos": 0,
    "valor_usd_acumulado": 0.0,
    "ultima_concentracion_maxima": None,
}


class CicloRequest(BaseModel):
    inyectar_anomalia: bool = False
    masa_kg: float = Field(default=2000.0, gt=0, le=10000)


@app.get("/")
def raiz():
    return {
        "sistema": "SIES-Merida",
        "evento": "InnovaFest Merida 2026",
        "version": app.version,
        "entorno": APP_ENV,
        "endpoints": ["GET /", "POST /api/ciclo-completo", "GET /api/estado", "GET /api/reporte"],
    }


@app.post("/api/ciclo-completo")
def ciclo_completo(req: CicloRequest):
    with _lock:
        resultado = ejecutar_ciclo_completo(req.inyectar_anomalia, req.masa_kg)
        estado["ciclos_ejecutados"] += 1
        estado["ultimo_ciclo"] = resultado["timestamp"]
        estado["ultima_accion"] = resultado["accion"]["accion"]
        estado["ultima_concentracion_maxima"] = resultado["impacto"]["concentracion_maxima"]
        if resultado["anomalia"]:
            estado["anomalias_detectadas"] += 1
        if resultado["token"]:
            estado["tokens_emitidos"] += 1
            estado["valor_usd_acumulado"] += resultado["token"]["valor_usd"]
    return resultado


@app.get("/api/estado")
def obtener_estado():
    datos = dict(estado)
    datos["modelo_entrenado"] = os.path.exists(MODEL_PATH)
    return datos


@app.get("/api/reporte", response_class=HTMLResponse)
def obtener_reporte():
    ruta = Path(EVIDENCIA_DIR) / "reporte.html"
    if not ruta.exists():
        raise HTTPException(status_code=404, detail="Aun no hay reporte. Ejecuta un ciclo primero.")
    return HTMLResponse(ruta.read_text(encoding="utf-8"))
