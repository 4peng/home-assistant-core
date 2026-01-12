from datetime import timedelta
from typing import Optional

class TimerOverride:

    def __init__(self) -> None:
        self.active: bool = False
        self.forced_state: Optional[str] = None
        self.forced_remaining: Optional[timedelta] = None

    def clear(self) -> None:
        self.active = False
        self.forced_state = None
        self.forced_remaining = None