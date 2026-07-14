#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Pronóstico municipal de balance hídrico y variables agroclimáticas.
Fuente: Open-Meteo Weather Forecast API.
No utiliza Ambient Weather Network (AWN).

Salida:
  docs/data/agroclima/prediccion_balance_hidrico.json

El balance calculado es climático y simplificado:
  precipitación prevista - ET0 de referencia

No incluye coeficiente de cultivo (Kc), escorrentía, infiltración,
capacidad de campo ni almacenamiento real del suelo.
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
from typing import Any, DefaultDict, Dict, Iterable, List, Optional, Tuple
from zoneinfo import ZoneInfo

import requests


API_URL = "https://api.open-meteo.com/v1/forecast"
OUTPUT_PATH = Path("docs/data/agroclima/prediccion_balance_hidrico.json")

TIMEZONE = os.getenv("OPENMETEO_TIMEZONE", "America/Guatemala")
TZ_GT = ZoneInfo(TIMEZONE)
FORECAST_DAYS = max(1, min(16, int(os.getenv("AGROCLIMA_FORECAST_DAYS", "16"))))
DRY_THRESHOLD_MM = max(
    0.0,
    float(os.getenv("AGROCLIMA_DRY_DAY_THRESHOLD_MM", "1.0")),
)
MODEL = os.getenv("OPENMETEO_FORECAST_MODEL", "").strip()

REQUEST_TIMEOUT = 60
MAX_ATTEMPTS = 4
DELAY_SECONDS = 0.5

# Variables diarias publicadas directamente por Open-Meteo.
DAILY_VARS = [
    "weather_code",
    "temperature_2m_mean",
    "temperature_2m_max",
    "temperature_2m_min",
    "precipitation_sum",
    "precipitation_probability_max",
    "sunshine_duration",
    "shortwave_radiation_sum",
    "et0_fao_evapotranspiration",
]

# Las variables de suelo y VPD se solicitan por hora y luego se agregan
# localmente por día, porque el Forecast API las documenta como horarias.
HOURLY_VARS = [
    "relative_humidity_2m",
    "vapour_pressure_deficit",
    "soil_moisture_0_to_1cm",
    "soil_moisture_1_to_3cm",
    "soil_moisture_3_to_9cm",
    "soil_moisture_9_to_27cm",
    "soil_moisture_27_to_81cm",
    "soil_temperature_0cm",
    "soil_temperature_6cm",
    "soil_temperature_18cm",
    "soil_temperature_54cm",
]

MUNICIPIOS = [
    {"id": "solola", "nombre": "Sololá", "lat": 14.7739, "lon": -91.1833},
    {"id": "concepcion", "nombre": "Concepción", "lat": 14.7833, "lon": -91.1500},
    {"id": "nahuala", "nombre": "Nahualá", "lat": 14.8417, "lon": -91.3167},
    {"id": "panajachel", "nombre": "Panajachel", "lat": 14.7419, "lon": -91.1592},
    {"id": "san_andres_semetabaj", "nombre": "San Andrés Semetabaj", "lat": 14.7444, "lon": -91.1333},
    {"id": "san_antonio_palopo", "nombre": "San Antonio Palopó", "lat": 14.6925, "lon": -91.1167},
    {"id": "san_jose_chacaya", "nombre": "San José Chacayá", "lat": 14.7714, "lon": -91.2144},
    {"id": "san_juan_la_laguna", "nombre": "San Juan La Laguna", "lat": 14.6947, "lon": -91.2867},
    {"id": "san_lucas_toliman", "nombre": "San Lucas Tolimán", "lat": 14.6319, "lon": -91.1425},
    {"id": "san_marcos_la_laguna", "nombre": "San Marcos La Laguna", "lat": 14.7250, "lon": -91.2583},
    {"id": "san_pablo_la_laguna", "nombre": "San Pablo La Laguna", "lat": 14.7208, "lon": -91.2722},
    {"id": "san_pedro_la_laguna", "nombre": "San Pedro La Laguna", "lat": 14.6928, "lon": -91.2722},
    {"id": "santa_catarina_ixtahuacan", "nombre": "Santa Catarina Ixtahuacán", "lat": 14.7972, "lon": -91.3608},
    {"id": "santa_catarina_palopo", "nombre": "Santa Catarina Palopó", "lat": 14.7236, "lon": -91.1347},
    {"id": "santa_clara_la_laguna", "nombre": "Santa Clara La Laguna", "lat": 14.7153, "lon": -91.3036},
    {"id": "santa_cruz_la_laguna", "nombre": "Santa Cruz La Laguna", "lat": 14.7431, "lon": -91.2072},
    {"id": "santa_lucia_utatlan", "nombre": "Santa Lucía Utatlán", "lat": 14.7700, "lon": -91.2667},
    {"id": "santa_maria_visitacion", "nombre": "Santa María Visitación", "lat": 14.7178, "lon": -91.3089},
    {"id": "santiago_atitlan", "nombre": "Santiago Atitlán", "lat": 14.6386, "lon": -91.2292},
]

SESSION = requests.Session()
SESSION.headers.update(
    {
        "User-Agent": "MTA-Solola-Agroclima/1.0",
        "Accept": "application/json",
    }
)


def now_gt() -> datetime:
    """Devuelve la fecha y hora actual en Guatemala."""
    return datetime.now(TZ_GT)


def now_utc() -> datetime:
    """Devuelve la fecha y hora actual en UTC."""
    return datetime.now(timezone.utc)


def clean(value: Any, digits: int = 3) -> Optional[float]:
    """Convierte valores numéricos y elimina nulos o NaN."""
    if value is None or value == "":
        return None

    try:
        number = float(value)
    except (TypeError, ValueError):
        return None

    if number != number:
        return None

    return round(number, digits)


def average(values: Iterable[Optional[float]], digits: int = 3) -> Optional[float]:
    """Promedio de valores válidos."""
    valid = [float(value) for value in values if value is not None]
    return round(mean(valid), digits) if valid else None


def maximum(values: Iterable[Optional[float]], digits: int = 2) -> Optional[float]:
    """Máximo de valores válidos."""
    valid = [float(value) for value in values if value is not None]
    return round(max(valid), digits) if valid else None


def minimum(values: Iterable[Optional[float]], digits: int = 2) -> Optional[float]:
    """Mínimo de valores válidos."""
    valid = [float(value) for value in values if value is not None]
    return round(min(valid), digits) if valid else None


def sum_values(values: Iterable[Optional[float]], digits: int = 2) -> Optional[float]:
    """Suma de valores válidos."""
    valid = [float(value) for value in values if value is not None]
    return round(sum(valid), digits) if valid else None


def weighted_profile(
    layers: Iterable[Tuple[Optional[float], float]],
    digits: int = 3,
) -> Optional[float]:
    """Promedio ponderado por el espesor aproximado de cada capa."""
    valid = [
        (float(value), float(depth))
        for value, depth in layers
        if value is not None and depth > 0
    ]

    if not valid:
        return None

    numerator = sum(value * depth for value, depth in valid)
    denominator = sum(depth for _, depth in valid)
    return round(numerator / denominator, digits)


def balance_category(value: Optional[float]) -> Optional[str]:
    """Clasificación descriptiva del balance diario P - ET0."""
    if value is None:
        return None
    if value <= -5:
        return "déficit alto"
    if value < -2:
        return "déficit moderado"
    if value <= 2:
        return "equilibrado"
    if value < 10:
        return "exceso moderado"
    return "exceso alto"


def vpd_category(value: Optional[float]) -> Optional[str]:
    """Clasificación general del VPD máximo diario."""
    if value is None:
        return None
    if value < 0.4:
        return "bajo / baja transpiración"
    if value <= 1.6:
        return "intermedio"
    return "alto"


def stress_level(
    balance: Optional[float],
    vpd_max: Optional[float],
    dry_streak: Optional[int],
) -> Optional[str]:
    """
    Indicador orientativo, no diagnóstico agronómico.

    Combina déficit climático, VPD y días secos consecutivos.
    No usa umbrales de humedad de suelo porque dependen de su textura.
    """
    if balance is None and vpd_max is None and dry_streak is None:
        return None

    score = 0

    if balance is not None:
        if balance <= -5:
            score += 2
        elif balance < 0:
            score += 1

    if vpd_max is not None:
        if vpd_max > 1.6:
            score += 2
        elif vpd_max > 1.2:
            score += 1

    if dry_streak is not None:
        if dry_streak >= 5:
            score += 2
        elif dry_streak >= 3:
            score += 1

    if score >= 4:
        return "alto"
    if score >= 2:
        return "moderado"
    return "bajo"


def request_json(params: Dict[str, Any]) -> Dict[str, Any]:
    """Consulta Open-Meteo con reintentos."""
    last_error: Optional[str] = None

    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            response = SESSION.get(
                API_URL,
                params=params,
                timeout=REQUEST_TIMEOUT,
            )
            response.raise_for_status()
            data = response.json()

            if not isinstance(data, dict):
                raise RuntimeError("Open-Meteo no devolvió un objeto JSON.")

            if data.get("error"):
                raise RuntimeError(
                    str(data.get("reason") or "Open-Meteo devolvió error=true.")
                )

            return data

        except Exception as exc:
            last_error = str(exc)
            print(
                f"Intento {attempt}/{MAX_ATTEMPTS} falló: {last_error}",
                file=sys.stderr,
            )

            if attempt < MAX_ATTEMPTS:
                time.sleep(3 * attempt)

    raise RuntimeError(last_error or "No se pudo consultar Open-Meteo.")


def build_params(municipio: Dict[str, Any]) -> Dict[str, Any]:
    """Construye los parámetros de la consulta municipal."""
    params: Dict[str, Any] = {
        "latitude": municipio["lat"],
        "longitude": municipio["lon"],
        "daily": ",".join(DAILY_VARS),
        "hourly": ",".join(HOURLY_VARS),
        "timezone": TIMEZONE,
        "forecast_days": FORECAST_DAYS,
        "temperature_unit": "celsius",
        "precipitation_unit": "mm",
        "timeformat": "iso8601",
        "cell_selection": "land",
    }

    if MODEL:
        params["models"] = MODEL

    return params


def index_value(values: List[Any], index: int, digits: int = 3) -> Optional[float]:
    """Obtiene de forma segura un valor de una serie."""
    if index >= len(values):
        return None
    return clean(values[index], digits)


def group_hourly_by_day(hourly: Dict[str, Any]) -> Dict[str, Dict[str, List[float]]]:
    """Agrupa las variables horarias por fecha local."""
    times = hourly.get("time") or []
    grouped: DefaultDict[str, DefaultDict[str, List[float]]] = defaultdict(
        lambda: defaultdict(list)
    )

    for index, timestamp in enumerate(times):
        if not timestamp:
            continue

        day = str(timestamp)[:10]

        for variable in HOURLY_VARS:
            values = hourly.get(variable) or []
            value = index_value(values, index, 4)
            if value is not None:
                grouped[day][variable].append(value)

    return {
        day: {variable: values for variable, values in variables.items()}
        for day, variables in grouped.items()
    }


def aggregate_hourly_day(
    variables: Dict[str, List[float]],
) -> Dict[str, Optional[float]]:
    """Calcula agregados diarios a partir de las horas disponibles."""
    sm_0_1 = average(variables.get("soil_moisture_0_to_1cm", []), 3)
    sm_1_3 = average(variables.get("soil_moisture_1_to_3cm", []), 3)
    sm_3_9 = average(variables.get("soil_moisture_3_to_9cm", []), 3)
    sm_9_27 = average(variables.get("soil_moisture_9_to_27cm", []), 3)
    sm_27_81 = average(variables.get("soil_moisture_27_to_81cm", []), 3)

    soil_profile = weighted_profile(
        [
            (sm_0_1, 1.0),
            (sm_1_3, 2.0),
            (sm_3_9, 6.0),
            (sm_9_27, 18.0),
            (sm_27_81, 54.0),
        ],
        digits=3,
    )

    st_0 = average(variables.get("soil_temperature_0cm", []), 2)
    st_6 = average(variables.get("soil_temperature_6cm", []), 2)
    st_18 = average(variables.get("soil_temperature_18cm", []), 2)
    st_54 = average(variables.get("soil_temperature_54cm", []), 2)

    soil_temperature_profile = weighted_profile(
        [
            (st_0, 1.0),
            (st_6, 8.0),
            (st_18, 24.0),
            (st_54, 48.0),
        ],
        digits=2,
    )

    return {
        "humedad_relativa_media_pct": average(
            variables.get("relative_humidity_2m", []),
            1,
        ),
        "humedad_relativa_minima_pct": minimum(
            variables.get("relative_humidity_2m", []),
            1,
        ),
        "vpd_medio_kpa": average(
            variables.get("vapour_pressure_deficit", []),
            2,
        ),
        "vpd_max_kpa": maximum(
            variables.get("vapour_pressure_deficit", []),
            2,
        ),
        "humedad_suelo_0_1cm_m3_m3": sm_0_1,
        "humedad_suelo_1_3cm_m3_m3": sm_1_3,
        "humedad_suelo_3_9cm_m3_m3": sm_3_9,
        "humedad_suelo_9_27cm_m3_m3": sm_9_27,
        "humedad_suelo_27_81cm_m3_m3": sm_27_81,
        "humedad_suelo_0_81cm_m3_m3": soil_profile,
        "temperatura_suelo_0cm_c": st_0,
        "temperatura_suelo_6cm_c": st_6,
        "temperatura_suelo_18cm_c": st_18,
        "temperatura_suelo_54cm_c": st_54,
        "temperatura_suelo_perfil_c": soil_temperature_profile,
    }


def normalize_records(data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Combina variables diarias y agregados horarios."""
    daily = data.get("daily") or {}
    dates = daily.get("time") or []
    hourly_by_day = group_hourly_by_day(data.get("hourly") or {})

    series: Dict[str, List[Any]] = {
        variable: daily.get(variable) or []
        for variable in DAILY_VARS
    }

    records: List[Dict[str, Any]] = []
    accumulated_balance = 0.0
    dry_streak = 0

    for index, day_value in enumerate(dates):
        day = str(day_value)

        precipitation = index_value(series["precipitation_sum"], index, 2)
        et0 = index_value(series["et0_fao_evapotranspiration"], index, 2)

        balance = (
            round(precipitation - et0, 2)
            if precipitation is not None and et0 is not None
            else None
        )

        if balance is not None:
            accumulated_balance = round(accumulated_balance + balance, 2)

        if precipitation is None:
            dry_day: Optional[bool] = None
            streak_value: Optional[int] = None
        else:
            dry_day = precipitation < DRY_THRESHOLD_MM
            dry_streak = dry_streak + 1 if dry_day else 0
            streak_value = dry_streak

        hourly_summary = aggregate_hourly_day(hourly_by_day.get(day, {}))
        vpd_max = hourly_summary.get("vpd_max_kpa")

        sunshine_seconds = index_value(series["sunshine_duration"], index, 0)
        weather_code = index_value(series["weather_code"], index, 0)

        record: Dict[str, Any] = {
            "fecha": day,
            "codigo_tiempo_wmo": int(weather_code) if weather_code is not None else None,
            "temperatura_media_c": index_value(series["temperature_2m_mean"], index, 2),
            "temperatura_maxima_c": index_value(series["temperature_2m_max"], index, 2),
            "temperatura_minima_c": index_value(series["temperature_2m_min"], index, 2),
            "precipitacion_mm": precipitation,
            "probabilidad_precipitacion_max_pct": index_value(
                series["precipitation_probability_max"],
                index,
                1,
            ),
            "et0_mm": et0,
            "balance_hidrico_mm": balance,
            "balance_hidrico_acumulado_mm": (
                accumulated_balance if balance is not None else None
            ),
            "deficit_hidrico_mm": (
                round(max(0.0, et0 - precipitation), 2)
                if balance is not None
                else None
            ),
            "exceso_hidrico_mm": (
                round(max(0.0, precipitation - et0), 2)
                if balance is not None
                else None
            ),
            "categoria_balance": balance_category(balance),
            "dia_seco": dry_day,
            "dias_secos_consecutivos": streak_value,
            "radiacion_solar_mj_m2": index_value(
                series["shortwave_radiation_sum"],
                index,
                2,
            ),
            "horas_sol": (
                round(sunshine_seconds / 3600.0, 2)
                if sunshine_seconds is not None
                else None
            ),
            **hourly_summary,
            "categoria_vpd": vpd_category(vpd_max),
            "nivel_estres_hidrico_orientativo": stress_level(
                balance,
                vpd_max,
                streak_value,
            ),
        }

        records.append(record)

    return records


def municipal_summary(records: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Resumen del periodo de pronóstico para un municipio."""
    return {
        "dias": len(records),
        "fecha_inicio": records[0]["fecha"] if records else None,
        "fecha_fin": records[-1]["fecha"] if records else None,
        "precipitacion_total_mm": sum_values(
            record.get("precipitacion_mm") for record in records
        ),
        "et0_total_mm": sum_values(record.get("et0_mm") for record in records),
        "balance_hidrico_total_mm": sum_values(
            record.get("balance_hidrico_mm") for record in records
        ),
        "deficit_hidrico_total_mm": sum_values(
            record.get("deficit_hidrico_mm") for record in records
        ),
        "exceso_hidrico_total_mm": sum_values(
            record.get("exceso_hidrico_mm") for record in records
        ),
        "vpd_maximo_kpa": maximum(record.get("vpd_max_kpa") for record in records),
        "humedad_suelo_superficial_media_m3_m3": average(
            record.get("humedad_suelo_0_1cm_m3_m3") for record in records
        ),
        "humedad_suelo_perfil_media_m3_m3": average(
            record.get("humedad_suelo_0_81cm_m3_m3") for record in records
        ),
        "radiacion_solar_total_mj_m2": sum_values(
            record.get("radiacion_solar_mj_m2") for record in records
        ),
        "horas_sol_total": sum_values(record.get("horas_sol") for record in records),
        "max_dias_secos_consecutivos": int(
            maximum(
                (record.get("dias_secos_consecutivos") for record in records),
                0,
            )
            or 0
        ),
        "dias_con_deficit": sum(
            1
            for record in records
            if record.get("balance_hidrico_mm") is not None
            and record["balance_hidrico_mm"] < 0
        ),
        "dias_estres_alto_orientativo": sum(
            1
            for record in records
            if record.get("nivel_estres_hidrico_orientativo") == "alto"
        ),
    }


def fetch_municipio(
    municipio: Dict[str, Any],
) -> Tuple[Dict[str, Any], Dict[str, Any], Dict[str, Any]]:
    """Descarga y normaliza el pronóstico de un municipio."""
    try:
        data = request_json(build_params(municipio))

        daily = data.get("daily") or {}
        if not daily.get("time"):
            raise RuntimeError("La respuesta no contiene daily.time.")

        records = normalize_records(data)

        location = {
            "latitude_resuelta": clean(data.get("latitude"), 5),
            "longitude_resuelta": clean(data.get("longitude"), 5),
            "elevation_m": clean(data.get("elevation"), 1),
            "timezone": data.get("timezone"),
            "timezone_abbreviation": data.get("timezone_abbreviation"),
        }

        result = {
            "id": municipio["id"],
            "nombre": municipio["nombre"],
            "lat": municipio["lat"],
            "lon": municipio["lon"],
            **location,
            "status": "ok" if records else "error",
            "error": None if records else "No se construyeron registros.",
            "resumen": municipal_summary(records),
            "registros": records,
        }

        return (
            result,
            data.get("daily_units") or {},
            data.get("hourly_units") or {},
        )

    except Exception as exc:
        return (
            {
                "id": municipio["id"],
                "nombre": municipio["nombre"],
                "lat": municipio["lat"],
                "lon": municipio["lon"],
                "status": "error",
                "error": str(exc),
                "resumen": municipal_summary([]),
                "registros": [],
            },
            {},
            {},
        )


def general_summary(municipios: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Resumen general del archivo municipal."""
    dates = sorted(
        {
            record["fecha"]
            for municipio in municipios
            for record in municipio.get("registros", [])
        }
    )

    return {
        "municipios_total": len(municipios),
        "municipios_con_datos": sum(
            bool(municipio.get("registros")) for municipio in municipios
        ),
        "municipios_con_error": sum(
            municipio.get("status") == "error" for municipio in municipios
        ),
        "fecha_inicio": dates[0] if dates else None,
        "fecha_fin": dates[-1] if dates else None,
        "dias": len(dates),
        "forecast_days_solicitados": FORECAST_DAYS,
        "umbral_dia_seco_mm": DRY_THRESHOLD_MM,
    }


def main() -> None:
    """Ejecuta el pronóstico para los 19 municipios de Sololá."""
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    municipios_out: List[Dict[str, Any]] = []
    daily_units: Dict[str, Any] = {}
    hourly_units: Dict[str, Any] = {}

    for index, municipio in enumerate(MUNICIPIOS, start=1):
        print(
            f"[{index:02d}/{len(MUNICIPIOS)}] "
            f"Descargando pronóstico: {municipio['nombre']}"
        )

        result, result_daily_units, result_hourly_units = fetch_municipio(municipio)
        municipios_out.append(result)

        if result_daily_units and not daily_units:
            daily_units = result_daily_units
        if result_hourly_units and not hourly_units:
            hourly_units = result_hourly_units

        print(
            f"  Estado: {result['status']} | "
            f"Registros: {len(result['registros'])}"
        )

        if result.get("error"):
            print(f"  Error: {result['error']}", file=sys.stderr)

        if index < len(MUNICIPIOS):
            time.sleep(DELAY_SECONDS)

    payload = {
        "ok": any(municipio.get("registros") for municipio in municipios_out),
        "generated_at_gt": now_gt().isoformat(timespec="seconds"),
        "generated_at_utc": now_utc().isoformat(timespec="seconds"),
        "source": {
            "name": "Open-Meteo Weather Forecast API",
            "url": API_URL,
            "timezone": TIMEZONE,
            "model": MODEL or "best_match automático",
            "forecast_days": FORECAST_DAYS,
            "daily_variables": DAILY_VARS,
            "hourly_variables": HOURLY_VARS,
            "daily_units_reported_by_api": daily_units,
            "hourly_units_reported_by_api": hourly_units,
            "note": (
                "Balance climático simple = precipitación prevista - ET0. "
                "No incluye coeficiente de cultivo, escorrentía, infiltración "
                "ni almacenamiento real del suelo."
            ),
            "soil_note": (
                "La humedad y temperatura del suelo provienen del modelo "
                "meteorológico y se agregan de valores horarios; no sustituyen "
                "mediciones de campo."
            ),
            "stress_note": (
                "El nivel de estrés es un indicador orientativo construido con "
                "balance P-ET0, VPD y días secos consecutivos; no es una alerta "
                "agronómica específica por cultivo."
            ),
        },
        "resumen": general_summary(municipios_out),
        "municipios": municipios_out,
    }

    OUTPUT_PATH.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print(f"OK: {OUTPUT_PATH} generado")
    print(json.dumps(payload["resumen"], ensure_ascii=False, indent=2))

    if not payload["ok"]:
        raise RuntimeError("No se obtuvieron datos para ningún municipio.")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(1)
