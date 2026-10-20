"""The Gira X1 integration."""
from __future__ import annotations

from datetime import timedelta
import logging
import socket

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_PASSWORD, CONF_USERNAME, Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import GiraX1ApiError, GiraX1Client
from .cert import ensure_certificate
from .const import (
    CALLBACK_PORT_DEFAULT,
    CLIENT_ID,
    DEFAULT_UPDATE_INTERVAL,
    DOMAIN,
    PUSH_FALLBACK_POLL_INTERVAL,
)
from .coordinator import GiraX1Coordinator
from .webhook_server import GiraX1CallbackServer

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [
    Platform.LIGHT,
    Platform.COVER,
    Platform.CLIMATE,
    Platform.SWITCH,
    Platform.SENSOR,
    Platform.BINARY_SENSOR,
    Platform.NUMBER,
    Platform.BUTTON,
    Platform.SCENE,
    Platform.MEDIA_PLAYER,
]


def _get_local_ip_for(remote_host: str) -> str:
    """Return the local IP HA uses to reach remote_host (no data is sent)."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        sock.connect((remote_host, 443))
        return sock.getsockname()[0]
    finally:
        sock.close()


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Gira X1 from a config entry."""
    session = async_get_clientsession(hass, verify_ssl=False)
    client = GiraX1Client(
        session,
        entry.data[CONF_HOST],
        entry.data[CONF_USERNAME],
        entry.data[CONF_PASSWORD],
        CLIENT_ID,
    )

    try:
        token = await client.register()
        ui_config = await client.get_ui_config()
    except GiraX1ApiError as err:
        raise ConfigEntryNotReady(
            f"Could not connect to Gira X1 at {entry.data[CONF_HOST]}: {err}"
        ) from err

    functions = ui_config.get("functions", [])

    coordinator = GiraX1Coordinator(hass, client, functions)
    coordinator.device_id = entry.entry_id
    coordinator.device_name = f"Gira X1 ({entry.data[CONF_HOST]})"

    await coordinator.async_config_entry_first_refresh()

    entry_data: dict = {
        "client": client,
        "coordinator": coordinator,
        "functions": functions,
        "callback_server": None,
    }
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = entry_data

    await _async_setup_push_updates(hass, entry, entry_data, token)

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(async_reload_entry))
    return True


async def _async_setup_push_updates(
    hass: HomeAssistant, entry: ConfigEntry, entry_data: dict, token: str
) -> None:
    """Best-effort: start a local HTTPS server and register it with the X1
    so value/service changes are pushed instantly instead of only polled.

    If anything goes wrong (port blocked, X1 can't reach HA, callback test
    fails, ...) this silently falls back to the regular polling interval.
    """
    client: GiraX1Client = entry_data["client"]
    coordinator: GiraX1Coordinator = entry_data["coordinator"]
    host = entry.data[CONF_HOST]

    try:
        local_ip = await hass.async_add_executor_job(_get_local_ip_for, host)

        cert_dir = hass.config.path(".storage", "gira_x1")
        cert_path = f"{cert_dir}/cert.pem"
        key_path = f"{cert_dir}/key.pem"
        await hass.async_add_executor_job(ensure_certificate, cert_path, key_path)

        async def _on_value_event(events: list[dict]) -> None:
            for event in events:
                if "uid" in event:
                    coordinator.values[event["uid"]] = event.get("value")
            coordinator.async_set_updated_data(coordinator.values)

        async def _on_service_event(events: list[dict]) -> None:
            for event in events:
                if event.get("event") == "uiConfigChanged":
                    _LOGGER.info(
                        "Gira X1 project configuration changed, reloading "
                        "the integration to pick up new/changed functions"
                    )
                    hass.async_create_task(
                        hass.config_entries.async_reload(entry.entry_id)
                    )

        server = GiraX1CallbackServer(
            CALLBACK_PORT_DEFAULT,
            cert_path,
            key_path,
            token,
            _on_service_event,
            _on_value_event,
        )
        bound_port = await server.start()
        entry_data["callback_server"] = server

        service_url = f"https://{local_ip}:{bound_port}/service"
        value_url = f"https://{local_ip}:{bound_port}/value"

        await client.register_callbacks(service_url, value_url, test=True)

        # Push works: only keep a slow safety-net poll running.
        coordinator.update_interval = timedelta(seconds=PUSH_FALLBACK_POLL_INTERVAL)
        _LOGGER.info(
            "Gira X1 push updates enabled (callback server on port %s, "
            "advertised as %s)",
            bound_port,
            local_ip,
        )
    except Exception as err:  # noqa: BLE001
        _LOGGER.warning(
            "Could not enable Gira X1 push updates (%s); falling back to "
            "polling every %s seconds. This is not fatal, entities will "
            "keep working, just with a small delay.",
            err,
            DEFAULT_UPDATE_INTERVAL,
        )
        server = entry_data.get("callback_server")
        if server is not None:
            await server.stop()
            entry_data["callback_server"] = None
        coordinator.update_interval = timedelta(seconds=DEFAULT_UPDATE_INTERVAL)


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload the config entry when options change."""
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        data = hass.data[DOMAIN].pop(entry.entry_id)
        server: GiraX1CallbackServer | None = data.get("callback_server")
        if server is not None:
            await server.stop()
        client: GiraX1Client = data["client"]
        await client.remove_callbacks()
        await client.unregister()
    return unload_ok
