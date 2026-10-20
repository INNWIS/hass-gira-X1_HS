"""Cover platform for Gira X1 shutter/blind functions."""
from __future__ import annotations

from homeassistant.components.cover import (
    CoverDeviceClass,
    CoverEntity,
    CoverEntityFeature,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN, FUNCTION_COVERING
from .entity import GiraX1Entity


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    data = hass.data[DOMAIN][entry.entry_id]
    coordinator = data["coordinator"]
    entities = [
        GiraX1Cover(coordinator, function)
        for function in data["functions"]
        if function.get("functionType") == FUNCTION_COVERING
    ]
    async_add_entities(entities)


class GiraX1Cover(GiraX1Entity, CoverEntity):
    """de.gira.schema.channels.BlindWithPos."""

    _attr_device_class = CoverDeviceClass.SHUTTER

    def __init__(self, coordinator, function) -> None:
        super().__init__(coordinator, function)
        features = (
            CoverEntityFeature.OPEN
            | CoverEntityFeature.CLOSE
            | CoverEntityFeature.STOP
        )
        if self._dp_uid("Position") is not None:
            features |= CoverEntityFeature.SET_POSITION
        if self._dp_uid("Slat-Position") is not None:
            features |= (
                CoverEntityFeature.SET_TILT_POSITION
                | CoverEntityFeature.OPEN_TILT
                | CoverEntityFeature.CLOSE_TILT
            )
        self._attr_supported_features = features

    @staticmethod
    def _invert(value) -> int | None:
        try:
            return 100 - int(round(float(value)))
        except (TypeError, ValueError):
            return None

    @property
    def current_cover_position(self) -> int | None:
        # Gira: 0% = fully open, 100% = fully closed. HA is the inverse.
        if self._dp_uid("Position") is None:
            return None
        return self._invert(self._get_value("Position"))

    @property
    def current_cover_tilt_position(self) -> int | None:
        if self._dp_uid("Slat-Position") is None:
            return None
        return self._invert(self._get_value("Slat-Position"))

    @property
    def is_closed(self) -> bool | None:
        pos = self.current_cover_position
        if pos is None:
            return None
        return pos <= 0

    async def async_open_cover(self, **kwargs) -> None:
        await self._async_set_value("Up-Down", 0)

    async def async_close_cover(self, **kwargs) -> None:
        await self._async_set_value("Up-Down", 1)

    async def async_stop_cover(self, **kwargs) -> None:
        await self._async_set_value("Step-Up-Down", 0)

    async def async_set_cover_position(self, **kwargs) -> None:
        position = kwargs.get("position")
        if position is not None:
            await self._async_set_value("Position", 100 - position)

    async def async_open_cover_tilt(self, **kwargs) -> None:
        await self._async_set_value("Slat-Position", 0)

    async def async_close_cover_tilt(self, **kwargs) -> None:
        await self._async_set_value("Slat-Position", 100)

    async def async_set_cover_tilt_position(self, **kwargs) -> None:
        tilt = kwargs.get("tilt_position")
        if tilt is not None:
            await self._async_set_value("Slat-Position", 100 - tilt)
