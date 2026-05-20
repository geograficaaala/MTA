"""
fetch_nasa_power.py
-------------------
Mesa Técnica Agroclimática de Sololá — MTA

Descarga la precipitación diaria corregida (PRECTOTCORR) de los 19 municipios
del departamento de Sololá desde el 1 de enero de 2026 hasta el día de ayer,
usando la API pública y gratuita de NASA POWER (sin API key ni registro).

Fuente  : NASA POWER Agroclimatology API — https://power.larc.nasa.gov
Variable: PRECTOTCORR  (precipitación diaria corregida, mm/día)
Comunidad: AG (Agroclimatología)

Salida  : docs/data/precipitaciones/historico_municipios.json

Uso:
    python fetch_nasa_power.py
"""

import json
import os
import time
import sys
from datetime import date, timedelta

import requests


# ---------------------------------------------------------------------------
# CONFIGURACIÓN
# ---------------------------------------------------------------------------

# Ruta de salida (relativa a la raíz del repositorio)
OUTPUT_PATH = os.path.join("docs", "data", "precipitaciones", "historico_municipios.json")

# Endpoint oficial de NASA POWER para datos puntuales diarios
NASA_POWER_URL = "https://power.larc.nasa.gov/api/temporal/daily/point"

# Variable de precipitación y comunidad
PARAMETER  = "PRECTOTCORR"
COMMUNITY  = "AG"

# Fecha de inicio fija del proyecto
START_DATE = date(2026, 1, 1)

# Fecha de fin: ayer (NASA POWER suele tener 1–3 días de retraso)
END_DATE = date.today() - timedelta(days=1)

# Pausa entre peticiones para respetar las políticas de uso de NASA
DELAY_SECONDS = 0.6

# Valor centinela que usa NASA para dato ausente; se convierte a 0.0
NASA_FILL_VALUE = -999.0
FILL_THRESHOLD  = -900.0   # cualquier valor menor que esto se trata como ausente


# ---------------------------------------------------------------------------
# DICCIONARIO DE MUNICIPIOS — 19 municipios verificados con fuentes oficiales
# ---------------------------------------------------------------------------

MUNICIPIOS = {
    "Sololá (Cabecera)":        {"lat":  14.772, "lon": -91.183},
    "Concepción":               {"lat":  14.783, "lon": -91.147},
    "Panajachel":               {"lat":  14.742, "lon": -91.155},
    "San Andrés Semetabaj":     {"lat":  14.744, "lon": -91.131},
    "San Antonio Palopó":       {"lat":  14.695, "lon": -91.112},
    "Santa Catarina Palopó":    {"lat":  14.724, "lon": -91.135},
    "San José Chacayá":         {"lat":  14.771, "lon": -91.213},
    "Santa Lucía Utatlán":      {"lat":  14.775, "lon": -91.264},
    "Santa María Visitación":   {"lat":  14.717, "lon": -91.315},
    "Santa Cruz La Laguna":     {"lat":  14.744, "lon": -91.205},
    "San Marcos La Laguna":     {"lat":  14.724, "lon": -91.263},
    "San Pablo La Laguna":      {"lat":  14.721, "lon": -91.274},
    "San Juan La Laguna":       {"lat":  14.701, "lon": -91.288},
    "San Pedro La Laguna":      {"lat":  14.693, "lon": -91.268},
    "Santiago Atitlán":         {"lat":  14.639, "lon": -91.229},
    "San Lucas Tolimán":        {"lat":  14.632, "lon": -91.144},
    "Nahualá":                  {"lat":  14.843, "lon": -91.318},
    "Santa Catarina Ixtahuacán":{"lat":  14.853, "lon": -91.359},
    "Santa Clara La Laguna":    {"lat":  14.713, "lon": -91.303},
}


# ---------------------------------------------------------------------------
# FUNCIONES
# ---------------------------------------------------------------------------

def format_date_for_api(d: date) -> str:
    """Convierte un objeto date a la cadena YYYYMMDD que requiere NASA POWER."""
    return d.strftime("%Y%m%d")


def parse_nasa_date(nasa_key: str) -> str:
    """
    Convierte la clave de fecha plana de NASA ('YYYYMMDD') al formato
    ISO 8601 ('YYYY-MM-DD') que usa el frontend.
    """
    return f"{nasa_key[:4]}-{nasa_key[4:6]}-{nasa_key[6:8]}"


def clean_value(raw_value) -> float:
    """
    Limpia un valor de precipitación de la NASA:
    - Si es None, no numérico o menor que el umbral del fill value → 0.0
    - Si es negativo pero mayor que el umbral → 0.0 (trazas negativas)
    - De lo contrario → float redondeado a 2 decimales
    """
    try:
        v = float(raw_value)
    except (TypeError, ValueError):
        return 0.0

    if v < FILL_THRESHOLD:
        return 0.0

    if v < 0.0:
        return 0.0

    return round(v, 2)


def fetch_municipio(nombre: str, lat: float, lon: float) -> list[dict] | None:
    """
    Hace una petición GET a NASA POWER para un punto geográfico.

    Retorna una lista de dicts  [{"fecha": "YYYY-MM-DD", "lluvia": float}, ...]
    o None si la petición falla.
    """
    params = {
        "parameters": PARAMETER,
        "community":  COMMUNITY,
        "longitude":  lon,
        "latitude":   lat,
        "start":      format_date_for_api(START_DATE),
        "end":        format_date_for_api(END_DATE),
        "format":     "JSON",
    }

    try:
        response = requests.get(
            NASA_POWER_URL,
            params=params,
            timeout=30,
        )
    except requests.exceptions.ConnectionError as e:
        print(f"  [ERROR] Sin conexión para '{nombre}': {e}")
        return None
    except requests.exceptions.Timeout:
        print(f"  [ERROR] Tiempo de espera agotado para '{nombre}'.")
        return None
    except requests.exceptions.RequestException as e:
        print(f"  [ERROR] Error de red para '{nombre}': {e}")
        return None

    if response.status_code != 200:
        print(
            f"  [ERROR] HTTP {response.status_code} al consultar '{nombre}'. "
            f"Detalle: {response.text[:200]}"
        )
        return None

    try:
        data = response.json()
    except ValueError:
        print(f"  [ERROR] Respuesta no válida (JSON mal formado) para '{nombre}'.")
        return None

    # Navegar la estructura de NASA POWER
    # properties → parameter → PRECTOTCORR → {"YYYYMMDD": valor, ...}
    try:
        raw_series = (
            data["properties"]["parameter"][PARAMETER]
        )
    except (KeyError, TypeError):
        print(f"  [ERROR] Estructura inesperada en la respuesta para '{nombre}'.")
        return None

    if not raw_series:
        print(f"  [AVISO] Serie vacía para '{nombre}'.")
        return []

    # Convertir a la estructura de salida
    registros = [
        {
            "fecha":  parse_nasa_date(fecha_raw),
            "lluvia": clean_value(valor),
        }
        for fecha_raw, valor in sorted(raw_series.items())
    ]

    return registros


def ensure_output_dir(path: str) -> None:
    """Crea el directorio de salida si no existe."""
    directory = os.path.dirname(path)
    if directory:
        os.makedirs(directory, exist_ok=True)


def save_json(data: dict, path: str) -> None:
    """Serializa el diccionario a JSON con indentación y lo escribe en disco."""
    ensure_output_dir(path)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"\n✓ Archivo guardado en: {path}")


# ---------------------------------------------------------------------------
# PROGRAMA PRINCIPAL
# ---------------------------------------------------------------------------

def main() -> None:
    print("=" * 60)
    print("  NASA POWER — Precipitación diaria, Sololá")
    print(f"  Periodo: {START_DATE} → {END_DATE}")
    print(f"  Municipios: {len(MUNICIPIOS)}")
    print("=" * 60)

    # Validación de fechas
    if END_DATE < START_DATE:
        print(
            "\n[AVISO] La fecha de fin es anterior a la de inicio. "
            "Esto ocurre si el script corre el mismo 1 de enero. "
            "No hay datos que descargar aún."
        )
        sys.exit(0)

    resultado: dict[str, list] = {}
    exitosos  = 0
    fallidos  = 0

    for i, (nombre, coords) in enumerate(MUNICIPIOS.items(), start=1):
        print(
            f"\n[{i:02d}/{len(MUNICIPIOS)}] {nombre} "
            f"(lat={coords['lat']}, lon={coords['lon']})"
        )

        registros = fetch_municipio(nombre, coords["lat"], coords["lon"])

        if registros is None:
            # La petición falló; guardamos lista vacía para no romper el JSON
            resultado[nombre] = []
            fallidos += 1
        else:
            resultado[nombre] = registros
            exitosos += 1
            dias = len(registros)
            total_lluvia = sum(r["lluvia"] for r in registros)
            print(
                f"  ✓ {dias} días descargados — "
                f"acumulado total: {total_lluvia:.1f} mm"
            )

        # Pausa de cortesía con el servidor de NASA
        if i < len(MUNICIPIOS):
            time.sleep(DELAY_SECONDS)

    # Guardar resultado
    save_json(resultado, OUTPUT_PATH)

    # Resumen final
    print("\n" + "=" * 60)
    print(f"  Municipios con datos : {exitosos}")
    print(f"  Municipios fallidos  : {fallidos}")
    print(f"  Archivo de salida    : {OUTPUT_PATH}")
    print("=" * 60)

    if fallidos > 0:
        print(
            f"\n[AVISO] {fallidos} municipio(s) no pudieron descargarse. "
            "El archivo JSON fue generado igualmente con lista vacía para esos municipios. "
            "Volvé a correr el script para reintentar."
        )
        sys.exit(1)   # Código de salida no-cero para que GitHub Actions marque el job


if __name__ == "__main__":
    main()
