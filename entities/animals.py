import random
from entities.base import Entity
from utils.constants import (
    HUNGER_THRESHOLD,
    MAX_HUNGER,
    MAX_THIRST,
    THIRST_THRESHOLD,
)


class Zebra(Entity):
    def __init__(self, entity_id, name, x, y):
        super().__init__(entity_id, name, x, y)
        self.thirst = 0
        self.target_water = None

    def update(self):
        if not self.is_alive:
            return

        if self.state == "DRINKING":
            self.thirst -= 25
            if self.thirst <= 0:
                self.thirst = 0
                self.state = "WANDERING"
            return

        self.thirst += 1

        if self.thirst >= MAX_THIRST:
            self.is_alive = False
            self.state = "DEAD"
            print(f"💀 {self.name} died of thirst!")
            return

        if self.thirst >= THIRST_THRESHOLD:
            self.state = "SEEKING_WATER"
            self.move_towards_water()
        else:
            self.state = "WANDERING"
            self.move_randomly()

    def move_randomly(self):
        self.move_by(random.choice([-1, 0, 1]), random.choice([-1, 0, 1]))

    def move_towards_water(self):
        if not self.target_water:
            return

        self.step_towards(self.target_water.x, self.target_water.y)


class Lion(Entity):
    def __init__(self, entity_id, name, x, y):
        super().__init__(entity_id, name, x, y)
        self.hunger = 0
        self.target_prey = None

    def update(self):
        if not self.is_alive:
            return

        if self.state == "EATING":
            self.hunger -= 50
            if self.hunger <= 0:
                self.hunger = 0
                self.state = "WANDERING"
            return

        self.hunger += 1

        if self.hunger >= MAX_HUNGER:
            self.is_alive = False
            self.state = "DEAD"
            print(f"💀 {self.name} starved to death!")
            return

        if self.hunger >= HUNGER_THRESHOLD:
            self.state = "HUNTING"
            self.move_towards_prey()
        else:
            self.state = "WANDERING"
            self.move_randomly()

    def move_randomly(self):
        self.move_by(random.choice([-1, 0, 1]), random.choice([-1, 0, 1]))

    def move_towards_prey(self):
        if not self.target_prey or not self.target_prey.is_alive:
            self.move_randomly()
            return

        self.step_towards(self.target_prey.x, self.target_prey.y)
