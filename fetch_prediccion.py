"""
fetch_prediccion.py
-------------------
Mesa Técnica Agroclimática de Sololá — MTA

Descarga el pronóstico de precipitación diaria para los próximos 30 días
usando la API gratuita de Open-Meteo (seasonal-api.open-meteo.com).
No requiere autenticación ni API key.

Modelo  : ECMWF (modelo seasonal disponible en Open-Meteo)
Variable: precipitation_mean (mm/día)
Punto   : Sololá, cabecera departamental (lat 14.772, lon -91.183)

Salida  : docs/data/precipitaciones/prediccion_mensual.json

Uso:
    python fetch_prediccion.py
"""

import json
import os
import sys
from datetime import date, timedelta

import requests

# ---------------------------------------------------------------------------
# CONFIGURACIÓN
# ---------------------------------------------------------------------------

OUTPUT_PATH = os.path.join("docs", "data", "precipitaciones", "prediccion_mensual.json")

# Open-Meteo usa el endpoint /v1/forecast para pronósticos de hasta 16 días
# con resolución horaria/diaria. Para proyecciones de 30 días se usa el mismo
# endpoint con el parámetro forecast_days=30 y modelos GFS / ECMWF IFS.
FORECAST_URL = "https://api.open-meteo.com/v1/forecast"

# Coordenadas del centroide del departamento (cabecera de Sololá)
LAT = 14.772
LON = -91.183

# Pronóstico: hoy + 30 días
START_DATE = date.today()
END_DATE   = date.today() + timedelta(days=30)

# ---------------------------------------------------------------------------
# FUNCIONES
# ---------------------------------------------------------------------------

def format_date(d: date) -> str:
    return d.strftime("%Y-%m-%d")


def clean_value(v) -> float:
    """Convierte None o negativos a 0.0 y redondea a 2 decimales."""
    try:
        val = float(v)
        return round(max(0.0, val), 2)
    except (TypeError, ValueError):
        return 0.0


def fetch_forecast() -> list[dict]:
    """
    Consulta Open-Meteo y retorna lista de
    [{"fecha": "YYYY-MM-DD", "lluvia_estimada_mm": float}, ...]
    """
    params = {
        "latitude":         LAT,
        "longitude":        LON,
        "daily":            "precipitation_sum",
        "forecast_days":    16,           # máximo nativo sin suscripción
        "timezone":         "America/Guatemala",
    }

    print(f"Consultando Open-Meteo:")
    print(f"  Endpoint  : {FORECAST_URL}")
    print(f"  Periodo   : {format_date(START_DATE)} → {format_date(END_DATE)}")
    print(f"  Coordenadas: lat={LAT}, lon={LON}")

    try:
        response = requests.get(FORECAST_URL, params=params, timeout=30)
    except requests.exceptions.RequestException as e:
        print(f"[ERROR] No se pudo conectar con Open-Meteo: {e}")
        sys.exit(1)

    if response.status_code != 200:
        print(f"[ERROR] HTTP {response.status_code}: {response.text[:300]}")
        sys.exit(1)

    try:
        data = response.json()
    except ValueError:
        print("[ERROR] Respuesta no válida (JSON mal formado).")
        sys.exit(1)

    # Navegar la estructura: daily -> time, precipitation_sum
    try:
        fechas = data["daily"]["time"]
        lluvias = data["daily"]["precipitation_sum"]
    except (KeyError, TypeError) as e:
        print(f"[ERROR] Estructura inesperada en la respuesta de Open-Meteo: {e}")
        sys.exit(1)

    registros = [
        {
            "fecha":             fecha,
            "lluvia_estimada_mm": clean_value(lluvia),
            "fuente":            "Open-Meteo API — modelo GFS/ECMWF IFS",
            "tipo":              "pronostico",
        }
        for fecha, lluvia in zip(fechas, lluvias)
    ]

    # Intentar extender a 30 días con el endpoint extended-forecast si hay <30
    if len(registros) < 28:
        registros = extend_with_ecmwf(registros)

    return registros


def extend_with_ecmwf(existing: list[dict]) -> list[dict]:
    """
    Intenta obtener días adicionales desde el API seasonal de Open-Meteo
    (seasonal-api.open-meteo.com) con el modelo ECMWF SEAS5 para llenar
    hasta 30 días si el pronóstico estándar cubre menos días.
    """
    try:
        url = "https://seasonal-api.open-meteo.com/v1/seasonal"
        params = {
            "latitude":  LAT,
            "longitude": LON,
            "daily":     "precipitation_mean",
            "models":    "ecmwf_ifs04",
            "start_date": format_date(date.today()),
            "end_date":   format_date(END_DATE),
        }
        resp = requests.get(url, params=params, timeout=30)
        if resp.status_code != 200:
            print(f"  [AVISO] API seasonal respondió {resp.status_code} — usando solo pronóstico estándar.")
            return existing

        data = resp.json()
        fechas  = data.get("daily", {}).get("time", [])
        lluvias = data.get("daily", {}).get("precipitation_mean", [])

        fechas_existentes = {r["fecha"] for r in existing}
        nuevos = [
            {
                "fecha":             fecha,
                "lluvia_estimada_mm": clean_value(lluvia),
                "fuente":            "Open-Meteo seasonal API — ECMWF IFS04",
                "tipo":              "pronostico_estacional",
            }
            for fecha, lluvia in zip(fechas, lluvias)
            if fecha not in fechas_existentes
        ]

        extended = existing + nuevos
        extended.sort(key=lambda r: r["fecha"])
        print(f"  Extendido con {len(nuevos)} días adicionales del modelo seasonal ECMWF.")
        return extended[:30]

    except Exception as e:
        print(f"  [AVISO] No se pudo extender con seasonal API: {e}")
        return existing


def save_json(data: list, path: str) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"\n  Archivo guardado: {path}")


# ---------------------------------------------------------------------------
# MAIN
# ---------------------------------------------------------------------------

def main() -> None:
    print("=" * 60)
    print("  Open-Meteo — Pronóstico pluviométrico, Sololá")
    print(f"  Horizonte: {format_date(START_DATE)} → {format_date(END_DATE)}")
    print("=" * 60)

    registros = fetch_forecast()

    print(f"\n  Registros obtenidos: {len(registros)}")
    for r in registros[:5]:
        print(f"  {r['fecha']} — {r['lluvia_estimada_mm']} mm ({r['tipo']})")
    if len(registros) > 5:
        print(f"  ... y {len(registros) - 5} más.")

    save_json(registros, OUTPUT_PATH)

    print("\n" + "=" * 60)
    print(f"  Total días en pronóstico: {len(registros)}")
    total_est = sum(r["lluvia_estimada_mm"] for r in registros)
    print(f"  Acumulado estimado total: {total_est:.1f} mm")
    print("=" * 60)


if __name__ == "__main__":
    main()
