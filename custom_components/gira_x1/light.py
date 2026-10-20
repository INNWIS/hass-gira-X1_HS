"""Light platform for Gira X1 dimmer / RGBW / tunable white functions."""
from __future__ import annotations

from homeassistant.components.light import (
    ATTR_BRIGHTNESS,
    ATTR_COLOR_TEMP_KELVIN,
    ATTR_RGBW_COLOR,
    ColorMode,
    LightEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    DOMAIN,
    FUNCTION_COLORED_LIGHT,
    FUNCTION_DIMMER,
    FUNCTION_TUNABLE_LIGHT,
    is_truthy,
)
from .entity import GiraX1Entity


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    data = hass.data[DOMAIN][entry.entry_id]
    coordinator = data["coordinator"]
    entities: list[GiraX1Entity] = []
    for function in data["functions"]:
        ftype = function.get("functionType")
        if ftype == FUNCTION_DIMMER:
            entities.append(GiraX1DimmerLight(coordinator, function))
        elif ftype == FUNCTION_COLORED_LIGHT:
            entities.append(GiraX1RGBWLight(coordinator, function))
        elif ftype == FUNCTION_TUNABLE_LIGHT:
            entities.append(GiraX1TunableLight(coordinator, function))
    async_add_entities(entities)


def _pct_to_255(value) -> int | None:
    try:
        return round(float(value) / 100 * 255)
    except (TypeError, ValueError):
        return None


def _255_to_pct(value: int) -> int:
    return round(value / 255 * 100)


class GiraX1DimmerLight(GiraX1Entity, LightEntity):
    """de.gira.schema.channels.KNX.Dimmer: OnOff (+ optional Brightness/Shift)."""

    def __init__(self, coordinator, function) -> None:
        super().__init__(coordinator, function)
        if self._dp_uid("Brightness") is not None:
            mode = ColorMode.BRIGHTNESS
        else:
            mode = ColorMode.ONOFF
        self._attr_color_mode = mode
        self._attr_supported_color_modes = {mode}

    @property
    def is_on(self) -> bool | None:
        return is_truthy(self._get_value("OnOff"))

    @property
    def brightness(self) -> int | None:
        if self._dp_uid("Brightness") is None:
            return None
        return _pct_to_255(self._get_value("Brightness"))

    async def async_turn_on(self, **kwargs) -> None:
        if ATTR_BRIGHTNESS in kwargs and self._dp_uid("Brightness") is not None:
            await self._async_set_value("Brightness", _255_to_pct(kwargs[ATTR_BRIGHTNESS]))
        else:
            await self._async_set_value("OnOff", 1)

    async def async_turn_off(self, **kwargs) -> None:
        await self._async_set_value("OnOff", 0)


class GiraX1RGBWLight(GiraX1Entity, LightEntity):
    """de.gira.schema.channels.DimmerRGBW: OnOff, Red, Green, Blue (+ White, Brightness)."""

    _attr_color_mode = ColorMode.RGBW
    _attr_supported_color_modes = {ColorMode.RGBW}

    @property
    def is_on(self) -> bool | None:
        return is_truthy(self._get_value("OnOff"))

    @property
    def brightness(self) -> int | None:
        if self._dp_uid("Brightness") is None:
            return None
        return _pct_to_255(self._get_value("Brightness"))

    @property
    def rgbw_color(self):
        try:
            r = _pct_to_255(self._get_value("Red", 0)) or 0
            g = _pct_to_255(self._get_value("Green", 0)) or 0
            b = _pct_to_255(self._get_value("Blue", 0)) or 0
            w = (
                _pct_to_255(self._get_value("White", 0)) or 0
                if self._dp_uid("White") is not None
                else 0
            )
            return (r, g, b, w)
        except (TypeError, ValueError):
            return None

    async def async_turn_on(self, **kwargs) -> None:
        if ATTR_RGBW_COLOR in kwargs:
            r, g, b, w = kwargs[ATTR_RGBW_COLOR]
            await self._async_set_value("Red", _255_to_pct(r))
            await self._async_set_value("Green", _255_to_pct(g))
            await self._async_set_value("Blue", _255_to_pct(b))
            if self._dp_uid("White") is not None:
                await self._async_set_value("White", _255_to_pct(w))
        elif ATTR_BRIGHTNESS in kwargs and self._dp_uid("Brightness") is not None:
            await self._async_set_value("Brightness", _255_to_pct(kwargs[ATTR_BRIGHTNESS]))
        else:
            await self._async_set_value("OnOff", 1)

    async def async_turn_off(self, **kwargs) -> None:
        await self._async_set_value("OnOff", 0)


class GiraX1TunableLight(GiraX1Entity, LightEntity):
    """de.gira.schema.channels.DimmerWhite: OnOff, Color-Temperature (+ Brightness)."""

    _attr_color_mode = ColorMode.COLOR_TEMP
    _attr_supported_color_modes = {ColorMode.COLOR_TEMP}
    _attr_min_color_temp_kelvin = 2000
    _attr_max_color_temp_kelvin = 6500

    @property
    def is_on(self) -> bool | None:
        return is_truthy(self._get_value("OnOff"))

    @property
    def brightness(self) -> int | None:
        if self._dp_uid("Brightness") is None:
            return None
        return _pct_to_255(self._get_value("Brightness"))

    @property
    def color_temp_kelvin(self) -> int | None:
        try:
            return round(float(self._get_value("Color-Temperature")))
        except (TypeError, ValueError):
            return None

    async def async_turn_on(self, **kwargs) -> None:
        if ATTR_COLOR_TEMP_KELVIN in kwargs:
            await self._async_set_value(
                "Color-Temperature", kwargs[ATTR_COLOR_TEMP_KELVIN]
            )
        elif ATTR_BRIGHTNESS in kwargs and self._dp_uid("Brightness") is not None:
            await self._async_set_value("Brightness", _255_to_pct(kwargs[ATTR_BRIGHTNESS]))
        else:
            await self._async_set_value("OnOff", 1)

    async def async_turn_off(self, **kwargs) -> None:
        await self._async_set_value("OnOff", 0)
