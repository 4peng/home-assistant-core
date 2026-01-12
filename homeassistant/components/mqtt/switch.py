"""Support for MQTT switches."""
from __future__ import annotations

import logging
from typing import Any, Final

import voluptuous as vol

from homeassistant.components import mqtt
from homeassistant.components.mqtt import (
    CONF_COMMAND_TOPIC,
    CONF_QOS,
    CONF_RETAIN,
    CONF_STATE_TOPIC,
    subscription,
)
from homeassistant.components.mqtt.entity import MqttEntity, async_setup_entry_helper
from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    CONF_NAME,
    CONF_OPTIMISTIC,
    CONF_PAYLOAD_OFF,
    CONF_PAYLOAD_ON,
)
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType

_LOGGER = logging.getLogger(__name__)

DEFAULT_NAME: Final = "MQTT Switch"
DEFAULT_PAYLOAD_ON: Final = "ON"
DEFAULT_PAYLOAD_OFF: Final = "OFF"
DEFAULT_OPTIMISTIC: Final = False

PLATFORM_SCHEMA = mqtt.MQTT_RW_PLATFORM_SCHEMA.extend(
    {
        vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string,
        vol.Optional(CONF_COMMAND_TOPIC): mqtt.valid_publish_topic,
        vol.Optional(CONF_STATE_TOPIC): mqtt.valid_subscribe_topic,
        vol.Optional(CONF_PAYLOAD_ON, default=DEFAULT_PAYLOAD_ON): cv.string,
        vol.Optional(CONF_PAYLOAD_OFF, default=DEFAULT_PAYLOAD_OFF): cv.string,
        vol.Optional(CONF_OPTIMISTIC, default=DEFAULT_OPTIMISTIC): cv.boolean,
    }
)

async def async_setup_platform(
    hass: HomeAssistant,
    config: ConfigType,
    async_add_entities: AddEntitiesCallback,
    discovery_info: DiscoveryInfoType | None = None,
) -> None:
    """Set up MQTT switch through configuration.yaml."""
    await async_setup_entry_helper(hass, config, async_add_entities, MqttSwitch, discovery_info)

async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up MQTT switch dynamically through MQTT discovery."""
    setup = functools.partial(
        _async_setup_entity, hass=hass, async_add_entities=async_add_entities, config_entry=config_entry
    )
    await mqtt.async_setup_entry_helper(hass, config_entry, setup, MqttSwitch)

class MqttSwitch(MqttEntity, SwitchEntity):
    """Representation of a switch that can be toggled using MQTT."""

    _entity_id_format = "switch.{}"

    def __init__(self, hass: HomeAssistant, config: ConfigType, config_entry: ConfigEntry, discovery_data: Any) -> None:
        """Initialize the MQTT switch."""
        MqttEntity.__init__(self, hass, config, config_entry, discovery_data)

    @property
    def is_on(self) -> bool | None:
        """Return true if device is on."""
        return self._attr_is_on

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the device on.

        This publishes a message to the command topic.
        """
        await mqtt.async_publish(
            self.hass,
            self._config[CONF_COMMAND_TOPIC],
            self._config[CONF_PAYLOAD_ON],
            self._config[CONF_QOS],
            self._config[CONF_RETAIN],
        )
        if self._config[CONF_OPTIMISTIC]:
            self._attr_is_on = True
            self.async_write_ha_state()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the device off.

        This publishes a message to the command topic.
        """
        await mqtt.async_publish(
            self.hass,
            self._config[CONF_COMMAND_TOPIC],
            self._config[CONF_PAYLOAD_OFF],
            self._config[CONF_QOS],
            self._config[CONF_RETAIN],
        )
        if self._config[CONF_OPTIMISTIC]:
            self._attr_is_on = False
            self.async_write_ha_state()