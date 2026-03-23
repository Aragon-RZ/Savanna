
import time
from utils.constants import TICK_RATE

class SimulationEngine:
    def __init__(self):
        self.tick_count = 0
        self.entities = []
        self.watering_holes = []

    def add_entity(self, entity):
        self.entities.append(entity)
        print(f"🌍 Spawned: {entity.name} at ({entity.x}, {entity.y})")

    def add_environment(self, env):
        self.watering_holes.append(env)
        print(f"🌍 Created location: {env.name} at ({env.x}, {env.y}) with capacity {env.capacity}")

    def run(self, max_ticks=15):
        """The main game loop"""
        print("\n" + "="*40)
        print("🦓 STARTING SAFARI SIMULATION")
        print("="*40 + "\n")
        
        for _ in range(max_ticks):
            self.tick_count += 1
            print(f"--- ⏰ Tick {self.tick_count} ---")
            
            # 1. Let every entity update its own internal state
            for entity in self.entities:
                entity.update()
                
                # Print their current status
                print(f"   [{entity.name}] Thirst: {entity.thirst}/100 | State: {entity.state} | Pos: ({entity.x}, {entity.y})")

                # 2. Check for interactions with the environment
                for hole in self.watering_holes:
                    
                    # If they just finished drinking (State reset to WANDERING), release the lock!
                    if entity.state != "DRINKING" and entity in hole.current_drinkers:
                        hole.finish_drinking(entity)

                    # If they are thirsty and standing on the water's coordinates, try to drink
                    if entity.state in ["SEEKING_WATER", "WAITING_IN_LINE"]:
                        if entity.x == hole.x and entity.y == hole.y:
                            hole.try_to_drink(entity)
            
            # 3. Clean up dead entities
            self.entities = [e for e in self.entities if e.is_alive]
            
            time.sleep(TICK_RATE)
            print("-" * 30)
            
        print("\n🛑 Simulation Paused/Ended.")