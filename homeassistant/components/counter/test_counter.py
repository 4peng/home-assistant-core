import asyncio
from types import SimpleNamespace
from __init__ import Counter, DEFAULT_INITIAL, DEFAULT_STEP

class MockHass:
    def __init__(self):
        self.bus = self

    def async_fire(self, event, data):
        print(f"Event fired: {event}, data: {data}")

async def test_counter():
    hass = MockHass()

    config = {
        "name": "Test Counter",
        "initial": 5,
        "step": 2,
        "minimum": 0,
        "maximum": 10,
        "restore": False,
        "id": "test_counter"
    }

    counter = Counter(config)
    counter.hass = hass
    counter.entity_id = "counter.test_counter"

    print(f"Initial state: {counter.state}")

    print("=== Increment ===")
    counter.async_increment()
    print(f"State after increment: {counter.state}")

    print("=== Increment beyond maximum ===")
    counter.async_increment()
    counter.async_increment()
    print(f"State after increments: {counter.state}")

    print("=== Decrement ===")
    counter.async_decrement()
    print(f"State after decrement: {counter.state}")

    print("=== Decrement beyond minimum ===")
    counter.async_decrement()
    counter.async_decrement()
    counter.async_decrement()
    print(f"State after decrements: {counter.state}")

    print("=== Reset ===")
    counter.async_reset()
    print(f"State after reset: {counter.state}")

    print("=== Set valid value ===")
    counter.async_set_value(8)
    print(f"State after set_value(8): {counter.state}")

    print("=== Set invalid value (should raise error) ===")
    try:
        counter.async_set_value(12)
    except ValueError as e:
        print(f"Caught expected error: {e}")


if __name__ == "__main__":
    asyncio.run(test_counter())