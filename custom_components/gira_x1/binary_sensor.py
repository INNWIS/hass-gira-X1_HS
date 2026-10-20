"""Binary sensor platform for Gira X1 BinaryStatus functions."""
from __future__ import annotations

from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN, FUNCTION_BINARY_STATUS, is_truthy
from .entity import GiraX1Entity


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    data = hass.data[DOMAIN][entry.entry_id]
    coordinator = data["coordinator"]
    entities = [
        GiraX1BinarySensor(coordinator, function)
        for function in data["functions"]
        if function.get("functionType") == FUNCTION_BINARY_STATUS
    ]
    async_add_entities(entities)


class GiraX1BinarySensor(GiraX1Entity, BinarySensorEntity):
    def __init__(self, coordinator, function) -> None:
        super().__init__(coordinator, function)
        self._value_dp_name = next(iter(self._datapoints), None)

    @property
    def is_on(self) -> bool | None:
        if self._value_dp_name is None:
            return None
        return is_truthy(self._get_value(self._value_dp_name))
