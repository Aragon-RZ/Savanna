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
from environment.nature import (
    GrazingArea,
    InsectivoreFeedingGround,
    RangerStation,
    River,
    SafariStation,
    WateringHole,
)
from environment.base import SavannaZone
from entities.animals import (
    Antelope,
    Buffalo,
    BushBaby,
    Cheetah,
    Elephant,
    Giraffe,
    Herbivore,
    Insectivore,
    Leopard,
    Lion,
    Meerkat,
    Pangolin,
    Rhino,
    Ostrich,
    Zebra,
)
from utils.constants import GRID_WIDTH, GRID_HEIGHT, TICK_RATE
from entities.humans import Ranger
from entities.vehicles import SafariJeep, BASE_X, BASE_Y


POPULATION_PROFILE = [
    (Zebra, "Zebra", 18, 12, 18),
    (Elephant, "Elephant", 5, 24, 24),
    (Giraffe, "Giraffe", 7, 36, 18),
    (Buffalo, "Buffalo", 10, 52, 34),
    (Rhino, "Rhino", 4, 70, 42),
    (Antelope, "Antelope", 16, 42, 66),
    (Ostrich, "Ostrich", 7, 18, 76),
    (Meerkat, "Meerkat", 10, 68, 76),
    (BushBaby, "BushBaby", 8, 58, 86),
    (Lion, "Lion", 1, 28, 38),
    (Leopard, "Leopard", 1, 76, 18),
    (Cheetah, "Cheetah", 1, 84, 60),
    (Pangolin, "Pangolin", 4, 62, 54),
]


class SafariBuilder:
    def __init__(self, max_ticks=240, logger_enabled=True,
                 display_output=True, tick_rate=TICK_RATE,
                 auto_start_workers=True):
        self.engine = SimulationEngine(
            max_ticks=max_ticks,
            logger_enabled=logger_enabled,
            display_output=display_output,
            tick_rate=tick_rate
        )
        self.water = []
        self.grazing_areas = []
        self.insect_feeding_grounds = []
        self.land_objects = []
        self.animal_counter = 1
        self.auto_start_workers = auto_start_workers
        self.display_output = display_output

    def build_environment(self):
        """Creates the environment using a Composite zone tree."""
        water_zone = SavannaZone("Water Zone")

        river_path = [(8, 6), (18, 20), (25, 32), (42, 44), (55, 58), (55, 73), (88, 94)]
        river = River(name="Mara River", x=42, y=44, capacity=30, path_points=river_path)
        river.display_output = self.display_output
        self.water.append(river)
        water_zone.add(river)

        for name, x, y, capacity in [
            ("North Bend Oasis", 70, 24, 7),
            ("Acacia Pool", 82, 61, 6),
            ("Southbank Pool", 30, 78, 8),
        ]:
            water = WateringHole(name=name, x=x, y=y, capacity=capacity)
            water.display_output = self.display_output
            self.water.append(water)
            water_zone.add(water)

        grazing_zone = SavannaZone("Grazing Zone")
        for name, x, y, capacity in [
            ("West Grassland", 18, 42, 12),
            ("Central Grazing Plain", 47, 36, 14),
            ("Southern Grassland", 66, 68, 12),
            ("Dry Meadow", 36, 82, 8),
        ]:
            grazing = GrazingArea(name=name, x=x, y=y, capacity=capacity)
            grazing.display_output = self.display_output
            self.grazing_areas.append(grazing)
            grazing_zone.add(grazing)

        insect_zone = SavannaZone("Insectivore Food Zone")
        for name, x, y, capacity in [
            ("Termite Mound", 63, 58, 8),
            ("Rocky Foraging Patch", 82, 34, 6),
            ("Night Insect Grove", 55, 88, 8),
        ]:
            feeding_ground = InsectivoreFeedingGround(name=name, x=x, y=y, capacity=capacity)
            feeding_ground.display_output = self.display_output
            self.insect_feeding_grounds.append(feeding_ground)
            insect_zone.add(feeding_ground)

        land_zone = SavannaZone("Buildings Zone")
        for building in [
            RangerStation("Ranger Station", 12, 52),
            SafariStation("Safari Station", 8, 14),
        ]:
            building.display_output = self.display_output
            self.land_objects.append(building)
            land_zone.add(building)

        # Build the full savanna tree
        savanna = SavannaZone("Savanna")
        savanna.add(water_zone)
        savanna.add(grazing_zone)
        savanna.add(insect_zone)
        savanna.add(land_zone)

        # Engine gets the root zone — one object, whole tree
        self.engine.add_environment(savanna)
        return self

    def _spawn_batch(self, animal_class, base_name, count, start_x, start_y):
        for i in range(count):
            x = max(0, min(GRID_WIDTH - 1, start_x + random.randint(-6, 6)))
            y = max(0, min(GRID_HEIGHT - 1, start_y + random.randint(-6, 6)))
            animal = animal_class(self.animal_counter, f"{base_name} {i+1}", x, y)
            self._configure_animal_targets(animal)
            animal.display_output = self.display_output
            self.engine.add_entity(animal)
            self.animal_counter += 1

    def _configure_animal_targets(self, animal):
        animal.target_water = self.water
        if isinstance(animal, Insectivore):
            animal.target_insects = self.insect_feeding_grounds
        elif isinstance(animal, Herbivore):
            animal.target_food = self.grazing_areas

    def add_population_profile(self, scale=1):
        """Populate the savanna with a broad, scalable species mix."""
        scale = max(1, int(scale))
        for animal_class, base_name, count, start_x, start_y in POPULATION_PROFILE:
            self._spawn_batch(animal_class, base_name, count * scale, start_x, start_y)
        return self

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

    def add_giraffes(self, count):
        self._spawn_batch(Giraffe, "Giraffe", count, start_x=36, start_y=18)
        return self

    def add_buffalo(self, count):
        self._spawn_batch(Buffalo, "Buffalo", count, start_x=52, start_y=34)
        return self

    def add_rhinos(self, count):
        self._spawn_batch(Rhino, "Rhino", count, start_x=70, start_y=42)
        return self

    def add_antelopes(self, count):
        self._spawn_batch(Antelope, "Antelope", count, start_x=42, start_y=66)
        return self

    def add_ostriches(self, count):
        self._spawn_batch(Ostrich, "Ostrich", count, start_x=18, start_y=76)
        return self

    def add_meerkats(self, count):
        self._spawn_batch(Meerkat, "Meerkat", count, start_x=68, start_y=76)
        return self

    def add_cheetahs(self, count):
        self._spawn_batch(Cheetah, "Cheetah", count, start_x=84, start_y=60)
        return self

    def add_pangolins(self, count):
        self._spawn_batch(Pangolin, "Pangolin", count, start_x=62, start_y=54)
        return self

    def get_engine(self):
        return self.engine
    
    def add_rangers(self, count):
        positions = [
            (3, 30, "north"),
            (22, 44, "north"),
            (15, 60, "south"),
            (42, 84, "south"),
        ]
        for i in range(min(count, len(positions))):
            x, y, territory = positions[i]
            ranger = Ranger(
                name=f"Ranger {i+1}",
                x=x,
                y=y,
                territory=territory,
                display_output=self.display_output
            )
            if self.auto_start_workers:
                ranger.start()
            self.engine.add_entity(ranger)
        return self
    
    def add_jeeps(self, count):
    # Each jeep gets its own patrol zone
        configs = [
            (BASE_X, BASE_Y, 15, 20, 14),
            (BASE_X, BASE_Y, 35, 75, 16),
            (BASE_X, BASE_Y, 70, 25, 15),
            (BASE_X, BASE_Y, 78, 72, 15),
        ]
        for i in range(min(count, len(configs))):
            start_x, start_y, zone_x, zone_y, radius = configs[i]
            jeep = SafariJeep(name=f"Jeep {i+1}", x=start_x, y=start_y,
                            zone_x=zone_x, zone_y=zone_y, zone_radius=radius,
                            display_output=self.display_output,
                            seat_capacity=random.choice([6, 8, 10]))
            jeep.known_entities = self.engine.entities
            if self.auto_start_workers:
                jeep.start()
            self.engine.add_entity(jeep)
        return self
