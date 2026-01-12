"""Constants for the schedule integration."""

import logging
from typing import Final

DOMAIN: Final = "schedule"
LOGGER = logging.getLogger(__package__)

CONF_DATA: Final = "data"
CONF_FRIDAY: Final = "friday"
CONF_FROM: Final = "from"
CONF_MONDAY: Final = "monday"
CONF_SATURDAY: Final = "saturday"
CONF_SUNDAY: Final = "sunday"
CONF_THURSDAY: Final = "thursday"
CONF_TO: Final = "to"
CONF_TUESDAY: Final = "tuesday"
CONF_WEDNESDAY: Final = "wednesday"
CONF_ALL_DAYS: Final = {
    CONF_MONDAY,
    CONF_TUESDAY,
    CONF_WEDNESDAY,
    CONF_THURSDAY,
    CONF_FRIDAY,
    CONF_SATURDAY,
    CONF_SUNDAY,
}

ATTR_NEXT_EVENT: Final = "next_event"

# Override mechanism attributes
ATTR_OVERRIDE_ACTIVE: Final = "override_active"
ATTR_OVERRIDE_STATE: Final = "override_state"
ATTR_OVERRIDE_UNTIL: Final = "override_until"
ATTR_OVERRIDE_REASON: Final = "override_reason"

WEEKDAY_TO_CONF: Final = {
    0: CONF_MONDAY,
    1: CONF_TUESDAY,
    2: CONF_WEDNESDAY,
    3: CONF_THURSDAY,
    4: CONF_FRIDAY,
    5: CONF_SATURDAY,
    6: CONF_SUNDAY,
}

SERVICE_GET: Final = "get_schedule"

# Override mechanism services
SERVICE_SET_OVERRIDE: Final = "set_override"
SERVICE_CLEAR_OVERRIDE: Final = "clear_override"

# Override mechanism configuration keys
CONF_STATE: Final = "state"
CONF_UNTIL: Final = "until"
CONF_DURATION: Final = "duration"
CONF_REASON: Final = "reason"
