
import random
from engine.simulation import SimulationEngine
from engine.database import DatabaseManager
from engine.analytics_db import EnhancedSchema
from environment.nature import WateringHole
from environment.food import FoodManager, GrassPatch
from entities.animals import Zebra, Elephant, Lion, Leopard, BushBaby
from entities.reproduction import ReproductionManager

class SafariBuilder:
    def __init__(self, max_ticks=240):  
        # Initialize database on startup
        DatabaseManager.initialize()
        EnhancedSchema.create_tables()  # NEW: Enhanced schema
        
        self.engine = SimulationEngine(max_ticks=max_ticks)
        self.water = None
        self.food_manager = FoodManager()
        self.reproduction_manager = ReproductionManager()
        self.animal_counter = 1

    def build_environment(self):
        """Creates the stationary locations like the Watering Hole."""
        self.water = WateringHole(name="Oasis", x=5, y=5, capacity=4) #Semaphore- capacity of 4
        self.engine.add_environment(self.water)
        
        # NEW: Create grass patches for food
        self._create_food_sources()
        
        # Set reproduction manager on engine for tick updates
        self.engine.set_reproduction_manager(self.reproduction_manager)
        
        return self #allows for chaining methods (e.g. .add_zebras().add_lions())

    def _create_food_sources(self):
        """Create grass patches across the savanna"""
        # Create grass patches spread across the map
        grass_positions = [
            (3, 3), (7, 7), (2, 8), (8, 2),  # Near water area
            (0, 5), (5, 0), (10, 10), (0, 10),  # Edges
            (4, 6), (6, 4), (3, 7), (7, 3),   # Around water
            (1, 1), (9, 9), (1, 9), (9, 1),   # Corners
        ]
        
        for x, y in grass_positions:
            patch = self.food_manager.add_grass_patch(x, y, max_quantity=30)
        
        # Set food manager on engine for tick updates
        self.engine.set_food_manager(self.food_manager)
        
        print(f"🌿 Created {len(self.food_manager)} grass patches")

    def _spawn_batch(self, animal_class, base_name, count, start_x, start_y):
        """Helper method to spawn a group of animals with a slight random spread."""
        for i in range(count):
            # Spread them out slightly so not all animals stack on the exact same coordinate
            x = start_x + random.randint(-2, 2)
            y = start_y + random.randint(-2, 2)
            
            animal = animal_class(self.animal_counter, f"{base_name} {i+1}", x, y)
            animal.target_water = self.water #gives animal access to watering hole 
            
            # NEW: Give herbivores access to food
            from entities.animals import Herbivore
            if isinstance(animal, Herbivore):
                animal.set_food_manager(self.food_manager)
            
            # NEW: Give reproduction manager to animals
            animal.reproduction_manager = self.reproduction_manager
            
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