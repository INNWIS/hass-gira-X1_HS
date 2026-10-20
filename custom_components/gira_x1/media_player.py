"""Media player platform for Gira X1 Audio / Sonos-Audio functions."""
from __future__ import annotations

from homeassistant.components.media_player import (
    MediaPlayerEntity,
    MediaPlayerEntityFeature,
    MediaPlayerState,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN, FUNCTION_AUDIO, FUNCTION_SONOS_AUDIO, is_truthy
from .entity import GiraX1Entity


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    data = hass.data[DOMAIN][entry.entry_id]
    coordinator = data["coordinator"]
    entities = [
        GiraX1MediaPlayer(coordinator, function)
        for function in data["functions"]
        if function.get("functionType") in (FUNCTION_AUDIO, FUNCTION_SONOS_AUDIO)
    ]
    async_add_entities(entities)


class GiraX1MediaPlayer(GiraX1Entity, MediaPlayerEntity):
    """AudioWithPlaylist channel (also used as base for Sonos.Audio)."""

    def __init__(self, coordinator, function) -> None:
        super().__init__(coordinator, function)
        features = (
            MediaPlayerEntityFeature.PLAY
            | MediaPlayerEntityFeature.PAUSE
            | MediaPlayerEntityFeature.VOLUME_SET
        )
        if self._dp_uid("Mute") is not None:
            features |= MediaPlayerEntityFeature.VOLUME_MUTE
        if self._dp_uid("Previous") is not None:
            features |= MediaPlayerEntityFeature.PREVIOUS_TRACK
        if self._dp_uid("Next") is not None:
            features |= MediaPlayerEntityFeature.NEXT_TRACK
        self._attr_supported_features = features

    @property
    def state(self) -> MediaPlayerState | None:
        val = self._get_value("Play")
        if val is None:
            return None
        return MediaPlayerState.PLAYING if is_truthy(val) else MediaPlayerState.PAUSED

    @property
    def volume_level(self) -> float | None:
        try:
            return float(self._get_value("Volume")) / 100
        except (TypeError, ValueError):
            return None

    @property
    def is_volume_muted(self) -> bool | None:
        if self._dp_uid("Mute") is None:
            return None
        return is_truthy(self._get_value("Mute"))

    @property
    def media_title(self) -> str | None:
        return self._get_value("Title")

    @property
    def media_artist(self) -> str | None:
        return self._get_value("Artist")

    @property
    def media_album_name(self) -> str | None:
        return self._get_value("Album")

    async def async_media_play(self) -> None:
        await self._async_set_value("Play", 1)

    async def async_media_pause(self) -> None:
        await self._async_set_value("Play", 0)

    async def async_set_volume_level(self, volume: float) -> None:
        await self._async_set_value("Volume", round(volume * 100))

    async def async_mute_volume(self, mute: bool) -> None:
        if self._dp_uid("Mute") is not None:
            await self._async_set_value("Mute", 1 if mute else 0)

    async def async_media_previous_track(self) -> None:
        await self._async_set_value("Previous", 1)

    async def async_media_next_track(self) -> None:
        await self._async_set_value("Next", 1)
