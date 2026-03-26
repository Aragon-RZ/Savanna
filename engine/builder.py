
import random
from engine.simulation import SimulationEngine
from environment.nature import WateringHole
from entities.animals import Zebra, Elephant, Lion, Leopard, BushBaby

class SafariBuilder:
    def __init__(self, max_ticks=240):  
        self.engine = SimulationEngine(max_ticks=max_ticks) #simulation engine: how long it runs
        self.water = None #stores watering hole; shared resource 
        self.animal_counter = 1

    def build_environment(self):
        """Creates the stationary locations like the Watering Hole."""
        self.water = WateringHole(name="Oasis", x=5, y=5, capacity=4) #Semaphore- capacity of 4
        self.engine.add_environment(self.water)
        return self #allows for chaining methods (e.g. .add_zebras().add_lions())

    def _spawn_batch(self, animal_class, base_name, count, start_x, start_y):
        """Helper method to spawn a group of animals with a slight random spread."""
        for i in range(count):
            # Spread them out slightly so not all animals stack on the exact same coordinate
            x = start_x + random.randint(-2, 2)
            y = start_y + random.randint(-2, 2)
            
            animal = animal_class(self.animal_counter, f"{base_name} {i+1}", x, y)
            animal.target_water = self.water #gives animal access to watering hole 
            self.engine.add_entity(animal) #adds animal to the simulaiton 
            self.animal_counter += 1

    # --- Animal Spawners --- functions used in animal.py 
    
    def add_zebras(self, count):
        self._spawn_batch(Zebra, "Zebra", count, start_x=2, start_y=2) #"controlled randomness"
        return self
        
    def add_elephants(self, count):
        self._spawn_batch(Elephant, "Elephant", count, start_x=8, start_y=8)
        return self

    def add_lions(self, count):
        self._spawn_batch(Lion, "Lion", count, start_x=0, start_y=0)
        return self

    def add_leopards(self, count):
        self._spawn_batch(Leopard, "Leopard", count, start_x=10, start_y=10)
        return self

    def add_bushbabies(self, count):
        self._spawn_batch(BushBaby, "BushBaby", count, start_x=6, start_y=6)
        return self

    def get_engine(self):
        """Returns the fully constructed and populated engine."""
        return self.engine