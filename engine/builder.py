# engine/builder.py
from engine.simulation import SimulationEngine
from entities.animals import Lion, Zebra
from environment.nature import WateringHole

def create_mvp_safari():
    """Builds and wires together the starting state of the world."""
    engine = SimulationEngine()

    # Create the Environment
    oasis = WateringHole(name="Main Oasis", x=5, y=5, capacity=2)
    engine.add_environment(oasis)

    # Create the Actors
    z1 = Zebra(entity_id=1, name="Zebra-Alpha", x=3, y=3)
    z2 = Zebra(entity_id=2, name="Zebra-Beta", x=7, y=5)
    z3 = Zebra(entity_id=3, name="Zebra-Charlie", x=5, y=7)

    # Fast-forward thirst for testing
    z1.thirst = 68
    z2.thirst = 69
    z3.thirst = 67

    # Give them GPS coordinates to the water
    z1.target_water = oasis
    z2.target_water = oasis
    z3.target_water = oasis

    # Add to engine
    engine.add_entity(z1)
    engine.add_entity(z2)
    engine.add_entity(z3)

    # Create a hungry Lion right next to the Zebras
    mufasa = Lion(entity_id=99, name="Lion-Mufasa", x=4, y=4)
    mufasa.hunger = 69  # Start hunting on the first tick
    engine.add_entity(mufasa)

    return engine
