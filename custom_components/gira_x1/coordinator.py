"""Coordinator that periodically polls all datapoint values from the X1."""
from __future__ import annotations

from datetime import timedelta
import logging

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import GiraX1ApiError, GiraX1Client
from .const import DEFAULT_UPDATE_INTERVAL, POLLABLE_FUNCTIONS

_LOGGER = logging.getLogger(__name__)


class GiraX1Coordinator(DataUpdateCoordinator):
    """Polls values per function and keeps a uid -> value cache."""

    def __init__(
        self,
        hass: HomeAssistant,
        client: GiraX1Client,
        functions: list[dict],
        update_interval: int = DEFAULT_UPDATE_INTERVAL,
    ) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name="gira_x1",
            update_interval=timedelta(seconds=update_interval),
        )
        self.client = client
        # Only poll function types for which we actually create an entity
        # that reads a value. Everything else (Camera, Link, system/service
        # functions, write-only Trigger/Scene functions, ...) is skipped so
        # it can never cause a poll error in the first place.
        self.functions = [
            f for f in functions if f.get("functionType") in POLLABLE_FUNCTIONS
        ]
        self.device_id: str = "gira_x1"
        self.device_name: str = "Gira X1"
        self.values: dict[str, object] = {}
        self._broken_uids: set[str] = set()

    async def _async_update_data(self) -> dict[str, object]:
        any_success = False
        last_error: Exception | None = None

        for function in self.functions:
            uid = function["uid"]
            if uid in self._broken_uids:
                continue
            try:
                items = await self.client.get_values(uid)
            except GiraX1ApiError as err:
                # Don't let one broken/unsupported function abort the whole
                # poll cycle; log it once and skip it from now on.
                _LOGGER.warning(
                    "Could not read values for function %s (%s), skipping it "
                    "from now on: %s",
                    uid,
                    function.get("displayName", uid),
                    err,
                )
                self._broken_uids.add(uid)
                last_error = err
                continue
            else:
                any_success = True
                for item in items:
                    self.values[item["uid"]] = item.get("value")

        if not any_success and self.functions and last_error is not None:
            raise UpdateFailed(str(last_error))

        return self.values

    async def async_set_value(self, uid: str | None, value) -> None:
        """Write a value to the device and optimistically update local cache."""
        if uid is None:
            return
        await self.client.set_value(uid, value)
        self.values[uid] = value
        self.async_set_updated_data(self.values)
