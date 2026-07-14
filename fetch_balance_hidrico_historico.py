#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Histórico municipal de balance hídrico y variables agroclimáticas.
Fuente: Open-Meteo Historical Weather API.
No utiliza Ambient Weather Network (AWN).

Salida:
  docs/data/agroclima/historico_municipios.json
"""

from __future__ import annotations

import json
import os
import sys
import time
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from statistics import mean
from typing import Any, Dict, Iterable, List, Optional, Tuple
from zoneinfo import ZoneInfo

import requests


API_URL = "https://archive-api.open-meteo.com/v1/archive"
OUTPUT_PATH = Path("docs/data/agroclima/historico_municipios.json")
TIMEZONE = os.getenv("OPENMETEO_TIMEZONE", "America/Guatemala")
TZ_GT = ZoneInfo(TIMEZONE)
START_DATE = os.getenv("AGROCLIMA_START_DATE", "2026-01-01")
DELAY_DAYS = max(1, int(os.getenv("AGROCLIMA_ARCHIVE_DELAY_DAYS", "5")))
DRY_THRESHOLD_MM = max(0.0, float(os.getenv("AGROCLIMA_DRY_DAY_THRESHOLD_MM", "1.0")))
MODEL = os.getenv("OPENMETEO_ARCHIVE_MODEL", "").strip()
TIMEOUT = 60
MAX_ATTEMPTS = 4

CORE_VARS = [
    "precipitation_sum",
    "et0_fao_evapotranspiration",
    "shortwave_radiation_sum",
    "sunshine_duration",
    "vapour_pressure_deficit_max",
]

SOIL_VARS = [
    "soil_moisture_0_to_7cm_mean",
    "soil_moisture_7_to_28cm_mean",
    "soil_moisture_28_to_100cm_mean",
    "soil_moisture_0_to_100cm_mean",
    "soil_temperature_0_to_7cm_mean",
    "soil_temperature_7_to_28cm_mean",
    "soil_temperature_28_to_100cm_mean",
    "soil_temperature_0_to_100cm_mean",
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
SESSION.headers.update({"User-Agent": "MTA-Solola-Agroclima/1.0", "Accept": "application/json"})


def now_gt() -> datetime:
    return datetime.now(TZ_GT)


def clean(value: Any, digits: int = 3) -> Optional[float]:
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
    valid = [float(v) for v in values if v is not None]
    return round(mean(valid), digits) if valid else None


def maximum(values: Iterable[Optional[float]], digits: int = 2) -> Optional[float]:
    valid = [float(v) for v in values if v is not None]
    return round(max(valid), digits) if valid else None


def sum_values(values: Iterable[Optional[float]], digits: int = 2) -> Optional[float]:
    valid = [float(v) for v in values if v is not None]
    return round(sum(valid), digits) if valid else None


def weighted_profile(a: Optional[float], b: Optional[float], c: Optional[float], digits: int) -> Optional[float]:
    layers = [(a, 7.0), (b, 21.0), (c, 72.0)]
    valid = [(v, depth) for v, depth in layers if v is not None]
    if not valid:
        return None
    return round(sum(float(v) * depth for v, depth in valid) / sum(depth for _, depth in valid), digits)


def balance_category(value: Optional[float]) -> Optional[str]:
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
    if value is None:
        return None
    if value < 0.4:
        return "bajo / baja transpiración"
    if value <= 1.6:
        return "intermedio"
    return "alto"


def request_json(params: Dict[str, Any]) -> Dict[str, Any]:
    last_error: Optional[str] = None
    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            response = SESSION.get(API_URL, params=params, timeout=TIMEOUT)
            response.raise_for_status()
            data = response.json()
            if not isinstance(data, dict):
                raise RuntimeError("Open-Meteo no devolvió un objeto JSON.")
            if data.get("error"):
                raise RuntimeError(str(data.get("reason") or "Open-Meteo devolvió error=true."))
            return data
        except Exception as exc:
            last_error = str(exc)
            print(f"Intento {attempt}/{MAX_ATTEMPTS} falló: {last_error}", file=sys.stderr)
            if attempt < MAX_ATTEMPTS:
                time.sleep(3 * attempt)
    raise RuntimeError(last_error or "No se pudo consultar Open-Meteo.")


def fetch_group(
    municipio: Dict[str, Any], variables: List[str], start_date: str, end_date: str
) -> Tuple[Dict[str, Dict[str, Optional[float]]], Dict[str, Any], Dict[str, Any]]:
    params: Dict[str, Any] = {
        "latitude": municipio["lat"],
        "longitude": municipio["lon"],
        "start_date": start_date,
        "end_date": end_date,
        "daily": ",".join(variables),
        "timezone": TIMEZONE,
        "temperature_unit": "celsius",
        "precipitation_unit": "mm",
        "timeformat": "iso8601",
        "cell_selection": "land",
    }
    if MODEL:
        params["models"] = MODEL

    data = request_json(params)
    daily = data.get("daily") or {}
    dates = daily.get("time") or []
    if not dates:
        raise RuntimeError("La respuesta no contiene daily.time.")

    rows: Dict[str, Dict[str, Optional[float]]] = {}
    for index, day in enumerate(dates):
        row: Dict[str, Optional[float]] = {}
        for variable in variables:
            values = daily.get(variable) or []
            row[variable] = clean(values[index] if index < len(values) else None)
        rows[str(day)] = row

    location = {
        "latitude_resuelta": clean(data.get("latitude"), 5),
        "longitude_resuelta": clean(data.get("longitude"), 5),
        "elevation_m": clean(data.get("elevation"), 1),
        "timezone": data.get("timezone"),
    }
    return rows, data.get("daily_units") or {}, location


def normalize_records(
    core: Dict[str, Dict[str, Optional[float]]],
    soil: Dict[str, Dict[str, Optional[float]]],
) -> List[Dict[str, Any]]:
    records: List[Dict[str, Any]] = []
    accumulated = 0.0
    dry_streak = 0

    for day in sorted(set(core) | set(soil)):
        raw = {**core.get(day, {}), **soil.get(day, {})}
        precipitation = clean(raw.get("precipitation_sum"), 2)
        et0 = clean(raw.get("et0_fao_evapotranspiration"), 2)
        balance = round(precipitation - et0, 2) if precipitation is not None and et0 is not None else None

        if balance is not None:
            accumulated = round(accumulated + balance, 2)

        if precipitation is None:
            is_dry = None
        else:
            is_dry = precipitation < DRY_THRESHOLD_MM
            dry_streak = dry_streak + 1 if is_dry else 0

        sm_0_7 = clean(raw.get("soil_moisture_0_to_7cm_mean"), 3)
        sm_7_28 = clean(raw.get("soil_moisture_7_to_28cm_mean"), 3)
        sm_28_100 = clean(raw.get("soil_moisture_28_to_100cm_mean"), 3)
        sm_0_100 = clean(raw.get("soil_moisture_0_to_100cm_mean"), 3)
        if sm_0_100 is None:
            sm_0_100 = weighted_profile(sm_0_7, sm_7_28, sm_28_100, 3)

        st_0_7 = clean(raw.get("soil_temperature_0_to_7cm_mean"), 2)
        st_7_28 = clean(raw.get("soil_temperature_7_to_28cm_mean"), 2)
        st_28_100 = clean(raw.get("soil_temperature_28_to_100cm_mean"), 2)
        st_0_100 = clean(raw.get("soil_temperature_0_to_100cm_mean"), 2)
        if st_0_100 is None:
            st_0_100 = weighted_profile(st_0_7, st_7_28, st_28_100, 2)

        sunshine_seconds = clean(raw.get("sunshine_duration"), 0)
        vpd = clean(raw.get("vapour_pressure_deficit_max"), 2)

        records.append({
            "fecha": day,
            "precipitacion_mm": precipitation,
            "et0_mm": et0,
            "balance_hidrico_mm": balance,
            "balance_hidrico_acumulado_mm": accumulated if balance is not None else None,
            "deficit_hidrico_mm": round(max(0.0, et0 - precipitation), 2) if balance is not None else None,
            "exceso_hidrico_mm": round(max(0.0, precipitation - et0), 2) if balance is not None else None,
            "categoria_balance": balance_category(balance),
            "dia_seco": is_dry,
            "dias_secos_consecutivos": dry_streak if precipitation is not None else None,
            "radiacion_solar_mj_m2": clean(raw.get("shortwave_radiation_sum"), 2),
            "horas_sol": round(sunshine_seconds / 3600, 2) if sunshine_seconds is not None else None,
            "vpd_max_kpa": vpd,
            "categoria_vpd": vpd_category(vpd),
            "humedad_suelo_0_7cm_m3_m3": sm_0_7,
            "humedad_suelo_7_28cm_m3_m3": sm_7_28,
            "humedad_suelo_28_100cm_m3_m3": sm_28_100,
            "humedad_suelo_0_100cm_m3_m3": sm_0_100,
            "temperatura_suelo_0_7cm_c": st_0_7,
            "temperatura_suelo_7_28cm_c": st_7_28,
            "temperatura_suelo_28_100cm_c": st_28_100,
            "temperatura_suelo_0_100cm_c": st_0_100,
        })
    return records


def municipal_summary(records: List[Dict[str, Any]]) -> Dict[str, Any]:
    return {
        "dias": len(records),
        "fecha_inicio": records[0]["fecha"] if records else None,
        "fecha_fin": records[-1]["fecha"] if records else None,
        "precipitacion_total_mm": sum_values(r.get("precipitacion_mm") for r in records),
        "et0_total_mm": sum_values(r.get("et0_mm") for r in records),
        "balance_hidrico_total_mm": sum_values(r.get("balance_hidrico_mm") for r in records),
        "deficit_hidrico_total_mm": sum_values(r.get("deficit_hidrico_mm") for r in records),
        "exceso_hidrico_total_mm": sum_values(r.get("exceso_hidrico_mm") for r in records),
        "vpd_maximo_kpa": maximum(r.get("vpd_max_kpa") for r in records),
        "humedad_suelo_superficial_media_m3_m3": average(r.get("humedad_suelo_0_7cm_m3_m3") for r in records),
        "humedad_suelo_perfil_media_m3_m3": average(r.get("humedad_suelo_0_100cm_m3_m3") for r in records),
        "radiacion_solar_total_mj_m2": sum_values(r.get("radiacion_solar_mj_m2") for r in records),
        "horas_sol_total": sum_values(r.get("horas_sol") for r in records),
        "max_dias_secos_consecutivos": int(
            maximum((r.get("dias_secos_consecutivos") for r in records), 0) or 0
        ),
    }


def fetch_municipio(municipio: Dict[str, Any], start_date: str, end_date: str) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    warnings: List[str] = []
    core: Dict[str, Dict[str, Optional[float]]] = {}
    soil: Dict[str, Dict[str, Optional[float]]] = {}
    units: Dict[str, Any] = {}
    location: Dict[str, Any] = {}

    try:
        core, core_units, location = fetch_group(municipio, CORE_VARS, start_date, end_date)
        units.update(core_units)
    except Exception as exc:
        warnings.append(f"Variables hídricas y solares: {exc}")

    try:
        soil, soil_units, soil_location = fetch_group(municipio, SOIL_VARS, start_date, end_date)
        units.update(soil_units)
        location = location or soil_location
    except Exception as exc:
        warnings.append(f"Variables del suelo: {exc}")

    records = normalize_records(core, soil)
    status = "ok" if core and soil else "partial" if records else "error"

    return {
        "id": municipio["id"],
        "nombre": municipio["nombre"],
        "lat": municipio["lat"],
        "lon": municipio["lon"],
        **location,
        "status": status,
        "error": "; ".join(warnings) if status == "error" else None,
        "warnings": warnings,
        "resumen": municipal_summary(records),
        "registros": records,
    }, units


def general_summary(municipios: List[Dict[str, Any]]) -> Dict[str, Any]:
    dates = sorted({r["fecha"] for m in municipios for r in m.get("registros", [])})
    return {
        "municipios_total": len(municipios),
        "municipios_con_datos": sum(bool(m.get("registros")) for m in municipios),
        "municipios_completos": sum(m.get("status") == "ok" for m in municipios),
        "municipios_parciales": sum(m.get("status") == "partial" for m in municipios),
        "municipios_con_error": sum(m.get("status") == "error" for m in municipios),
        "fecha_inicio": dates[0] if dates else None,
        "fecha_fin": dates[-1] if dates else None,
        "dias": len(dates),
        "umbral_dia_seco_mm": DRY_THRESHOLD_MM,
    }


def main() -> None:
    end_date = (now_gt().date() - timedelta(days=DELAY_DAYS)).isoformat()
    if date.fromisoformat(START_DATE) > date.fromisoformat(end_date):
        raise ValueError("AGROCLIMA_START_DATE es posterior a la fecha final calculada.")

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    municipios_out: List[Dict[str, Any]] = []
    units: Dict[str, Any] = {}

    for index, municipio in enumerate(MUNICIPIOS, start=1):
        print(f"[{index:02d}/{len(MUNICIPIOS)}] Descargando: {municipio['nombre']}")
        result, result_units = fetch_municipio(municipio, START_DATE, end_date)
        municipios_out.append(result)
        units.update(result_units)
        print(f"  Estado: {result['status']} | Registros: {len(result['registros'])}")
        if index < len(MUNICIPIOS):
            time.sleep(0.6)

    payload = {
        "ok": any(m.get("registros") for m in municipios_out),
        "generated_at_gt": now_gt().isoformat(timespec="seconds"),
        "generated_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "source": {
            "name": "Open-Meteo Historical Weather API",
            "url": API_URL,
            "timezone": TIMEZONE,
            "model": MODEL or "best_match automático",
            "start": START_DATE,
            "end": end_date,
            "archive_delay_days": DELAY_DAYS,
            "daily_variables": CORE_VARS + SOIL_VARS,
            "units_reported_by_api": units,
            "note": "Balance climático simple = precipitación - ET0; no incluye coeficiente de cultivo, escorrentía, infiltración ni almacenamiento real del suelo.",
            "classification_note": "Las categorías de balance son descriptivas para el tablero y deben ajustarse por cultivo; las categorías VPD usan <0.4 kPa, 0.4-1.6 kPa y >1.6 kPa como referencia general.",
        },
        "resumen": general_summary(municipios_out),
        "municipios": municipios_out,
    }

    OUTPUT_PATH.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
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
