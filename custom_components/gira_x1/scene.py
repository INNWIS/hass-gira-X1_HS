"""Scene platform for Gira X1 Scene functions."""
from __future__ import annotations

from homeassistant.components.scene import Scene
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN, FUNCTION_SCENE
from .entity import GiraX1Entity


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    data = hass.data[DOMAIN][entry.entry_id]
    coordinator = data["coordinator"]
    entities = [
        GiraX1Scene(coordinator, function)
        for function in data["functions"]
        if function.get("functionType") == FUNCTION_SCENE
    ]
    async_add_entities(entities)


class GiraX1Scene(GiraX1Entity, Scene):
    """Covers both SceneSet ('Execute') and SceneControl ('Scene') channels."""

    async def async_activate(self, **kwargs) -> None:
        if self._dp_uid("Execute") is not None:
            await self._async_set_value("Execute", 1)
        elif self._dp_uid("Scene") is not None:
            await self._async_set_value("Scene", 1)
