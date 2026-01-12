"""Support for functionality to keep track of the sun."""

from __future__ import annotations

from datetime import datetime, timedelta
import logging
from typing import Any

from astral.location import Elevation, Location

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EVENT_CORE_CONFIG_UPDATE
from homeassistant.core import CALLBACK_TYPE, Event, HomeAssistant, callback
from homeassistant.helpers import event
from homeassistant.helpers.dispatcher import async_dispatcher_send
from homeassistant.helpers.entity import Entity
from homeassistant.helpers.sun import get_astral_location
from homeassistant.util import dt as dt_util

from .const import (
    CONF_ELEVATION_UPDATE_INTERVAL,
    PHASE_ASTRONOMICAL_TWILIGHT,
    PHASE_DAY,
    PHASE_NAUTICAL_TWILIGHT,
    PHASE_NIGHT,
    PHASE_SMALL_DAY,
    PHASE_TWILIGHT,
    SIGNAL_EVENTS_CHANGED,
    SIGNAL_POSITION_CHANGED,
    STATE_ABOVE_HORIZON,
    STATE_ATTR_AZIMUTH,
    STATE_ATTR_ELEVATION,
    STATE_ATTR_NEXT_BLUE_HOUR_END,
    STATE_ATTR_NEXT_BLUE_HOUR_START,
    STATE_ATTR_NEXT_DAWN,
    STATE_ATTR_NEXT_DUSK,
    STATE_ATTR_NEXT_GOLDEN_HOUR_END,
    STATE_ATTR_NEXT_GOLDEN_HOUR_START,
    STATE_ATTR_NEXT_MIDNIGHT,
    STATE_ATTR_NEXT_NOON,
    STATE_ATTR_NEXT_RISING,
    STATE_ATTR_NEXT_SETTING,
    STATE_ATTR_RISING,
    STATE_BELOW_HORIZON,
)
from .util import get_sun_state

type SunConfigEntry = ConfigEntry[Sun]

_LOGGER = logging.getLogger(__name__)

ENTITY_ID = "sun.sun"

# 4 mins is one degree of arc change of the sun on its circle.
# During the night and the middle of the day we don't update
# that much since it's not important.
_PHASE_UPDATES = {
    PHASE_NIGHT: timedelta(minutes=4 * 5),
    PHASE_ASTRONOMICAL_TWILIGHT: timedelta(minutes=4 * 2),
    PHASE_NAUTICAL_TWILIGHT: timedelta(minutes=4),
    PHASE_TWILIGHT: timedelta(minutes=2),
    PHASE_SMALL_DAY: timedelta(minutes=2),
    PHASE_DAY: timedelta(minutes=4),
}


class Sun(Entity):
    """Representation of the Sun."""

    _unrecorded_attributes = frozenset(
        {
            STATE_ATTR_AZIMUTH,
            STATE_ATTR_ELEVATION,
            STATE_ATTR_RISING,
            STATE_ATTR_NEXT_DAWN,
            STATE_ATTR_NEXT_DUSK,
            STATE_ATTR_NEXT_MIDNIGHT,
            STATE_ATTR_NEXT_NOON,
            STATE_ATTR_NEXT_RISING,
            STATE_ATTR_NEXT_SETTING,
            STATE_ATTR_NEXT_GOLDEN_HOUR_START,
            STATE_ATTR_NEXT_GOLDEN_HOUR_END,
            STATE_ATTR_NEXT_BLUE_HOUR_START,
            STATE_ATTR_NEXT_BLUE_HOUR_END,
        }
    )

    _attr_name = "Sun"
    entity_id = ENTITY_ID

    location: Location
    elevation: Elevation
    next_rising: datetime
    next_setting: datetime
    next_dawn: datetime
    next_dusk: datetime
    next_midnight: datetime
    next_noon: datetime
    solar_elevation: float
    solar_azimuth: float
    rising: bool
    _next_change: datetime
    next_golden_hour_start: datetime | None
    next_golden_hour_end: datetime | None
    next_blue_hour_start: datetime | None
    next_blue_hour_end: datetime | None

    def __init__(self, hass: HomeAssistant, entry: SunConfigEntry | None = None) -> None:
        """Initialize the sun."""
        self.hass = hass
        self.entry = entry
        self.phase: str | None = None

        self._config_listener: CALLBACK_TYPE | None = None
        self._update_events_listener: CALLBACK_TYPE | None = None
        self._update_sun_position_listener: CALLBACK_TYPE | None = None
        self._config_listener = self.hass.bus.async_listen(
            EVENT_CORE_CONFIG_UPDATE, self.update_location
        )

    async def async_added_to_hass(self) -> None:
        """Update after entity has been added."""
        await super().async_added_to_hass()
        self.update_location(initial=True)

    @callback
    def update_location(self, _: Event | None = None, initial: bool = False) -> None:
        """Update location."""
        location, elevation = get_astral_location(self.hass)
        if not initial and location == self.location:
            return
        self.location = location
        self.elevation = elevation
        if self._update_events_listener:
            self._update_events_listener()
        self.update_events()

    @callback
    def remove_listeners(self) -> None:
        """Remove listeners."""
        if self._config_listener:
            self._config_listener()
        if self._update_events_listener:
            self._update_events_listener()
        if self._update_sun_position_listener:
            self._update_sun_position_listener()

    @property
    def state(self) -> str:
        """Return the state of the sun."""
        # 0.8333 is the same value as astral uses
        if self.solar_elevation > -0.833:
            return STATE_ABOVE_HORIZON

        return STATE_BELOW_HORIZON

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return the state attributes of the sun."""
        data = {
            STATE_ATTR_NEXT_DAWN: self.next_dawn.isoformat(),
            STATE_ATTR_NEXT_DUSK: self.next_dusk.isoformat(),
            STATE_ATTR_NEXT_MIDNIGHT: self.next_midnight.isoformat(),
            STATE_ATTR_NEXT_NOON: self.next_noon.isoformat(),
            STATE_ATTR_NEXT_RISING: self.next_rising.isoformat(),
            STATE_ATTR_NEXT_SETTING: self.next_setting.isoformat(),
            STATE_ATTR_ELEVATION: self.solar_elevation,
            STATE_ATTR_AZIMUTH: self.solar_azimuth,
            STATE_ATTR_RISING: self.rising,
        }
        if self.next_golden_hour_start:
            data[STATE_ATTR_NEXT_GOLDEN_HOUR_START] = (
                self.next_golden_hour_start.isoformat()
            )
        if self.next_golden_hour_end:
            data[STATE_ATTR_NEXT_GOLDEN_HOUR_END] = (
                self.next_golden_hour_end.isoformat()
            )
        if self.next_blue_hour_start:
            data[STATE_ATTR_NEXT_BLUE_HOUR_START] = (
                self.next_blue_hour_start.isoformat()
            )
        if self.next_blue_hour_end:
            data[STATE_ATTR_NEXT_BLUE_HOUR_END] = self.next_blue_hour_end.isoformat()
        return data

    @callback
    def update_events(self, now: datetime | None = None) -> None:
        """Update the attributes containing solar events."""
        # Grab current time in case system clock changed since last time we ran.
        utc_point_in_time = dt_util.utcnow()
        
        sun_state = get_sun_state(self.location, self.elevation, utc_point_in_time)

        self.next_dawn = sun_state.next_dawn
        self.next_dusk = sun_state.next_dusk
        self.next_midnight = sun_state.next_midnight
        self.next_noon = sun_state.next_noon
        self.next_rising = sun_state.next_rising
        self.next_setting = sun_state.next_setting
        self.phase = sun_state.phase
        self.rising = sun_state.rising
        self._next_change = sun_state.next_change
        
        self.next_golden_hour_start = sun_state.next_golden_hour_start
        self.next_golden_hour_end = sun_state.next_golden_hour_end
        self.next_blue_hour_start = sun_state.next_blue_hour_start
        self.next_blue_hour_end = sun_state.next_blue_hour_end

        _LOGGER.debug(
            "sun phase_update@%s: phase=%s", utc_point_in_time.isoformat(), self.phase
        )
        if self._update_sun_position_listener:
            self._update_sun_position_listener()
        self.update_sun_position()
        async_dispatcher_send(self.hass, SIGNAL_EVENTS_CHANGED)

        # Safety guard: Ensure next change is in the future
        # to prevent infinite loops (Time Travel Bug)
        if self._next_change <= utc_point_in_time:
             self._next_change = utc_point_in_time + timedelta(seconds=10)
             _LOGGER.warning(
                 "Solar event calculation loop protection enabled, next change: %s, now: %s",
                 self._next_change,
                 utc_point_in_time,
             )

        # Set timer for the next solar event
        self._update_events_listener = event.async_track_point_in_utc_time(
            self.hass, self.update_events, self._next_change
        )
        _LOGGER.debug("next time: %s", self._next_change.isoformat())

    @callback
    def update_sun_position(self, now: datetime | None = None) -> None:
        """Calculate the position of the sun."""
        # Grab current time in case system clock changed since last time we ran.
        utc_point_in_time = dt_util.utcnow()
        self.solar_azimuth = round(
            self.location.solar_azimuth(utc_point_in_time, self.elevation), 2
        )
        self.solar_elevation = round(
            self.location.solar_elevation(utc_point_in_time, self.elevation), 2
        )

        _LOGGER.debug(
            "sun position_update@%s: elevation=%s azimuth=%s",
            utc_point_in_time.isoformat(),
            self.solar_elevation,
            self.solar_azimuth,
        )
        self.async_write_ha_state()

        async_dispatcher_send(self.hass, SIGNAL_POSITION_CHANGED)

        update_interval = None
        if self.entry:
            update_interval = self.entry.options.get(CONF_ELEVATION_UPDATE_INTERVAL)
            
        if update_interval is not None:
            delta = timedelta(seconds=update_interval)
        else:
            # Next update as per the current phase
            assert self.phase
            delta = _PHASE_UPDATES[self.phase]

        # if the next update is within 1.25 of the next
        # position update just drop it
        if utc_point_in_time + delta * 1.25 > self._next_change:
            self._update_sun_position_listener = None
            return
        self._update_sun_position_listener = event.async_track_point_in_utc_time(
            self.hass, self.update_sun_position, utc_point_in_time + delta
        )