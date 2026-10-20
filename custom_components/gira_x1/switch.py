"""Switch platform for Gira X1 on/off (Switch) functions."""
from __future__ import annotations

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN, FUNCTION_SWITCH, is_truthy
from .entity import GiraX1Entity


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    data = hass.data[DOMAIN][entry.entry_id]
    coordinator = data["coordinator"]
    entities = [
        GiraX1Switch(coordinator, function)
        for function in data["functions"]
        if function.get("functionType") == FUNCTION_SWITCH
    ]
    async_add_entities(entities)


class GiraX1Switch(GiraX1Entity, SwitchEntity):
    """de.gira.schema.channels.Switch: OnOff."""

    @property
    def is_on(self) -> bool | None:
        return is_truthy(self._get_value("OnOff"))

    async def async_turn_on(self, **kwargs) -> None:
        await self._async_set_value("OnOff", 1)

    async def async_turn_off(self, **kwargs) -> None:
        await self._async_set_value("OnOff", 0)
