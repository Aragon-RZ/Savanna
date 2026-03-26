# main.py
from engine.simulation import SimulationEngine
from environment.nature import WateringHole
from entities.animals import Zebra, Elephant, Lion, Leopard, BushBaby
from engine.builder import create_mvp_safari

def main():
    # 1. Create the Engine (240 ticks = 10 full days!)
    engine = SimulationEngine(max_ticks=240)

    # 2. Create the Watering Hole 
    main_water = WateringHole(name="Oasis", x=5, y=5, capacity=4)
    engine.add_environment(main_water)

    # 3. Spawn Herbivores (Daytime Wanderers)
    herbivores = [
        Zebra(1, "Zazu the Zebra", 2, 2),
        Elephant(2, "Dumbo the Elephant", 8, 8),
        Zebra(3, "Stripes the Zebra", 3, 2)
    ]
    
    # 4. Spawn Predators
    predators = [
        Lion(4, "Mufasa the Lion", 0, 0),             # Hunts during the day
        Leopard(5, "Shadow the Leopard", 10, 10)      # Hunts at night!
    ]

    # 5. Spawn Nocturnal Critters
    nocturnal = [
        BushBaby(6, "Blinky the BushBaby", 6, 6)
    ]

    # Add everyone to the engine and give them the water map
    all_animals = herbivores + predators + nocturnal
    for animal in all_animals:
        animal.target_water = main_water
        engine.add_entity(animal)

    # 6. Start the simulation!
    engine.start()
    engine.join()
    
    # Using the Builder to create a more complex world with less boilerplate
    ####### in the future



if __name__ == "__main__":
    main()