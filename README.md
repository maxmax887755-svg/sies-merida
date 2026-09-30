# SIES-Merida

Sistema Inteligente de Ecosistemas Sostenibles - InnovaFest Merida 2026.

Pipeline: sensores (Yucatan) -> IA en el borde (autoencoder) -> gemelo digital del manglar
(adveccion-difusion) -> actuador autonomo -> tokenizacion de creditos -> reporte HTML.

## Instalacion

```bash
python -m venv venv
venv\Scripts\activate        # Linux/Mac: source venv/bin/activate
pip install -r requirements.txt
```

## Uso (desde la carpeta SIES-Merida)

```bash
python -m src.main                  # ciclo completo por consola
pytest                              # 11 tests
uvicorn src.api:app --reload        # API en http://localhost:8000
streamlit run dashboard/app.py      # dashboard (requiere la API activa)
```

Los resultados se guardan en `evidencia/` (gemelo_digital.png, series_temporales.png, reporte.html).

## Reglas del actuador

- Sin anomalia: accion `ninguna`.
- Anomalia y concentracion maxima > 50 kg/celda: `desplegar_barrera_absorbente`.
- Anomalia con concentracion menor: `activar_bomba_flushing` (15 min).

## Contrato

`contracts/ResilienceToken.sol`: ERC-1155 (OpenZeppelin 5.x); `emitirCredito` restringida a verificadores.
