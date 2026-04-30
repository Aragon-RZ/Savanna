
# entities/strategies.py
# ============================================================
# STRATEGY PATTERN — Animal Behavior Algorithms
# ============================================================
# How it works:
#   - BehaviorStrategy is the abstract interface
#   - Each concrete strategy (Wander, Flee, Hunt, SeekWater)
#     encapsulates ONE algorithm for what an animal does
#   - Animals hold a strategy object and call
#     strategy.execute(animal, entities) each tick
#   - Strategy can be SWAPPED at runtime — a Zebra spotting
#     a lion switches from WanderStrategy to FleeStrategy
#     instantly, without changing the Zebra class at all
#
# Why we use it here:
#   Before this, act() logic was hardcoded into Herbivore and
#   Carnivore classes. Now each behavior is its own clean,
#   testable class. Adding MigrationStrategy later = one new
#   class, zero changes to existing animal code.
# ============================================================

import random
from abc import ABC, abstractmethod
from utils.events import event_bus, Event
from utils.constants import THIRST_THRESHOLD, HUNGER_THRESHOLD, GRID_WIDTH, GRID_HEIGHT


# ── STRATEGY INTERFACE ───────────────────────────────────────
class BehaviorStrategy(ABC):
    @abstractmethod
    def execute(self, animal, entities: list):
        pass

    def __repr__(self):
        return self.__class__.__name__


# ── CONCRETE STRATEGIES ──────────────────────────────────────

class WanderStrategy(BehaviorStrategy):
    """Default calm behavior — animal roams randomly."""
    def execute(self, animal, entities: list):
        animal.state = "WANDERING"
        animal.move_randomly()


class SeekWaterStrategy(BehaviorStrategy):
    """Animal is thirsty — moves directly toward its closest watering hole."""
    def execute(self, animal, entities: list):
        if animal.target_water:
            animal.state = "SEEKING_WATER"
            waters = animal.target_water if isinstance(animal.target_water, list) else [animal.target_water]
            target_x, target_y = self._closest_water_point(animal, waters)
            animal.move_towards(target_x, target_y)
        else:
            animal.state = "WANDERING"
            animal.move_randomly()

    def _closest_water_point(self, animal, waters):
        candidates = []
        for water in waters:
            points = getattr(water, "path_points", None) or [(water.x, water.y)]
            for x, y in points:
                distance = abs(x - animal.x) + abs(y - animal.y)
                candidates.append((distance, x, y))
        _, target_x, target_y = min(candidates)
        return target_x, target_y


class SeekFoodStrategy(BehaviorStrategy):
    """Herbivore is hungry — moves to the closest grazing area."""
    def execute(self, animal, entities: list):
        food_sources = getattr(animal, "target_food", None)
        if food_sources:
            animal.state = "SEEKING_FOOD"
            sources = food_sources if isinstance(food_sources, list) else [food_sources]
            closest_food = min(sources, key=lambda f: abs(f.x - animal.x) + abs(f.y - animal.y))
            animal.move_towards(closest_food.x, closest_food.y)
        else:
            animal.state = "WANDERING"
            animal.move_randomly()


class SeekInsectsStrategy(BehaviorStrategy):
    """Insectivore is hungry — moves to the closest insect-rich patch."""
    def execute(self, animal, entities: list):
        food_sources = getattr(animal, "target_insects", None)
        if food_sources:
            animal.state = "SEEKING_INSECTS"
            sources = food_sources if isinstance(food_sources, list) else [food_sources]
            closest_food = min(sources, key=lambda f: abs(f.x - animal.x) + abs(f.y - animal.y))
            animal.move_towards(closest_food.x, closest_food.y)
        else:
            animal.state = "WANDERING"
            animal.move_randomly()


class FleeStrategy(BehaviorStrategy):
    """
    Animal detected a nearby predator and runs away.
    Moves in the OPPOSITE direction from the closest threat.
    Automatically reverts to WanderStrategy when safe.
    """
    DETECTION_RANGE = 5  # Manhattan distance in grid units

    def execute(self, animal, entities: list):
        from entities.animals import Carnivore  # local import avoids circular dependency

        threat = None
        min_dist = self.DETECTION_RANGE

        for e in entities:
            if isinstance(e, Carnivore) and e.is_alive and e is not animal:
                dist = abs(e.x - animal.x) + abs(e.y - animal.y)
                if dist < min_dist:
                    min_dist = dist
                    threat = e

        if threat:
            animal.state = "FLEEING"
            dx = animal.x - threat.x
            dy = animal.y - threat.y
            animal.x += (1 if dx > 0 else -1 if dx < 0 else random.choice([-1, 1]))
            animal.y += (1 if dy > 0 else -1 if dy < 0 else random.choice([-1, 1]))
            # ✅ Clamp to grid boundaries
            animal.x = max(0, min(GRID_WIDTH - 1, animal.x))
            animal.y = max(0, min(GRID_HEIGHT - 1, animal.y))   

        else:
            # Safe — revert to wandering
            animal.behavior = WanderStrategy()
            animal.state = "WANDERING"
            animal.move_randomly()


class HuntStrategy(BehaviorStrategy):
    """
    Carnivore is hungry — tracks and kills the closest prey.
    Emits ANIMAL_HUNTING event on a successful kill.
    """
    def execute(self, animal, entities: list):
        from entities.animals import Herbivore, Insectivore  # local import

        prey_list = [
            e for e in entities
            if isinstance(e, (Herbivore, Insectivore)) and e.is_alive
        ]

        if not prey_list:
            animal.state = "WANDERING"
            animal.move_randomly()
            return

        # Pick closest prey by Manhattan distance
        target = min(prey_list,
                     key=lambda e: abs(e.x - animal.x) + abs(e.y - animal.y))

        animal.state = "HUNTING"
        animal.move_towards(target.x, target.y)

        if animal.x == target.x and animal.y == target.y:
            event_bus.emit(Event.ANIMAL_HUNTING, {
                "predator": animal,
                "prey": target
            })
            target.die(f"Hunted by {animal.name}")
            animal.hunger = 0
            animal.state = "WANDERING"
            animal._print(f"🥩 {animal.name} feasted on {target.name}!")
