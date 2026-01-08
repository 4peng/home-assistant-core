"""Test the Schedule override mechanism."""

from __future__ import annotations

from datetime import timedelta
from typing import Any

from freezegun.api import FrozenDateTimeFactory
import pytest

from homeassistant.components.schedule import STORAGE_VERSION, STORAGE_VERSION_MINOR
from homeassistant.components.schedule.const import (
    ATTR_NEXT_EVENT,
    ATTR_OVERRIDE_ACTIVE,
    ATTR_OVERRIDE_REASON,
    ATTR_OVERRIDE_STATE,
    ATTR_OVERRIDE_UNTIL,
    CONF_DURATION,
    CONF_FROM,
    CONF_REASON,
    CONF_STATE,
    CONF_SUNDAY,
    CONF_TO,
    CONF_UNTIL,
    DOMAIN,
    SERVICE_CLEAR_OVERRIDE,
    SERVICE_SET_OVERRIDE,
)
from homeassistant.const import (
    CONF_ENTITY_ID,
    CONF_ICON,
    CONF_ID,
    CONF_NAME,
    STATE_OFF,
    STATE_ON,
)
from homeassistant.core import HomeAssistant
from homeassistant.setup import async_setup_component
from homeassistant.util import dt as dt_util

from tests.common import async_fire_time_changed


@pytest.fixture
async def schedule_setup(hass: HomeAssistant, hass_storage: dict[str, Any]):
    """Schedule setup."""
    hass_storage[DOMAIN] = {
        "key": DOMAIN,
        "version": STORAGE_VERSION,
        "minor_version": STORAGE_VERSION_MINOR,
        "data": {
            "items": [
                {
                    CONF_ID: "test_schedule",
                    CONF_NAME: "Test Schedule",
                    CONF_ICON: "mdi:calendar",
                    CONF_SUNDAY: [
                        {
                            CONF_FROM: "10:00:00",
                            CONF_TO: "12:00:00",
                        },
                    ],
                }
            ]
        },
    }
    assert await async_setup_component(hass, DOMAIN, {})
    await hass.async_block_till_done()


@pytest.mark.enable_socket
async def test_override_indefinite(
    hass: HomeAssistant,
    schedule_setup: None,
    freezer: FrozenDateTimeFactory,
) -> None:
    """Test setting an indefinite override."""
    # Sunday 11:00 AM - Schedule should be ON
    freezer.move_to("2022-09-04 11:00:00-07:00")
    async_fire_time_changed(hass)
    await hass.async_block_till_done()

    state = hass.states.get("schedule.test_schedule")
    assert state.state == STATE_ON

    # Override to OFF indefinitely
    await hass.services.async_call(
        DOMAIN,
        SERVICE_SET_OVERRIDE,
        {
            CONF_ENTITY_ID: "schedule.test_schedule",
            CONF_STATE: STATE_OFF,
            CONF_REASON: "Vacation",
        },
        blocking=True,
    )

    state = hass.states.get("schedule.test_schedule")
    assert state.state == STATE_OFF
    assert state.attributes[ATTR_OVERRIDE_ACTIVE] is True
    assert state.attributes[ATTR_OVERRIDE_STATE] == STATE_OFF
    assert state.attributes[ATTR_OVERRIDE_REASON] == "Vacation"
    assert state.attributes.get(ATTR_OVERRIDE_UNTIL) is None
    assert state.attributes.get(ATTR_NEXT_EVENT) is None

    # Advance time significantly, still OFF
    freezer.move_to("2022-09-05 11:00:00-07:00")
    async_fire_time_changed(hass)
    await hass.async_block_till_done()

    state = hass.states.get("schedule.test_schedule")
    assert state.state == STATE_OFF

    # Clear override
    await hass.services.async_call(
        DOMAIN,
        SERVICE_CLEAR_OVERRIDE,
        {CONF_ENTITY_ID: "schedule.test_schedule"},
        blocking=True,
    )

    state = hass.states.get("schedule.test_schedule")
    # Monday 11:00 AM - Schedule should be OFF (schedule only on Sunday)
    assert state.state == STATE_OFF
    assert state.attributes[ATTR_OVERRIDE_ACTIVE] is False
    assert state.attributes.get(ATTR_OVERRIDE_STATE) is None


@pytest.mark.enable_socket
async def test_override_with_duration(
    hass: HomeAssistant,
    schedule_setup: None,
    freezer: FrozenDateTimeFactory,
) -> None:
    """Test override with duration."""
    # Sunday 09:00 AM - Schedule OFF
    now = dt_util.parse_datetime("2022-09-04 09:00:00-07:00")
    freezer.move_to(now)
    async_fire_time_changed(hass)
    await hass.async_block_till_done()

    state = hass.states.get("schedule.test_schedule")
    assert state.state == STATE_OFF

    # Override to ON for 1 hour
    await hass.services.async_call(
        DOMAIN,
        SERVICE_SET_OVERRIDE,
        {
            CONF_ENTITY_ID: "schedule.test_schedule",
            CONF_STATE: STATE_ON,
            CONF_DURATION: {"hours": 1},
        },
        blocking=True,
    )

    state = hass.states.get("schedule.test_schedule")
    assert state.state == STATE_ON
    assert state.attributes[ATTR_OVERRIDE_ACTIVE] is True

    # Check expiry
    expiration = now + timedelta(hours=1)
    assert state.attributes[ATTR_OVERRIDE_UNTIL] == expiration
    assert state.attributes[ATTR_NEXT_EVENT] == expiration

    # Advance to just before expiration
    freezer.move_to(expiration - timedelta(seconds=1))
    async_fire_time_changed(hass)
    await hass.async_block_till_done()

    state = hass.states.get("schedule.test_schedule")
    assert state.state == STATE_ON
    assert state.attributes[ATTR_OVERRIDE_ACTIVE] is True

    # Advance to expiration
    freezer.move_to(expiration)
    async_fire_time_changed(hass)
    await hass.async_block_till_done()

    state = hass.states.get("schedule.test_schedule")
    # 10:00 AM - Schedule normally turns ON at 10:00, so it should stay ON
    # but override attributes should be gone
    assert state.state == STATE_ON
    assert state.attributes[ATTR_OVERRIDE_ACTIVE] is False
    assert state.attributes.get(ATTR_OVERRIDE_STATE) is None


@pytest.mark.enable_socket
async def test_override_with_until(
    hass: HomeAssistant,
    schedule_setup: None,
    freezer: FrozenDateTimeFactory,
) -> None:
    """Test override with explicit until time."""
    # Sunday 11:00 AM - Schedule ON
    now = dt_util.parse_datetime("2022-09-04 11:00:00-07:00")
    freezer.move_to(now)
    async_fire_time_changed(hass)
    await hass.async_block_till_done()

    state = hass.states.get("schedule.test_schedule")
    assert state.state == STATE_ON

    # Override to OFF until 11:30 AM
    until = dt_util.parse_datetime("2022-09-04 11:30:00-07:00")

    await hass.services.async_call(
        DOMAIN,
        SERVICE_SET_OVERRIDE,
        {
            CONF_ENTITY_ID: "schedule.test_schedule",
            CONF_STATE: STATE_OFF,
            CONF_UNTIL: until,
        },
        blocking=True,
    )

    state = hass.states.get("schedule.test_schedule")
    assert state.state == STATE_OFF
    assert state.attributes[ATTR_OVERRIDE_ACTIVE] is True
    assert state.attributes[ATTR_OVERRIDE_UNTIL] == until

    # Advance to 11:30 AM
    freezer.move_to(until)
    async_fire_time_changed(hass)
    await hass.async_block_till_done()

    state = hass.states.get("schedule.test_schedule")
    # 11:30 AM - Schedule is still normally ON (until 12:00)
    assert state.state == STATE_ON
    assert state.attributes[ATTR_OVERRIDE_ACTIVE] is False
