# main.py
from engine.simulation import SimulationEngine
from entities.animals import Zebra
from environment.nature import WateringHole

def main():
    # 1. Initialize the Engine
    engine = SimulationEngine()

    # 2. Create the Environment (Capacity 2 to force a traffic jam)
    oasis = WateringHole(name="Main Oasis", x=5, y=5, capacity=2)
    engine.add_environment(oasis)

    # 3. Create the Actors
    z1 = Zebra(entity_id=1, name="Zebra-Alpha", x=3, y=3)
    z2 = Zebra(entity_id=2, name="Zebra-Beta", x=7, y=5)
    z3 = Zebra(entity_id=3, name="Zebra-Charlie", x=5, y=7)

    # (Test Hack: Fast-forward their thirst so they seek water immediately)
    z1.thirst = 68
    z2.thirst = 69
    z3.thirst = 67

    # Give them the GPS coordinates of the water
    z1.target_water = oasis
    z2.target_water = oasis
    z3.target_water = oasis

    # 4. Add them to the world
    engine.add_entity(z1)
    engine.add_entity(z2)
    engine.add_entity(z3)

    # 5. Run the simulation for 15 ticks!
    engine.run(max_ticks=15)

if __name__ == "__main__":
    main()