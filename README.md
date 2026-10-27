# Urja Meter API

A small read-only FastAPI service over the Urja Meter Ops portal. It hides the portal login and request-signing details and returns consistent JSON for meters, transformers, locations and energy readings.

## Why this shape

The portal already has useful internal endpoints, including a bulk meter export. I used that bulk endpoint as a short-lived local index instead of adding a database. This keeps the submission small while allowing filters that the portal does not provide directly.

## Project structure

```text
app/config.py      environment settings
app/upstream.py    portal login, session handling and export signing
app/normalize.py   converts portal fields into clean API values
app/models.py      API response models
app/service.py     cache, filtering, joins and lookups
app/main.py        FastAPI routes and error handling
tests/test_core.py focused offline tests
```

## Install and run

Python 3.11 or newer is recommended.

```bash
python -m venv .venv
```

Windows PowerShell:

```powershell
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
```

macOS/Linux:

```bash
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Update `URJA_PASSWORD` in `.env`, then run:

```bash
uvicorn app.main:app --reload
```

Swagger UI is available at `http://127.0.0.1:8000/docs`.

## Sample requests

```bash
curl "http://127.0.0.1:8000/api/meters?make=Genus&status=Installed&limit=10"
curl "http://127.0.0.1:8000/api/meters/J100000"
curl "http://127.0.0.1:8000/api/meters/J100000/energy"
curl "http://127.0.0.1:8000/api/transformers/DT-001/meters"
```

## API endpoints

- `GET /api/health`
- `GET /api/meters`
- `GET /api/meters/{meter_id}`
- `GET /api/meters/{meter_id}/energy`
- `GET /api/transformers`
- `GET /api/transformers/{code}`
- `GET /api/transformers/{code}/meters`

Meter filters: `q`, `status`, `phase`, `make`, `install_type`, `build`, `dt`, `feeder`, `limit`, `offset`.

Transformer filters: `q`, `limit`, `offset`.

## Assumptions and decisions

- Portal energy timestamps do not include a timezone. The API assumes IST (`+05:30`) and documents that assumption rather than claiming it is confirmed.
- Energy values are converted from strings to numbers. Empty or invalid values become `null`.
- `consumption_kwh` is derived from consecutive cumulative readings. The first value is `null`. If the total decreases, the derived value is also `null` because it may indicate a reset or correction.
- Meter lists use coordinates from the bulk export. A single-meter request calls the portal's geo endpoint for its more precise value.
- Meter and transformer datasets are cached in memory for five minutes by default. This avoids repeated portal calls without adding Redis or a database.
- The service has no write endpoints and does not expose the portal signing secret.

## Trade-offs

The in-memory cache is appropriate for the small dataset discovered during investigation and for a single-process take-home service. Different worker processes would have separate caches. At a larger scale I would add a scheduled ingestion job, durable storage and indexed queries.

The client retries once after authentication or network failure. More complex retry policies and circuit breaking were intentionally left out to keep behavior easy to understand.

## Intentionally omitted

- New API authentication
- Database and background synchronization
- Write operations
- Web interface
- Geospatial search
- Multi-process cache coordination

These are useful production concerns, but they are not needed to demonstrate a clean read-only service over the portal.

## Tests

```bash
pytest
```

Tests are offline and focus on unusual behavior: numeric conversion, timezone normalization, cumulative-consumption calculation, counter resets and the signing formula.

## OpenAPI

`openapi.json` contains the generated OpenAPI 3.x description. FastAPI also serves the same contract at `/openapi.json` while the application is running.

See [PROTOCOL.md](PROTOCOL.md) for the portal investigation and [REFLECTION.md](REFLECTION.md) for the requested reflection.
