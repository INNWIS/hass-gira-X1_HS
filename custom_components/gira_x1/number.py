"""Number platform for Gira X1 'value transmitter' functions."""
from __future__ import annotations

from homeassistant.components.number import NumberEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    DOMAIN,
    FUNCTION_DECIMAL_VALUE,
    FUNCTION_PERCENT_VALUE,
    FUNCTION_SIGNED8_VALUE,
    FUNCTION_SIGNED_VALUE,
    FUNCTION_TEMPERATURE_VALUE,
    FUNCTION_UNSIGNED8_VALUE,
    FUNCTION_UNSIGNED_VALUE,
)
from .entity import GiraX1Entity

# functionType -> (min, max, step)
VALUE_FUNCTIONS = {
    FUNCTION_UNSIGNED8_VALUE: (0, 255, 1),
    FUNCTION_SIGNED8_VALUE: (-128, 127, 1),
    FUNCTION_PERCENT_VALUE: (0, 100, 1),
    FUNCTION_TEMPERATURE_VALUE: (-50, 100, 0.1),
    FUNCTION_UNSIGNED_VALUE: (0, 4294967295, 1),
    FUNCTION_SIGNED_VALUE: (-2147483648, 2147483647, 1),
    FUNCTION_DECIMAL_VALUE: (-100000, 100000, 0.01),
}


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    data = hass.data[DOMAIN][entry.entry_id]
    coordinator = data["coordinator"]
    entities: list[GiraX1Entity] = []
    for function in data["functions"]:
        ftype = function.get("functionType")
        if ftype in VALUE_FUNCTIONS:
            min_v, max_v, step = VALUE_FUNCTIONS[ftype]
            entities.append(GiraX1Number(coordinator, function, min_v, max_v, step))
    async_add_entities(entities)


class GiraX1Number(GiraX1Entity, NumberEntity):
    def __init__(self, coordinator, function, min_v: float, max_v: float, step: float) -> None:
        super().__init__(coordinator, function)
        self._attr_native_min_value = min_v
        self._attr_native_max_value = max_v
        self._attr_native_step = step
        self._value_dp_name = next(iter(self._datapoints), None)

    @property
    def native_value(self) -> float | None:
        if self._value_dp_name is None:
            return None
        val = self._get_value(self._value_dp_name)
        try:
            return float(val)
        except (TypeError, ValueError):
            return None

    async def async_set_native_value(self, value: float) -> None:
        if self._value_dp_name is not None:
            await self._async_set_value(self._value_dp_name, value)
