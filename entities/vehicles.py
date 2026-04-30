# entities/vehicles.py
# ============================================================
# OBSERVER PATTERN — Jeep listens to animal events
# STRATEGY PATTERN — Jeep swaps between patrol and chase
# THREAD          — runs independently of the engine tick loop
# ============================================================

import threading
import time
import random
from utils.events import event_bus, Event, EventListener
from utils.constants import GRID_WIDTH, GRID_HEIGHT

# Tour schedule — (start_hour, end_hour, is_nocturnal)
TOURS = [
    (6,  12, False),   # morning tour
    (14, 18, False),   # afternoon tour
    (19, 23, True),    # nocturnal special
]

BASE_X, BASE_Y = 5, 12   # close to the oasis area


def on_tour(hour):
    """Returns (True, is_nocturnal) if hour falls in any tour window."""
    for start, end, nocturnal in TOURS:
        if start <= hour < end:
            return True, nocturnal
    return False, False


# ── STRATEGY PATTERN — Jeep Behaviors ────────────────────────

class PatrolRouteStrategy:
    """Jeep patrols a specific zone of the savanna."""
    
    def __init__(self, zone_x=5, zone_y=5, radius=15):
        self.zone_x = zone_x   # center of patrol zone
        self.zone_y = zone_y
        self.radius = radius   # how far from center to wander

    def execute(self, jeep):
        jeep.state = "ON TOUR"
        # Wander within assigned zone
        jeep.x = max(self.zone_x - self.radius,
                     min(self.zone_x + self.radius,
                         jeep.x + random.choice([-3, -2, -1, 0, 1, 2, 3])))
        jeep.y = max(self.zone_y - self.radius,
                     min(self.zone_y + self.radius,
                         jeep.y + random.choice([-3, -2, -1, 0, 1, 2, 3])))
        jeep.x = max(0, min(GRID_WIDTH - 1, jeep.x))
        jeep.y = max(0, min(GRID_HEIGHT - 1, jeep.y))

        # Passive sighting within zone
        nearby = [e for e in jeep.known_entities
                  if hasattr(e,'is_alive') and e.is_alive
                  and hasattr(e,'state') 
                  and e.__class__.__name__ not in ("Ranger","SafariJeep")
                  and abs(e.x - jeep.x) + abs(e.y - jeep.y) <= 8]
        if nearby:
            spotted = nearby[0]
            jeep._print(f"   📷 [{jeep.name}] Tourists spotted: "
                        f"{spotted.name} ({spotted.state}) nearby!")
            jeep.sightings += 1


class ChaseStrategy:
    """Jeep drives toward a dramatic event location."""
    def __init__(self, target_x, target_y, event_desc):
        self.target_x = target_x
        self.target_y = target_y
        self.event_desc = event_desc
        self.reported = False

    def execute(self, jeep):
        jeep.state = f"CHASING EVENT"

        if jeep.x < self.target_x: jeep.x += 2
        elif jeep.x > self.target_x: jeep.x -= 2
        if jeep.y < self.target_y: jeep.y += 2
        elif jeep.y > self.target_y: jeep.y -= 2

        jeep.x = max(0, min(GRID_WIDTH  - 1, jeep.x))
        jeep.y = max(0, min(GRID_HEIGHT - 1, jeep.y))

        dist = abs(jeep.x - self.target_x) + abs(jeep.y - self.target_y)
        if dist <= 3:
            if not self.reported:
                jeep._print(f"   📸 [{jeep.name}] SIGHTING! Tourists witnessed: "
                            f"{self.event_desc}!")
                jeep.sightings += 1
                self.reported = True
            jeep.behavior = PatrolRouteStrategy()
            jeep.state = "ON TOUR"


class ReturnToBaseStrategy:
    """Jeep heads back to base at end of tour."""
    def execute(self, jeep):
        jeep.state = "RETURNING TO BASE"
        if jeep.x < BASE_X: jeep.x += 2
        elif jeep.x > BASE_X: jeep.x -= 2
        if jeep.y < BASE_Y: jeep.y += 2
        elif jeep.y > BASE_Y: jeep.y -= 2

        jeep.x = max(0, min(GRID_WIDTH  - 1, jeep.x))
        jeep.y = max(0, min(GRID_HEIGHT - 1, jeep.y))

        if jeep.x == BASE_X and jeep.y == BASE_Y:
            jeep.behavior = None   # will be set to PARKED
            jeep.state = "PARKED"
            jeep._print(f"   🚙 [{jeep.name}] Tour complete! "
                        f"Total sightings today: {jeep.sightings}")


# ── SAFARI JEEP ───────────────────────────────────────────────

class SafariJeep(threading.Thread, EventListener):

    DRIVE_SPEED = 1.5

    def __init__(self, name: str, x: int = BASE_X, y: int = BASE_Y,
             zone_x: int = 5, zone_y: int = 5, zone_radius: int = 10,
             display_output: bool = True):
        threading.Thread.__init__(self)
        self.name = name
        self.id = ""
        self.x = x
        self.y = y
        self.engine_ref = None
        self.state = "PARKED"
        self.is_alive = True
        self.sightings = 0
        self.behavior = None
        self.daemon = True
        self.is_running = False
        self.display_output = display_output
        self._lock = threading.Lock()
        self.current_hour = 0
        self.known_entities = []
        self.zone_x = zone_x        # 👈 new
        self.zone_y = zone_y        # 👈 new
        self.zone_radius = zone_radius  # 👈 new

        event_bus.subscribe(Event.ANIMAL_HUNTING,   self)
        event_bus.subscribe(Event.ANIMAL_DIED,      self)

    def update(self, current_hour, entities):
        """Engine calls this every tick to sync the hour."""
        self.current_hour = current_hour
        self.known_entities = entities

    def on_event(self, event_type: str, payload: dict):
        with self._lock:
            # Only react if on tour and not already chasing
            touring, _ = on_tour(self.current_hour)
            if not touring:
                return
            if isinstance(self.behavior, ChaseStrategy):
                return

            if event_type == Event.ANIMAL_HUNTING:
                predator = payload.get("predator")
                prey = payload.get("prey")
                if predator and prey:
                    desc = f"{predator.name} hunted {prey.name}"
                    self._print(f"   🚙 [{self.name}] Hunt nearby! Racing to scene...")
                    self.behavior = ChaseStrategy(predator.x, predator.y, desc)

            elif event_type == Event.ANIMAL_DIED:
                entity = payload.get("entity")
                cause = payload.get("cause", "")
                if entity and "Hunted" in cause:
                    desc = f"{entity.name} — {cause}"
                    self.behavior = ChaseStrategy(entity.x, entity.y, desc)

    def run(self):
        self.is_running = True
        self._print(f"🚙 [{self.name}] Safari jeep ready at base ({self.x}, {self.y})")
        last_tour_state = False

        while self.is_running:
            # PAUSE CHECK — wait if engine is paused
            if hasattr(self, 'engine_ref') and self.engine_ref and self.engine_ref.is_paused():
                time.sleep(0.1)
                continue

            with self._lock:
                touring, nocturnal = on_tour(self.current_hour)

                if touring and not last_tour_state:
                    tour_type = "NOCTURNAL SPECIAL" if nocturnal else "SAFARI TOUR"
                    self._print(f"\n🚙 [{self.name}] {tour_type} departing! Hour {self.current_hour}:00")
                    self.sightings = 0
                    self.behavior = PatrolRouteStrategy(self.zone_x, self.zone_y, self.zone_radius)
                    last_tour_state = True

                elif not touring and last_tour_state:
                    if not isinstance(self.behavior, ReturnToBaseStrategy):
                        self.behavior = ReturnToBaseStrategy()
                    last_tour_state = False

                if touring and self.behavior:
                    self.behavior.execute(self)
                    self._print(f"   🚙 [{self.name}] @({self.x},{self.y}) | "
                                f"{self.state} | sightings: {self.sightings}")
                elif not touring:
                    if isinstance(self.behavior, ReturnToBaseStrategy):
                        self.behavior.execute(self)
                    elif self.state != "PARKED":
                        self.state = "PARKED"

            time.sleep(self.DRIVE_SPEED)

    def stop(self):
        self.is_running = False
        event_bus.unsubscribe(Event.ANIMAL_HUNTING, self)
        event_bus.unsubscribe(Event.ANIMAL_DIED, self)

    def _print(self, *args, **kwargs):
        if self.display_output:
            print(*args, **kwargs)
