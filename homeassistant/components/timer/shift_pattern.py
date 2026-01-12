from datetime import datetime

class ShiftPattern:

    def __init__(
        self,
        cycle_length: int,
        active_days: set[int],
        reference: datetime,
    ) -> None:
        self.cycle_length = cycle_length
        self.active_days = active_days
        self.reference = reference

    def is_active(self, now: datetime) -> bool:
        delta_days = (now.date() - self.reference.date()).days
        cycle_day = delta_days % self.cycle_length
        return cycle_day in self.active_days