
# entities/animals.py

import random
from entities.base import Entity
from entities.strategies import (
    WanderStrategy, SeekWaterStrategy, SeekFoodStrategy, SeekInsectsStrategy,
    FleeStrategy, HuntStrategy
)
from utils.constants import (
    THIRST_THRESHOLD, MAX_THIRST, SUNRISE_HOUR, SUNSET_HOUR,
    MAX_HUNGER, HUNGER_THRESHOLD, CARNIVORE_HUNT_THRESHOLD, DESPERATION_THRESHOLD,
    GRID_WIDTH, GRID_HEIGHT
)
from utils.events import event_bus, Event


class Animal(Entity):
    def __init__(self, entity_id, name, x, y, is_diurnal=True):
        super().__init__(entity_id, name, x, y)
        self.thirst = random.randint(0, 45)
        self.hunger = random.randint(0, 55)
        self.target_water = None
        self.target_food = None
        self.target_insects = None
        self.is_diurnal = is_diurnal
        self.behavior = WanderStrategy()
        self.display_output = True
        self.birth_tick = 0
        self.last_reproduction_tick = -999999
        self.death_cause = None

    def die(self, cause):
        if not self.is_alive:
            return
        self.is_alive = False
        self.state = "DEAD"
        self.ticks_dead = 0
        self.death_cause = cause
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
        needs_resource = (self.thirst >= THIRST_THRESHOLD or
                          self.hunger >= HUNGER_THRESHOLD)

        is_daytime = SUNRISE_HOUR <= current_hour < SUNSET_HOUR
        should_be_awake = is_daytime if self.is_diurnal else not is_daytime

        if is_desperate or needs_resource:
            should_be_awake = True
        if is_desperate:
            if self.state == "SLEEPING":
                self._print(f"⚠️  {self.name} woke up in a panic!")
                self.state = "DESPERATE"
                event_bus.emit(Event.ANIMAL_DESPERATE, {"entity": self})

        if not should_be_awake and self.state not in ["SLEEPING", "DRINKING", "GRAZING", "FORAGING"]:
            self.state = "SLEEPING"
            self._print(f"💤 {self.name} went to sleep.")
        elif should_be_awake and self.state == "SLEEPING":
            self.state = "WANDERING"
            self._print(f"☀️/🌙 {self.name} woke up.")

        if self.state == "DRINKING":
            self.thirst = max(0, self.thirst - 25)
            self.hunger += 1
            if self.hunger >= MAX_HUNGER:
                self.die("Starvation")
                return
            if self.thirst == 0:
                self.state = "WANDERING"
            return

        if self.state in ["GRAZING", "FORAGING"]:
            self.hunger = max(0, self.hunger - 25)
            self.thirst += 2
            if self.thirst >= MAX_THIRST:
                self.die("Extreme Thirst")
                return
            if self.hunger == 0:
                self.state = "WANDERING"
            return

        self.thirst += 2
        self.hunger += 1

        if self.thirst >= MAX_THIRST:
            self.die("Extreme Thirst")
            return
        if self.hunger >= MAX_HUNGER:
            self.die("Starvation")
            return

        if self.state == "SLEEPING":
            return

        self.act(entities)

    def act(self, entities):
        self.behavior.execute(self, entities)

    def _water_more_urgent_than_food(self, has_food_target):
        if not self.target_water or self.thirst < THIRST_THRESHOLD:
            return False
        if not has_food_target or self.hunger < HUNGER_THRESHOLD:
            return True

        ticks_until_thirst_death = (MAX_THIRST - self.thirst) / 2
        ticks_until_hunger_death = MAX_HUNGER - self.hunger
        return ticks_until_thirst_death <= ticks_until_hunger_death

    def _avoid_water_centers(self):
        if self.state in ["SEEKING_WATER", "DRINKING", "WAITING_IN_LINE", "DESPERATE"]:
            return
        if not self.target_water:
            return

        waters = self.target_water if isinstance(self.target_water, list) else [self.target_water]
        for water in waters:
            if abs(self.x - water.x) + abs(self.y - water.y) >= 2:
                continue

            dx = self.x - water.x
            dy = self.y - water.y
            if dx == 0 and dy == 0:
                dx = 1
            self.x = max(0, min(GRID_WIDTH - 1, self.x + (1 if dx > 0 else -1)))
            self.y = max(0, min(GRID_HEIGHT - 1, self.y + (1 if dy > 0 else -1)))

    def move_randomly(self):
        # ✅ FIXED — clamped to grid boundaries
        self.x = max(0, min(GRID_WIDTH - 1,  self.x + random.choice([-1, 0, 1])))
        self.y = max(0, min(GRID_HEIGHT - 1, self.y + random.choice([-1, 0, 1])))
        self._avoid_water_centers()

    def move_towards(self, target_x, target_y):
        # ✅ FIXED — clamped to grid boundaries
        if self.x < target_x: self.x += 1
        elif self.x > target_x: self.x -= 1
        if self.y < target_y: self.y += 1
        elif self.y > target_y: self.y -= 1
        self.x = max(0, min(GRID_WIDTH - 1, self.x))
        self.y = max(0, min(GRID_HEIGHT - 1, self.y))
        self._avoid_water_centers()


class Herbivore(Animal):
    def act(self, entities):
        # Water takes priority when it is the most urgent survival need.
        if self._water_more_urgent_than_food(has_food_target=bool(self.target_food)):
            self.behavior = SeekWaterStrategy()
            self.behavior.execute(self, entities)
            return

        if self.hunger >= DESPERATION_THRESHOLD and self.target_food:
            self.behavior = SeekFoodStrategy()
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
        elif self.hunger >= HUNGER_THRESHOLD and self.target_food:
            self.behavior = SeekFoodStrategy()
        else:
            self.behavior = WanderStrategy()

        self.behavior.execute(self, entities)


class Insectivore(Herbivore):
    def act(self, entities):
        if self._water_more_urgent_than_food(has_food_target=bool(self.target_insects)):
            self.behavior = SeekWaterStrategy()
        elif self.hunger >= HUNGER_THRESHOLD and self.target_insects:
            self.behavior = SeekInsectsStrategy()
        else:
            self.behavior = WanderStrategy()

        self.behavior.execute(self, entities)


class Carnivore(Animal):
    def act(self, entities):
        wants_to_hunt = self.hunger >= CARNIVORE_HUNT_THRESHOLD
        if self._water_more_urgent_than_food(has_food_target=wants_to_hunt):
            self.behavior = SeekWaterStrategy()
        elif wants_to_hunt:
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
