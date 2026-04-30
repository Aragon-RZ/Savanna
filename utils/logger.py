# utils/logger.py
# ============================================================
# CSV LOGGER - Performance Metrics
# ============================================================
# Records per-tick simulation stats to a CSV file so we can
# generate graphs for the final report.
#
# Tracks:
#   - Tick number, hour, weather, and population totals
#   - Animal health ranges and state counts
#   - Water, grazing, and insectivore-feeding utilization
#   - Ranger/jeep/poacher counts and outcomes
#   - Birth/death event counters from the engine
# ============================================================

import csv
import os
from datetime import datetime


class SimulationLogger:
    """
    Writes one row per tick to a CSV file.
    Called by the engine at the end of each tick.
    """

    def __init__(self, filename: str = None):
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"simulation_{timestamp}.csv"

        self.filepath = os.path.join(os.path.dirname(__file__), '..', filename)
        self.filepath = os.path.normpath(self.filepath)
        self.header = [
            "tick",
            "hour",
            "weather",
            "total_entities",
            "alive_total",
            "dead_total",
            "births_total",
            "deaths_total",
            "alive_herbivores",
            "alive_carnivores",
            "alive_insectivores",
            "avg_thirst",
            "avg_hunger",
            "min_thirst",
            "max_thirst",
            "min_hunger",
            "max_hunger",
            "desperate_count",
            "sleeping_count",
            "drinking_count",
            "grazing_count",
            "foraging_count",
            "hunting_count",
            "fleeing_count",
            "water_drinkers",
            "water_capacity",
            "water_utilization_pct",
            "grazers",
            "grazing_capacity",
            "grazing_utilization_pct",
            "insect_feeders",
            "insect_capacity",
            "insect_utilization_pct",
            "rangers",
            "jeeps",
            "avg_jeep_fuel",
            "min_jeep_fuel",
            "total_sightings",
            "active_poachers",
            "poacher_spawns_total",
            "poachers_arrested_total",
            "poachers_escaped_total",
            "poached_animals_total",
            "temporary_camps",
            "temporary_camps_created",
            "deaths_thirst",
            "deaths_starvation",
            "deaths_hunting",
            "births_this_tick",
            "deaths_this_tick",
            "poachers_arrested_this_tick",
            "poachers_escaped_this_tick",
            "poached_animals_this_tick",
        ]

        with open(self.filepath, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(self.header)

        print(f"Logger started - writing to {self.filepath}")

    def log(self, tick: int, hour: int, entities: list,
            weather_name: str, environments: list, metrics: dict = None):
        """Call this once per tick from the engine."""
        from entities.animals import Carnivore, Herbivore, Insectivore

        metrics = metrics or {}
        living = [
            e for e in entities
            if hasattr(e, 'is_alive') and e.is_alive and hasattr(e, 'thirst')
        ]
        animals = [e for e in entities if hasattr(e, 'thirst')]
        thirst_values = [e.thirst for e in living]
        hunger_values = [e.hunger for e in living]

        alive_total = len(living)
        dead_total = sum(1 for e in animals if not e.is_alive)
        alive_herbivores = sum(
            1 for e in living
            if isinstance(e, Herbivore) and not isinstance(e, Insectivore)
        )
        alive_carnivores = sum(1 for e in living if isinstance(e, Carnivore))
        alive_insectivores = sum(1 for e in living if isinstance(e, Insectivore))

        leaves = self._environment_leaves(environments)
        water_sources = [leaf for leaf in leaves if hasattr(leaf, "current_drinkers")]
        grazing_sources = [leaf for leaf in leaves if hasattr(leaf, "current_grazers")]
        insect_sources = [leaf for leaf in leaves if hasattr(leaf, "current_feeders")]

        water_drinkers, water_capacity, water_util = self._resource_utilization(
            water_sources, "current_drinkers"
        )
        grazers, grazing_capacity, grazing_util = self._resource_utilization(
            grazing_sources, "current_grazers"
        )
        insect_feeders, insect_capacity, insect_util = self._resource_utilization(
            insect_sources, "current_feeders"
        )

        rangers = [e for e in entities if e.__class__.__name__ == "Ranger"]
        jeeps = [e for e in entities if e.__class__.__name__ == "SafariJeep"]
        fuel_values = [
            getattr(jeep, "fuel_level", 0)
            for jeep in jeeps
            if getattr(jeep, "fuel_level", None) is not None
        ]
        death_causes = metrics.get("deaths_by_cause", {})

        with open(self.filepath, 'a', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([
                tick, hour, weather_name,
                len(entities),
                alive_total,
                dead_total,
                metrics.get("births_total", 0),
                metrics.get("deaths_total", 0),
                alive_herbivores, alive_carnivores, alive_insectivores,
                self._average(thirst_values),
                self._average(hunger_values),
                min(thirst_values) if thirst_values else 0,
                max(thirst_values) if thirst_values else 0,
                min(hunger_values) if hunger_values else 0,
                max(hunger_values) if hunger_values else 0,
                self._state_count(living, "DESPERATE"),
                self._state_count(living, "SLEEPING"),
                self._state_count(living, "DRINKING"),
                self._state_count(living, "GRAZING"),
                self._state_count(living, "FORAGING"),
                self._state_count(living, "HUNTING"),
                self._state_count(living, "FLEEING"),
                water_drinkers, water_capacity, water_util,
                grazers, grazing_capacity, grazing_util,
                insect_feeders, insect_capacity, insect_util,
                len(rangers),
                len(jeeps),
                self._average(fuel_values),
                min(fuel_values) if fuel_values else 0,
                sum(getattr(jeep, "sightings", 0) for jeep in jeeps),
                metrics.get("active_poachers", 0),
                metrics.get("poacher_spawns_total", 0),
                metrics.get("poachers_arrested_total", 0),
                metrics.get("poachers_escaped_total", 0),
                metrics.get("poached_animals_total", 0),
                metrics.get("temporary_camps", 0),
                metrics.get("temporary_camps_created", 0),
                self._cause_count(death_causes, "thirst"),
                self._cause_count(death_causes, "starvation"),
                self._cause_count(death_causes, "hunted"),
                metrics.get("births_this_tick", 0),
                metrics.get("deaths_this_tick", 0),
                metrics.get("poachers_arrested_this_tick", 0),
                metrics.get("poachers_escaped_this_tick", 0),
                metrics.get("poached_animals_this_tick", 0),
            ])

    def _environment_leaves(self, environments):
        leaves = []
        for env in environments:
            if hasattr(env, "get_all_leaves"):
                leaves.extend(env.get_all_leaves())
            else:
                leaves.append(env)
        return leaves

    def _resource_utilization(self, resources, current_attr):
        current = sum(len(getattr(resource, current_attr, [])) for resource in resources)
        capacity = sum(getattr(resource, "capacity", 0) for resource in resources)
        utilization = round((current / capacity) * 100, 1) if capacity else 0
        return current, capacity, utilization

    def _state_count(self, entities, state):
        return sum(1 for entity in entities if getattr(entity, "state", None) == state)

    def _cause_count(self, death_causes, keyword):
        keyword = keyword.lower()
        return sum(
            count for cause, count in death_causes.items()
            if keyword in str(cause).lower()
        )

    def _average(self, values):
        return round(sum(values) / len(values), 1) if values else 0
