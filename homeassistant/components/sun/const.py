"""Constants for the Sun integration."""

from typing import Final

DOMAIN: Final = "sun"

DEFAULT_NAME: Final = "Sun"

SIGNAL_POSITION_CHANGED = f"{DOMAIN}_position_changed"
SIGNAL_EVENTS_CHANGED = f"{DOMAIN}_events_changed"


STATE_ABOVE_HORIZON = "above_horizon"
STATE_BELOW_HORIZON = "below_horizon"

# As documented in wikipedia: https://en.wikipedia.org/wiki/Twilight
# sun is:
# < -18° of horizon - all stars visible
PHASE_NIGHT = "night"
# 18°-12° - some stars not visible
PHASE_ASTRONOMICAL_TWILIGHT = "astronomical_twilight"
# 12°-6° - horizon visible
PHASE_NAUTICAL_TWILIGHT = "nautical_twilight"
# 6°-0° - objects visible
PHASE_TWILIGHT = "twilight"
# 0°-10° above horizon, sun low on horizon
PHASE_SMALL_DAY = "small_day"
# > 10° above horizon
PHASE_DAY = "day"


STATE_ATTR_AZIMUTH = "azimuth"
STATE_ATTR_ELEVATION = "elevation"
STATE_ATTR_RISING = "rising"
STATE_ATTR_NEXT_DAWN = "next_dawn"
STATE_ATTR_NEXT_DUSK = "next_dusk"
STATE_ATTR_NEXT_MIDNIGHT = "next_midnight"
STATE_ATTR_NEXT_NOON = "next_noon"
STATE_ATTR_NEXT_RISING = "next_rising"
STATE_ATTR_NEXT_SETTING = "next_setting"

STATE_ATTR_NEXT_GOLDEN_HOUR_START = "next_golden_hour_start"
STATE_ATTR_NEXT_GOLDEN_HOUR_END = "next_golden_hour_end"
STATE_ATTR_NEXT_BLUE_HOUR_START = "next_blue_hour_start"
STATE_ATTR_NEXT_BLUE_HOUR_END = "next_blue_hour_end"

CONF_ELEVATION_UPDATE_INTERVAL = "elevation_update_interval"
