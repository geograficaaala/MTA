#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Descarga datos diarios de temperatura y humedad relativa para los 19 municipios
de Sololá usando NASA POWER Agroclimatology API.

Salida:
  docs/data/temperatura/historico_municipios.json

Variables NASA POWER:
  T2M       Temperatura media a 2 m, grados Celsius
  T2M_MAX   Temperatura máxima a 2 m, grados Celsius
  T2M_MIN   Temperatura mínima a 2 m, grados Celsius
  T2M_RANGE Rango térmico diario, grados Celsius
  RH2M      Humedad relativa a 2 m, porcentaje
"""

from __future__ import annotations

import json
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

import requests
from zoneinfo import ZoneInfo


API_URL = "https://power.larc.nasa.gov/api/temporal/daily/point"
OUTPUT_PATH = Path("docs/data/temperatura/historico_municipios.json")
START_DATE = "20260101"
PARAMETERS = ["T2M", "T2M_MAX", "T2M_MIN", "T2M_RANGE", "RH2M"]

# Coordenadas aproximadas de cabeceras/centroides municipales de Sololá.
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


def gt_now() -> datetime:
    return datetime.now(ZoneInfo("America/Guatemala"))


def nasa_end_date() -> str:
    """NASA POWER puede tener rezago. Usamos ayer como fecha final inicial."""
    return (gt_now().date() - timedelta(days=1)).strftime("%Y%m%d")


def clean_number(value: Any) -> Optional[float]:
    if value is None:
        return None

    try:
        number = float(value)
    except (TypeError, ValueError):
        return None

    # NASA POWER usa valores tipo -999 cuando falta información.
    if number <= -900:
        return None

    return round(number, 2)


def iso_date(yyyymmdd: str) -> str:
    return f"{yyyymmdd[0:4]}-{yyyymmdd[4:6]}-{yyyymmdd[6:8]}"


def fetch_municipio(mun: Dict[str, Any], end_date: str) -> Dict[str, Any]:
    params = {
        "parameters": ",".join(PARAMETERS),
        "community": "AG",
        "longitude": mun["lon"],
        "latitude": mun["lat"],
        "start": START_DATE,
        "end": end_date,
        "format": "JSON",
        "time-standard": "UTC",
    }

    last_error: Optional[str] = None

    for attempt in range(1, 4):
        try:
            response = requests.get(API_URL, params=params, timeout=40)
            response.raise_for_status()
            payload = response.json()

            parameter_data = payload.get("properties", {}).get("parameter", {})
            if not parameter_data:
                raise RuntimeError("La respuesta de NASA POWER no contiene properties.parameter")

            fechas = sorted({
                fecha
                for serie in parameter_data.values()
                for fecha in serie.keys()
            })

            registros: List[Dict[str, Any]] = []

            for fecha in fechas:
                t_media = clean_number(parameter_data.get("T2M", {}).get(fecha))
                t_max = clean_number(parameter_data.get("T2M_MAX", {}).get(fecha))
                t_min = clean_number(parameter_data.get("T2M_MIN", {}).get(fecha))
                rango = clean_number(parameter_data.get("T2M_RANGE", {}).get(fecha))
                rh = clean_number(parameter_data.get("RH2M", {}).get(fecha))

                # No guardar filas completamente vacías.
                if all(v is None for v in [t_media, t_max, t_min, rango, rh]):
                    continue

                registros.append({
                    "fecha": iso_date(fecha),
                    "t_media_c": t_media,
                    "t_max_c": t_max,
                    "t_min_c": t_min,
                    "rango_c": rango,
                    "humedad_relativa_pct": rh,
                })

            return {
                "id": mun["id"],
                "nombre": mun["nombre"],
                "lat": mun["lat"],
                "lon": mun["lon"],
                "registros": registros,
                "status": "ok",
                "error": None,
            }

        except Exception as exc:
            last_error = str(exc)
            print(f"Intento {attempt}/3 falló para {mun['nombre']}: {last_error}")
            time.sleep(2 * attempt)

    return {
        "id": mun["id"],
        "nombre": mun["nombre"],
        "lat": mun["lat"],
        "lon": mun["lon"],
        "registros": [],
        "status": "error",
        "error": last_error or "Error desconocido",
    }


def build_resumen(municipios: List[Dict[str, Any]]) -> Dict[str, Any]:
    all_dates = sorted({
        r["fecha"]
        for m in municipios
        for r in m.get("registros", [])
    })

    ok_count = sum(
        1
        for m in municipios
        if m.get("status") == "ok" and m.get("registros")
    )

    return {
        "municipios_total": len(municipios),
        "municipios_con_datos": ok_count,
        "fecha_inicio": all_dates[0] if all_dates else None,
        "fecha_fin": all_dates[-1] if all_dates else None,
        "dias": len(all_dates),
        "variables": {
            "t_media_c": "Temperatura media diaria a 2 m en grados Celsius",
            "t_max_c": "Temperatura máxima diaria a 2 m en grados Celsius",
            "t_min_c": "Temperatura mínima diaria a 2 m en grados Celsius",
            "rango_c": "Rango térmico diario en grados Celsius",
            "humedad_relativa_pct": "Humedad relativa diaria a 2 m en porcentaje",
        },
    }


def main() -> None:
    generated_at_gt = gt_now().isoformat(timespec="seconds")
    generated_at_utc = datetime.now(timezone.utc).isoformat(timespec="seconds")
    end_date = nasa_end_date()

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    municipios_out: List[Dict[str, Any]] = []

    for idx, municipio in enumerate(MUNICIPIOS, start=1):
        print(f"[{idx:02d}/{len(MUNICIPIOS)}] Descargando temperatura NASA POWER: {municipio['nombre']}")
        municipios_out.append(fetch_municipio(municipio, end_date))

    payload = {
        "ok": any(m.get("registros") for m in municipios_out),
        "generated_at_gt": generated_at_gt,
        "generated_at_utc": generated_at_utc,
        "source": {
            "name": "NASA POWER Agroclimatology API",
            "url": API_URL,
            "community": "AG",
            "parameters": PARAMETERS,
            "start": START_DATE,
            "end": end_date,
        },
        "resumen": build_resumen(municipios_out),
        "municipios": municipios_out,
    }

    OUTPUT_PATH.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print(f"OK temperatura NASA POWER escrita en: {OUTPUT_PATH}")
    print(json.dumps(payload["resumen"], ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
