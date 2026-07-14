#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Descarga datos diarios de viento para los 19 municipios de Sololá usando
NASA POWER Agroclimatology API.

Salida:
  docs/data/viento/historico_municipios.json

Variables NASA POWER:
  WS10M       Velocidad media diaria del viento a 10 m
  WS10M_MAX   Velocidad máxima diaria del viento a 10 m
  WS10M_MIN   Velocidad mínima diaria del viento a 10 m
  WS10M_RANGE Rango diario de velocidad del viento a 10 m
  WD10M       Dirección media diaria del viento a 10 m

Las velocidades se convierten y almacenan en km/h.
La dirección se almacena en grados y como punto cardinal.
"""

from __future__ import annotations

import json
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from zoneinfo import ZoneInfo

import requests


API_URL = "https://power.larc.nasa.gov/api/temporal/daily/point"
OUTPUT_PATH = Path("docs/data/viento/historico_municipios.json")

START_DATE = "20260101"

PARAMETERS = [
    "WS10M",
    "WS10M_MAX",
    "WS10M_MIN",
    "WS10M_RANGE",
    "WD10M",
]

DELAY_SECONDS = 0.8
MAX_ATTEMPTS = 3
REQUEST_TIMEOUT = 45


# Coordenadas aproximadas de cabeceras/centroides municipales de Sololá.
MUNICIPIOS = [
    {
        "id": "solola",
        "nombre": "Sololá",
        "lat": 14.7739,
        "lon": -91.1833,
    },
    {
        "id": "concepcion",
        "nombre": "Concepción",
        "lat": 14.7833,
        "lon": -91.1500,
    },
    {
        "id": "nahuala",
        "nombre": "Nahualá",
        "lat": 14.8417,
        "lon": -91.3167,
    },
    {
        "id": "panajachel",
        "nombre": "Panajachel",
        "lat": 14.7419,
        "lon": -91.1592,
    },
    {
        "id": "san_andres_semetabaj",
        "nombre": "San Andrés Semetabaj",
        "lat": 14.7444,
        "lon": -91.1333,
    },
    {
        "id": "san_antonio_palopo",
        "nombre": "San Antonio Palopó",
        "lat": 14.6925,
        "lon": -91.1167,
    },
    {
        "id": "san_jose_chacaya",
        "nombre": "San José Chacayá",
        "lat": 14.7714,
        "lon": -91.2144,
    },
    {
        "id": "san_juan_la_laguna",
        "nombre": "San Juan La Laguna",
        "lat": 14.6947,
        "lon": -91.2867,
    },
    {
        "id": "san_lucas_toliman",
        "nombre": "San Lucas Tolimán",
        "lat": 14.6319,
        "lon": -91.1425,
    },
    {
        "id": "san_marcos_la_laguna",
        "nombre": "San Marcos La Laguna",
        "lat": 14.7250,
        "lon": -91.2583,
    },
    {
        "id": "san_pablo_la_laguna",
        "nombre": "San Pablo La Laguna",
        "lat": 14.7208,
        "lon": -91.2722,
    },
    {
        "id": "san_pedro_la_laguna",
        "nombre": "San Pedro La Laguna",
        "lat": 14.6928,
        "lon": -91.2722,
    },
    {
        "id": "santa_catarina_ixtahuacan",
        "nombre": "Santa Catarina Ixtahuacán",
        "lat": 14.7972,
        "lon": -91.3608,
    },
    {
        "id": "santa_catarina_palopo",
        "nombre": "Santa Catarina Palopó",
        "lat": 14.7236,
        "lon": -91.1347,
    },
    {
        "id": "santa_clara_la_laguna",
        "nombre": "Santa Clara La Laguna",
        "lat": 14.7153,
        "lon": -91.3036,
    },
    {
        "id": "santa_cruz_la_laguna",
        "nombre": "Santa Cruz La Laguna",
        "lat": 14.7431,
        "lon": -91.2072,
    },
    {
        "id": "santa_lucia_utatlan",
        "nombre": "Santa Lucía Utatlán",
        "lat": 14.7700,
        "lon": -91.2667,
    },
    {
        "id": "santa_maria_visitacion",
        "nombre": "Santa María Visitación",
        "lat": 14.7178,
        "lon": -91.3089,
    },
    {
        "id": "santiago_atitlan",
        "nombre": "Santiago Atitlán",
        "lat": 14.6386,
        "lon": -91.2292,
    },
]


def gt_now() -> datetime:
    """Devuelve la fecha y hora actual de Guatemala."""
    return datetime.now(ZoneInfo("America/Guatemala"))


def nasa_end_date() -> str:
    """NASA POWER puede tener rezago; se solicita hasta el día de ayer."""
    return (gt_now().date() - timedelta(days=1)).strftime("%Y%m%d")


def iso_date(yyyymmdd: str) -> str:
    """Convierte YYYYMMDD a YYYY-MM-DD."""
    return f"{yyyymmdd[0:4]}-{yyyymmdd[4:6]}-{yyyymmdd[6:8]}"


def clean_number(value: Any) -> Optional[float]:
    """Convierte un dato NASA a float y elimina valores ausentes."""
    if value is None:
        return None

    try:
        number = float(value)
    except (TypeError, ValueError):
        return None

    # NASA POWER usa valores cercanos a -999 para datos ausentes.
    if number <= -900:
        return None

    return number


def speed_to_kmh(
    value: Any,
    source_unit: Optional[str],
) -> Optional[float]:
    """Convierte una velocidad de NASA POWER a km/h."""
    number = clean_number(value)

    if number is None:
        return None

    unit = (
        source_unit or "m/s"
    ).strip().lower().replace(" ", "")

    if unit in {
        "m/s",
        "m/s-1",
        "ms-1",
        "meter/second",
        "meters/second",
    }:
        number *= 3.6

    elif unit in {
        "mph",
        "mi/h",
        "mile/hour",
        "miles/hour",
    }:
        number *= 1.609344

    elif unit in {
        "km/h",
        "kmhr",
        "kph",
        "kilometer/hour",
        "kilometers/hour",
    }:
        pass

    else:
        # NASA POWER normalmente entrega estas velocidades en m/s.
        number *= 3.6

    return round(number, 2)


def clean_direction(value: Any) -> Optional[float]:
    """Limpia y normaliza una dirección entre 0 y 359.9 grados."""
    number = clean_number(value)

    if number is None:
        return None

    return round(number % 360, 1)


def direction_to_cardinal(
    degrees: Optional[float],
) -> Optional[str]:
    """Convierte grados meteorológicos a uno de 16 puntos cardinales."""
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

    index = int((degrees + 11.25) // 22.5) % 16

    return directions[index]


def extract_units(
    payload: Dict[str, Any],
) -> Dict[str, Optional[str]]:
    """Extrae las unidades declaradas en el metadato de NASA POWER."""
    metadata = payload.get("parameters", {})
    units: Dict[str, Optional[str]] = {}

    for parameter in PARAMETERS:
        parameter_info = metadata.get(parameter, {})
        units[parameter] = parameter_info.get("units")

    return units


def fetch_municipio(
    municipio: Dict[str, Any],
    end_date: str,
) -> Tuple[
    Dict[str, Any],
    Dict[str, Optional[str]],
]:
    """Descarga y normaliza los datos de un municipio."""
    params = {
        "parameters": ",".join(PARAMETERS),
        "community": "AG",
        "longitude": municipio["lon"],
        "latitude": municipio["lat"],
        "start": START_DATE,
        "end": end_date,
        "format": "JSON",
        "time-standard": "UTC",
    }

    last_error: Optional[str] = None

    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            response = requests.get(
                API_URL,
                params=params,
                timeout=REQUEST_TIMEOUT,
            )

            response.raise_for_status()

            payload = response.json()

            parameter_data = (
                payload
                .get("properties", {})
                .get("parameter", {})
            )

            if not parameter_data:
                raise RuntimeError(
                    "La respuesta de NASA POWER no contiene "
                    "properties.parameter"
                )

            units = extract_units(payload)

            default_speed_unit = (
                units.get("WS10M") or "m/s"
            )

            fechas = sorted({
                fecha
                for serie in parameter_data.values()
                if isinstance(serie, dict)
                for fecha in serie.keys()
            })

            registros: List[Dict[str, Any]] = []

            for fecha in fechas:
                velocidad_media = speed_to_kmh(
                    parameter_data
                    .get("WS10M", {})
                    .get(fecha),
                    units.get("WS10M")
                    or default_speed_unit,
                )

                velocidad_maxima = speed_to_kmh(
                    parameter_data
                    .get("WS10M_MAX", {})
                    .get(fecha),
                    units.get("WS10M_MAX")
                    or default_speed_unit,
                )

                velocidad_minima = speed_to_kmh(
                    parameter_data
                    .get("WS10M_MIN", {})
                    .get(fecha),
                    units.get("WS10M_MIN")
                    or default_speed_unit,
                )

                rango_velocidad = speed_to_kmh(
                    parameter_data
                    .get("WS10M_RANGE", {})
                    .get(fecha),
                    units.get("WS10M_RANGE")
                    or default_speed_unit,
                )

                direccion = clean_direction(
                    parameter_data
                    .get("WD10M", {})
                    .get(fecha)
                )

                values = [
                    velocidad_media,
                    velocidad_maxima,
                    velocidad_minima,
                    rango_velocidad,
                    direccion,
                ]

                # No guardar filas completamente vacías.
                if all(value is None for value in values):
                    continue

                registros.append({
                    "fecha": iso_date(fecha),
                    "velocidad_media_10m_kmh": velocidad_media,
                    "velocidad_maxima_10m_kmh": velocidad_maxima,
                    "velocidad_minima_10m_kmh": velocidad_minima,
                    "rango_velocidad_10m_kmh": rango_velocidad,
                    "direccion_media_10m_grados": direccion,
                    "direccion_media_10m_cardinal":
                        direction_to_cardinal(direccion),
                })

            municipio_resultado = {
                "id": municipio["id"],
                "nombre": municipio["nombre"],
                "lat": municipio["lat"],
                "lon": municipio["lon"],
                "registros": registros,
                "status": "ok",
                "error": None,
            }

            return municipio_resultado, units

        except Exception as exc:
            last_error = str(exc)

            print(
                f"Intento {attempt}/{MAX_ATTEMPTS} falló para "
                f"{municipio['nombre']}: {last_error}"
            )

            if attempt < MAX_ATTEMPTS:
                time.sleep(2 * attempt)

    municipio_error = {
        "id": municipio["id"],
        "nombre": municipio["nombre"],
        "lat": municipio["lat"],
        "lon": municipio["lon"],
        "registros": [],
        "status": "error",
        "error": last_error or "Error desconocido",
    }

    return municipio_error, {}


def build_resumen(
    municipios: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """Crea el resumen general del archivo."""
    all_dates = sorted({
        registro["fecha"]
        for municipio in municipios
        for registro in municipio.get("registros", [])
    })

    municipios_con_datos = sum(
        1
        for municipio in municipios
        if (
            municipio.get("status") == "ok"
            and municipio.get("registros")
        )
    )

    return {
        "municipios_total": len(municipios),
        "municipios_con_datos": municipios_con_datos,
        "fecha_inicio": (
            all_dates[0] if all_dates else None
        ),
        "fecha_fin": (
            all_dates[-1] if all_dates else None
        ),
        "dias": len(all_dates),
        "variables": {
            "velocidad_media_10m_kmh": (
                "Velocidad media diaria del viento "
                "a 10 m en km/h"
            ),
            "velocidad_maxima_10m_kmh": (
                "Velocidad máxima diaria del viento "
                "a 10 m en km/h; no representa una "
                "racha instrumental"
            ),
            "velocidad_minima_10m_kmh": (
                "Velocidad mínima diaria del viento "
                "a 10 m en km/h"
            ),
            "rango_velocidad_10m_kmh": (
                "Rango diario de velocidad del viento "
                "a 10 m en km/h"
            ),
            "direccion_media_10m_grados": (
                "Dirección media diaria del viento "
                "a 10 m en grados"
            ),
            "direccion_media_10m_cardinal": (
                "Dirección media diaria expresada "
                "como punto cardinal"
            ),
        },
    }


def main() -> None:
    """Ejecuta la descarga de los 19 municipios."""
    generated_at_gt = gt_now().isoformat(
        timespec="seconds"
    )

    generated_at_utc = datetime.now(
        timezone.utc
    ).isoformat(timespec="seconds")

    end_date = nasa_end_date()

    if end_date < START_DATE:
        raise RuntimeError(
            "La fecha final calculada es anterior a "
            "START_DATE. Revisa la fecha inicial."
        )

    OUTPUT_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    municipios_out: List[Dict[str, Any]] = []
    nasa_units: Dict[str, Optional[str]] = {}

    for index, municipio in enumerate(
        MUNICIPIOS,
        start=1,
    ):
        print(
            f"[{index:02d}/{len(MUNICIPIOS)}] "
            f"Descargando viento NASA POWER: "
            f"{municipio['nombre']}"
        )

        municipio_out, units = fetch_municipio(
            municipio,
            end_date,
        )

        municipios_out.append(municipio_out)

        if units and not nasa_units:
            nasa_units = units

        if index < len(MUNICIPIOS):
            time.sleep(DELAY_SECONDS)

    payload = {
        "ok": any(
            municipio.get("registros")
            for municipio in municipios_out
        ),
        "generated_at_gt": generated_at_gt,
        "generated_at_utc": generated_at_utc,
        "source": {
            "name": (
                "NASA POWER Agroclimatology API"
            ),
            "url": API_URL,
            "community": "AG",
            "parameters": PARAMETERS,
            "original_units": nasa_units,
            "output_speed_unit": "km/h",
            "time_standard": "UTC",
            "start": START_DATE,
            "end": end_date,
            "note": (
                "WS10M_MAX es la velocidad máxima "
                "diaria estimada por NASA POWER; "
                "no se interpreta como racha "
                "instrumental."
            ),
        },
        "resumen": build_resumen(
            municipios_out
        ),
        "municipios": municipios_out,
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
        f"OK viento NASA POWER escrito en: "
        f"{OUTPUT_PATH}"
    )

    print(
        json.dumps(
            payload["resumen"],
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
