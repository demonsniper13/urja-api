import hashlib
import hmac
import threading
import time
from urllib.parse import urlencode

import httpx

from app.config import Settings


class UpstreamError(Exception):
    pass


class PortalUnavailable(UpstreamError):
    pass


class NotFound(UpstreamError):
    pass


class UrjaClient:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.client = httpx.Client(
            base_url=settings.urja_base_url,
            timeout=settings.request_timeout_seconds,
            headers={"Origin": settings.urja_base_url},
            follow_redirects=True,
        )
        self.signing_secret: str | None = None
        self.login_lock = threading.Lock()

    def close(self):
        self.client.close()

    def login(self):
        with self.login_lock:
            try:
                response = self.client.post(
                    "/login",
                    data={"email": self.settings.urja_email, "password": self.settings.urja_password},
                )
            except httpx.RequestError as exc:
                raise PortalUnavailable("Could not reach the Urja portal") from exc

            cookie_name = "__Secure-better-auth.session_token"
            if cookie_name not in self.client.cookies:
                raise UpstreamError(f"Portal login failed with status {response.status_code}")

    def _request(self, method: str, path: str, **kwargs) -> httpx.Response:
        last_error = None
        for attempt in range(2):
            if "__Secure-better-auth.session_token" not in self.client.cookies:
                self.login()

            try:
                response = self.client.request(method, path, **kwargs)
            except httpx.RequestError as exc:
                last_error = exc
                if attempt == 0:
                    continue
                raise PortalUnavailable("Could not reach the Urja portal") from exc

            if response.status_code == 401 and attempt == 0:
                self.client.cookies.clear()
                self.signing_secret = None
                continue
            if response.status_code == 404:
                raise NotFound("Resource was not found in the Urja portal")
            if response.status_code >= 500:
                last_error = UpstreamError(f"Portal returned {response.status_code}")
                if attempt == 0:
                    continue
            if response.status_code >= 400:
                raise UpstreamError(f"Portal returned {response.status_code}: {response.text[:200]}")
            return response

        raise UpstreamError(str(last_error or "Portal request failed"))

    def get_json(self, path: str, params: dict | None = None) -> dict:
        return self._request("GET", path, params=params).json()

    def get_signing_secret(self) -> str:
        if not self.signing_secret:
            payload = self.get_json("/portal/keys")
            self.signing_secret = payload["data"]["signingSecret"]
        return self.signing_secret

    def get_export(self) -> dict:
        params = {"page": 1}
        query = urlencode(params)
        timestamp = str(int(time.time()))
        message = "\n".join(["GET", "/portal/export", query, timestamp])
        signature = hmac.new(
            self.get_signing_secret().encode(), message.encode(), hashlib.sha256
        ).hexdigest()
        headers = {"x-signature": signature, "x-timestamp": timestamp}
        return self._request("GET", "/portal/export", params=params, headers=headers).json()

    def get_transformers(self) -> list[dict]:
        rows: list[dict] = []
        page = 1
        while True:
            payload = self.get_json("/portal/dts", {"page": page})
            batch = payload["data"]
            rows.extend(batch)
            if not batch or len(rows) >= payload["total"]:
                return rows
            page += 1

    def get_geo(self, meter_id: str) -> dict:
        return self.get_json(f"/portal/meters/{meter_id}/geo")

    def get_energy(self, meter_id: str) -> dict:
        return self.get_json(f"/portal/meters/{meter_id}/energy")
