"""Button platform for Gira X1 Trigger functions."""
from __future__ import annotations

from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN, FUNCTION_TRIGGER
from .entity import GiraX1Entity


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    data = hass.data[DOMAIN][entry.entry_id]
    coordinator = data["coordinator"]
    entities = [
        GiraX1Button(coordinator, function)
        for function in data["functions"]
        if function.get("functionType") == FUNCTION_TRIGGER
    ]
    async_add_entities(entities)


class GiraX1Button(GiraX1Entity, ButtonEntity):
    """de.gira.schema.channels.Trigger: writes 1 to the Trigger datapoint."""

    async def async_press(self) -> None:
        await self._async_set_value("Trigger", 1)
