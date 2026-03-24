import random
import threading
import time

from entities.animals import Lion, Zebra
from utils.constants import TICK_RATE


class SimulationEngine(threading.Thread):
    def __init__(self):
        super().__init__(daemon=True)
        self.tick_count = 0
        self.entities = []
        self.environments = []
        self.is_running = False

    def add_entity(self, entity):
        self.entities.append(entity)

    def add_environment(self, env):
        self.environments.append(env)

    def stop(self):
        self.is_running = False
        print("\n🛑 Stopping Simulation Engine...")

    def _log_entity_status(self, entity):
        status_parts = [f"State: {entity.state}", f"Pos: ({entity.x}, {entity.y})"]
        if hasattr(entity, "thirst"):
            status_parts.insert(0, f"Thirst: {entity.thirst}/100")
        if hasattr(entity, "hunger"):
            status_parts.insert(0, f"Hunger: {entity.hunger}/100")
        print(f"   [{entity.name}] " + " | ".join(status_parts))

    def _handle_environment_interactions(self, entity):
        for env in self.environments:
            if entity.state != "DRINKING" and entity in getattr(env, "current_drinkers", []):
                env.finish_drinking(entity)

            if entity.state in {"SEEKING_WATER", "WAITING_IN_LINE"}:
                if entity.x == env.x and entity.y == env.y:
                    env.try_to_drink(entity)

    def _handle_predator_prey(self):
        lions = [entity for entity in self.entities if isinstance(entity, Lion) and entity.is_alive]
        zebras = [entity for entity in self.entities if isinstance(entity, Zebra) and entity.is_alive]

        for lion in lions:
            if lion.state != "HUNTING":
                continue

            if zebras and (lion.target_prey is None or not lion.target_prey.is_alive):
                lion.target_prey = random.choice(zebras)
                print(f"👀 {lion.name} locked onto {lion.target_prey.name}!")

            if lion.target_prey and lion.x == lion.target_prey.x and lion.y == lion.target_prey.y:
                kill_chance = 0.40

                if random.random() < kill_chance:
                    print(f"🦁 💥 {lion.name} successfully hunted {lion.target_prey.name}!")
                    lion.target_prey.is_alive = False
                    lion.state = "EATING"
                    lion.target_prey = None
                else:
                    print(f"💨 {lion.target_prey.name} escaped from {lion.name}'s ambush!")
                    lion.target_prey.move_randomly()
                    lion.target_prey.move_randomly()
                    lion.target_prey = None

    def _cleanup_dead_entities(self):
        for env in self.environments:
            for entity in list(getattr(env, "current_drinkers", [])):
                if not entity.is_alive:
                    env.finish_drinking(entity)

        self.entities = [entity for entity in self.entities if entity.is_alive]

    def run(self):
        self.is_running = True
        print("\n" + "=" * 40)
        print("🌍 SAFARI SIMULATION ENGINE STARTED")
        print("=" * 40 + "\n")

        while self.is_running:
            self.tick_count += 1
            print(f"--- ⏰ Tick {self.tick_count} ---")

            for entity in self.entities:
                entity.update()
                self._log_entity_status(entity)
                self._handle_environment_interactions(entity)

            self._handle_predator_prey()
            self._cleanup_dead_entities()
            time.sleep(TICK_RATE)
            print("-" * 30)
