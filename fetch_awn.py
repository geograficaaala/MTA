"""
fetch_awn.py
------------
Mesa Técnica Agroclimática de Sololá — MTA

Descarga el historial de precipitación de la estación meteorológica propia
registrada en Ambient Weather Network (AWN) y guarda los datos localmente
para que el sitio web los sirva sin problemas de CORS.

Estación : Santa Catarina Palopó
Activa   : desde el 23 de abril de 2026
Salida   : docs/data/precipitaciones/awn_estacion.json

Uso:
    python fetch_awn.py
"""

import json
import os
import sys
import time
from collections import defaultdict
from datetime import date, datetime, timedelta, timezone

import requests

# ---------------------------------------------------------------------------
# CREDENCIALES AWN
# ---------------------------------------------------------------------------

AWN_API_KEY = "c797c082863c4f748e1acace9fab1ac4afc5f7c7f03049dcb529bc15f636ffe2"
AWN_APP_KEY = "bcecf231a4454f01b5d5bb1d52cfd23ca3403d8b48954ca5ab7699b7ebf85c9c"
AWN_BASE    = "https://api.ambientweather.net/v1"

# ---------------------------------------------------------------------------
# CONFIGURACIÓN
# ---------------------------------------------------------------------------

OUTPUT_PATH   = os.path.join("docs", "data", "precipitaciones", "awn_estacion.json")
STATION_START = date(2026, 4, 23)          # la estación está activa desde esta fecha
GT_OFFSET     = timedelta(hours=6)         # Guatemala = UTC-6
RATE_LIMIT_S  = 1.1                        # espera entre peticiones (AWN free = 1 req/s)


# ---------------------------------------------------------------------------
# UTILIDADES
# ---------------------------------------------------------------------------

def epoch_ms(dt: datetime) -> int:
    """Convierte datetime a milisegundos epoch (requerido por AWN)."""
    return int(dt.timestamp() * 1000)


def gt_date(epoch_ms_val: int) -> str:
    """Convierte epoch ms a fecha en hora Guatemala (UTC-6)."""
    utc = datetime.fromtimestamp(epoch_ms_val / 1000, tz=timezone.utc)
    gt  = utc - GT_OFFSET
    return gt.strftime("%Y-%m-%d")


def gt_datetime_str(epoch_ms_val: int) -> str:
    """Convierte epoch ms a datetime legible en hora Guatemala."""
    utc = datetime.fromtimestamp(epoch_ms_val / 1000, tz=timezone.utc)
    gt  = utc - GT_OFFSET
    return gt.strftime("%Y-%m-%dT%H:%M:%S")


def inches_to_mm(inches) -> float:
    """Convierte pulgadas a milímetros y limpia valores inválidos."""
    try:
        val = float(inches)
        return round(max(0.0, val) * 25.4, 2)
    except (TypeError, ValueError):
        return 0.0


# ---------------------------------------------------------------------------
# API AWN
# ---------------------------------------------------------------------------

def get_devices() -> list[dict]:
    """Retorna la lista de dispositivos de la cuenta AWN."""
    resp = requests.get(
        f"{AWN_BASE}/devices",
        params={
            "applicationKey": AWN_APP_KEY,
            "apiKey":         AWN_API_KEY,
        },
        timeout=30,
    )
    if not resp.ok:
        raise RuntimeError(f"Error al obtener dispositivos: HTTP {resp.status_code}")
    return resp.json()


def fetch_device_page(mac: str, end_epoch_ms: int, limit: int = 288) -> list[dict]:
    """
    Obtiene hasta `limit` registros terminando en `end_epoch_ms`.
    AWN entrega los registros en orden descendente (más reciente primero).
    """
    resp = requests.get(
        f"{AWN_BASE}/devices/{mac}",
        params={
            "applicationKey": AWN_APP_KEY,
            "apiKey":         AWN_API_KEY,
            "endDate":        end_epoch_ms,
            "limit":          limit,
        },
        timeout=30,
    )

    if resp.status_code == 429:
        print("  [AVISO] Rate limit alcanzado. Esperando 5 segundos.")
        time.sleep(5)
        return []

    if not resp.ok:
        print(f"  [AVISO] HTTP {resp.status_code} — página saltada.")
        return []

    return resp.json() or []


def fetch_full_history(mac: str) -> list[dict]:
    """
    Pagina hacia atrás desde hoy hasta STATION_START
    para obtener todos los registros disponibles.
    """
    # end = fin del día de hoy en UTC
    end_dt  = datetime.now(tz=timezone.utc).replace(hour=23, minute=59, second=59)
    # start = inicio de la primera noche de operación en UTC
    start_dt = datetime(
        STATION_START.year, STATION_START.month, STATION_START.day,
        0, 0, 0, tzinfo=timezone.utc
    )

    current_end = epoch_ms(end_dt)
    start_limit = epoch_ms(start_dt)

    all_records: list[dict] = []
    page = 0

    print(f"  Descargando historial (paginado, desde {STATION_START})...")

    while current_end > start_limit:
        page += 1
        records = fetch_device_page(mac, current_end)

        if not records:
            break

        all_records.extend(records)

        # El campo dateutc viene en epoch ms desde AWN
        earliest = min(r["dateutc"] for r in records if "dateutc" in r)

        print(f"  Página {page}: {len(records)} registros | "
              f"más antiguo: {gt_datetime_str(earliest)}")

        if earliest <= start_limit:
            break

        current_end = earliest - 1
        time.sleep(RATE_LIMIT_S)

    print(f"  Total registros crudos obtenidos: {len(all_records)}")
    return all_records


# ---------------------------------------------------------------------------
# PROCESAMIENTO — SOLO PRECIPITACIÓN
# ---------------------------------------------------------------------------

def aggregate_daily_rain(records: list[dict]) -> list[dict]:
    """
    Agrega precipitación por día usando el campo `dailyrainin`.
    El valor máximo de `dailyrainin` en cada día de Guatemala
    equivale a la precipitación acumulada de ese día.

    Returns:
        Lista de {"fecha": "YYYY-MM-DD", "lluvia_mm": float}
        ordenada de más antigua a más reciente.
    """
    daily_max: dict[str, float] = defaultdict(float)

    for rec in records:
        if "dateutc" not in rec:
            continue

        epoch = rec["dateutc"]
        fecha = gt_date(epoch)

        # Solo incluir desde la fecha de activación
        if fecha < str(STATION_START):
            continue

        rain_in = rec.get("dailyrainin")
        if rain_in is None:
            continue

        val = max(0.0, float(rain_in))
        if val > daily_max[fecha]:
            daily_max[fecha] = val

    resultado = [
        {
            "fecha":     d,
            "lluvia_mm": round(daily_max[d] * 25.4, 2),
        }
        for d in sorted(daily_max.keys())
    ]

    return resultado


def get_last_record(records: list[dict]) -> dict | None:
    """Retorna el registro más reciente de la lista."""
    valid = [r for r in records if "dateutc" in r]
    if not valid:
        return None
    return max(valid, key=lambda r: r["dateutc"])


# ---------------------------------------------------------------------------
# MAIN
# ---------------------------------------------------------------------------

def main() -> None:
    print("=" * 60)
    print("  AWN — Precipitación, Santa Catarina Palopó")
    print(f"  Periodo: {STATION_START} → hoy")
    print("=" * 60)

    # 1. Obtener dispositivos
    print("\n[1] Obteniendo lista de dispositivos...")
    try:
        devices = get_devices()
    except RuntimeError as e:
        print(f"[ERROR] {e}")
        sys.exit(1)

    if not devices:
        print("[ERROR] No se encontraron dispositivos en la cuenta AWN.")
        sys.exit(1)

    device = devices[0]
    mac    = device.get("macAddress", "")
    info   = device.get("info", {})
    last   = device.get("lastData", {})

    print(f"  Dispositivo  : {info.get('name', 'Sin nombre')}")
    print(f"  MAC Address  : {mac}")
    print(f"  Coordenadas  : lat={info.get('coords', {}).get('lat','—')}, "
          f"lon={info.get('coords', {}).get('lon','—')}")

    # 2. Obtener historial completo
    print("\n[2] Descargando historial de precipitación...")
    raw_records = fetch_full_history(mac)

    # 3. Agregar por día
    print("\n[3] Agregando precipitación diaria...")
    historico = aggregate_daily_rain(raw_records)

    total_mm = sum(r["lluvia_mm"] for r in historico)
    dias_lluvia = sum(1 for r in historico if r["lluvia_mm"] > 0)

    print(f"  Días con dato: {len(historico)}")
    print(f"  Días con lluvia: {dias_lluvia}")
    print(f"  Acumulado total: {total_mm:.1f} mm")

    # 4. Obtener última lectura
    last_rec = get_last_record(raw_records) or last

    ultima_lectura = {
        "fecha_utc":         gt_datetime_str(last_rec["dateutc"]) if "dateutc" in last_rec else None,
        "lluvia_diaria_mm":  inches_to_mm(last_rec.get("dailyrainin")),
        "lluvia_evento_mm":  inches_to_mm(last_rec.get("eventrainin")),
        "lluvia_semanal_mm": inches_to_mm(last_rec.get("weeklyrainin")),
        "lluvia_mensual_mm": inches_to_mm(last_rec.get("monthlyrainin")),
    }

    # 5. Construir JSON de salida
    output = {
        "estacion": {
            "nombre":       info.get("name", "Estación MTA"),
            "mac":          mac,
            "municipio":    "Santa Catarina Palopó",
            "departamento": "Sololá",
            "lat":          info.get("coords", {}).get("lat", 14.724),
            "lon":          info.get("coords", {}).get("lon", -91.135),
            "activa_desde": str(STATION_START),
            "fuente":       "Ambient Weather Network (AWN)",
        },
        "ultima_lectura":  ultima_lectura,
        "historico_diario": historico,
        "resumen": {
            "dias_con_dato":   len(historico),
            "dias_con_lluvia": dias_lluvia,
            "total_mm":        round(total_mm, 2),
            "max_diario_mm":   max((r["lluvia_mm"] for r in historico), default=0),
            "generado_utc":    datetime.now(tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        },
    }

    # 6. Guardar
    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"\n  Archivo guardado: {OUTPUT_PATH}")
    print("\n" + "=" * 60)
    print(f"  Última lectura : {ultima_lectura['fecha_utc']}")
    print(f"  Lluvia diaria  : {ultima_lectura['lluvia_diaria_mm']} mm")
    print(f"  Lluvia mensual : {ultima_lectura['lluvia_mensual_mm']} mm")
    print("=" * 60)


if __name__ == "__main__":
    main()
