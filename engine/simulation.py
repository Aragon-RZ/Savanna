
# engine/simulation.py
import time
import threading
from utils.constants import TICK_RATE, TICKS_PER_DAY, SUNRISE_HOUR, SUNSET_HOUR
from utils.colors import Colors

class SimulationEngine(threading.Thread):
    def __init__(self, max_ticks=50):
        super().__init__()
        self.tick_count = 0
        self.max_ticks = max_ticks
        self.is_running = False
        self.entities = []
        self.environments = []

    def add_entity(self, entity):
        self.entities.append(entity)
        
    def add_environment(self, environment):
        self.environments.append(environment)

    def run(self):
        self.is_running = True
        print("\n" + "="*40)
        print("🌍 SAFARI SIMULATION ENGINE STARTED")
        print("="*40 + "\n")
        
        while self.is_running:
            self.tick_count += 1
            
            # --- DAY/NIGHT CLOCK ---
            current_hour = self.tick_count % TICKS_PER_DAY
            
            if current_hour == SUNRISE_HOUR:
                print("\n🌅 The sun is rising over the savanna...")
            elif current_hour == SUNSET_HOUR:
                print("\n🌇 The sun is setting. It is getting dark...")

            print(f"--- ⏰ Tick {self.tick_count} | Hour: {current_hour}:00 ---")
            
            # 1. Update entities
            for entity in self.entities:
                if entity.is_alive:
                    # Pass the master list of entities so predators can see prey!
                    entity.update(current_hour, self.entities) 
                    
                    status_parts = [f"State: {Colors.state(entity.state)}"]
                    if hasattr(entity, "thirst"):
                        status_parts.insert(0, f"Thirst: {Colors.thirst(f'{entity.thirst}/100')}")
                    position_str = Colors.position(f"@({entity.x}, {entity.y})")
                    print(f"   [{entity.name} {entity.id}] {position_str} | " + " | ".join(status_parts))

                # 2. Handle Environment Interactions
                for env in self.environments:
                    # Check if animal finished drinking
                    if entity.state != "DRINKING" and entity in getattr(env, 'current_drinkers', []):
                        env.finish_drinking(entity)

                    # Check if animal wants to drink and is at the right location
                    if entity.state in ["SEEKING_WATER", "WAITING_IN_LINE"]:
                        if entity.x == env.x and entity.y == env.y:
                            env.try_to_drink(entity)

            # 3. Stop condition
            if self.tick_count >= self.max_ticks:
                print("\n🛑 Max ticks reached. Stopping simulation.")
                self.is_running = False
                break
                
            # 4. Wait for next tick
            time.sleep(TICK_RATE)