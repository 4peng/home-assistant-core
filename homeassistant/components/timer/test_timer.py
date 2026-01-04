import asyncio
from datetime import datetime, timedelta, time
from typing import Optional, Callable



class TimerOverride:
    def __init__(self) -> None:
        self.active: bool = False
        self.forced_state: Optional[str] = None
        self.forced_remaining: Optional[timedelta] = None

    def clear(self) -> None:
        self.active = False
        self.forced_state = None
        self.forced_remaining = None


class ShiftPattern:
    def __init__(self, start: time, end: time) -> None:
        self.start = start
        self.end = end

    def is_active(self, now: datetime) -> bool:
        """Проверяем, попадает ли текущее время в активное окно."""
        return self.start <= now.time() <= self.end



STATUS_IDLE = "idle"
STATUS_ACTIVE = "active"
STATUS_PAUSED = "paused"

class Timer:
    def __init__(self, config: dict) -> None:
        self._override = TimerOverride()
        self._shift_pattern = ShiftPattern(start=time(0, 0), end=time(23, 59))
        self._config = config
        self._state: str = STATUS_IDLE
        self._running_duration: timedelta = config.get("duration", timedelta(seconds=5))
        self._remaining: Optional[timedelta] = None
        self._end: Optional[datetime] = None
        self._listener: Optional[Callable[[], None]] = None
        self.hass = None
        self.entity_id = "timer.mock_timer"

    @property
    def state(self) -> str:
        return self._state

    def async_start(self, duration: Optional[timedelta] = None) -> None:
        if self._shift_pattern and not self._shift_pattern.is_active(datetime.now()):
            print("Timer start blocked by shift pattern")
            return

        if duration:
            self._remaining = self._running_duration = duration
        elif not self._remaining:
            self._remaining = self._running_duration

        self._end = datetime.now() + self._remaining
        self._state = STATUS_ACTIVE
        print(f"[START] State: {self._state}, Remaining: {self._remaining}")

    def async_pause(self) -> None:
        if self._state != STATUS_ACTIVE or self._end is None:
            return
        self._remaining = self._end - datetime.now()
        self._end = None
        self._state = STATUS_PAUSED
        print(f"[PAUSE] State: {self._state}, Remaining: {self._remaining}")

    def async_finish(self) -> None:
        self._state = STATUS_IDLE
        self._remaining = None
        self._end = None
        print(f"[FINISH] State: {self._state}, Remaining: {self._remaining}")



class MockHass:
    def __init__(self):
        self.bus = self

    def async_fire(self, event, data):
        print(f"Event fired: {event}, data: {data}")



async def test_timer():
    hass = MockHass()

    config = {
        "name": "Test Timer",
        "duration": timedelta(seconds=5),
    }
    timer = Timer(config)
    timer.hass = hass

    print("=== Starting Timer ===")
    timer.async_start(timedelta(seconds=5))

    await asyncio.sleep(1)

    print("=== Pausing Timer ===")
    timer.async_pause()

    await asyncio.sleep(1)

    print("=== Resuming Timer ===")
    timer.async_start()

    await asyncio.sleep(1)

    print("=== Finishing Timer ===")
    timer.async_finish()


if __name__ == "__main__":
    asyncio.run(test_timer())