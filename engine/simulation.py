
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
from utils.events import Event, event_bus
from engine.weather import WeatherSystem
from utils.logger import SimulationLogger


class SimulationEngine(threading.Thread):
    def __init__(self, max_ticks=50, logger_enabled=True,
                 display_output=True, tick_rate=TICK_RATE):
        super().__init__()
        self.tick_count = 0
        self.max_ticks = max_ticks
        self.is_running = False
        self.display_output = display_output
        self.tick_rate = tick_rate
        self.entities = []
        self.environments = []
        self.weather = WeatherSystem(display_output=display_output)
        self.logger = SimulationLogger() if logger_enabled else None
        self._lock = threading.RLock()
        self._pause_event = threading.Event()
        self._pause_event.set()
        self._stop_event = threading.Event()

    def add_entity(self, entity):
        with self._lock:
            self.entities.append(entity)
            if (self.is_running
                    and isinstance(entity, threading.Thread)
                    and entity.ident is None):
                entity.start()
        event_bus.emit(Event.ENTITY_ADDED, {"entity": entity})

    def add_environment(self, environment):
        with self._lock:
            self.environments.append(environment)

    def next_entity_id(self):
        with self._lock:
            numeric_ids = [
                entity.id for entity in self.entities
                if isinstance(getattr(entity, "id", None), int)
            ]
        return max(numeric_ids, default=0) + 1

    def first_water_hole(self):
        with self._lock:
            holes = self._water_hole_objects()
        return holes[0] if holes else None

    def pause(self):
        self._pause_event.clear()

    def resume(self):
        self._pause_event.set()

    def stop(self):
        self.is_running = False
        self._stop_event.set()
        self._pause_event.set()
        self._stop_background_threads()

    def is_paused(self):
        return not self._pause_event.is_set()

    def _print(self, *args, **kwargs):
        if self.display_output:
            print(*args, **kwargs)

    def _start_background_threads(self):
        if not self.weather.is_alive() and self.weather.ident is None:
            self.weather.start()

        for entity in self.entities:
            if isinstance(entity, threading.Thread) and entity.ident is None:
                entity.start()

    def _stop_background_threads(self):
        if hasattr(self.weather, "stop"):
            self.weather.stop()

        current_thread = threading.current_thread()
        for entity in list(self.entities):
            if hasattr(entity, "stop"):
                entity.stop()
            if (isinstance(entity, threading.Thread)
                    and entity is not current_thread
                    and threading.Thread.is_alive(entity)):
                entity.join(timeout=0.2)

    def run(self):
        self.is_running = True
        self._stop_event.clear()
        self._pause_event.set()

        try:
            self._start_background_threads()
            self._print("\n" + "="*40)
            self._print("🌍 SAFARI SIMULATION ENGINE STARTED")
            self._print("="*40 + "\n")

            while self.is_running and not self._stop_event.is_set():
                self._pause_event.wait()
                if self._stop_event.is_set():
                    break

                with self._lock:
                    self._tick_once()

                if self._stop_event.wait(self.tick_rate):
                    break
        finally:
            self.is_running = False
            self._stop_background_threads()

    def _tick_once(self):
        self.tick_count += 1
        current_hour = self.tick_count % TICKS_PER_DAY

        if current_hour == SUNRISE_HOUR:
            self._print("\n🌅 The sun is rising over the savanna...")
        elif current_hour == SUNSET_HOUR:
            self._print("\n🌇 The sun is setting. It is getting dark...")

        self._print(f"--- ⏰ Tick {self.tick_count} | Hour: {current_hour}:00 ---")

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
                self._display_entity(entity)
        for entity in self.entities:
            if not entity.is_alive and hasattr(entity, 'ticks_dead'):
                entity.ticks_dead += 1

        # 2. Update environments — Composite handles the rest internally
        for env in self.environments:
            env.update(self.tick_count, self.entities)

        # 3. Print environment status every 6 ticks
        if self.tick_count % 6 == 0:
            for env in self.environments:
                self._print(f"\n{env.status()}\n")

        # 4. Stop condition
        if self.tick_count >= self.max_ticks:
            self._print("\n🛑 Max ticks reached. Stopping simulation.")
            self.is_running = False
            self._stop_event.set()
            return

        if self.logger:
            self.logger.log(
                tick=self.tick_count,
                hour=current_hour,
                entities=self.entities,
                weather_name=self.weather.current_weather.name,
                environments=self.environments
            )

    def _display_entity(self, entity):
        if not self.display_output or entity.__class__.__name__ == "Ranger":
            return

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

        self._print(f"   [{Colors.state(entity.name)} {entity.id}] "
                    f"@({entity.x}, {entity.y}) | " + " | ".join(status_parts))

    def snapshot(self):
        with self._lock:
            entity_snapshots = [self._entity_snapshot(e) for e in self.entities]
            water_holes = self._water_hole_snapshots()
            alive_animals = [
                e for e in entity_snapshots
                if e["is_alive"] and e["category"] in {"herbivore", "carnivore", "insectivore"}
            ]
            thirst_values = [
                e["thirst"] for e in alive_animals
                if e["thirst"] is not None
            ]
            hunger_values = [
                e["hunger"] for e in alive_animals
                if e["hunger"] is not None
            ]

            return {
                "tick": self.tick_count,
                "hour": self.tick_count % TICKS_PER_DAY,
                "max_ticks": self.max_ticks,
                "is_running": self.is_running,
                "is_paused": self.is_paused(),
                "weather": self.weather.current_weather.name,
                "entities": entity_snapshots,
                "water_holes": water_holes,
                "grazing_areas": self._grazing_area_snapshots(),
                "environment_status": [env.status() for env in self.environments],
                "summary": {
                    "alive_total": len(alive_animals),
                    "total_entities": len(entity_snapshots),
                    "alive_herbivores": sum(1 for e in alive_animals if e["category"] == "herbivore"),
                    "alive_carnivores": sum(1 for e in alive_animals if e["category"] == "carnivore"),
                    "alive_insectivores": sum(1 for e in alive_animals if e["category"] == "insectivore"),
                    "avg_thirst": round(sum(thirst_values) / len(thirst_values), 1) if thirst_values else 0,
                    "avg_hunger": round(sum(hunger_values) / len(hunger_values), 1) if hunger_values else 0,
                }
            }

    def _entity_snapshot(self, entity):
        lock = getattr(entity, "_lock", None)
        if lock:
            with lock:
                return self._entity_snapshot_unlocked(entity)
        return self._entity_snapshot_unlocked(entity)

    def _entity_snapshot_unlocked(self, entity):
        return {
            "id": getattr(entity, "id", ""),
            "name": getattr(entity, "name", entity.__class__.__name__),
            "species": entity.__class__.__name__,
            "category": self._entity_category(entity),
            "x": getattr(entity, "x", 0),
            "y": getattr(entity, "y", 0),
            "state": getattr(entity, "state", "UNKNOWN"),
            "is_alive": getattr(entity, "is_alive", True),
            "thirst": getattr(entity, "thirst", None),
            "hunger": getattr(entity, "hunger", None),
            "sightings": getattr(entity, "sightings", None),
            "territory": getattr(entity, "territory", None),
            "ticks_dead": getattr(entity, "ticks_dead", 0),
        }

    def _entity_category(self, entity):
        species = entity.__class__.__name__
        if species == "Ranger":
            return "ranger"
        if species == "SafariJeep":
            return "vehicle"
        if species in {"Lion", "Cheetah", "Leopard"}:
            return "carnivore"
        if species in {"BushBaby", "Meerkat", "Pangolin"}:
            return "insectivore"
        return "herbivore" if hasattr(entity, "thirst") else "other"

    def _water_hole_snapshots(self):
        return [
            {
                "name": hole.name,
                "x": hole.x,
                "y": hole.y,
                "capacity": hole.capacity,
                "drinkers": len(hole.current_drinkers),
                "drinker_names": [e.name for e in hole.current_drinkers],
                "free_spots": hole.capacity - len(hole.current_drinkers),
            }
            for hole in self._water_hole_objects()
        ]

    def _water_hole_objects(self):
        leaves = []
        for env in self.environments:
            if hasattr(env, "get_all_leaves"):
                leaves.extend(env.get_all_leaves())
            else:
                leaves.append(env)

        return [
            leaf for leaf in leaves
            if hasattr(leaf, "capacity") and hasattr(leaf, "current_drinkers")
        ]

    def _grazing_area_snapshots(self):
        """Return a list of grazing area snapshots (capacity, grazers, free spots)."""
        leaves = []
        for env in self.environments:
            if hasattr(env, "get_all_leaves"):
                leaves.extend(env.get_all_leaves())
            else:
                leaves.append(env)

        grazing_areas = [
            leaf for leaf in leaves
            if hasattr(leaf, "capacity") and hasattr(leaf, "current_grazers")
        ]

        return [
            {
                "name": area.name,
                "x": area.x,
                "y": area.y,
                "capacity": area.capacity,
                "grazers": len(area.current_grazers),
                "grazer_names": [e.name for e in area.current_grazers],
                "free_spots": area.capacity - len(area.current_grazers),
            }
            for area in grazing_areas
        ]
