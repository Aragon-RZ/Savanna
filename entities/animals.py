# These are the classes for the animals in our simulation.
# Each animal will have its own unique behaviors and states.
#  The Engine will call the `update()` method of each animal 
# every tick to simulate their actions and interactions with the environment.



##### ZEBRA #####
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
        self.target_water = None  # The Engine will give the Zebra this destination

    def update(self):
        # 1. Check if dead
        if not self.is_alive:
            return

        # 2. Handle the "DRINKING" state
        if self.state == "DRINKING":
            self.thirst -= 25  # Thirst goes down fast while drinking
            if self.thirst <= 0:
                self.thirst = 0
                self.state = "WANDERING"
                # (The Simulation Engine will tell the Watering Hole to release the lock)
            return

        # 3. Handle normal life (thirst goes up)
        self.thirst += 1
        
        # 4. Handle Death
        if self.thirst >= MAX_THIRST:
            self.is_alive = False
            self.state = "DEAD"
            print(f"💀 {self.name} died of thirst!")
            return

        # 5. State Machine: Wandering vs. Seeking Water
        if self.thirst >= THIRST_THRESHOLD:
            self.state = "SEEKING_WATER"
            self.move_towards_water()
        else:
            self.state = "WANDERING"
            self.move_randomly()

    def move_randomly(self):
        self.x += random.choice([-1, 0, 1])
        self.y += random.choice([-1, 0, 1])

    def move_towards_water(self):
        if not self.target_water:
            return  # Can't move if it doesn't know where the water is!
        
        # Move 1 step closer on the X and Y axis
        if self.x < self.target_water.x: self.x += 1
        elif self.x > self.target_water.x: self.x -= 1
        
        if self.y < self.target_water.y: self.y += 1
        elif self.y > self.target_water.y: self.y -= 1


#### LION #####

class Lion(Entity):
    def __init__(self, entity_id, name, x, y):
        super().__init__(entity_id, name, x, y)
        self.hunger = 0
        self.target_prey = None  # The Engine will assign a Zebra to this

    def update(self):
        if not self.is_alive:
            return

        # 1. Handle the "EATING" state
        if self.state == "EATING":
            self.hunger -= 50  # Eating restores hunger fast
            if self.hunger <= 0:
                self.hunger = 0
                self.state = "WANDERING"
            return

        # 2. Normal life (hunger goes up)
        self.hunger += 1

        # 3. Handle Starvation
        if self.hunger >= MAX_HUNGER:
            self.is_alive = False
            self.state = "DEAD"
            print(f"💀 {self.name} starved to death!")
            return

        # 4. State Machine: Wandering vs. Hunting
        if self.hunger >= HUNGER_THRESHOLD:
            self.state = "HUNTING"
            self.move_towards_prey()
        else:
            self.state = "WANDERING"
            self.move_randomly()

    def move_randomly(self):
        self.x += random.choice([-1, 0, 1])
        self.y += random.choice([-1, 0, 1])

    def move_towards_prey(self):
        # If it has no prey, or the prey is already dead, just wander
        if not self.target_prey or not self.target_prey.is_alive:
            self.move_randomly()
            return
        
        # Stalk the prey! Move 1 step closer on the X and Y axis
        if self.x < self.target_prey.x: self.x += 1
        elif self.x > self.target_prey.x: self.x -= 1
        
        if self.y < self.target_prey.y: self.y += 1
        elif self.y > self.target_prey.y: self.y -= 1
