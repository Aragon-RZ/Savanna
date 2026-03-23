import time
from utils.constants import TICK_RATE

class SimulationEngine:
    def __init__(self):
        self.tick_count = 0
        self.entities = []  # Master list of everything in the world

    def add_entity(self, entity):
        self.entities.append(entity)
        print(f"Spawned: {entity.name}")

    def run(self, max_ticks=10):
        """The main game loop"""
        print("\n🌍 Starting Safari Simulation...\n")
        
        for _ in range(max_ticks):
            self.tick_count += 1
            print(f"--- ⏰ Tick {self.tick_count} ---")
            
            # 1. Update all entities
            for entity in self.entities:
                if entity.is_alive:
                    entity.update()
                    print(entity) # Print their status to the console
            
            # 2. Clean up dead entities (The "Poof" method)
            self.entities = [e for e in self.entities if e.is_alive]
            
            # 3. Wait for the next tick
            time.sleep(TICK_RATE)
            print("-" * 20)
            
        print("\n🛑 Simulation Paused/Ended.")