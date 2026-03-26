

import time
import threading
from utils.constants import TICK_RATE, TICKS_PER_DAY, SUNRISE_HOUR, SUNSET_HOUR, MAX_THIRST, MAX_HUNGER
from utils.colors import Colors

class SimulationEngine(threading.Thread):
    def __init__(self, max_ticks=50):
        super().__init__()
        self.tick_count = 0 #tracks how many ticks have passed 
        self.max_ticks = max_ticks
        self.is_running = False #controls wether the simulaition loop is running 
        self.entities = [] #all animals / entities in the simulaiton 
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
            self.tick_count += 1 #move time forward 
            #while running, update everything and wait a bit - represents one moment in time : tick 
            #first, we advance time and calculate the current hour, which drives the day and night cycle.
            #then, we update every animal in the system — this is where they move, get thirsty or hungry, hunt, drink, or sleep depending on their state.
            #after that, we handle interactions with the environment, like animals accessing the watering hole or waiting if it’s full.
            #finally, we display the current state in the terminal and pause briefly before repeating
            
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
                    entity.update(current_hour, self.entities)  #Update the animal (pass time + all entities for interactions like hunting)
                  
                    
                    # --- Colorize the State ---
                    if entity.state == "DEAD":
                        c_state = Colors.dead(entity.state)
                    elif entity.state == "DESPERATE":  # <--- NEW Desperation state!
                        c_state = Colors.desperate(entity.state)
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

                    # --- Build the Status String with Progress Bars ---
                    status_parts = [f"State: {c_state}"]
                    
                    if hasattr(entity, "thirst"):
                        # Injecting the visual Thirst bar!
                        bar = Colors.bar(entity.thirst, MAX_THIRST)
                        status_parts.insert(0, f"Thirst: {bar} {entity.thirst}")
                        
                    if hasattr(entity, "hunger"):
                        # Injecting the visual Hunger bar!
                        bar = Colors.bar(entity.hunger, MAX_HUNGER)
                        status_parts.insert(0, f"Hunger: {bar} {entity.hunger}")
                        
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