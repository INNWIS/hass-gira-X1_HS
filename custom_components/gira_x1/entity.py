"""Base entity for all Gira X1 entities."""
from __future__ import annotations

from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import GiraX1Coordinator


class GiraX1Entity(CoordinatorEntity[GiraX1Coordinator]):
    """Common base for a Gira X1 'function' (light, cover, climate, ...)."""

    _attr_has_entity_name = True

    def __init__(self, coordinator: GiraX1Coordinator, function: dict) -> None:
        super().__init__(coordinator)
        self._function = function
        self._uid = function["uid"]
        self._attr_name = function.get("displayName") or self._uid
        self._attr_unique_id = f"{coordinator.device_id}_{self._uid}"
        # map datapoint "name" (e.g. "OnOff", "Brightness") -> its uid
        self._datapoints = {
            dp["name"]: dp["uid"] for dp in function.get("dataPoints", [])
        }

    @property
    def device_info(self) -> DeviceInfo:
        return DeviceInfo(
            identifiers={(DOMAIN, self.coordinator.device_id)},
            name=self.coordinator.device_name,
            manufacturer="Gira",
            model="X1 / HomeServer / FacilityServer",
        )

    def _dp_uid(self, name: str) -> str | None:
        return self._datapoints.get(name)

    def _get_value(self, name: str, default=None):
        uid = self._dp_uid(name)
        if uid is None:
            return default
        return self.coordinator.data.get(uid, default)

    async def _async_set_value(self, name: str, value) -> None:
        uid = self._dp_uid(name)
        if uid is not None:
            await self.coordinator.async_set_value(uid, value)
