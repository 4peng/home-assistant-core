"""Sun component utility functions."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
import logging

from astral import SunDirection
from astral.location import Location
import astral.sun

from homeassistant.const import SUN_EVENT_SUNRISE, SUN_EVENT_SUNSET
from homeassistant.helpers.sun import get_location_astral_event_next

from .const import (
    PHASE_ASTRONOMICAL_TWILIGHT,
    PHASE_DAY,
    PHASE_NAUTICAL_TWILIGHT,
    PHASE_NIGHT,
    PHASE_SMALL_DAY,
    PHASE_TWILIGHT,
)

_LOGGER = logging.getLogger(__name__)


@dataclass(slots=True)
class SunState:
    """Class to hold sun state."""

    next_dawn: datetime
    next_dusk: datetime
    next_midnight: datetime
    next_noon: datetime
    next_rising: datetime
    next_setting: datetime
    next_change: datetime
    phase: str
    rising: bool
    # New attributes
    next_golden_hour_start: datetime | None = None
    next_golden_hour_end: datetime | None = None
    next_blue_hour_start: datetime | None = None
    next_blue_hour_end: datetime | None = None


def get_sun_state(
    location: Location, elevation: float, utc_point_in_time: datetime
) -> SunState:
    """Calculate the current sun state."""
    next_change = utc_point_in_time + timedelta(days=400)
    phase = None

    # Helper to check event and update next_change/phase
    def check_event(
        evt: str, depression: str | float, before_phase: str | None
    ) -> datetime:
        nonlocal next_change, phase
        # Set depression
        location.solar_depression = depression

        # Calculate next event
        next_utc = get_location_astral_event_next(
            location, elevation, evt, utc_point_in_time
        )

        if next_utc < next_change:
            next_change = next_utc
            phase = before_phase
        return next_utc

    # Sequence from entity.py
    check_event("dawn", "astronomical", PHASE_NIGHT)
    check_event("dawn", "nautical", PHASE_ASTRONOMICAL_TWILIGHT)
    next_dawn = check_event("dawn", "civil", PHASE_NAUTICAL_TWILIGHT)

    # Sunrise doesn't use depression, but check_event sets it.
    next_rising = check_event(SUN_EVENT_SUNRISE, "civil", PHASE_TWILIGHT)

    check_event("dawn", -10, PHASE_SMALL_DAY)
    next_noon = check_event("noon", -10, None)

    check_event("dusk", -10, PHASE_DAY)
    next_setting = check_event(SUN_EVENT_SUNSET, -10, PHASE_SMALL_DAY)

    next_dusk = check_event("dusk", "civil", PHASE_TWILIGHT)
    check_event("dusk", "nautical", PHASE_NAUTICAL_TWILIGHT)
    check_event("dusk", "astronomical", PHASE_ASTRONOMICAL_TWILIGHT)

    next_midnight = check_event("midnight", "astronomical", None)

    # Fallback phase calculation if next is noon/midnight
    if phase is None:
        # Reset depression just in case
        location.solar_depression = "civil"

        elev = location.solar_elevation(next_change, elevation)
        if elev >= 10:
            phase = PHASE_DAY
        elif elev >= 0:
            phase = PHASE_SMALL_DAY
        elif elev >= -6:
            phase = PHASE_TWILIGHT
        elif elev >= -12:
            phase = PHASE_NAUTICAL_TWILIGHT
        elif elev >= -18:
            phase = PHASE_ASTRONOMICAL_TWILIGHT
        else:
            phase = PHASE_NIGHT

    rising = next_noon < next_midnight

    # Golden/Blue hour calculation
    def get_next_range_event(method, direction):
        mod = -1
        # Limit to 366 days search like get_location_astral_event_next
        while mod < 367:
            day = utc_point_in_time.date() + timedelta(days=mod)
            try:
                # astral uses observer from location
                start, end = method(location.observer, day, direction=direction)
                
                if start > utc_point_in_time:
                    return start, end
            except ValueError:
                pass
            mod += 1
        return None, None

    gh_events = []
    bh_events = []

    for direction in [SunDirection.RISING, SunDirection.SETTING]:
        s, e = get_next_range_event(astral.sun.golden_hour, direction)
        if s:
            gh_events.append((s, e))
        s, e = get_next_range_event(astral.sun.blue_hour, direction)
        if s:
            bh_events.append((s, e))

    # Sort by start time
    gh_events.sort(key=lambda x: x[0])
    bh_events.sort(key=lambda x: x[0])

    gh_next = gh_events[0] if gh_events else (None, None)
    bh_next = bh_events[0] if bh_events else (None, None)

    return SunState(
        next_dawn=next_dawn,
        next_dusk=next_dusk,
        next_midnight=next_midnight,
        next_noon=next_noon,
        next_rising=next_rising,
        next_setting=next_setting,
        next_change=next_change,
        phase=phase,
        rising=rising,
        next_golden_hour_start=gh_next[0],
        next_golden_hour_end=gh_next[1],
        next_blue_hour_start=bh_next[0],
        next_blue_hour_end=bh_next[1],
    )
