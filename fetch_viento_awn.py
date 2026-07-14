#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Descarga datos de viento desde Ambient Weather Network.

Salida:
    docs/data/viento/awn_viento.json

Secrets o variables de entorno requeridas:
    AMBIENT_WEATHER_API_KEY
    AMBIENT_WEATHER_APPLICATION_KEY

Opcionales:
    AMBIENT_WEATHER_MAC_ADDRESS
    AMBIENT_WEATHER_STATION_NAME
    AMBIENT_WEATHER_HISTORY_LIMIT
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
from zoneinfo import ZoneInfo

import requests


API_BASE = "https://api.ambientweather.net/v1"
DEVICES_URL = f"{API_BASE}/devices"

OUTPUT_PATH = Path(
    "docs/data/viento/awn_viento.json"
)

TZ_GT = ZoneInfo("America/Guatemala")

MAX_ATTEMPTS = 3
REQUEST_TIMEOUT = 45
DEFAULT_HISTORY_LIMIT = 288


class AmbientWeatherError(RuntimeError):
    """Error controlado de Ambient Weather."""


def now_gt() -> datetime:
    """Fecha y hora actual de Guatemala."""
    return datetime.now(TZ_GT)


def now_utc() -> datetime:
    """Fecha y hora actual UTC."""
    return datetime.now(timezone.utc)


def clean_float(
    value: Any,
    digits: int = 2,
) -> Optional[float]:
    """Convierte un valor a número flotante."""
    if value is None or value == "":
        return None

    try:
        number = float(value)
    except (TypeError, ValueError):
        return None

    if number != number:
        return None

    return round(number, digits)


def mph_to_kmh(value: Any) -> Optional[float]:
    """Convierte millas por hora a kilómetros por hora."""
    number = clean_float(value, digits=4)

    if number is None:
        return None

    return round(number * 1.609344, 2)


def normalize_direction(value: Any) -> Optional[float]:
    """Normaliza una dirección entre 0 y 359.9 grados."""
    number = clean_float(value, digits=2)

    if number is None:
        return None

    return round(number % 360, 1)


def direction_to_cardinal(
    degrees: Optional[float],
) -> Optional[str]:
    """Convierte grados a uno de 16 puntos cardinales."""
    if degrees is None:
        return None

    directions = [
        "N",
        "NNE",
        "NE",
        "ENE",
        "E",
        "ESE",
        "SE",
        "SSE",
        "S",
        "SSO",
        "SO",
        "OSO",
        "O",
        "ONO",
        "NO",
        "NNO",
    ]

    index = int(
        (degrees + 11.25) // 22.5
    ) % 16

    return directions[index]


def iso_from_ambient_time(
    value: Any,
) -> Optional[str]:
    """
    Convierte dateutc de Ambient Weather a fecha local
    de Guatemala.
    """
    if value is None or value == "":
        return None

    try:
        number = float(value)

        if number > 10_000_000_000:
            date_time = datetime.fromtimestamp(
                number / 1000.0,
                timezone.utc,
            )
        else:
            date_time = datetime.fromtimestamp(
                number,
                timezone.utc,
            )

        return date_time.astimezone(
            TZ_GT
        ).isoformat(timespec="seconds")

    except (TypeError, ValueError, OSError):
        pass

    try:
        text = str(value).replace(
            "Z",
            "+00:00",
        )

        date_time = datetime.fromisoformat(text)

        if date_time.tzinfo is None:
            date_time = date_time.replace(
                tzinfo=timezone.utc
            )

        return date_time.astimezone(
            TZ_GT
        ).isoformat(timespec="seconds")

    except Exception:
        return str(value)


def compact_dict(
    data: Dict[str, Any],
) -> Dict[str, Any]:
    """Elimina valores None sin eliminar ceros."""
    return {
        key: value
        for key, value in data.items()
        if value is not None
    }


def normalize_reading(
    raw: Dict[str, Any],
) -> Dict[str, Any]:
    """Normaliza una lectura de viento de Ambient Weather."""
    fecha = iso_from_ambient_time(
        raw.get("dateutc")
        or raw.get("date")
        or raw.get("created_at")
    )

    velocidad = mph_to_kmh(
        raw.get("windspeedmph")
    )

    racha = mph_to_kmh(
        raw.get("windgustmph")
    )

    racha_maxima_diaria = mph_to_kmh(
        raw.get("maxdailygust")
    )

    direccion = normalize_direction(
        raw.get("winddir")
    )

    direccion_racha = normalize_direction(
        raw.get("windgustdir")
    )

    velocidad_promedio_2min = mph_to_kmh(
        raw.get("windspdmph_avg2m")
    )

    direccion_promedio_2min = normalize_direction(
        raw.get("winddir_avg2m")
    )

    velocidad_promedio_10min = mph_to_kmh(
        raw.get("windspdmph_avg10m")
    )

    direccion_promedio_10min = normalize_direction(
        raw.get("winddir_avg10m")
    )

    return compact_dict({
        "fecha": fecha,
        "timestamp": fecha,
        "dateutc": raw.get("dateutc"),

        "velocidad_viento_kmh": velocidad,

        "racha_viento_kmh": racha,

        "racha_maxima_diaria_kmh":
            racha_maxima_diaria,

        "direccion_viento_grados":
            direccion,

        "direccion_viento_cardinal":
            direction_to_cardinal(direccion),

        "direccion_racha_grados":
            direccion_racha,

        "direccion_racha_cardinal":
            direction_to_cardinal(
                direccion_racha
            ),

        "velocidad_promedio_2min_kmh":
            velocidad_promedio_2min,

        "direccion_promedio_2min_grados":
            direccion_promedio_2min,

        "direccion_promedio_2min_cardinal":
            direction_to_cardinal(
                direccion_promedio_2min
            ),

        "velocidad_promedio_10min_kmh":
            velocidad_promedio_10min,

        "direccion_promedio_10min_grados":
            direccion_promedio_10min,

        "direccion_promedio_10min_cardinal":
            direction_to_cardinal(
                direccion_promedio_10min
            ),

        "datos_originales": compact_dict({
            "windspeedmph":
                clean_float(
                    raw.get("windspeedmph")
                ),

            "windgustmph":
                clean_float(
                    raw.get("windgustmph")
                ),

            "maxdailygust":
                clean_float(
                    raw.get("maxdailygust")
                ),

            "winddir":
                clean_float(
                    raw.get("winddir")
                ),

            "windgustdir":
                clean_float(
                    raw.get("windgustdir")
                ),

            "windspdmph_avg2m":
                clean_float(
                    raw.get("windspdmph_avg2m")
                ),

            "winddir_avg2m":
                clean_float(
                    raw.get("winddir_avg2m")
                ),

            "windspdmph_avg10m":
                clean_float(
                    raw.get("windspdmph_avg10m")
                ),

            "winddir_avg10m":
                clean_float(
                    raw.get("winddir_avg10m")
                ),
        }),
    })


def request_json(
    url: str,
    params: Dict[str, Any],
) -> Any:
    """Realiza una petición con reintentos."""
    last_error: Optional[str] = None

    for attempt in range(
        1,
        MAX_ATTEMPTS + 1,
    ):
        try:
            response = requests.get(
                url,
                params=params,
                timeout=REQUEST_TIMEOUT,
            )

            response.raise_for_status()

            return response.json()

        except Exception as exc:
            last_error = str(exc)

            print(
                f"Intento {attempt}/{MAX_ATTEMPTS} "
                f"falló para {url}: {last_error}",
                file=sys.stderr,
            )

            if attempt < MAX_ATTEMPTS:
                time.sleep(2 * attempt)

    raise AmbientWeatherError(
        last_error
        or f"No se pudo consultar {url}"
    )


def get_credentials() -> Dict[str, str]:
    """Obtiene las credenciales desde variables de entorno."""
    api_key = os.getenv(
        "AMBIENT_WEATHER_API_KEY",
        "",
    ).strip()

    application_key = os.getenv(
        "AMBIENT_WEATHER_APPLICATION_KEY",
        "",
    ).strip()

    if not api_key or not application_key:
        raise AmbientWeatherError(
            "Faltan AMBIENT_WEATHER_API_KEY y/o "
            "AMBIENT_WEATHER_APPLICATION_KEY. "
            "Configúralas como GitHub Secrets."
        )

    return {
        "apiKey": api_key,
        "applicationKey": application_key,
    }


def choose_device(
    devices: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """Selecciona la estación configurada."""
    if not devices:
        raise AmbientWeatherError(
            "Ambient Weather respondió sin estaciones."
        )

    wanted_mac = os.getenv(
        "AMBIENT_WEATHER_MAC_ADDRESS",
        "",
    ).strip().lower()

    wanted_name = os.getenv(
        "AMBIENT_WEATHER_STATION_NAME",
        "",
    ).strip().lower()

    if wanted_mac:
        for device in devices:
            device_mac = str(
                device.get("macAddress", "")
            ).strip().lower()

            if device_mac == wanted_mac:
                return device

        raise AmbientWeatherError(
            "No se encontró una estación con la MAC "
            f"{wanted_mac}."
        )

    if wanted_name:
        for device in devices:
            info = device.get("info") or {}

            device_name = str(
                info.get("name")
                or device.get("name")
                or ""
            ).lower()

            if wanted_name in device_name:
                return device

        raise AmbientWeatherError(
            "No se encontró una estación cuyo nombre "
            f"contenga: {wanted_name}"
        )

    return devices[0]


def get_history_limit() -> int:
    """Obtiene el límite de lecturas históricas."""
    raw_limit = os.getenv(
        "AMBIENT_WEATHER_HISTORY_LIMIT",
        str(DEFAULT_HISTORY_LIMIT),
    )

    try:
        limit = int(raw_limit)
    except ValueError:
        limit = DEFAULT_HISTORY_LIMIT

    return max(1, min(288, limit))


def fetch_history(
    mac_address: str,
    credentials: Dict[str, str],
) -> List[Dict[str, Any]]:
    """Descarga el histórico reciente de la estación."""
    safe_mac = quote(
        mac_address,
        safe="",
    )

    url = f"{DEVICES_URL}/{safe_mac}"

    params = {
        **credentials,
        "endDate": int(
            now_utc().timestamp() * 1000
        ),
        "limit": get_history_limit(),
    }

    data = request_json(
        url,
        params=params,
    )

    if not isinstance(data, list):
        return []

    return [
        normalize_reading(row)
        for row in data
        if isinstance(row, dict)
    ]


def has_wind_data(
    reading: Dict[str, Any],
) -> bool:
    """Comprueba si una lectura contiene datos de viento."""
    wind_fields = [
        "velocidad_viento_kmh",
        "racha_viento_kmh",
        "racha_maxima_diaria_kmh",
        "direccion_viento_grados",
        "velocidad_promedio_2min_kmh",
        "velocidad_promedio_10min_kmh",
    ]

    return any(
        reading.get(field) is not None
        for field in wind_fields
    )


def deduplicate_readings(
    readings: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """Elimina lecturas repetidas por fecha."""
    readings_by_date: Dict[str, Dict[str, Any]] = {}

    for reading in readings:
        fecha = str(
            reading.get("fecha")
            or reading.get("dateutc")
            or ""
        )

        if not fecha:
            continue

        readings_by_date[fecha] = reading

    result = list(
        readings_by_date.values()
    )

    result.sort(
        key=lambda reading: str(
            reading.get("fecha") or ""
        )
    )

    return result


def main() -> None:
    """Ejecuta la descarga de datos."""
    OUTPUT_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    credentials = get_credentials()

    devices = request_json(
        DEVICES_URL,
        params=credentials,
    )

    if not isinstance(devices, list):
        raise AmbientWeatherError(
            "La respuesta de /devices no fue una lista."
        )

    device = choose_device(devices)

    info = device.get("info") or {}

    mac_address = str(
        device.get("macAddress") or ""
    )

    last_data = device.get("lastData") or {}

    if (
        not isinstance(last_data, dict)
        or not last_data
    ):
        raise AmbientWeatherError(
            "La estación seleccionada no contiene "
            "lastData."
        )

    latest = normalize_reading(
        last_data
    )

    if not has_wind_data(latest):
        raise AmbientWeatherError(
            "La lectura actual no contiene datos "
            "de viento."
        )

    warnings: List[str] = []
    history: List[Dict[str, Any]] = []

    if mac_address:
        try:
            history = fetch_history(
                mac_address,
                credentials,
            )

        except Exception as exc:
            warning = (
                "No se pudo leer el histórico reciente "
                f"de Ambient Weather: {exc}"
            )

            warnings.append(warning)

            print(
                warning,
                file=sys.stderr,
            )

    history = [
        reading
        for reading in history
        if has_wind_data(reading)
    ]

    history.append(latest)

    history = deduplicate_readings(
        history
    )

    payload = {
        "ok": True,

        "generated_at_gt":
            now_gt().isoformat(
                timespec="seconds"
            ),

        "generated_at_utc":
            now_utc().isoformat(
                timespec="seconds"
            ),

        "source": {
            "name":
                "Ambient Weather REST API",

            "devices_endpoint":
                DEVICES_URL,

            "history_endpoint":
                f"{DEVICES_URL}/{{macAddress}}",

            "original_speed_unit":
                "mph",

            "output_speed_unit":
                "km/h",

            "history_limit":
                get_history_limit(),
        },

        "station": {
            "name":
                info.get("name")
                or device.get("name"),

            "location":
                info.get("location"),

            "coords":
                info.get("coords"),

            "address":
                info.get("address"),

            "macAddress":
                mac_address,
        },

        "variables": {
            "velocidad_viento_kmh":
                "Velocidad instantánea del viento",

            "racha_viento_kmh":
                "Racha registrada en la lectura",

            "racha_maxima_diaria_kmh":
                "Racha máxima registrada durante el día",

            "direccion_viento_grados":
                "Dirección instantánea del viento",

            "velocidad_promedio_2min_kmh":
                "Velocidad media durante dos minutos",

            "direccion_promedio_2min_grados":
                "Dirección media durante dos minutos",

            "velocidad_promedio_10min_kmh":
                "Velocidad media durante diez minutos",

            "direccion_promedio_10min_grados":
                "Dirección media durante diez minutos",
        },

        "latest": latest,
        "history": history,
        "registros": history,
        "warnings": warnings,
    }

    OUTPUT_PATH.write_text(
        json.dumps(
            payload,
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    print(
        f"OK: {OUTPUT_PATH} generado"
    )

    print(
        "Estación: "
        f"{payload['station'].get('name') or 'sin nombre'}"
    )

    print(
        f"Lecturas históricas: {len(history)}"
    )

    print(
        "Velocidad actual: "
        f"{latest.get('velocidad_viento_kmh')} km/h"
    )

    print(
        "Racha actual: "
        f"{latest.get('racha_viento_kmh')} km/h"
    )

    print(
        "Dirección actual: "
        f"{latest.get('direccion_viento_cardinal')}"
    )


if __name__ == "__main__":
    try:
        main()

    except Exception as exc:
        print(
            f"ERROR: {exc}",
            file=sys.stderr,
        )

        sys.exit(1)
