
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
                    
                    # --- NEW: Colorize the State ---
                    if entity.state == "DEAD":
                        c_state = Colors.dead(entity.state)
                    elif entity.state == "SLEEPING":
                        c_state = f"{Colors.MAGENTA}{entity.state}{Colors.RESET}"
                    elif entity.state == "SEEKING_WATER":
                        c_state = f"{Colors.CYAN}{entity.state}{Colors.RESET}"
                    elif entity.state == "DRINKING":
                        c_state = f"{Colors.BLUE}{entity.state}{Colors.RESET}"
                    elif entity.state == "HUNTING":
                        c_state = f"{Colors.RED}{entity.state}{Colors.RESET}"
                    else:
                        c_state = f"{Colors.GREEN}{entity.state}{Colors.RESET}"

                    # Build the status string
                    status_parts = [f"State: {c_state}"]
                    
                    if hasattr(entity, "thirst"):
                        status_parts.insert(0, f"Thirst: {entity.thirst}/100")
                    if hasattr(entity, "hunger"):
                        status_parts.insert(0, f"Hunger: {entity.hunger}/100")
                        
                    print(f"   [{Colors.state(entity.name)} {entity.id}] @({entity.x}, {entity.y}) | " + " | ".join(status_parts))

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