# engine/builder.py
# ============================================================
# SafariBuilder — updated to use Composite environment tree
# ============================================================
# Changes from original:
#   - Wraps the WateringHole in a SavannaZone (Composite)
#   - Engine receives the zone root instead of bare list
#   - Everything else (method chaining, spawning) unchanged
# ============================================================

import random
from engine.simulation import SimulationEngine
from environment.nature import WateringHole
from environment.base import SavannaZone
from entities.animals import Zebra, Elephant, Lion, Leopard, BushBaby
from utils.constants import GRID_WIDTH, GRID_HEIGHT


class SafariBuilder:
    def __init__(self, max_ticks=240):
        self.engine = SimulationEngine(max_ticks=max_ticks)
        self.water = None
        self.animal_counter = 1

    def build_environment(self):
        """Creates the environment using a Composite zone tree."""
        self.water = WateringHole(name="Oasis", x=5, y=5, capacity=8)

        # COMPOSITE — wrap in a zone; add more leaves later freely
        water_zone = SavannaZone("Water Zone")
        water_zone.add(self.water)

        savanna = SavannaZone("Savanna")
        savanna.add(water_zone)

        # Engine gets the root zone — one object, whole tree
        self.engine.add_environment(savanna)
        return self

    def _spawn_batch(self, animal_class, base_name, count, start_x, start_y):
        for i in range(count):
            x = max(0, min(GRID_WIDTH - 1, start_x + random.randint(-2, 2)))
            y = max(0, min(GRID_HEIGHT - 1, start_y + random.randint(-2, 2)))
            animal = animal_class(self.animal_counter, f"{base_name} {i+1}", x, y)
            animal.target_water = self.water
            self.engine.add_entity(animal)
            self.animal_counter += 1

    def add_zebras(self, count):
        self._spawn_batch(Zebra, "Zebra", count, start_x=2, start_y=2)
        return self

    def add_elephants(self, count):
        self._spawn_batch(Elephant, "Elephant", count, start_x=8, start_y=8)
        return self

    def add_lions(self, count):
        self._spawn_batch(Lion, "Lion", count, start_x=3, start_y=3)  # 👈 was 0,0
        return self

    def add_leopards(self, count):
        self._spawn_batch(Leopard, "Leopard", count, start_x=10, start_y=10)
        return self

    def add_bushbabies(self, count):
        self._spawn_batch(BushBaby, "BushBaby", count, start_x=6, start_y=6)
        return self

    def get_engine(self):
        return self.engine