"""Trace support for automation."""

from __future__ import annotations

from collections.abc import Generator
from contextlib import contextmanager
import time
from typing import Any

from homeassistant.components.trace import (
    CONF_STORED_TRACES,
    ActionTrace,
    async_store_trace,
)
from homeassistant.core import Context, HomeAssistant
from homeassistant.helpers.typing import ConfigType

from .const import DOMAIN


class AutomationTrace(ActionTrace):
    """Container for automation trace."""

    _domain = DOMAIN

    def __init__(
        self,
        item_id: str | None,
        config: ConfigType | None,
        blueprint_inputs: ConfigType | None,
        context: Context,
    ) -> None:
        """Container for automation trace."""
        super().__init__(item_id, config, blueprint_inputs, context)
        self._trigger_description: str | None = None

    def set_trigger_description(self, trigger: str) -> None:
        """Set trigger description."""
        self._trigger_description = trigger

    def as_short_dict(self) -> dict[str, Any]:
        """Return a brief dictionary version of this AutomationTrace."""
        if self._short_dict:
            return self._short_dict

        result = super().as_short_dict()
        result["trigger"] = self._trigger_description
        return result


@contextmanager
def trace_automation(
    hass: HomeAssistant,
    automation_id: str | None,
    config: ConfigType | None,
    blueprint_inputs: ConfigType | None,
    context: Context,
    trace_config: ConfigType,
) -> Generator[AutomationTrace]:
    """Trace action execution of automation with automation_id."""
    trace = AutomationTrace(automation_id, config, blueprint_inputs, context)
    async_store_trace(hass, trace, trace_config[CONF_STORED_TRACES])

    try:
        yield trace
    except Exception as ex:
        if automation_id:
            trace.set_error(ex)
        raise
    finally:
        if automation_id:
            trace.finished()


class PerformanceTimer:
    """Track performance metrics for automation steps."""

    def __init__(self) -> None:
        """Initialize the performance timer."""
        self.start_time: float | None = None
        self.step_times: dict[str, dict[str, float]] = {}

    def start(self) -> None:
        """Start the overall timer."""
        self.start_time = time.time()

    def start_step(self, step_name: str) -> None:
        """Start timing a specific step.

        Args:
            step_name: Name of the step to time (e.g., 'trigger_handling')

        """
        self.step_times[step_name] = {"start": time.time()}

    def end_step(self, step_name: str) -> float | None:
        """End timing a specific step and calculate duration.

        Args:
            step_name: Name of the step to end timing for

        Returns:
            Duration in seconds, or None if step wasn't started

        """
        if step_name not in self.step_times:
            return None

        end_time = time.time()
        self.step_times[step_name]["end"] = end_time
        duration = end_time - self.step_times[step_name]["start"]
        self.step_times[step_name]["duration"] = duration
        return duration

    def get_total_time(self) -> float | None:
        """Get total execution time since start.

        Returns:
            Total duration in seconds, or None if not started

        """
        if self.start_time is None:
            return None
        return time.time() - self.start_time

    def get_metrics(self) -> dict[str, float]:
        """Get all performance metrics.

        Returns:
            Dictionary with step names as keys and durations as values

        """
        metrics: dict[str, float] = {}

        # Add individual step durations
        for step_name, times in self.step_times.items():
            if "duration" in times:
                metrics[step_name] = times["duration"]

        # Add total time if available
        total = self.get_total_time()
        if total is not None:
            metrics["total"] = total

        return metrics
