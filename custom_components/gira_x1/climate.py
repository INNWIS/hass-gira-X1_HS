"""Climate platform for Gira X1 heating/cooling/sauna/fan-coil functions."""
from __future__ import annotations

from homeassistant.components.climate import (
    ClimateEntity,
    ClimateEntityFeature,
    HVACMode,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    DOMAIN,
    FUNCTION_FANCOIL,
    FUNCTION_HEATING_COOLING,
    FUNCTION_SAUNA,
    is_truthy,
)
from .entity import GiraX1Entity


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    data = hass.data[DOMAIN][entry.entry_id]
    coordinator = data["coordinator"]
    entities = [
        GiraX1Climate(coordinator, function)
        for function in data["functions"]
        if function.get("functionType")
        in (FUNCTION_SAUNA, FUNCTION_HEATING_COOLING, FUNCTION_FANCOIL)
    ]
    async_add_entities(entities)


class GiraX1Climate(GiraX1Entity, ClimateEntity):
    """Covers RoomTemperatureSwitchable, KNX.HeatingCoolingSwitchable and KNX.FanCoil."""

    _attr_temperature_unit = UnitOfTemperature.CELSIUS
    _attr_target_temperature_step = 0.5

    def __init__(self, coordinator, function) -> None:
        super().__init__(coordinator, function)
        self._has_onoff = self._dp_uid("OnOff") is not None
        self._has_heat_cool = self._dp_uid("Heat-Cool") is not None

        features = ClimateEntityFeature.TARGET_TEMPERATURE
        if self._has_onoff:
            features |= (
                ClimateEntityFeature.TURN_ON | ClimateEntityFeature.TURN_OFF
            )
        self._attr_supported_features = features

        modes = [HVACMode.HEAT]
        if self._has_onoff:
            modes.append(HVACMode.OFF)
        if self._has_heat_cool:
            modes.append(HVACMode.COOL)
        self._attr_hvac_modes = modes

    @property
    def current_temperature(self) -> float | None:
        try:
            return float(self._get_value("Current"))
        except (TypeError, ValueError):
            return None

    @property
    def target_temperature(self) -> float | None:
        try:
            return float(self._get_value("Set-Point"))
        except (TypeError, ValueError):
            return None

    @property
    def hvac_mode(self) -> HVACMode:
        if self._has_onoff and not is_truthy(self._get_value("OnOff")):
            return HVACMode.OFF
        if self._has_heat_cool and is_truthy(self._get_value("Heat-Cool")):
            return HVACMode.COOL
        return HVACMode.HEAT

    async def async_set_temperature(self, **kwargs) -> None:
        temperature = kwargs.get("temperature")
        if temperature is not None:
            await self._async_set_value("Set-Point", temperature)

    async def async_set_hvac_mode(self, hvac_mode: HVACMode) -> None:
        if hvac_mode == HVACMode.OFF:
            if self._has_onoff:
                await self._async_set_value("OnOff", 0)
            return
        if self._has_onoff:
            await self._async_set_value("OnOff", 1)
        if self._has_heat_cool:
            await self._async_set_value(
                "Heat-Cool", 1 if hvac_mode == HVACMode.COOL else 0
            )

    async def async_turn_on(self) -> None:
        await self._async_set_value("OnOff", 1)

    async def async_turn_off(self) -> None:
        await self._async_set_value("OnOff", 0)
