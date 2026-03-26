# These are the classes for the animals in our simulation.
# Each animal will have its own unique behaviors and states.
#  The Engine will call the `update()` method of each animal 
# every tick to simulate their actions and interactions with the environment.


# entities/animals.py
import random
from entities.base import Entity
from utils.constants import THIRST_THRESHOLD, MAX_THIRST, SUNRISE_HOUR, SUNSET_HOUR, MAX_HUNGER, HUNGER_THRESHOLD
from utils.constants import DESPERATION_THRESHOLD 

# ==========================================
# BASE ANIMAL LOGIC
# ==========================================
class Animal(Entity):
    def __init__(self, entity_id, name, x, y, is_diurnal=True):
        super().__init__(entity_id, name, x, y)
        self.thirst = 0
        self.hunger = 0
        self.target_water = None
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
        
        # --- DESPERATION OVERRIDE ---
        if is_desperate:
            should_be_awake = True  # Panic wakes them up!
            if self.state == "SLEEPING":
                print(f"⚠️ {self.name} woke up in a panic due to extreme thirst/hunger!")
                self.state = "DESPERATE"

        # Normal sleep logic
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
        self.hunger = 0 # Grass is everywhere, they don't starve for now
        
        if self.thirst >= THIRST_THRESHOLD and self.target_water:
            self.state = "SEEKING_WATER"
            self.move_towards(self.target_water.x, self.target_water.y)
        else:
            self.state = "WANDERING"
            self.move_randomly()

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
        