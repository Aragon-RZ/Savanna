
# engine/simulation.py
# ============================================================
# SimulationEngine — simplified now that environment owns
# its own update() logic (Composite pattern handles it)
# ============================================================
# Changes from original:
#   - Environment loop now just calls env.update(tick, entities)
#     The Composite tree handles everything internally
#   - Removed manual "finish_drinking / try_to_drink" checks
#     (those now live in WateringHole.update())
# ============================================================

import time
import threading
from utils.constants import TICK_RATE, TICKS_PER_DAY, SUNRISE_HOUR, SUNSET_HOUR, MAX_THIRST, MAX_HUNGER
from utils.colors import Colors
from engine.weather import WeatherSystem
from utils.logger import SimulationLogger


class SimulationEngine(threading.Thread):
    def __init__(self, max_ticks=50):
        super().__init__()
        self.tick_count = 0
        self.max_ticks = max_ticks
        self.is_running = False
        self.entities = []
        self.environments = []
        self.weather = WeatherSystem()
        self.logger = SimulationLogger()

    def add_entity(self, entity):
        self.entities.append(entity)

    def add_environment(self, environment):
        self.environments.append(environment)

    def run(self):
        self.is_running = True
        self.weather.start()   # ← starts the daemon thread
        print("\n" + "="*40)
        print("🌍 SAFARI SIMULATION ENGINE STARTED")
        print("="*40 + "\n")

        while self.is_running:
            self.tick_count += 1
            current_hour = self.tick_count % TICKS_PER_DAY

            if current_hour == SUNRISE_HOUR:
                print("\n🌅 The sun is rising over the savanna...")
            elif current_hour == SUNSET_HOUR:
                print("\n🌇 The sun is setting. It is getting dark...")

            print(f"--- ⏰ Tick {self.tick_count} | Hour: {current_hour}:00 ---")

            # WEATHER — apply modifiers to all living entities this tick
            thirst_mod, hunger_mod = self.weather.get_modifiers()
            if thirst_mod != 0 or hunger_mod != 0:
                for entity in self.entities:
                    if entity.is_alive and hasattr(entity, 'thirst'):
                        entity.thirst = max(0, entity.thirst + thirst_mod)
                        entity.hunger = max(0, entity.hunger + hunger_mod)

            # 1. Update all entities
            for entity in self.entities:
                if entity.is_alive:
                    entity.update(current_hour, self.entities)

                    # Skip display for Rangers — they print themselves
                    if entity.__class__.__name__ == "Ranger":
                        continue

                    # Colorize state for display
                    if entity.state == "DEAD":
                        c_state = Colors.dead(entity.state)
                    elif entity.state == "DESPERATE":
                        c_state = Colors.desperate(entity.state)
                    elif entity.state == "SLEEPING":
                        c_state = f"{Colors.MAGENTA}{entity.state}{Colors.RESET}"
                    elif entity.state == "SEEKING_WATER":
                        c_state = f"{Colors.CYAN}{entity.state}{Colors.RESET}"
                    elif entity.state == "DRINKING":
                        c_state = f"{Colors.BLUE}{entity.state}{Colors.RESET}"
                    elif entity.state == "HUNTING":
                        c_state = f"{Colors.RED}{entity.state}{Colors.RESET}"
                    elif entity.state == "FLEEING":
                        c_state = f"{Colors.YELLOW}{entity.state}{Colors.RESET}"
                    else:
                        c_state = f"{Colors.GREEN}{entity.state}{Colors.RESET}"

                    status_parts = [f"State: {c_state}"]

                    if hasattr(entity, "thirst"):
                        bar = Colors.bar(entity.thirst, MAX_THIRST)
                        status_parts.insert(0, f"Thirst: {bar} {entity.thirst}")
                    if hasattr(entity, "hunger"):
                        bar = Colors.bar(entity.hunger, MAX_HUNGER)
                        status_parts.insert(0, f"Hunger: {bar} {entity.hunger}")

                    print(f"   [{Colors.state(entity.name)} {entity.id}] "
                          f"@({entity.x}, {entity.y}) | " + " | ".join(status_parts))

            # 2. Update environments — Composite handles the rest internally
            for env in self.environments:
                env.update(self.tick_count, self.entities)

            # 3. Print environment status every 6 ticks
            if self.tick_count % 6 == 0:
                for env in self.environments:
                    print(f"\n{env.status()}\n")

            # 4. Stop condition
            if self.tick_count >= self.max_ticks:
                print("\n🛑 Max ticks reached. Stopping simulation.")
                self.is_running = False
                break

            self.logger.log(
                tick=self.tick_count,
                hour=current_hour,
                entities=self.entities,
                weather_name=self.weather.current_weather.name,
                environments=self.environments
            )

            time.sleep(TICK_RATE)