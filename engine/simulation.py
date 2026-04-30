
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

import random
import time
import threading
from utils.constants import (
    TICK_RATE, TICKS_PER_DAY, SUNRISE_HOUR, SUNSET_HOUR, MAX_THIRST, MAX_HUNGER,
    GRID_WIDTH, GRID_HEIGHT, REPRODUCTION_CHECK_INTERVAL, REPRODUCTION_CHANCE,
    REPRODUCTION_RADIUS, REPRODUCTION_MIN_AGE_TICKS, REPRODUCTION_COOLDOWN_TICKS,
    REPRODUCTION_MAX_ANIMALS, REPRODUCTION_MAX_BIRTHS_PER_TICK,
    REPRODUCTION_MAX_THIRST, REPRODUCTION_MAX_HUNGER
)
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
        self.births_total = 0
        self.deaths_total = 0
        self.births_this_tick = 0
        self.deaths_this_tick = 0
        self.births_by_species = {}
        self.deaths_by_species = {}
        self.deaths_by_cause = {}
        self._known_dead_ids = set()

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

    def add_environment_component(self, component):
        with self._lock:
            if self.environments and hasattr(self.environments[0], "add"):
                self.environments[0].add(component)
            else:
                self.environments.append(component)
        event_bus.emit(Event.ENVIRONMENT_ADDED, {"environment": component})

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

    def water_sources(self):
        with self._lock:
            return list(self._water_hole_objects())

    def grazing_sources(self):
        with self._lock:
            return list(self._grazing_area_objects())

    def insect_food_sources(self):
        with self._lock:
            return list(self._insect_feeding_objects())

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
        self.births_this_tick = 0
        self.deaths_this_tick = 0

        if current_hour == SUNRISE_HOUR:
            self._print("\n🌅 The sun is rising over the savanna...")
        elif current_hour == SUNSET_HOUR:
            self._print("\n🌇 The sun is setting. It is getting dark...")

        self._print(f"--- ⏰ Tick {self.tick_count} | Hour: {current_hour}:00 ---")

        # WEATHER — apply modifiers to all living entities this tick
        thirst_mod, hunger_mod = self.weather.get_modifiers()
        if thirst_mod != 0 or hunger_mod != 0:
            for entity in self.entities:
                if getattr(entity, "is_alive", False) and hasattr(entity, 'thirst'):
                    entity.thirst = max(0, entity.thirst + thirst_mod)
                    entity.hunger = max(0, entity.hunger + hunger_mod)

        # 1. Update all entities
        for entity in list(self.entities):
            if getattr(entity, "is_alive", False):
                entity.update(current_hour, self.entities)
                self._display_entity(entity)
            elif hasattr(entity, "ticks_dead"):
                entity.ticks_dead += 1

        # 2. Update environments — Composite handles the rest internally
        for env in self.environments:
            env.update(self.tick_count, self.entities)

        self._record_new_deaths()
        self._try_reproduction()

        # 3. Print environment status every 6 ticks
        if self.tick_count % 6 == 0:
            for env in self.environments:
                self._print(f"\n{env.status()}\n")

        if self.logger:
            self.logger.log(
                tick=self.tick_count,
                hour=current_hour,
                entities=self.entities,
                weather_name=self.weather.current_weather.name,
                environments=self.environments,
                metrics=self._metrics_snapshot_unlocked()
            )

        # 4. Stop condition
        if self.tick_count >= self.max_ticks:
            self._print("\n🛑 Max ticks reached. Stopping simulation.")
            self.is_running = False
            self._stop_event.set()
            return

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

    def _record_new_deaths(self):
        for entity in self.entities:
            if not hasattr(entity, "thirst") or getattr(entity, "is_alive", True):
                continue

            entity_key = id(entity)
            if entity_key in self._known_dead_ids:
                continue

            self._known_dead_ids.add(entity_key)
            cause = getattr(entity, "death_cause", None) or "Unknown"
            species = entity.__class__.__name__
            self.deaths_total += 1
            self.deaths_this_tick += 1
            self.deaths_by_species[species] = self.deaths_by_species.get(species, 0) + 1
            self.deaths_by_cause[cause] = self.deaths_by_cause.get(cause, 0) + 1

    def _try_reproduction(self):
        if self.tick_count % REPRODUCTION_CHECK_INTERVAL != 0:
            return

        from entities.animals import Carnivore, Herbivore, Insectivore

        living_animals = [
            entity for entity in self.entities
            if getattr(entity, "is_alive", False) and hasattr(entity, "thirst")
        ]
        available_slots = REPRODUCTION_MAX_ANIMALS - len(living_animals)
        if available_slots <= 0:
            return

        candidates = []
        for animal in living_animals:
            if isinstance(animal, Carnivore):
                continue
            if not isinstance(animal, (Herbivore, Insectivore)):
                continue
            if not self._eligible_for_reproduction(animal):
                continue
            candidates.append(animal)

        if len(candidates) < 2:
            return

        random.shuffle(candidates)
        used = set()
        births_remaining = min(REPRODUCTION_MAX_BIRTHS_PER_TICK, available_slots)

        for animal in candidates:
            if births_remaining <= 0:
                break
            if id(animal) in used:
                continue

            mate = self._find_reproduction_mate(animal, candidates, used)
            if mate is None or random.random() > REPRODUCTION_CHANCE:
                continue

            offspring = self._create_offspring(animal, mate)
            self.add_entity(offspring)
            self._record_birth(offspring)

            animal.last_reproduction_tick = self.tick_count
            mate.last_reproduction_tick = self.tick_count
            used.add(id(animal))
            used.add(id(mate))
            births_remaining -= 1

            event_bus.emit(Event.ANIMAL_BORN, {
                "entity": offspring,
                "parent_a": animal,
                "parent_b": mate
            })

    def _eligible_for_reproduction(self, animal):
        state = getattr(animal, "state", "")
        if state in {"DEAD", "DESPERATE", "DRINKING", "GRAZING", "FORAGING", "FLEEING", "HUNTING"}:
            return False
        if getattr(animal, "thirst", MAX_THIRST) > REPRODUCTION_MAX_THIRST:
            return False
        if getattr(animal, "hunger", MAX_HUNGER) > REPRODUCTION_MAX_HUNGER:
            return False
        if self.tick_count - getattr(animal, "birth_tick", 0) < REPRODUCTION_MIN_AGE_TICKS:
            return False
        if self.tick_count - getattr(animal, "last_reproduction_tick", -999999) < REPRODUCTION_COOLDOWN_TICKS:
            return False
        return True

    def _find_reproduction_mate(self, animal, candidates, used):
        nearby = [
            mate for mate in candidates
            if mate is not animal
            and id(mate) not in used
            and mate.__class__ is animal.__class__
            and self._distance(animal, mate) <= REPRODUCTION_RADIUS
        ]
        if not nearby:
            return None
        return min(nearby, key=lambda mate: self._distance(animal, mate))

    def _create_offspring(self, parent_a, parent_b):
        animal_class = parent_a.__class__
        entity_id = self.next_entity_id()
        x = self._clamp_grid(
            round((parent_a.x + parent_b.x) / 2) + random.randint(-2, 2),
            GRID_WIDTH
        )
        y = self._clamp_grid(
            round((parent_a.y + parent_b.y) / 2) + random.randint(-2, 2),
            GRID_HEIGHT
        )
        offspring = animal_class(entity_id, f"{animal_class.__name__} Young {entity_id}", x, y)
        offspring.display_output = self.display_output
        offspring.thirst = random.randint(5, 30)
        offspring.hunger = random.randint(5, 30)
        offspring.birth_tick = self.tick_count
        offspring.last_reproduction_tick = self.tick_count
        self._configure_offspring_targets(offspring)
        return offspring

    def _configure_offspring_targets(self, offspring):
        from entities.animals import Herbivore, Insectivore

        offspring.target_water = self._water_hole_objects()
        if isinstance(offspring, Insectivore):
            offspring.target_insects = self._insect_feeding_objects()
        elif isinstance(offspring, Herbivore):
            offspring.target_food = self._grazing_area_objects()

    def _record_birth(self, offspring):
        species = offspring.__class__.__name__
        self.births_total += 1
        self.births_this_tick += 1
        self.births_by_species[species] = self.births_by_species.get(species, 0) + 1

    def _distance(self, entity_a, entity_b):
        return abs(entity_a.x - entity_b.x) + abs(entity_a.y - entity_b.y)

    def _clamp_grid(self, value, limit):
        return max(0, min(limit - 1, int(value)))

    def _metrics_snapshot_unlocked(self):
        return {
            "births_total": self.births_total,
            "deaths_total": self.deaths_total,
            "births_this_tick": self.births_this_tick,
            "deaths_this_tick": self.deaths_this_tick,
            "births_by_species": dict(sorted(self.births_by_species.items())),
            "deaths_by_species": dict(sorted(self.deaths_by_species.items())),
            "deaths_by_cause": dict(sorted(self.deaths_by_cause.items())),
        }

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
                "insect_feeding_grounds": self._insect_feeding_snapshots(),
                "land_objects": self._land_object_snapshots(),
                "environment_status": [env.status() for env in self.environments],
                "summary": {
                    "alive_total": len(alive_animals),
                    "total_entities": len(entity_snapshots),
                    "alive_herbivores": sum(1 for e in alive_animals if e["category"] == "herbivore"),
                    "alive_carnivores": sum(1 for e in alive_animals if e["category"] == "carnivore"),
                    "alive_insectivores": sum(1 for e in alive_animals if e["category"] == "insectivore"),
                    "avg_thirst": round(sum(thirst_values) / len(thirst_values), 1) if thirst_values else 0,
                    "avg_hunger": round(sum(hunger_values) / len(hunger_values), 1) if hunger_values else 0,
                    "active_species": self._active_species(entity_snapshots),
                    "births_total": self.births_total,
                    "deaths_total": self.deaths_total,
                    "births_this_tick": self.births_this_tick,
                    "deaths_this_tick": self.deaths_this_tick,
                    "births_by_species": dict(sorted(self.births_by_species.items())),
                    "deaths_by_species": dict(sorted(self.deaths_by_species.items())),
                    "deaths_by_cause": dict(sorted(self.deaths_by_cause.items())),
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
            "seats_taken": getattr(entity, "seats_taken", None),
            "seat_capacity": getattr(entity, "seat_capacity", None),
            "fuel_level": getattr(entity, "fuel_level", None),
            "fuel_capacity": getattr(entity, "fuel_capacity", None),
            "territory": getattr(entity, "territory", None),
            "ticks_dead": getattr(entity, "ticks_dead", 0),
            "birth_tick": getattr(entity, "birth_tick", None),
            "death_cause": getattr(entity, "death_cause", None),
        }

    def _active_species(self, entity_snapshots):
        counts = {}
        for entity in entity_snapshots:
            if not entity["is_alive"]:
                continue
            if entity["category"] not in {"herbivore", "carnivore", "insectivore"}:
                continue
            counts[entity["species"]] = counts.get(entity["species"], 0) + 1
        return dict(sorted(counts.items()))

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
                "kind": hole.__class__.__name__,
                "x": hole.x,
                "y": hole.y,
                "path_points": getattr(hole, "path_points", None),
                "capacity": hole.capacity,
                "drinkers": len(hole.current_drinkers),
                "drinker_names": [e.name for e in hole.current_drinkers],
                "free_spots": hole.capacity - len(hole.current_drinkers),
            }
            for hole in self._water_hole_objects()
        ]

    def _water_hole_objects(self):
        return [
            leaf for leaf in self._environment_leaves()
            if hasattr(leaf, "capacity") and hasattr(leaf, "current_drinkers")
        ]

    def _grazing_area_snapshots(self):
        """Return a list of grazing area snapshots (capacity, grazers, free spots)."""
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
            for area in self._grazing_area_objects()
        ]

    def _grazing_area_objects(self):
        return [
            leaf for leaf in self._environment_leaves()
            if hasattr(leaf, "capacity") and hasattr(leaf, "current_grazers")
        ]

    def _insect_feeding_snapshots(self):
        return [
            {
                "name": area.name,
                "x": area.x,
                "y": area.y,
                "capacity": area.capacity,
                "feeders": len(area.current_feeders),
                "feeder_names": [e.name for e in area.current_feeders],
                "free_spots": area.capacity - len(area.current_feeders),
            }
            for area in self._insect_feeding_objects()
        ]

    def _insect_feeding_objects(self):
        return [
            leaf for leaf in self._environment_leaves()
            if hasattr(leaf, "capacity") and hasattr(leaf, "current_feeders")
        ]

    def _land_object_snapshots(self):
        return [
            {
                "name": obj.name,
                "x": obj.x,
                "y": obj.y,
                "land_type": getattr(obj, "land_type", "land"),
            }
            for obj in self._environment_leaves()
            if hasattr(obj, "land_type")
        ]

    def _environment_leaves(self):
        leaves = []
        for env in self.environments:
            if hasattr(env, "get_all_leaves"):
                leaves.extend(env.get_all_leaves())
            else:
                leaves.append(env)
        return leaves
