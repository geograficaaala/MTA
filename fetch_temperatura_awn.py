#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Descarga datos de temperatura desde Ambient Weather Network para el módulo de
Temperatura de la Mesa Técnica Agroclimática de Sololá.

Salida:
  docs/data/temperatura/awn_temperatura.json

Requiere GitHub Secrets o variables de entorno:
  AMBIENT_WEATHER_API_KEY
  AMBIENT_WEATHER_APPLICATION_KEY

Opcionales:
  AMBIENT_WEATHER_MAC_ADDRESS   Para forzar una estación específica.
  AMBIENT_WEATHER_STATION_NAME  Para buscar una estación por nombre.

El JSON generado queda compatible con docs/temperatura_index.html.
"""

from __future__ import annotations

import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional
from urllib.parse import quote

import requests
from zoneinfo import ZoneInfo


API_BASE = "https://api.ambientweather.net/v1"
DEVICES_URL = f"{API_BASE}/devices"
OUTPUT_PATH = Path("docs/data/temperatura/awn_temperatura.json")
TZ_GT = ZoneInfo("America/Guatemala")


class AmbientWeatherError(RuntimeError):
    pass


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


def f_to_c(value: Any) -> Optional[float]:
    number = clean_float(value, digits=4)
    if number is None:
        return None
    return round((number - 32.0) * 5.0 / 9.0, 2)


def pct(value: Any) -> Optional[float]:
    number = clean_float(value, digits=2)
    if number is None:
        return None
    return max(0.0, min(100.0, number))


def iso_from_ambient_time(value: Any) -> Optional[str]:
    """Convierte dateutc milisegundos o fecha ISO a hora local de Guatemala."""
    if value is None or value == "":
        return None

    # Ambient Weather normalmente usa dateutc en milisegundos Unix.
    try:
        number = float(value)
        if number > 10_000_000_000:  # milisegundos
            dt = datetime.fromtimestamp(number / 1000.0, timezone.utc)
        else:  # segundos, por si algún export usa Unix seconds
            dt = datetime.fromtimestamp(number, timezone.utc)
        return dt.astimezone(TZ_GT).isoformat(timespec="seconds")
    except (TypeError, ValueError, OSError):
        pass

    # Fallback para strings ISO.
    try:
        text = str(value).replace("Z", "+00:00")
        dt = datetime.fromisoformat(text)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(TZ_GT).isoformat(timespec="seconds")
    except Exception:
        return str(value)


def compact_dict(data: Dict[str, Any]) -> Dict[str, Any]:
    """Elimina claves con valor None sin tocar ceros."""
    return {k: v for k, v in data.items() if v is not None}


def normalize_reading(raw: Dict[str, Any]) -> Dict[str, Any]:
    """Normaliza una lectura Ambient Weather al esquema del dashboard."""
    fecha = iso_from_ambient_time(raw.get("dateutc") or raw.get("date") or raw.get("created_at"))

    # Ambient Weather suele reportar temperatura en Fahrenheit.
    temperature_c = (
        f_to_c(raw.get("tempf"))
        if raw.get("tempf") is not None
        else clean_float(raw.get("temperature_c") or raw.get("temp_c"))
    )

    feels_like_c = None
    for key in ("feelsLike", "feelslike", "feels_like", "feelsLikef"):
        if raw.get(key) is not None:
            feels_like_c = f_to_c(raw.get(key))
            break
    if feels_like_c is None:
        feels_like_c = clean_float(raw.get("feels_like_c") or raw.get("sensacion_c"))

    dew_point_c = None
    for key in ("dewPoint", "dewpoint", "dewPointf"):
        if raw.get(key) is not None:
            dew_point_c = f_to_c(raw.get(key))
            break
    if dew_point_c is None:
        dew_point_c = clean_float(raw.get("dew_point_c") or raw.get("dewpoint_c") or raw.get("rocio_c"))

    heat_index_c = None
    for key in ("heatIndex", "heatindex", "heatIndexf"):
        if raw.get(key) is not None:
            heat_index_c = f_to_c(raw.get(key))
            break

    wind_chill_c = None
    for key in ("windChill", "windchill", "windChillf"):
        if raw.get(key) is not None:
            wind_chill_c = f_to_c(raw.get(key))
            break

    humidity = pct(raw.get("humidity") or raw.get("humidityin"))

    normalized = compact_dict({
        "fecha": fecha,
        "timestamp": fecha,
        "dateutc": raw.get("dateutc"),
        "temperature_c": temperature_c,
        "temp_c": temperature_c,
        "humidity": humidity,
        "humidity_pct": humidity,
        "humedad_relativa_pct": humidity,
        "feels_like_c": feels_like_c,
        "sensacion_c": feels_like_c,
        "dew_point_c": dew_point_c,
        "dewpoint_c": dew_point_c,
        "rocio_c": dew_point_c,
        "heat_index_c": heat_index_c,
        "wind_chill_c": wind_chill_c,
        "raw_tempf": clean_float(raw.get("tempf")),
    })

    return normalized


def request_json(url: str, params: Dict[str, Any], timeout: int = 45) -> Any:
    last_error: Optional[str] = None
    for attempt in range(1, 4):
        try:
            response = requests.get(url, params=params, timeout=timeout)
            response.raise_for_status()
            return response.json()
        except Exception as exc:
            last_error = str(exc)
            print(f"Intento {attempt}/3 falló para {url}: {last_error}", file=sys.stderr)
            time.sleep(2 * attempt)
    raise AmbientWeatherError(last_error or f"No se pudo consultar {url}")


def get_credentials() -> Dict[str, str]:
    api_key = os.getenv("AMBIENT_WEATHER_API_KEY", "").strip()
    app_key = os.getenv("AMBIENT_WEATHER_APPLICATION_KEY", "").strip()

    if not api_key or not app_key:
        raise AmbientWeatherError(
            "Faltan AMBIENT_WEATHER_API_KEY y/o AMBIENT_WEATHER_APPLICATION_KEY. "
            "Configúralas como GitHub Secrets."
        )

    return {"apiKey": api_key, "applicationKey": app_key}


def choose_device(devices: List[Dict[str, Any]]) -> Dict[str, Any]:
    if not devices:
        raise AmbientWeatherError("Ambient Weather respondió sin estaciones asociadas a la cuenta.")

    wanted_mac = os.getenv("AMBIENT_WEATHER_MAC_ADDRESS", "").strip().lower()
    wanted_name = os.getenv("AMBIENT_WEATHER_STATION_NAME", "").strip().lower()

    if wanted_mac:
        for device in devices:
            if str(device.get("macAddress", "")).strip().lower() == wanted_mac:
                return device
        raise AmbientWeatherError(f"No se encontró una estación con MAC {wanted_mac}.")

    if wanted_name:
        for device in devices:
            info = device.get("info") or {}
            name = str(info.get("name") or device.get("name") or "").lower()
            if wanted_name in name:
                return device
        raise AmbientWeatherError(f"No se encontró una estación cuyo nombre contenga: {wanted_name}")

    return devices[0]


def fetch_history(mac_address: str, credentials: Dict[str, str], limit: int = 288) -> List[Dict[str, Any]]:
    """Intenta leer histórico reciente. Si falla, el flujo principal conserva latest."""
    safe_mac = quote(mac_address, safe="")
    url = f"{DEVICES_URL}/{safe_mac}"
    params = {
        **credentials,
        "endDate": int(now_utc().timestamp() * 1000),
        "limit": limit,
    }

    data = request_json(url, params=params)
    if isinstance(data, list):
        return [normalize_reading(row) for row in data if isinstance(row, dict)]
    return []


def main() -> None:
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    credentials = get_credentials()
    devices = request_json(DEVICES_URL, params=credentials)
    if not isinstance(devices, list):
        raise AmbientWeatherError("La respuesta de Ambient Weather /devices no fue una lista.")

    device = choose_device(devices)
    info = device.get("info") or {}
    mac_address = device.get("macAddress") or ""
    last_data = device.get("lastData") or {}

    if not isinstance(last_data, dict) or not last_data:
        raise AmbientWeatherError("La estación seleccionada no trae lastData en la respuesta.")

    latest = normalize_reading(last_data)
    warnings: List[str] = []

    history: List[Dict[str, Any]] = []
    if mac_address:
        try:
            history = fetch_history(str(mac_address), credentials)
        except Exception as exc:
            warnings.append(f"No se pudo leer histórico reciente de Ambient Weather: {exc}")
            print(warnings[-1], file=sys.stderr)

    # Asegura que el dashboard tenga al menos una lectura para graficar.
    if not history:
        history = [latest]

    # Orden cronológico y limpieza de lecturas sin temperatura.
    history = [r for r in history if r.get("temperature_c") is not None]
    history.sort(key=lambda r: str(r.get("fecha") or ""))

    payload = {
        "ok": True,
        "generated_at_gt": now_gt().isoformat(timespec="seconds"),
        "generated_at_utc": now_utc().isoformat(timespec="seconds"),
        "source": {
            "name": "Ambient Weather REST API",
            "devices_endpoint": DEVICES_URL,
            "history_endpoint": f"{DEVICES_URL}/{{macAddress}}",
        },
        "station": {
            "name": info.get("name") or device.get("name"),
            "location": info.get("location"),
            "coords": info.get("coords"),
            "macAddress": mac_address,
        },
        "latest": latest,
        "history": history,
        "registros": history,
        "warnings": warnings,
    }

    OUTPUT_PATH.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"OK: {OUTPUT_PATH} generado")
    print(f"Estación: {payload['station'].get('name') or 'sin nombre'}")
    print(f"Lecturas históricas: {len(history)}")
    print(f"Temperatura actual: {latest.get('temperature_c')} °C")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(1)
