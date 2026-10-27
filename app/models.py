from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class Geo(BaseModel):
    lat: float
    lng: float


class HierarchyNode(BaseModel):
    name: str
    code: str


class MeterHierarchy(BaseModel):
    zone: HierarchyNode
    circle: HierarchyNode
    division: HierarchyNode
    subdivision: HierarchyNode
    substation: HierarchyNode
    feeder: HierarchyNode
    dt: HierarchyNode


class Meter(BaseModel):
    meter_id: str
    serial_no: str
    make: str
    phase_type: str
    install_status: str
    install_type: str
    build: str
    dt_code: str
    hierarchy: MeterHierarchy
    geo: Geo


class MeterDetail(Meter):
    transformer: "Transformer | None" = None


class Transformer(BaseModel):
    code: str
    name: str
    feeder_code: str
    capacity_kva: int


class TransformerDetail(Transformer):
    meter_count: int


class EnergyReading(BaseModel):
    timestamp: datetime
    kwh: float | None
    kvah: float | None
    volt_r: float | None
    consumption_kwh: float | None = None


class MeterListResponse(BaseModel):
    data: list[Meter]
    total: int
    limit: int
    offset: int


class TransformerListResponse(BaseModel):
    data: list[Transformer]
    total: int
    limit: int
    offset: int


class EnergyResponse(BaseModel):
    meter_id: str
    data: list[EnergyReading]


class HealthResponse(BaseModel):
    status: str
    portal_reachable: bool
    meter_cache_age_seconds: int | None = None
    transformer_cache_age_seconds: int | None = None


class ErrorResponse(BaseModel):
    error: dict[str, Any] = Field(
        examples=[{"code": "meter_not_found", "message": "Meter J999999 was not found."}]
    )
