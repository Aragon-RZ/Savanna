# These are the classes for the animals in our simulation.
# Each animal will have its own unique behaviors and states.
#  The Engine will call the `update()` method of each animal 
# every tick to simulate their actions and interactions with the environment.


import random
import time
from entities.base import Entity
from utils.constants import THIRST_THRESHOLD, MAX_THIRST, SUNRISE_HOUR, SUNSET_HOUR, MAX_HUNGER, HUNGER_THRESHOLD
from utils.constants import DESPERATION_THRESHOLD 
from utils.colors import Colors
# ==========================================
# BASE ANIMAL LOGIC
# ==========================================
class Animal(Entity):
    def __init__(self, entity_id, name, x, y, is_diurnal=True):
        super().__init__(entity_id, name, x, y)
        self.thirst = 0
        self.hunger = 0
        self.target_water = None #shared resource animals can move toward
        self.is_diurnal = is_diurnal  

    def die(self, cause):
        self.is_alive = False
        self.state = "DEAD"
        print(f"💀 {self.name} died! Cause: {cause}.")

    def update(self, current_hour, entities):
        if not self.is_alive:
            return
        
        # 0. Check for Desperation!
        is_desperate = self.thirst >= DESPERATION_THRESHOLD or self.hunger >= DESPERATION_THRESHOLD

        # 1. Sleep Cycle
        is_daytime = SUNRISE_HOUR <= current_hour < SUNSET_HOUR
        should_be_awake = is_daytime if self.is_diurnal else not is_daytime

        if is_desperate:
            should_be_awake = True
            if self.state == "SLEEPING":
                print(f"⚠️ {self.name} woke up in a panic due to extreme thirst/hunger!")
                self.state = "DESPERATE"

        if not should_be_awake and self.state not in ["SLEEPING", "DRINKING"]:
            self.state = "SLEEPING"
            print(f"💤 {self.name} went to sleep.")
        elif should_be_awake and self.state == "SLEEPING":
            self.state = "WANDERING"
            print(f"☀️/🌙 {self.name} woke up.")

        # 2. Survival Stats
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

        # 3. Let the specific animal decide what to do!
        self.act(entities)
    
    def herd(self, herd_animal: bool):
        while herd_animal:
            self.move_with_herd()
            time.sleep(1)

    def move_with_herd(self):        # Logic to move with the herd (e.g., follow the nearest herbivore)
        herd = [] #this would be the herd of animals that will move together, for example, a herd of zebras.
                #  The logic to determine which animals are in the herd and how they move together would be implemented here.

        if herd:
            # Move towards the average position of the herd
            avg_x = sum(animal.x for animal in herd) / len(herd)
            avg_y = sum(animal.y for animal in herd) / len(herd)
            self.move_towards(avg_x, avg_y)

    def join_herd(self, herd_animal: bool, herd: list):
        if random.random() < 0.45:  # 50% chance to join the herd
            self.herd(herd_animal)
            herd.append(self)  # Add this animal to the herd list
            print(f"🐾 {self.name} has joined the herd!")

    def act(self, entities):
        pass # Overridden by Herbivore/Carnivore

    def move_randomly(self):
        self.x += random.choice([-1, 0, 1])
        self.y += random.choice([-1, 0, 1])

    def move_towards(self, target_x, target_y):
        if self.x < target_x: self.x += 1
        elif self.x > target_x: self.x -= 1
        if self.y < target_y: self.y += 1
        elif self.y > target_y: self.y -= 1

# ==========================================
# DIET TYPES (The Logic)
# ==========================================
class Herbivore(Animal):
    def act(self, entities):
        """The main decision engine for herbivores."""
        self.hunger = 0 # Grass is everywhere, they don't starve for now
        
        # 1. Survival: Check for danger first
        closest_predator = self._scan_for_predators(entities)
        if closest_predator:
            self.state = "FLEEING"
            self.escape_predator(closest_predator)
            return

        # 2. Survival: Check for thirst
        if self._handle_thirst():
            return

        # 3. Social: Move with the herd or wander
        self._handle_herding(entities)

    # --- INTERNAL HELPER FUNCTIONS ---

    def _scan_for_predators(self, entities):
        """Scans the map and returns the closest predator within 4 spaces, or None."""
        predators = [e for e in entities if isinstance(e, Carnivore) and e.is_alive]
        closest_predator = None
        closest_dist = 999
        
        for p in predators:
            dist = abs(self.x - p.x) + abs(self.y - p.y)
            if dist <= 4:  # Predator is in the danger zone!
                if dist < closest_dist:
                    closest_dist = dist
                    closest_predator = p
                    
        return closest_predator

    def _handle_thirst(self):
        """Checks thirst and moves to water if needed. Returns True if thirsty."""

        if self.thirst >= THIRST_THRESHOLD and self.target_water:
            self.state = "SEEKING_WATER"
            self.move_towards(self.target_water.x, self.target_water.y)
            return True
        return False

    def _handle_herding(self, entities):
        """Finds nearby friends of the same species and follows them."""

        self.state = "WANDERING"

        if not getattr(self, 'is_herd_animal', True):  # If this species doesn't herd, just move randomly
            self.move_randomly()
            return
        
        friends = [e for e in entities if type(e) == type(self) and e.is_alive and e.id != self.id]
        
        # Only care about friends within a radius of 6 spaces
        nearby_herd = [f for f in friends if (abs(self.x - f.x) + abs(self.y - f.y)) <= 6]
        
        if nearby_herd:
            # Find the center coordinates of the herd
            avg_x = sum(f.x for f in nearby_herd) / len(nearby_herd)
            avg_y = sum(f.y for f in nearby_herd) / len(nearby_herd)
            
            # 80% chance to follow the herd, 20% chance to stray and explore
            if random.random() < 0.8:
                self.move_towards(avg_x, avg_y)
            else:
                self.move_randomly()
        else:
            self.move_randomly()

    def escape_predator(self, predator):
        """Moves in the exact opposite direction of the threat."""

        print(f"💨 {self.name} spotted a predator and is {Colors.fleeing('FLEEING!')}")
        if self.x < predator.x: self.x -= 1
        elif self.x > predator.x: self.x += 1
        if self.y < predator.y: self.y -= 1
        elif self.y > predator.y: self.y += 1
class Insectivore(Herbivore):
    pass # Behaves exactly like a herbivore, just eats bugs instead of grass

class Carnivore(Animal):
    def act(self, entities):
        # 1. Prioritize Water
        if self.thirst >= THIRST_THRESHOLD and self.target_water:
            self.state = "SEEKING_WATER"
            self.move_towards(self.target_water.x, self.target_water.y)
            return

        # 2. Prioritize Hunting
        if self.hunger >= HUNGER_THRESHOLD:
            self.state = "HUNTING"
            # Find prey (Any alive Herbivore or Insectivore)
            prey_list = [e for e in entities if isinstance(e, (Herbivore, Insectivore)) and e.is_alive]
            
            if prey_list:
                # Simple tracking: pick the first prey in the list
                target = prey_list[0]
                self.move_towards(target.x, target.y)
                
                # The Kill!
                if self.x == target.x and self.y == target.y:
                    target.die(f"Hunted by {self.name}")
                    self.hunger = 0
                    self.state = "WANDERING"
                    print(f"🥩 {self.name} feasted on {target.name}!")
            else:
                self.move_randomly() # No prey found, keep wandering
        else:
            self.state = "WANDERING"
            self.move_randomly()

# ==========================================
# SPECIFIC ANIMALS (The easy part!)
# ==========================================
# Diurnal Herbivores
class Zebra(Herbivore): pass
class Elephant(Herbivore): pass
class Giraffe(Herbivore): pass
class Buffalo(Herbivore): pass
class Rhino(Herbivore): pass
class Antelope(Herbivore): pass
class Ostrich(Herbivore): pass
class Meerkat(Insectivore): pass

# Diurnal Carnivores
class Lion(Carnivore): pass
class Cheetah(Carnivore): pass

# Nocturnal Animals (is_diurnal=False)
class Leopard(Carnivore):
    def __init__(self, entity_id, name, x, y):
        super().__init__(entity_id, name, x, y, is_diurnal=False)

class BushBaby(Insectivore):
    def __init__(self, entity_id, name, x, y):
        super().__init__(entity_id, name, x, y, is_diurnal=False)

class Pangolin(Insectivore):
    def __init__(self, entity_id, name, x, y):
        super().__init__(entity_id, name, x, y, is_diurnal=False)
        
