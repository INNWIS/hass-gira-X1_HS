"""Minimal async client for the Gira IoT REST API v2."""
from __future__ import annotations

import logging

import aiohttp

_LOGGER = logging.getLogger(__name__)


class GiraX1ApiError(Exception):
    """Generic API error."""


class GiraX1AuthError(GiraX1ApiError):
    """Raised when credentials are rejected."""


class GiraX1Client:
    """Talks to a Gira X1 / HomeServer / FacilityServer over the IoT REST API."""

    def __init__(
        self,
        session: aiohttp.ClientSession,
        host: str,
        username: str,
        password: str,
        client_id: str,
    ) -> None:
        self._session = session
        self._host = host.rstrip("/")
        self._username = username
        self._password = password
        self._client_id = client_id
        self._token: str | None = None

    @property
    def base_url(self) -> str:
        return f"https://{self._host}/api/v2"

    async def register(self) -> str:
        """Register this client and obtain an access token (chapter 4.2)."""
        url = f"{self.base_url}/clients"
        auth = aiohttp.BasicAuth(self._username, self._password)
        try:
            async with self._session.post(
                url, json={"client": self._client_id}, auth=auth, ssl=False
            ) as resp:
                if resp.status == 201:
                    data = await resp.json()
                    self._token = data["token"]
                    return self._token
                if resp.status == 401:
                    raise GiraX1AuthError("Invalid username or password")
                text = await resp.text()
                raise GiraX1ApiError(
                    f"Registration failed ({resp.status}): {text}"
                )
        except aiohttp.ClientError as err:
            raise GiraX1ApiError(f"Connection error: {err}") from err

    async def unregister(self) -> None:
        """Unregister this client (chapter 4.3). Best-effort, never raises."""
        if not self._token:
            return
        url = f"{self.base_url}/clients/{self._token}"
        try:
            async with self._session.delete(url, ssl=False):
                pass
        except Exception:  # noqa: BLE001 - best effort cleanup
            _LOGGER.debug("Failed to unregister Gira X1 client", exc_info=True)
        self._token = None

    async def _request(self, method: str, path: str, retry: bool = True, **kwargs):
        if not self._token:
            await self.register()

        url = f"{self.base_url}{path}"
        params = kwargs.pop("params", {}) or {}
        params["token"] = self._token

        try:
            async with self._session.request(
                method, url, params=params, ssl=False, **kwargs
            ) as resp:
                if resp.status == 401 and retry:
                    # token became invalid -> re-register once and retry
                    self._token = None
                    return await self._request(method, path, retry=False, **kwargs)
                if resp.status == 204:
                    return None
                if resp.status >= 400:
                    text = await resp.text()
                    raise GiraX1ApiError(
                        f"{method} {path} failed ({resp.status}): {text}"
                    )
                # Some endpoints (e.g. PUT /values/<uid>) reply with 200 OK
                # and an empty or non-JSON body. Only decode JSON when there
                # is actually a body to decode.
                text = await resp.text()
                if not text:
                    return None
                try:
                    return await resp.json(content_type=None)
                except ValueError:
                    return None
        except aiohttp.ClientError as err:
            raise GiraX1ApiError(f"Connection error: {err}") from err

    async def get_ui_config(self) -> dict:
        """Fetch the full UI configuration (chapter 5.2)."""
        return await self._request(
            "GET",
            "/uiconfig",
            params={"expand": "dataPointFlags,parameters,locations,trades"},
        )

    async def get_values(self, uid: str) -> list[dict]:
        """Get all datapoint values for a function or a single datapoint (chapter 6.1)."""
        data = await self._request("GET", f"/values/{uid}")
        return data.get("values", []) if data else []

    async def set_value(self, uid: str, value) -> None:
        """Set a single datapoint value (chapter 6.3)."""
        await self._request("PUT", f"/values/{uid}", json={"value": value})

    async def register_callbacks(
        self,
        service_url: str | None,
        value_url: str | None,
        test: bool = True,
    ) -> None:
        """Register service/value callback URLs (chapter 4.4)."""
        body: dict = {"testCallbacks": test}
        if service_url:
            body["serviceCallback"] = service_url
        if value_url:
            body["valueCallback"] = value_url
        await self._request("POST", f"/clients/{self._token}/callbacks", json=body)

    async def remove_callbacks(self) -> None:
        """Remove any registered callbacks (chapter 4.5). Best-effort."""
        if not self._token:
            return
        try:
            await self._request("DELETE", f"/clients/{self._token}/callbacks")
        except GiraX1ApiError:
            _LOGGER.debug("Failed to remove Gira X1 callbacks", exc_info=True)
