import time

from app.models import Meter, MeterDetail, Transformer, TransformerDetail
from app.normalize import normalize_energy, normalize_geo, normalize_meter, normalize_transformer
from app.upstream import NotFound, UrjaClient


class UrjaService:
    def __init__(self, client: UrjaClient, cache_ttl_seconds: int):
        self.client = client
        self.cache_ttl_seconds = cache_ttl_seconds
        self._meters: list[Meter] | None = None
        self._transformers: list[Transformer] | None = None
        self._meters_loaded_at: float | None = None
        self._transformers_loaded_at: float | None = None

    def _fresh(self, loaded_at: float | None) -> bool:
        return loaded_at is not None and time.time() - loaded_at < self.cache_ttl_seconds

    def meters(self) -> list[Meter]:
        if self._meters is None or not self._fresh(self._meters_loaded_at):
            payload = self.client.get_export()
            self._meters = [normalize_meter(row) for row in payload["data"]]
            self._meters_loaded_at = time.time()
        return self._meters

    def transformers(self) -> list[Transformer]:
        if self._transformers is None or not self._fresh(self._transformers_loaded_at):
            self._transformers = [normalize_transformer(row) for row in self.client.get_transformers()]
            self._transformers_loaded_at = time.time()
        return self._transformers

    def list_meters(
        self,
        q: str | None,
        status: str | None,
        phase: str | None,
        make: str | None,
        install_type: str | None,
        build: str | None,
        dt: str | None,
        feeder: str | None,
        limit: int,
        offset: int,
    ) -> tuple[list[Meter], int]:
        rows = self.meters()

        if q:
            value = q.casefold()
            rows = [m for m in rows if value in m.meter_id.casefold() or value in m.serial_no.casefold()]
        if status:
            rows = [m for m in rows if m.install_status.casefold() == status.casefold()]
        if phase:
            rows = [m for m in rows if m.phase_type.casefold() == phase.casefold()]
        if make:
            rows = [m for m in rows if m.make.casefold() == make.casefold()]
        if install_type:
            rows = [m for m in rows if m.install_type.casefold() == install_type.casefold()]
        if build:
            rows = [m for m in rows if m.build.casefold() == build.casefold()]
        if dt:
            rows = [m for m in rows if m.dt_code.casefold() == dt.casefold()]
        if feeder:
            rows = [m for m in rows if m.hierarchy.feeder.code.casefold() == feeder.casefold()]

        return rows[offset : offset + limit], len(rows)

    def get_meter(self, meter_id: str) -> MeterDetail:
        meter = next((m for m in self.meters() if m.meter_id.casefold() == meter_id.casefold()), None)
        if not meter:
            raise NotFound(f"Meter {meter_id} was not found")

        precise_geo = normalize_geo(self.client.get_geo(meter.meter_id))
        transformer = next((t for t in self.transformers() if t.code == meter.dt_code), None)
        return MeterDetail(**meter.model_dump(exclude={"geo"}), geo=precise_geo, transformer=transformer)

    def get_energy(self, meter_id: str):
        if not any(m.meter_id.casefold() == meter_id.casefold() for m in self.meters()):
            raise NotFound(f"Meter {meter_id} was not found")
        return normalize_energy(self.client.get_energy(meter_id))

    def list_transformers(self, q: str | None, limit: int, offset: int):
        rows = self.transformers()
        if q:
            value = q.casefold()
            rows = [t for t in rows if value in t.code.casefold() or value in t.name.casefold()]
        return rows[offset : offset + limit], len(rows)

    def get_transformer(self, code: str) -> TransformerDetail:
        transformer = next((t for t in self.transformers() if t.code.casefold() == code.casefold()), None)
        if not transformer:
            raise NotFound(f"Transformer {code} was not found")
        count = sum(m.dt_code.casefold() == code.casefold() for m in self.meters())
        return TransformerDetail(**transformer.model_dump(), meter_count=count)

    def cache_age(self, loaded_at: float | None) -> int | None:
        return None if loaded_at is None else int(time.time() - loaded_at)
