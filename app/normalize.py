from datetime import datetime, timedelta, timezone

from app.models import EnergyReading, Geo, Meter, Transformer

IST = timezone(timedelta(hours=5, minutes=30))


def to_float(value) -> float | None:
    if value is None or value == "":
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def normalize_meter(row: dict) -> Meter:
    return Meter.model_validate(
        {
            "meter_id": row["meterId"],
            "serial_no": row["serialNo"],
            "make": row["make"],
            "phase_type": row["phaseType"],
            "install_status": row["installStatus"],
            "install_type": row["installType"],
            "build": row["build"],
            "dt_code": row["dtCode"],
            "hierarchy": row["hierarchy"],
            "geo": {"lat": row["geo"]["lat"], "lng": row["geo"]["lng"]},
        }
    )


def normalize_transformer(row: dict) -> Transformer:
    return Transformer(
        code=row["code"],
        name=row["name"],
        feeder_code=row["feederCode"],
        capacity_kva=int(row["capacityKva"]),
    )


def normalize_geo(payload: dict) -> Geo:
    data = payload["data"]
    return Geo(lat=float(data["latitude"]), lng=float(data["longitude"]))


def normalize_energy(payload: dict) -> list[EnergyReading]:
    readings: list[EnergyReading] = []
    previous_kwh: float | None = None

    for row in payload["data"]:
        current_kwh = to_float(row.get("kwh"))
        consumption = None
        if previous_kwh is not None and current_kwh is not None:
            difference = current_kwh - previous_kwh
            if difference >= 0:
                consumption = round(difference, 6)

        readings.append(
            EnergyReading(
                timestamp=datetime.strptime(row["timestamp"], "%d/%m/%Y %H:%M").replace(tzinfo=IST),
                kwh=current_kwh,
                kvah=to_float(row.get("kvah")),
                volt_r=to_float(row.get("voltR")),
                consumption_kwh=consumption,
            )
        )
        previous_kwh = current_kwh

    return readings
