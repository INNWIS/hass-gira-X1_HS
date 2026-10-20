"""Sensor platform for Gira X1 status value functions."""
from __future__ import annotations

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    DOMAIN,
    FUNCTION_NUMERIC_FLOAT_STATUS,
    FUNCTION_NUMERIC_SIGNED_STATUS,
    FUNCTION_NUMERIC_UNSIGNED_STATUS,
    FUNCTION_TEXT_STATUS,
)
from .entity import GiraX1Entity

NUMERIC_TYPES = (
    FUNCTION_NUMERIC_UNSIGNED_STATUS,
    FUNCTION_NUMERIC_SIGNED_STATUS,
    FUNCTION_NUMERIC_FLOAT_STATUS,
)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    data = hass.data[DOMAIN][entry.entry_id]
    coordinator = data["coordinator"]
    entities: list[GiraX1Entity] = []
    for function in data["functions"]:
        ftype = function.get("functionType")
        if ftype in NUMERIC_TYPES:
            entities.append(
                GiraX1NumericSensor(
                    coordinator, function, is_float=ftype == FUNCTION_NUMERIC_FLOAT_STATUS
                )
            )
        elif ftype == FUNCTION_TEXT_STATUS:
            entities.append(GiraX1TextSensor(coordinator, function))
    async_add_entities(entities)


class _SingleDatapointSensor(GiraX1Entity, SensorEntity):
    """Base for status functions that expose exactly one datapoint."""

    def __init__(self, coordinator, function) -> None:
        super().__init__(coordinator, function)
        self._value_dp_name = next(iter(self._datapoints), None)

    def _raw_value(self):
        if self._value_dp_name is None:
            return None
        return self._get_value(self._value_dp_name)


class GiraX1NumericSensor(_SingleDatapointSensor):
    def __init__(self, coordinator, function, is_float: bool = False) -> None:
        super().__init__(coordinator, function)
        self._is_float = is_float

    @property
    def native_value(self):
        val = self._raw_value()
        if val is None:
            return None
        try:
            return float(val) if self._is_float else int(float(val))
        except (TypeError, ValueError):
            return val


class GiraX1TextSensor(_SingleDatapointSensor):
    @property
    def native_value(self):
        return self._raw_value()
