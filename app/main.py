from contextlib import asynccontextmanager

from fastapi import FastAPI, Query, Request
from fastapi.responses import JSONResponse

from app.config import get_settings
from app.models import (
    EnergyResponse,
    HealthResponse,
    MeterDetail,
    MeterListResponse,
    TransformerDetail,
    TransformerListResponse,
)
from app.service import UrjaService
from app.upstream import NotFound, PortalUnavailable, UpstreamError, UrjaClient

settings = get_settings()
client = UrjaClient(settings)
service = UrjaService(client, settings.cache_ttl_seconds)


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    client.close()


app = FastAPI(
    title="Urja Meter API",
    version="1.0.0",
    description="A small read-only API over the Urja Meter Ops portal.",
    lifespan=lifespan,
)


def error(code: str, message: str, status_code: int):
    return JSONResponse(status_code=status_code, content={"error": {"code": code, "message": message}})


@app.exception_handler(NotFound)
def handle_not_found(request: Request, exc: NotFound):
    return error("not_found", str(exc), 404)


@app.exception_handler(PortalUnavailable)
def handle_unavailable(request: Request, exc: PortalUnavailable):
    return error("portal_unavailable", str(exc), 503)


@app.exception_handler(UpstreamError)
def handle_upstream_error(request: Request, exc: UpstreamError):
    return error("upstream_error", str(exc), 502)


@app.get("/api/health", response_model=HealthResponse)
def health():
    try:
        client.get_json("/portal/dts", {"page": 1})
        reachable = True
    except UpstreamError:
        reachable = False
    return HealthResponse(
        status="ok" if reachable else "degraded",
        portal_reachable=reachable,
        meter_cache_age_seconds=service.cache_age(service._meters_loaded_at),
        transformer_cache_age_seconds=service.cache_age(service._transformers_loaded_at),
    )


@app.get("/api/meters", response_model=MeterListResponse)
def list_meters(
    q: str | None = None,
    status: str | None = None,
    phase: str | None = None,
    make: str | None = None,
    install_type: str | None = None,
    build: str | None = None,
    dt: str | None = None,
    feeder: str | None = None,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
):
    rows, total = service.list_meters(q, status, phase, make, install_type, build, dt, feeder, limit, offset)
    return MeterListResponse(data=rows, total=total, limit=limit, offset=offset)


@app.get("/api/meters/{meter_id}", response_model=MeterDetail)
def get_meter(meter_id: str):
    return service.get_meter(meter_id)


@app.get("/api/meters/{meter_id}/energy", response_model=EnergyResponse)
def get_energy(meter_id: str):
    return EnergyResponse(meter_id=meter_id, data=service.get_energy(meter_id))


@app.get("/api/transformers", response_model=TransformerListResponse)
def list_transformers(
    q: str | None = None,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
):
    rows, total = service.list_transformers(q, limit, offset)
    return TransformerListResponse(data=rows, total=total, limit=limit, offset=offset)


@app.get("/api/transformers/{code}", response_model=TransformerDetail)
def get_transformer(code: str):
    return service.get_transformer(code)


@app.get("/api/transformers/{code}/meters", response_model=MeterListResponse)
def transformer_meters(
    code: str,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
):
    service.get_transformer(code)
    rows, total = service.list_meters(None, None, None, None, None, None, code, None, limit, offset)
    return MeterListResponse(data=rows, total=total, limit=limit, offset=offset)
