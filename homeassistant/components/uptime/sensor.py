"""Platform to retrieve uptime for Home Assistant."""

from __future__ import annotations

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.util import dt as dt_util

from .const import DOMAIN


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up the platform from config_entry."""
    async_add_entities([UptimeSensor(entry)])


class UptimeSensor(SensorEntity):
    """Representation of an uptime sensor."""

    _attr_device_class = SensorDeviceClass.TIMESTAMP
    _attr_has_entity_name = True
    _attr_name = None
    _attr_should_poll = False  # Keep this false as we don't need to poll external APIs

    def __init__(self, entry: ConfigEntry) -> None:
        """Initialize the uptime sensor."""
        self._attr_native_value = dt_util.utcnow()
        self._attr_unique_id = entry.entry_id
        self._attr_device_info = DeviceInfo(
            name=entry.title,
            identifiers={(DOMAIN, entry.entry_id)},
            entry_type=DeviceEntryType.SERVICE,
        )

    @property
    def extra_state_attributes(self):
        """Return the state attributes."""
        # Calculate the duration between NOW and the START TIME (native_value)
        if self._attr_native_value:
            now = dt_util.utcnow()
            uptime_duration = now - self._attr_native_value
            
            # Extract days, hours, and minutes for the friendly string
            days = uptime_duration.days
            hours, remainder = divmod(uptime_duration.seconds, 3600)
            minutes, _ = divmod(remainder, 60)
            
            # Return the new attribute
            return {
                "friendly_uptime": f"{days}d {hours}h {minutes}m"
            }
        return {}