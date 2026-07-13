Fuente    : NASA POWER Agroclimatology API — https://power.larc.nasa.gov
Variables :
    T2M       Temperatura media diaria a 2 metros (°C)
    T2M_MAX   Temperatura máxima diaria a 2 metros (°C)
    T2M_MIN   Temperatura mínima diaria a 2 metros (°C)
    T2M_RANGE Rango térmico diario (°C)
    RH2M      Humedad relativa media diaria a 2 metros (%)
Comunidad : AG (Agroclimatología)

Salida:
    docs/data/temperatura/historico_municipios.json

Uso:
    python fetch_temperatura_nasa.py
"""

from __future__ import annotations

import json
import os
import sys
import time
from datetime import date, datetime, timedelta, timezone
from typing import Any

import requests


# ---------------------------------------------------------------------------
# CONFIGURACIÓN
# ---------------------------------------------------------------------------

OUTPUT_PATH = os.path.join("docs", "data", "temperatura", "historico_municipios.json")
NASA_POWER_URL = "https://power.larc.nasa.gov/api/temporal/daily/point"

PARAMETERS = ["T2M", "T2M_MAX", "T2M_MIN", "T2M_RANGE", "RH2M"]
COMMUNITY = "AG"

# Mantiene el mismo inicio operativo usado en el módulo de lluvia.
START_DATE = date(2026, 1, 1)

# NASA POWER puede tener 1–3 días de retraso; usar ayer evita pedir datos aún no consolidados.
END_DATE = date.today() - timedelta(days=1)

DELAY_SECONDS = 0.6
FILL_THRESHOLD = -900.0


# ---------------------------------------------------------------------------
# MUNICIPIOS — 19 municipios de Sololá
# ---------------------------------------------------------------------------

MUNICIPIOS = {
    "Sololá (Cabecera)":         {"lat": 14.772, "lon": -91.183},
    "Concepción":                {"lat": 14.783, "lon": -91.147},
    "Panajachel":                {"lat": 14.742, "lon": -91.155},
    "San Andrés Semetabaj":      {"lat": 14.744, "lon": -91.131},
    "San Antonio Palopó":        {"lat": 14.695, "lon": -91.112},
    "Santa Catarina Palopó":     {"lat": 14.724, "lon": -91.135},
    "San José Chacayá":          {"lat": 14.771, "lon": -91.213},
    "Santa Lucía Utatlán":       {"lat": 14.775, "lon": -91.264},
    "Santa María Visitación":    {"lat": 14.717, "lon": -91.315},
    "Santa Cruz La Laguna":      {"lat": 14.744, "lon": -91.205},
    "San Marcos La Laguna":      {"lat": 14.724, "lon": -91.263},
    "San Pablo La Laguna":       {"lat": 14.721, "lon": -91.274},
    "San Juan La Laguna":        {"lat": 14.701, "lon": -91.288},
    "San Pedro La Laguna":       {"lat": 14.693, "lon": -91.268},
    "Santiago Atitlán":          {"lat": 14.639, "lon": -91.229},
    "San Lucas Tolimán":         {"lat": 14.632, "lon": -91.144},
    "Nahualá":                   {"lat": 14.843, "lon": -91.318},
    "Santa Catarina Ixtahuacán": {"lat": 14.853, "lon": -91.359},
    "Santa Clara La Laguna":     {"lat": 14.713, "lon": -91.303},
}


# ---------------------------------------------------------------------------
# FUNCIONES AUXILIARES
# ---------------------------------------------------------------------------

def format_date_for_api(d: date) -> str:
    """Convierte date a YYYYMMDD para NASA POWER."""
    return d.strftime("%Y%m%d")


def parse_nasa_date(nasa_key: str) -> str:
    """Convierte YYYYMMDD a YYYY-MM-DD."""
    return f"{nasa_key[:4]}-{nasa_key[4:6]}-{nasa_key[6:8]}"


def clean_number(raw_value: Any, decimals: int = 2) -> float | None:
    """
    Limpia valores numéricos de NASA.

    NASA usa valores centinela cercanos a -999 cuando el dato no existe.
    En temperatura no se deben convertir valores negativos reales a cero, por eso
    solo se descartan valores menores a FILL_THRESHOLD.
    """
    try:
        value = float(raw_value)
    except (TypeError, ValueError):
        return None

    if value < FILL_THRESHOLD:
        return None

    return round(value, decimals)


def clean_humidity(raw_value: Any) -> float | None:
    """Limpia humedad relativa y limita valores válidos a 0–100 %."""
    value = clean_number(raw_value, 1)
    if value is None:
        return None
    return round(max(0.0, min(100.0, value)), 1)


def fetch_municipio(nombre: str, lat: float, lon: float) -> list[dict[str, Any]] | None:
    """
    Consulta NASA POWER para un municipio.

    Retorna una lista de registros diarios:
    {
      "fecha": "YYYY-MM-DD",
      "t_media_c": float | null,
      "t_max_c": float | null,
      "t_min_c": float | null,
      "rango_c": float | null,
      "humedad_relativa_pct": float | null
    }
    """
    params = {
        "parameters": ",".join(PARAMETERS),
        "community": COMMUNITY,
        "longitude": lon,
        "latitude": lat,
        "start": format_date_for_api(START_DATE),
        "end": format_date_for_api(END_DATE),
        "format": "JSON",
    }

    try:
        response = requests.get(NASA_POWER_URL, params=params, timeout=45)
        response.raise_for_status()
    except requests.exceptions.HTTPError:
        print(f"  [ERROR] HTTP {response.status_code} para '{nombre}': {response.text[:240]}")
        return None
    except requests.exceptions.Timeout:
        print(f"  [ERROR] Tiempo de espera agotado para '{nombre}'.")
        return None
    except requests.exceptions.RequestException as exc:
        print(f"  [ERROR] Error de red para '{nombre}': {exc}")
        return None

    try:
        data = response.json()
        raw_parameters = data["properties"]["parameter"]
    except (ValueError, KeyError, TypeError) as exc:
        print(f"  [ERROR] Estructura inesperada en la respuesta para '{nombre}': {exc}")
        return None

    # Crear unión de fechas disponibles para no depender de una sola variable.
    fechas: set[str] = set()
    for parameter in PARAMETERS:
        series = raw_parameters.get(parameter, {})
        if isinstance(series, dict):
            fechas.update(series.keys())

    if not fechas:
        print(f"  [AVISO] Serie vacía para '{nombre}'.")
        return []

    registros: list[dict[str, Any]] = []
    for fecha_raw in sorted(fechas):
        t_media = clean_number(raw_parameters.get("T2M", {}).get(fecha_raw))
        t_max = clean_number(raw_parameters.get("T2M_MAX", {}).get(fecha_raw))
        t_min = clean_number(raw_parameters.get("T2M_MIN", {}).get(fecha_raw))
        rango = clean_number(raw_parameters.get("T2M_RANGE", {}).get(fecha_raw))
        humedad = clean_humidity(raw_parameters.get("RH2M", {}).get(fecha_raw))

        # Si NASA no trae T2M_RANGE pero sí max/min, se calcula como respaldo.
        if rango is None and t_max is not None and t_min is not None:
            rango = round(t_max - t_min, 2)

        registros.append({
            "fecha": parse_nasa_date(fecha_raw),
            "t_media_c": t_media,
            "t_max_c": t_max,
            "t_min_c": t_min,
            "rango_c": rango,
            "humedad_relativa_pct": humedad,
        })

    return registros


def ensure_output_dir(path: str) -> None:
    directory = os.path.dirname(path)
    if directory:
        os.makedirs(directory, exist_ok=True)


def save_json(data: dict[str, Any], path: str) -> None:
    ensure_output_dir(path)
    with open(path, "w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=2)
    print(f"\n✓ Archivo guardado en: {path}")


def summarize_records(registros: list[dict[str, Any]]) -> tuple[int, float | None, float | None, float | None]:
    medias = [r["t_media_c"] for r in registros if r.get("t_media_c") is not None]
    maximas = [r["t_max_c"] for r in registros if r.get("t_max_c") is not None]
    minimas = [r["t_min_c"] for r in registros if r.get("t_min_c") is not None]

    mean_temp = round(sum(medias) / len(medias), 2) if medias else None
    max_temp = max(maximas) if maximas else None
    min_temp = min(minimas) if minimas else None
    return len(registros), mean_temp, max_temp, min_temp


# ---------------------------------------------------------------------------
# PROGRAMA PRINCIPAL
# ---------------------------------------------------------------------------

def main() -> None:
    print("=" * 72)
    print("  NASA POWER — Temperatura diaria, Sololá")
    print(f"  Periodo: {START_DATE} → {END_DATE}")
    print(f"  Variables: {', '.join(PARAMETERS)}")
    print(f"  Municipios: {len(MUNICIPIOS)}")
    print("=" * 72)

    if END_DATE < START_DATE:
        print("\n[AVISO] La fecha de fin es anterior a la fecha de inicio. No hay datos que descargar aún.")
        sys.exit(0)

    resultado: dict[str, Any] = {
        "metadata": {
            "fuente": "NASA POWER",
            "comunidad": COMMUNITY,
            "endpoint": NASA_POWER_URL,
            "variables": PARAMETERS,
            "unidades": {
                "t_media_c": "°C",
                "t_max_c": "°C",
                "t_min_c": "°C",
                "rango_c": "°C",
                "humedad_relativa_pct": "%",
            },
            "fecha_inicio": START_DATE.isoformat(),
            "fecha_fin": END_DATE.isoformat(),
            "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        },
        "municipios": {},
    }

    exitosos = 0
    fallidos = 0

    for idx, (nombre, coords) in enumerate(MUNICIPIOS.items(), start=1):
        print(f"\n[{idx:02d}/{len(MUNICIPIOS)}] {nombre} (lat={coords['lat']}, lon={coords['lon']})")
        registros = fetch_municipio(nombre, coords["lat"], coords["lon"])

        if registros is None:
            resultado["municipios"][nombre] = []
            fallidos += 1
        else:
            resultado["municipios"][nombre] = registros
            exitosos += 1
            dias, t_media, t_max, t_min = summarize_records(registros)
            print(
                f"  ✓ {dias} días — media: {t_media if t_media is not None else 's/d'} °C, "
                f"máx.: {t_max if t_max is not None else 's/d'} °C, "
                f"mín.: {t_min if t_min is not None else 's/d'} °C"
            )

        if idx < len(MUNICIPIOS):
            time.sleep(DELAY_SECONDS)

    save_json(resultado, OUTPUT_PATH)

    print("\n" + "=" * 72)
    print(f"  Municipios con datos : {exitosos}")
    print(f"  Municipios fallidos  : {fallidos}")
    print(f"  Archivo de salida    : {OUTPUT_PATH}")
    print("=" * 72)

    if fallidos > 0:
        print(f"\n[AVISO] {fallidos} municipio(s) no pudieron descargarse. Reintentá ejecutando el workflow otra vez.")
        sys.exit(1)


if __name__ == "__main__":
    main()
