"""Demo lock platform that offers a fake lock."""
from __future__ import annotations

from typing import Any

from homeassistant.components.lock import LockEntity, LockEntityFeature
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType

LIGHT_LOCK = "Front Door"
DEMO_LOCK = "Kitchen"


async def async_setup_platform(
    hass: HomeAssistant,
    config: ConfigType,
    async_add_entities: AddEntitiesCallback,
    discovery_info: DiscoveryInfoType | None = None,
) -> None:
    """Set up the Demo lock platform."""
    async_add_entities(
        [
            DemoLock(LIGHT_LOCK, LockEntityFeature.OPEN),
            DemoLock(DEMO_LOCK, LockEntityFeature.OPEN),
        ]
    )


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Demo config entry."""
    await async_setup_platform(hass, {}, async_add_entities)


class DemoLock(LockEntity):
    """Representation of a Demo lock."""

    _attr_should_poll = False

    def __init__(self, name: str, features: LockEntityFeature) -> None:
        """Initialize the lock."""
        self._attr_name = name
        self._attr_supported_features = features
        self._attr_is_locked = True
        self._attr_is_jammed = False

    def lock(self, **kwargs: Any) -> None:
        """Lock the device."""
        self._attr_is_locked = True
        self.schedule_update_ha_state()

    def unlock(self, **kwargs: Any) -> None:
        """Unlock the device."""
        self._attr_is_locked = False
        self.schedule_update_ha_state()

    def open(self, **kwargs: Any) -> None:
        """Open the door latch."""
        self.schedule_update_ha_state()