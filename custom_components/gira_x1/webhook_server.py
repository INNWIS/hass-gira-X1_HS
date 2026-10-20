"""A minimal local HTTPS server that receives Gira X1 push callbacks.

Implements the two endpoints described in chapters 4.6 and 4.7 of the Gira
IoT REST API documentation: POST <serviceCallback> and POST <valueCallback>.
"""
from __future__ import annotations

from collections.abc import Awaitable, Callable
import asyncio
import logging
import ssl

from aiohttp import web

_LOGGER = logging.getLogger(__name__)

EventHandler = Callable[[list[dict]], Awaitable[None]]


def _build_ssl_context(cert_path: str, key_path: str) -> ssl.SSLContext:
    """Blocking: build the SSL context. Must be run in an executor."""
    ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    ssl_context.load_cert_chain(cert_path, key_path)
    return ssl_context


class GiraX1CallbackServer:
    """Runs its own aiohttp HTTPS listener, independent of HA's own server."""

    def __init__(
        self,
        port: int,
        cert_path: str,
        key_path: str,
        expected_token: str,
        on_service_event: EventHandler,
        on_value_event: EventHandler,
    ) -> None:
        self._port = port
        self._cert_path = cert_path
        self._key_path = key_path
        self._expected_token = expected_token
        self._on_service_event = on_service_event
        self._on_value_event = on_value_event
        self._runner: web.AppRunner | None = None

    async def start(self) -> int:
        """Start listening. Returns the port it actually bound to."""
        app = web.Application()
        app.router.add_post("/service", self._handle_service)
        app.router.add_post("/value", self._handle_value)

        ssl_context = await asyncio.get_running_loop().run_in_executor(
            None, _build_ssl_context, self._cert_path, self._key_path
        )

        self._runner = web.AppRunner(app)
        await self._runner.setup()

        port = self._port
        last_error: OSError | None = None
        for _ in range(10):
            try:
                site = web.TCPSite(
                    self._runner, "0.0.0.0", port, ssl_context=ssl_context
                )
                await site.start()
                self._port = port
                return port
            except OSError as err:
                last_error = err
                port += 1

        await self._runner.cleanup()
        self._runner = None
        raise OSError(
            f"Could not bind Gira X1 callback server to a free port: {last_error}"
        )

    async def stop(self) -> None:
        if self._runner is not None:
            await self._runner.cleanup()
            self._runner = None

    @property
    def port(self) -> int:
        return self._port

    def _token_matches(self, body: dict) -> bool:
        return body.get("token") == self._expected_token

    async def _handle_service(self, request: web.Request) -> web.Response:
        try:
            body = await request.json()
        except ValueError:
            return web.Response(status=400)
        if not self._token_matches(body):
            _LOGGER.debug("Ignoring service callback with unexpected token")
            return web.Response(status=200)
        await self._on_service_event(body.get("events", []))
        return web.Response(status=200)

    async def _handle_value(self, request: web.Request) -> web.Response:
        try:
            body = await request.json()
        except ValueError:
            return web.Response(status=400)
        if not self._token_matches(body):
            _LOGGER.debug("Ignoring value callback with unexpected token")
            return web.Response(status=200)
        await self._on_value_event(body.get("events", []))
        return web.Response(status=200)
