
# entities/animals.py

import random
from entities.base import Entity
from entities.strategies import (
    WanderStrategy, SeekWaterStrategy, FleeStrategy, HuntStrategy
)
from utils.constants import (
    THIRST_THRESHOLD, MAX_THIRST, SUNRISE_HOUR, SUNSET_HOUR,
    MAX_HUNGER, HUNGER_THRESHOLD, DESPERATION_THRESHOLD,
    GRID_WIDTH, GRID_HEIGHT
)
from utils.events import event_bus, Event


class Animal(Entity):
    def __init__(self, entity_id, name, x, y, is_diurnal=True):
        super().__init__(entity_id, name, x, y)
        self.thirst = 0
        self.hunger = 0
        self.target_water = None
        self.is_diurnal = is_diurnal
        self.behavior = WanderStrategy()
        self.display_output = True

    def die(self, cause):
        self.is_alive = False
        self.state = "DEAD"
        self._print(f"💀 {self.name} died! Cause: {cause}.")
        event_bus.emit(Event.ANIMAL_DIED, {"entity": self, "cause": cause})

    def _print(self, *args, **kwargs):
        if self.display_output:
            print(*args, **kwargs)

    def update(self, current_hour, entities):
        if not self.is_alive:
            return

        is_desperate = (self.thirst >= DESPERATION_THRESHOLD or
                        self.hunger >= DESPERATION_THRESHOLD)

        is_daytime = SUNRISE_HOUR <= current_hour < SUNSET_HOUR
        should_be_awake = is_daytime if self.is_diurnal else not is_daytime

        if is_desperate:
            should_be_awake = True
            if self.state == "SLEEPING":
                self._print(f"⚠️  {self.name} woke up in a panic!")
                self.state = "DESPERATE"
                event_bus.emit(Event.ANIMAL_DESPERATE, {"entity": self})

        if not should_be_awake and self.state not in ["SLEEPING", "DRINKING"]:
            self.state = "SLEEPING"
            self._print(f"💤 {self.name} went to sleep.")
        elif should_be_awake and self.state == "SLEEPING":
            self.state = "WANDERING"
            self._print(f"☀️/🌙 {self.name} woke up.")

        self.thirst += 2
        self.hunger += 1

        if self.thirst >= MAX_THIRST:
            self.die("Extreme Thirst")
            return
        if self.hunger >= MAX_HUNGER:
            self.die("Starvation")
            return

        if self.state in ["SLEEPING", "DRINKING"]:
            if self.state == "DRINKING":
                self.thirst -= 25
                if self.thirst <= 0:
                    self.thirst = 0
                    self.state = "WANDERING"
            return

        self.act(entities)

    def act(self, entities):
        self.behavior.execute(self, entities)

    def move_randomly(self):
        # ✅ FIXED — clamped to grid boundaries
        self.x = max(0, min(GRID_WIDTH - 1,  self.x + random.choice([-1, 0, 1])))
        self.y = max(0, min(GRID_HEIGHT - 1, self.y + random.choice([-1, 0, 1])))

    def move_towards(self, target_x, target_y):
        # ✅ FIXED — clamped to grid boundaries
        if self.x < target_x: self.x += 1
        elif self.x > target_x: self.x -= 1
        if self.y < target_y: self.y += 1
        elif self.y > target_y: self.y -= 1
        self.x = max(0, min(GRID_WIDTH - 1, self.x))
        self.y = max(0, min(GRID_HEIGHT - 1, self.y))


class Herbivore(Animal):
    def act(self, entities):
        self.hunger = 0  # ✅ FIXED — this line is now correctly inside act()

        # Water takes priority if desperate
        if self.thirst >= DESPERATION_THRESHOLD and self.target_water:
            self.behavior = SeekWaterStrategy()
            self.behavior.execute(self, entities)
            return

        # Then check for threats
        threat_nearby = any(
            isinstance(e, Carnivore) and e.is_alive and
            abs(e.x - self.x) + abs(e.y - self.y) < FleeStrategy.DETECTION_RANGE
            for e in entities
        )

        if threat_nearby:
            self.behavior = FleeStrategy()
        elif self.thirst >= THIRST_THRESHOLD and self.target_water:
            self.behavior = SeekWaterStrategy()
        else:
            self.behavior = WanderStrategy()

        self.behavior.execute(self, entities)


class Insectivore(Herbivore):
    pass


class Carnivore(Animal):
    def act(self, entities):
        if self.thirst >= THIRST_THRESHOLD and self.target_water:
            self.behavior = SeekWaterStrategy()
        elif self.hunger >= HUNGER_THRESHOLD:
            self.behavior = HuntStrategy()
        else:
            self.behavior = WanderStrategy()

        self.behavior.execute(self, entities)


# ── SPECIFIC ANIMALS ─────────────────────────────────────────

class Zebra(Herbivore): pass
class Elephant(Herbivore): pass
class Giraffe(Herbivore): pass
class Buffalo(Herbivore): pass
class Rhino(Herbivore): pass
class Antelope(Herbivore): pass
class Ostrich(Herbivore): pass
class Meerkat(Insectivore): pass

class Lion(Carnivore): pass
class Cheetah(Carnivore): pass

class Leopard(Carnivore):
    def __init__(self, entity_id, name, x, y):
        super().__init__(entity_id, name, x, y, is_diurnal=False)

class BushBaby(Insectivore):
    def __init__(self, entity_id, name, x, y):
        super().__init__(entity_id, name, x, y, is_diurnal=False)

class Pangolin(Insectivore):
    def __init__(self, entity_id, name, x, y):
        super().__init__(entity_id, name, x, y, is_diurnal=False)
