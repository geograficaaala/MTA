#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Descarga pronóstico de temperatura para Sololá usando Open-Meteo Forecast API.

Salida:
  docs/data/temperatura/prediccion_temperatura.json

El JSON generado queda compatible con docs/temperatura_index.html.
No requiere API key para uso no comercial dentro de los límites de Open-Meteo.

Opcionales por variable de entorno:
  OPENMETEO_LAT
  OPENMETEO_LON
  OPENMETEO_TIMEZONE
  OPENMETEO_FORECAST_DAYS
"""

from __future__ import annotations

import json
import os
import sys
import time
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from statistics import mean
from typing import Any, Dict, Iterable, List, Optional

import requests
from zoneinfo import ZoneInfo


API_URL = "https://api.open-meteo.com/v1/forecast"
OUTPUT_PATH = Path("docs/data/temperatura/prediccion_temperatura.json")
TZ_NAME = os.getenv("OPENMETEO_TIMEZONE", "America/Guatemala")
TZ_GT = ZoneInfo(TZ_NAME)

# Coordenada por defecto: cabecera de Sololá. Puedes sobrescribir con variables de entorno.
LAT = float(os.getenv("OPENMETEO_LAT", "14.7739"))
LON = float(os.getenv("OPENMETEO_LON", "-91.1833"))
FORECAST_DAYS = max(1, min(16, int(os.getenv("OPENMETEO_FORECAST_DAYS", "16"))))

HOURLY_VARS = [
    "temperature_2m",
    "relative_humidity_2m",
    "dew_point_2m",
    "apparent_temperature",
]

CURRENT_VARS = [
    "temperature_2m",
    "relative_humidity_2m",
    "apparent_temperature",
]


def now_gt() -> datetime:
    return datetime.now(TZ_GT)


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


def clean_float(value: Any, digits: int = 2) -> Optional[float]:
    if value is None or value == "":
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    if number != number:  # NaN
        return None
    return round(number, digits)


def avg(values: Iterable[Optional[float]]) -> Optional[float]:
    clean = [float(v) for v in values if v is not None]
    if not clean:
        return None
    return round(mean(clean), 2)


def vmin(values: Iterable[Optional[float]]) -> Optional[float]:
    clean = [float(v) for v in values if v is not None]
    if not clean:
        return None
    return round(min(clean), 2)


def vmax(values: Iterable[Optional[float]]) -> Optional[float]:
    clean = [float(v) for v in values if v is not None]
    if not clean:
        return None
    return round(max(clean), 2)


def request_json(url: str, params: Dict[str, Any], timeout: int = 45) -> Dict[str, Any]:
    last_error: Optional[str] = None
    for attempt in range(1, 4):
        try:
            response = requests.get(url, params=params, timeout=timeout)
            response.raise_for_status()
            data = response.json()
            if isinstance(data, dict) and data.get("error"):
                raise RuntimeError(data.get("reason") or "Open-Meteo devolvió error=true")
            if not isinstance(data, dict):
                raise RuntimeError("Open-Meteo no devolvió un objeto JSON.")
            return data
        except Exception as exc:
            last_error = str(exc)
            print(f"Intento {attempt}/3 falló para Open-Meteo: {last_error}", file=sys.stderr)
            time.sleep(2 * attempt)
    raise RuntimeError(last_error or "No se pudo consultar Open-Meteo")


def build_params() -> Dict[str, Any]:
    return {
        "latitude": LAT,
        "longitude": LON,
        "hourly": ",".join(HOURLY_VARS),
        "current": ",".join(CURRENT_VARS),
        "timezone": TZ_NAME,
        "forecast_days": FORECAST_DAYS,
        "temperature_unit": "celsius",
        "wind_speed_unit": "kmh",
        "precipitation_unit": "mm",
        "timeformat": "iso8601",
    }


def group_hourly_to_daily(hourly: Dict[str, Any]) -> List[Dict[str, Any]]:
    times = hourly.get("time") or []
    temps = hourly.get("temperature_2m") or []
    hums = hourly.get("relative_humidity_2m") or []
    dews = hourly.get("dew_point_2m") or []
    feels = hourly.get("apparent_temperature") or []

    grouped: Dict[str, Dict[str, List[Optional[float]]]] = defaultdict(lambda: {
        "temp": [],
        "humidity": [],
        "dew": [],
        "feels": [],
    })

    for idx, tstamp in enumerate(times):
        if not tstamp:
            continue
        fecha = str(tstamp)[:10]
        grouped[fecha]["temp"].append(clean_float(temps[idx]) if idx < len(temps) else None)
        grouped[fecha]["humidity"].append(clean_float(hums[idx]) if idx < len(hums) else None)
        grouped[fecha]["dew"].append(clean_float(dews[idx]) if idx < len(dews) else None)
        grouped[fecha]["feels"].append(clean_float(feels[idx]) if idx < len(feels) else None)

    registros: List[Dict[str, Any]] = []
    for fecha in sorted(grouped.keys()):
        values = grouped[fecha]
        t_max = vmax(values["temp"])
        t_min = vmin(values["temp"])
        t_mean = avg(values["temp"])
        rango = round(t_max - t_min, 2) if t_max is not None and t_min is not None else None

        registros.append({
            "fecha": fecha,
            "date": fecha,
            "t_media_c": t_mean,
            "temperature_2m_mean": t_mean,
            "mean_c": t_mean,
            "t_max_c": t_max,
            "temperature_2m_max": t_max,
            "max_c": t_max,
            "t_min_c": t_min,
            "temperature_2m_min": t_min,
            "min_c": t_min,
            "rango_c": rango,
            "humedad_relativa_pct": avg(values["humidity"]),
            "relative_humidity_2m_mean": avg(values["humidity"]),
            "dew_point_c": avg(values["dew"]),
            "sensacion_media_c": avg(values["feels"]),
            "sensacion_max_c": vmax(values["feels"]),
            "sensacion_min_c": vmin(values["feels"]),
        })

    return registros


def normalize_current(current: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "fecha": current.get("time"),
        "timestamp": current.get("time"),
        "temperature_c": clean_float(current.get("temperature_2m")),
        "temp_c": clean_float(current.get("temperature_2m")),
        "humidity": clean_float(current.get("relative_humidity_2m")),
        "humidity_pct": clean_float(current.get("relative_humidity_2m")),
        "feels_like_c": clean_float(current.get("apparent_temperature")),
        "sensacion_c": clean_float(current.get("apparent_temperature")),
    }


def build_resumen(registros: List[Dict[str, Any]]) -> Dict[str, Any]:
    return {
        "dias": len(registros),
        "fecha_inicio": registros[0]["fecha"] if registros else None,
        "fecha_fin": registros[-1]["fecha"] if registros else None,
        "t_media_c": avg(r.get("t_media_c") for r in registros),
        "t_max_c": vmax(r.get("t_max_c") for r in registros),
        "t_min_c": vmin(r.get("t_min_c") for r in registros),
        "humedad_relativa_pct": avg(r.get("humedad_relativa_pct") for r in registros),
    }


def main() -> None:
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    params = build_params()
    data = request_json(API_URL, params=params)

    hourly = data.get("hourly") or {}
    if not isinstance(hourly, dict) or not hourly.get("time"):
        raise RuntimeError("La respuesta de Open-Meteo no contiene hourly.time.")

    registros = group_hourly_to_daily(hourly)
    if not registros:
        raise RuntimeError("No se pudieron construir registros diarios desde hourly.")

    payload = {
        "ok": True,
        "generated_at_gt": now_gt().isoformat(timespec="seconds"),
        "generated_at_utc": now_utc().isoformat(timespec="seconds"),
        "source": {
            "name": "Open-Meteo Forecast API",
            "url": API_URL,
            "latitude": LAT,
            "longitude": LON,
            "timezone": TZ_NAME,
            "forecast_days": FORECAST_DAYS,
            "hourly_variables": HOURLY_VARS,
            "current_variables": CURRENT_VARS,
        },
        "location": {
            "name": "Sololá, Guatemala",
            "lat": LAT,
            "lon": LON,
            "timezone": TZ_NAME,
            "elevation_m": data.get("elevation"),
        },
        "current": normalize_current(data.get("current") or {}),
        "resumen": build_resumen(registros),
        "registros": registros,
        "daily": registros,
        "prediccion": registros,
        "raw_generationtime_ms": data.get("generationtime_ms"),
    }

    OUTPUT_PATH.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"OK: {OUTPUT_PATH} generado")
    print(json.dumps(payload["resumen"], ensure_ascii=False, indent=2))


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(1)
