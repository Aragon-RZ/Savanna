# engine/simulation.py
import time
import threading
from utils.constants import TICK_RATE
import random

class SimulationEngine(threading.Thread):
    def __init__(self):
        # Initialize the Thread as a "daemon" so it automatically stops when the program closes
        super().__init__(daemon=True) 
        self.tick_count = 0
        self.entities = []
        self.environments = []
        self.is_running = False  # Thread control flag

    def add_entity(self, entity):
        self.entities.append(entity)

    def add_environment(self, env):
        self.environments.append(env)

    def stop(self):
        """Gracefully shuts down the simulation thread."""
        self.is_running = False
        print("\n🛑 Stopping Simulation Engine...")

    def run(self):
        """This overrides threading.Thread's run method. It executes when you call .start()"""
        self.is_running = True
        print("\n" + "="*40)
        print("🌍 SAFARI SIMULATION ENGINE STARTED")
        print("="*40 + "\n")
        
        while self.is_running:
            self.tick_count += 1
            print(f"--- ⏰ Tick {self.tick_count} ---")
            
            # 1. Update entities
            for entity in self.entities:
                entity.update()
                status_parts = [f"State: {entity.state}"]
                if hasattr(entity, "thirst"):
                    status_parts.insert(0, f"Thirst: {entity.thirst}/100")
                if hasattr(entity, "hunger"):
                    status_parts.insert(0, f"Hunger: {entity.hunger}/100")
                print(f"   [{entity.name}] " + " | ".join(status_parts))

                # 2. Handle Environment Interactions
                for env in self.environments:
                    # Check if animal finished drinking
                    if entity.state != "DRINKING" and entity in getattr(env, 'current_drinkers', []):
                        env.finish_drinking(entity)

                    # Check if animal wants to drink and is at the right location
                    if entity.state in ["SEEKING_WATER", "WAITING_IN_LINE"]:
                        if entity.x == env.x and entity.y == env.y:
                            env.try_to_drink(entity)




            # --- NEW PREDATOR/PREY LOGIC ----------------------------------

            # 1. Filter our lists to see who is on the board
            lions = [e for e in self.entities if type(e).__name__ == "Lion" and e.is_alive]
            zebras = [e for e in self.entities if type(e).__name__ == "Zebra" and e.is_alive]

            for lion in lions:
                if lion.state == "HUNTING":
                    # Give the Lion a target if it doesn't have one
                    if zebras and (lion.target_prey is None or not lion.target_prey.is_alive):
                        lion.target_prey = random.choice(zebras) # Simple radar: pick a random zebra
                        print(f"👀 {lion.name} locked onto {lion.target_prey.name}!")

                    # Check for collision: Did the Lion catch the Zebra?
                    if lion.target_prey and lion.x == lion.target_prey.x and lion.y == lion.target_prey.y:
                        
                        # 🎲 THE PROBABILITY MECHANIC (e.g., 40% chance of a successful kill)
                        kill_chance = 0.40 
                        
                        if random.random() < kill_chance:
                            # SUCCESS
                            print(f"🦁 💥 {lion.name} successfully hunted {lion.target_prey.name}!")
                            lion.target_prey.is_alive = False # Kill the zebra
                            lion.state = "EATING"
                            lion.target_prey = None # Reset target
                        else:
                            # FAILURE
                            print(f"💨 {lion.target_prey.name} escaped from {lion.name}'s ambush!")
                            # Force the zebra to flee rapidly so it isn't eaten on the next tick
                            lion.target_prey.move_randomly()
                            lion.target_prey.move_randomly()
                            lion.target_prey = None # Lion loses track, must find new prey next tick



            # 3. Clean up dead entities
            self.entities = [e for e in self.entities if e.is_alive]
            
            # 4. Wait for the next tick
            time.sleep(TICK_RATE)
            print("-" * 30)
