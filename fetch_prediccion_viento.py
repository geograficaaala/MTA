#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Descarga el pronóstico de viento para Sololá utilizando
Open-Meteo Forecast API.

Salida:
    docs/data/viento/prediccion_viento.json

No requiere API key.

Variables de entorno opcionales:
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
from datetime import datetime, timezone
from pathlib import Path
from statistics import mean
from typing import Any, Dict, Iterable, List, Optional
from zoneinfo import ZoneInfo

import requests


API_URL = "https://api.open-meteo.com/v1/forecast"

OUTPUT_PATH = Path(
    "docs/data/viento/prediccion_viento.json"
)

TZ_NAME = os.getenv(
    "OPENMETEO_TIMEZONE",
    "America/Guatemala",
)

TZ_GT = ZoneInfo(TZ_NAME)

LAT = float(
    os.getenv(
        "OPENMETEO_LAT",
        "14.7739",
    )
)

LON = float(
    os.getenv(
        "OPENMETEO_LON",
        "-91.1833",
    )
)

FORECAST_DAYS = max(
    1,
    min(
        16,
        int(
            os.getenv(
                "OPENMETEO_FORECAST_DAYS",
                "16",
            )
        ),
    ),
)

REQUEST_TIMEOUT = 45
MAX_ATTEMPTS = 3


CURRENT_VARS = [
    "wind_speed_10m",
    "wind_direction_10m",
    "wind_gusts_10m",
]


HOURLY_VARS = [
    "wind_speed_10m",
    "wind_direction_10m",
    "wind_gusts_10m",
]


DAILY_VARS = [
    "wind_speed_10m_mean",
    "wind_speed_10m_max",
    "wind_speed_10m_min",
    "wind_gusts_10m_mean",
    "wind_gusts_10m_max",
    "wind_direction_10m_dominant",
]


def now_gt() -> datetime:
    """Devuelve la fecha y hora actual en Guatemala."""
    return datetime.now(TZ_GT)


def now_utc() -> datetime:
    """Devuelve la fecha y hora actual en UTC."""
    return datetime.now(timezone.utc)


def clean_float(
    value: Any,
    digits: int = 2,
) -> Optional[float]:
    """Convierte un valor a float y elimina valores inválidos."""
    if value is None or value == "":
        return None

    try:
        number = float(value)
    except (TypeError, ValueError):
        return None

    if number != number:
        return None

    return round(number, digits)


def normalize_direction(
    value: Any,
) -> Optional[float]:
    """Normaliza una dirección entre 0 y 359.9 grados."""
    number = clean_float(
        value,
        digits=2,
    )

    if number is None:
        return None

    return round(
        number % 360,
        1,
    )


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


def average(
    values: Iterable[Optional[float]],
) -> Optional[float]:
    """Calcula el promedio de valores válidos."""
    valid_values = [
        float(value)
        for value in values
        if value is not None
    ]

    if not valid_values:
        return None

    return round(
        mean(valid_values),
        2,
    )


def maximum(
    values: Iterable[Optional[float]],
) -> Optional[float]:
    """Obtiene el máximo de valores válidos."""
    valid_values = [
        float(value)
        for value in values
        if value is not None
    ]

    if not valid_values:
        return None

    return round(
        max(valid_values),
        2,
    )


def minimum(
    values: Iterable[Optional[float]],
) -> Optional[float]:
    """Obtiene el mínimo de valores válidos."""
    valid_values = [
        float(value)
        for value in values
        if value is not None
    ]

    if not valid_values:
        return None

    return round(
        min(valid_values),
        2,
    )


def wind_category(
    speed_kmh: Optional[float],
) -> Optional[str]:
    """Clasificación sencilla según velocidad del viento."""
    if speed_kmh is None:
        return None

    if speed_kmh < 2:
        return "Calma"

    if speed_kmh < 12:
        return "Brisa ligera"

    if speed_kmh < 20:
        return "Brisa moderada"

    if speed_kmh < 29:
        return "Brisa fresca"

    if speed_kmh < 39:
        return "Viento fuerte"

    if speed_kmh < 50:
        return "Viento muy fuerte"

    if speed_kmh < 62:
        return "Temporal"

    return "Viento severo"


def request_json(
    url: str,
    params: Dict[str, Any],
) -> Dict[str, Any]:
    """Consulta Open-Meteo con reintentos."""
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

            data = response.json()

            if not isinstance(data, dict):
                raise RuntimeError(
                    "Open-Meteo no devolvió un objeto JSON."
                )

            if data.get("error"):
                raise RuntimeError(
                    data.get("reason")
                    or "Open-Meteo devolvió error=true."
                )

            return data

        except Exception as exc:
            last_error = str(exc)

            print(
                f"Intento {attempt}/{MAX_ATTEMPTS} falló: "
                f"{last_error}",
                file=sys.stderr,
            )

            if attempt < MAX_ATTEMPTS:
                time.sleep(
                    2 * attempt
                )

    raise RuntimeError(
        last_error
        or "No se pudo consultar Open-Meteo."
    )


def build_params() -> Dict[str, Any]:
    """Construye los parámetros para Open-Meteo."""
    return {
        "latitude": LAT,
        "longitude": LON,

        "current": ",".join(
            CURRENT_VARS
        ),

        "hourly": ",".join(
            HOURLY_VARS
        ),

        "daily": ",".join(
            DAILY_VARS
        ),

        "timezone": TZ_NAME,

        "forecast_days":
            FORECAST_DAYS,

        "wind_speed_unit":
            "kmh",

        "timeformat":
            "iso8601",
    }


def normalize_current(
    current: Dict[str, Any],
) -> Dict[str, Any]:
    """Normaliza las condiciones actuales."""
    speed = clean_float(
        current.get(
            "wind_speed_10m"
        )
    )

    gust = clean_float(
        current.get(
            "wind_gusts_10m"
        )
    )

    direction = normalize_direction(
        current.get(
            "wind_direction_10m"
        )
    )

    return {
        "fecha":
            current.get("time"),

        "timestamp":
            current.get("time"),

        "intervalo_segundos":
            current.get("interval"),

        "velocidad_viento_10m_kmh":
            speed,

        "velocidad_viento_kmh":
            speed,

        "racha_viento_10m_kmh":
            gust,

        "racha_viento_kmh":
            gust,

        "direccion_viento_10m_grados":
            direction,

        "direccion_viento_grados":
            direction,

        "direccion_viento_cardinal":
            direction_to_cardinal(
                direction
            ),

        "categoria":
            wind_category(speed),
    }


def normalize_hourly(
    hourly: Dict[str, Any],
) -> List[Dict[str, Any]]:
    """Normaliza los registros horarios."""
    times = hourly.get("time") or []

    speeds = (
        hourly.get(
            "wind_speed_10m"
        )
        or []
    )

    directions = (
        hourly.get(
            "wind_direction_10m"
        )
        or []
    )

    gusts = (
        hourly.get(
            "wind_gusts_10m"
        )
        or []
    )

    registros: List[
        Dict[str, Any]
    ] = []

    for index, timestamp in enumerate(
        times
    ):
        if not timestamp:
            continue

        speed = clean_float(
            speeds[index]
            if index < len(speeds)
            else None
        )

        gust = clean_float(
            gusts[index]
            if index < len(gusts)
            else None
        )

        direction = normalize_direction(
            directions[index]
            if index < len(directions)
            else None
        )

        if (
            speed is None
            and gust is None
            and direction is None
        ):
            continue

        registros.append({
            "fecha":
                timestamp,

            "timestamp":
                timestamp,

            "dia":
                str(timestamp)[:10],

            "hora":
                str(timestamp)[11:16],

            "velocidad_viento_10m_kmh":
                speed,

            "velocidad_viento_kmh":
                speed,

            "racha_viento_10m_kmh":
                gust,

            "racha_viento_kmh":
                gust,

            "direccion_viento_10m_grados":
                direction,

            "direccion_viento_grados":
                direction,

            "direccion_viento_cardinal":
                direction_to_cardinal(
                    direction
                ),

            "categoria":
                wind_category(speed),
        })

    return registros


def get_daily_value(
    values: List[Any],
    index: int,
) -> Any:
    """Obtiene de forma segura un valor diario."""
    if index >= len(values):
        return None

    return values[index]


def normalize_daily(
    daily: Dict[str, Any],
) -> List[Dict[str, Any]]:
    """Normaliza el pronóstico diario."""
    dates = daily.get("time") or []

    mean_speeds = (
        daily.get(
            "wind_speed_10m_mean"
        )
        or []
    )

    max_speeds = (
        daily.get(
            "wind_speed_10m_max"
        )
        or []
    )

    min_speeds = (
        daily.get(
            "wind_speed_10m_min"
        )
        or []
    )

    mean_gusts = (
        daily.get(
            "wind_gusts_10m_mean"
        )
        or []
    )

    max_gusts = (
        daily.get(
            "wind_gusts_10m_max"
        )
        or []
    )

    dominant_directions = (
        daily.get(
            "wind_direction_10m_dominant"
        )
        or []
    )

    registros: List[
        Dict[str, Any]
    ] = []

    for index, date in enumerate(
        dates
    ):
        if not date:
            continue

        mean_speed = clean_float(
            get_daily_value(
                mean_speeds,
                index,
            )
        )

        max_speed = clean_float(
            get_daily_value(
                max_speeds,
                index,
            )
        )

        min_speed = clean_float(
            get_daily_value(
                min_speeds,
                index,
            )
        )

        mean_gust = clean_float(
            get_daily_value(
                mean_gusts,
                index,
            )
        )

        max_gust = clean_float(
            get_daily_value(
                max_gusts,
                index,
            )
        )

        direction = normalize_direction(
            get_daily_value(
                dominant_directions,
                index,
            )
        )

        registros.append({
            "fecha":
                date,

            "date":
                date,

            "velocidad_media_10m_kmh":
                mean_speed,

            "velocidad_media_kmh":
                mean_speed,

            "velocidad_maxima_10m_kmh":
                max_speed,

            "velocidad_maxima_kmh":
                max_speed,

            "velocidad_minima_10m_kmh":
                min_speed,

            "velocidad_minima_kmh":
                min_speed,

            "racha_media_10m_kmh":
                mean_gust,

            "racha_media_kmh":
                mean_gust,

            "racha_maxima_10m_kmh":
                max_gust,

            "racha_maxima_kmh":
                max_gust,

            "direccion_dominante_10m_grados":
                direction,

            "direccion_dominante_grados":
                direction,

            "direccion_dominante_cardinal":
                direction_to_cardinal(
                    direction
                ),

            "categoria":
                wind_category(
                    mean_speed
                ),

            "categoria_maxima":
                wind_category(
                    max_speed
                ),
        })

    return registros


def build_resumen(
    registros: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """Construye un resumen del pronóstico."""
    mean_speeds = [
        registro.get(
            "velocidad_media_10m_kmh"
        )
        for registro in registros
    ]

    max_speeds = [
        registro.get(
            "velocidad_maxima_10m_kmh"
        )
        for registro in registros
    ]

    max_gusts = [
        registro.get(
            "racha_maxima_10m_kmh"
        )
        for registro in registros
    ]

    return {
        "dias":
            len(registros),

        "fecha_inicio":
            (
                registros[0]["fecha"]
                if registros
                else None
            ),

        "fecha_fin":
            (
                registros[-1]["fecha"]
                if registros
                else None
            ),

        "velocidad_media_periodo_kmh":
            average(mean_speeds),

        "velocidad_maxima_periodo_kmh":
            maximum(max_speeds),

        "velocidad_minima_periodo_kmh":
            minimum(mean_speeds),

        "racha_maxima_periodo_kmh":
            maximum(max_gusts),
    }


def main() -> None:
    """Ejecuta la descarga del pronóstico."""
    OUTPUT_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    params = build_params()

    print(
        "Consultando pronóstico de viento "
        "en Open-Meteo..."
    )

    print(
        f"Coordenadas: {LAT}, {LON}"
    )

    print(
        f"Horizonte: {FORECAST_DAYS} días"
    )

    data = request_json(
        API_URL,
        params=params,
    )

    daily_data = data.get(
        "daily"
    ) or {}

    hourly_data = data.get(
        "hourly"
    ) or {}

    if (
        not isinstance(daily_data, dict)
        or not daily_data.get("time")
    ):
        raise RuntimeError(
            "La respuesta de Open-Meteo no contiene "
            "daily.time."
        )

    if (
        not isinstance(hourly_data, dict)
        or not hourly_data.get("time")
    ):
        raise RuntimeError(
            "La respuesta de Open-Meteo no contiene "
            "hourly.time."
        )

    daily_records = normalize_daily(
        daily_data
    )

    hourly_records = normalize_hourly(
        hourly_data
    )

    if not daily_records:
        raise RuntimeError(
            "No se pudieron construir registros "
            "diarios de viento."
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
                "Open-Meteo Forecast API",

            "url":
                API_URL,

            "latitude":
                LAT,

            "longitude":
                LON,

            "timezone":
                TZ_NAME,

            "forecast_days":
                FORECAST_DAYS,

            "wind_speed_unit":
                "km/h",

            "current_variables":
                CURRENT_VARS,

            "hourly_variables":
                HOURLY_VARS,

            "daily_variables":
                DAILY_VARS,

            "current_units":
                data.get(
                    "current_units"
                ),

            "hourly_units":
                data.get(
                    "hourly_units"
                ),

            "daily_units":
                data.get(
                    "daily_units"
                ),
        },

        "location": {
            "name":
                "Sololá, Guatemala",

            "lat":
                data.get(
                    "latitude",
                    LAT,
                ),

            "lon":
                data.get(
                    "longitude",
                    LON,
                ),

            "timezone":
                data.get(
                    "timezone",
                    TZ_NAME,
                ),

            "timezone_abbreviation":
                data.get(
                    "timezone_abbreviation"
                ),

            "elevation_m":
                data.get(
                    "elevation"
                ),
        },

        "current":
            normalize_current(
                data.get(
                    "current"
                )
                or {}
            ),

        "resumen":
            build_resumen(
                daily_records
            ),

        "registros":
            daily_records,

        "daily":
            daily_records,

        "prediccion":
            daily_records,

        "hourly":
            hourly_records,

        "registros_horarios":
            hourly_records,

        "raw_generationtime_ms":
            data.get(
                "generationtime_ms"
            ),
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
        json.dumps(
            payload["resumen"],
            ensure_ascii=False,
            indent=2,
        )
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
