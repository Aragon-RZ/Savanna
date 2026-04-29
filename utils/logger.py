
# utils/logger.py
# ============================================================
# CSV LOGGER — Performance Metrics
# ============================================================
# Records per-tick simulation stats to a CSV file so we can
# generate graphs for the final report.
#
# Tracks:
#   - Tick number and current hour
#   - How many animals are alive per species type
#   - Average thirst and hunger across all living animals
#   - Current weather
#   - Watering hole utilization (drinkers / capacity)
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
            # Auto-name with timestamp so runs don't overwrite each other
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"simulation_{timestamp}.csv"

        self.filepath = os.path.join(os.path.dirname(__file__), '..', filename)
        self.filepath = os.path.normpath(self.filepath)

        # Write CSV header
        with open(self.filepath, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([
                "tick",
                "hour",
                "alive_total",
                "alive_herbivores",
                "alive_carnivores",
                "alive_insectivores",
                "avg_thirst",
                "avg_hunger",
                "weather",
                "hole_drinkers",
                "hole_capacity",
                "hole_utilization_pct"
            ])

        print(f"📊 Logger started — writing to {self.filepath}")

    def log(self, tick: int, hour: int, entities: list,
            weather_name: str, environments: list):
        """Call this once per tick from the engine."""
        from entities.animals import Herbivore, Carnivore, Insectivore
        from environment.nature import WateringHole
        from environment.base import SavannaZone

        # Count living animals by type
        living = [e for e in entities
                  if hasattr(e, 'is_alive') and e.is_alive
                  and hasattr(e, 'thirst')]

        alive_total       = len(living)
        alive_herbivores  = sum(1 for e in living if type(e).__mro__[1] == Herbivore or isinstance(e, Herbivore))
        alive_carnivores  = sum(1 for e in living if isinstance(e, Carnivore))
        alive_insectivores = sum(1 for e in living if isinstance(e, Insectivore))

        # Average thirst and hunger
        avg_thirst = round(sum(e.thirst for e in living) / alive_total, 1) if alive_total else 0
        avg_hunger = round(sum(e.hunger for e in living) / alive_total, 1) if alive_total else 0

        # Watering hole stats — find all WateringHole leaves
        holes = []
        for env in environments:
            if isinstance(env, SavannaZone):
                holes.extend([l for l in env.get_all_leaves()
                               if isinstance(l, WateringHole)])
            elif isinstance(env, WateringHole):
                holes.append(env)

        total_drinkers = sum(len(h.current_drinkers) for h in holes)
        total_capacity = sum(h.capacity for h in holes)
        utilization = round((total_drinkers / total_capacity) * 100, 1) if total_capacity else 0

        # Write row
        with open(self.filepath, 'a', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([
                tick, hour, alive_total,
                alive_herbivores, alive_carnivores, alive_insectivores,
                avg_thirst, avg_hunger,
                weather_name,
                total_drinkers, total_capacity, utilization
            ])