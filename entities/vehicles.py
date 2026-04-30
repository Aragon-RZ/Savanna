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
FUEL_STATION_X, FUEL_STATION_Y = 8, 14


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
        self.spotted_this_tour = set()
        self.waypoint = None

    def execute(self, jeep):
        if not self._inside_zone(jeep.x, jeep.y):
            jeep.state = "TRAVELLING TO TOUR ZONE"
            jeep.move_towards(self.zone_x, self.zone_y, jeep.CRUISE_STEP)
            return

        jeep.state = "ON TOUR"
        living = [
            entity for entity in jeep.known_entities
            if hasattr(entity, "is_alive") and entity.is_alive
            and hasattr(entity, "thirst")
            and self._inside_zone(entity.x, entity.y, margin=5)
        ]

        if living and random.random() < 0.55:
            nearest = min(living, key=lambda e: abs(e.x - jeep.x) + abs(e.y - jeep.y))
            jeep.move_towards(nearest.x, nearest.y, jeep.PATROL_STEP)
        else:
            target_x, target_y = self._current_waypoint(jeep)
            jeep.move_towards(target_x, target_y, jeep.PATROL_STEP)

        # Passive sighting within zone
        nearby = [
            entity for entity in jeep.known_entities
            if hasattr(entity, "is_alive") and entity.is_alive
            and hasattr(entity, "state")
            and hasattr(entity, "thirst")
            and abs(entity.x - jeep.x) + abs(entity.y - jeep.y) <= 8
            and entity.id not in self.spotted_this_tour
        ]
        if nearby:
            spotted = nearby[0]
            self.spotted_this_tour.add(spotted.id)
            jeep._print(f"   📷 [{jeep.name}] Tourists spotted: "
                        f"{spotted.name} ({spotted.state}) nearby!")
            jeep.sightings += 1

    def _inside_zone(self, x, y, margin=0):
        return (
            self.zone_x - self.radius - margin <= x <= self.zone_x + self.radius + margin
            and self.zone_y - self.radius - margin <= y <= self.zone_y + self.radius + margin
        )

    def _current_waypoint(self, jeep):
        if self.waypoint:
            distance = abs(jeep.x - self.waypoint[0]) + abs(jeep.y - self.waypoint[1])
            if distance > 3:
                return self.waypoint

        min_x = max(0, self.zone_x - self.radius)
        max_x = min(GRID_WIDTH - 1, self.zone_x + self.radius)
        min_y = max(0, self.zone_y - self.radius)
        max_y = min(GRID_HEIGHT - 1, self.zone_y + self.radius)
        self.waypoint = (random.randint(min_x, max_x), random.randint(min_y, max_y))
        return self.waypoint


class ChaseStrategy:
    """Jeep drives toward a dramatic event location."""
    def __init__(self, target_x, target_y, event_desc):
        self.target_x = target_x
        self.target_y = target_y
        self.event_desc = event_desc
        self.reported = False

    def execute(self, jeep):
        jeep.state = f"CHASING EVENT"

        jeep.move_towards(self.target_x, self.target_y, jeep.CHASE_STEP)

        dist = abs(jeep.x - self.target_x) + abs(jeep.y - self.target_y)
        if dist <= 3:
            if not self.reported:
                jeep._print(f"   📸 [{jeep.name}] SIGHTING! Tourists witnessed: "
                            f"{self.event_desc}!")
                jeep.sightings += 1
                self.reported = True
            jeep.behavior = PatrolRouteStrategy(jeep.zone_x, jeep.zone_y, jeep.zone_radius)
            jeep.state = "ON TOUR"


class CampingTripStrategy:
    """A multi-day premium jeep trip that camps in a remote zone."""
    def __init__(self, schedule_index, trip):
        self.schedule_index = schedule_index
        self.name = trip.get("name", "Camping Trip")
        self.start_tick = trip["start_tick"]
        self.end_tick = trip["end_tick"]
        self.camp_x = trip["camp_x"]
        self.camp_y = trip["camp_y"]
        self.radius = trip.get("radius", 9)
        self.waypoint = None

    def execute(self, jeep):
        if jeep.current_tick >= self.end_tick:
            jeep.completed_long_trips.add(self.schedule_index)
            jeep.active_long_trip = None
            jeep.behavior = ReturnToBaseStrategy()
            jeep.state = "RETURNING FROM CAMP"
            jeep.behavior.execute(jeep)
            return

        day = max(1, ((jeep.current_tick - self.start_tick) // 24) + 1)
        jeep.state = f"CAMPING DAY {day}"

        if abs(jeep.x - self.camp_x) + abs(jeep.y - self.camp_y) > self.radius:
            jeep.move_towards(self.camp_x, self.camp_y, jeep.CRUISE_STEP)
            return

        target_x, target_y = self._current_waypoint(jeep)
        jeep.move_towards(target_x, target_y, jeep.PATROL_STEP)

    def _current_waypoint(self, jeep):
        if self.waypoint:
            distance = abs(jeep.x - self.waypoint[0]) + abs(jeep.y - self.waypoint[1])
            if distance > 3:
                return self.waypoint

        min_x = max(0, self.camp_x - self.radius)
        max_x = min(GRID_WIDTH - 1, self.camp_x + self.radius)
        min_y = max(0, self.camp_y - self.radius)
        max_y = min(GRID_HEIGHT - 1, self.camp_y + self.radius)
        self.waypoint = (random.randint(min_x, max_x), random.randint(min_y, max_y))
        return self.waypoint


class ReturnToBaseStrategy:
    """Jeep heads back to base at end of tour."""
    def execute(self, jeep):
        jeep.state = "RETURNING TO BASE"
        jeep.move_towards(BASE_X, BASE_Y, jeep.RETURN_STEP)

        if jeep.x == BASE_X and jeep.y == BASE_Y:
            jeep.behavior = None   # will be set to PARKED
            jeep.state = "PARKED"
            jeep.seats_taken = 0
            jeep._print(f"   🚙 [{jeep.name}] Tour complete! "
                        f"Total sightings today: {jeep.sightings}")


class RefuelStrategy:
    """Jeep returns to the safari station and refuels before touring again."""
    def execute(self, jeep):
        jeep.seats_taken = 0

        if jeep.x != FUEL_STATION_X or jeep.y != FUEL_STATION_Y:
            jeep.state = "RETURNING TO REFUEL"
            jeep.move_towards(FUEL_STATION_X, FUEL_STATION_Y, jeep.RETURN_STEP)
            return

        jeep.state = "REFUELLING"
        jeep.fuel_level = min(jeep.fuel_capacity, jeep.fuel_level + jeep.refuel_rate)
        if jeep.fuel_level < jeep.fuel_capacity:
            return

        touring, nocturnal = on_tour(jeep.current_hour)
        if touring:
            jeep.depart_tour(nocturnal)
        else:
            jeep.behavior = None
            jeep.state = "PARKED"


# ── SAFARI JEEP ───────────────────────────────────────────────

class SafariJeep(threading.Thread, EventListener):

    DRIVE_SPEED = 0.75
    CRUISE_STEP = 6
    PATROL_STEP = 5
    CHASE_STEP = 4
    RETURN_STEP = 5

    def __init__(self, name: str, x: int = BASE_X, y: int = BASE_Y,
             zone_x: int = 5, zone_y: int = 5, zone_radius: int = 10,
             display_output: bool = True, seat_capacity: int = 6,
             long_trip_schedule=None):
        threading.Thread.__init__(self)
        self.name = name
        self.id = ""
        self.x = x
        self.y = y
        self.engine_ref = None
        self.state = "PARKED"
        self.is_alive = True
        self.sightings = 0
        self.seat_capacity = seat_capacity
        self.seats_taken = 0
        self.fuel_capacity = 160
        self.fuel_level = 160
        self.fuel_low_threshold = 35
        self.minimum_tour_fuel = 90
        self.minimum_long_trip_fuel = 120
        self.fuel_burn_rate = 0.16
        self.refuel_rate = 40
        self.behavior = None
        self.daemon = True
        self.is_running = False
        self.display_output = display_output
        self._lock = threading.Lock()
        self.current_hour = 0
        self.current_tick = 0
        self.known_entities = []
        self.zone_x = zone_x        # 👈 new
        self.zone_y = zone_y        # 👈 new
        self.zone_radius = zone_radius  # 👈 new
        self.long_trip_schedule = long_trip_schedule or []
        self.completed_long_trips = set()
        self.active_long_trip = None

        event_bus.subscribe(Event.ANIMAL_HUNTING,   self)
        event_bus.subscribe(Event.ANIMAL_DIED,      self)

    def update(self, current_hour, entities):
        """Engine calls this every tick to sync the hour."""
        self.current_hour = current_hour
        if self.engine_ref:
            self.current_tick = getattr(self.engine_ref, "tick_count", self.current_tick)
        self.known_entities = entities

    def on_event(self, event_type: str, payload: dict):
        with self._lock:
            # Only react if on tour and not already chasing
            touring, _ = on_tour(self.current_hour)
            if not touring:
                return
            if isinstance(self.behavior, (ChaseStrategy, RefuelStrategy, CampingTripStrategy)):
                return
            if self.needs_refuel():
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

        while self.is_running:
            if self.engine_ref and self.engine_ref.is_paused():
                time.sleep(0.1)
                continue

            with self._lock:
                if self.engine_ref:
                    self.current_tick = getattr(self.engine_ref, "tick_count", self.current_tick)
                touring, nocturnal = on_tour(self.current_hour)
                camping = isinstance(self.behavior, CampingTripStrategy)
                long_trip = self._scheduled_long_trip()

                if self.needs_refuel() and not camping and not isinstance(self.behavior, RefuelStrategy):
                    self.start_refuelling()

                if isinstance(self.behavior, RefuelStrategy):
                    pass
                elif camping:
                    pass
                elif long_trip:
                    schedule_index, trip = long_trip
                    if self.fuel_level >= self.minimum_long_trip_fuel:
                        self.depart_long_trip(schedule_index, trip)
                    else:
                        self.start_refuelling()
                elif touring:
                    if not self.is_active_tour():
                        if self.fuel_level >= self.minimum_tour_fuel:
                            self.depart_tour(nocturnal)
                        else:
                            self.start_refuelling()
                else:
                    if self.is_active_tour():
                        self.behavior = ReturnToBaseStrategy()
                    elif self.fuel_level < self.fuel_capacity:
                        self.start_refuelling()
                    elif self.state != "PARKED":
                        self.state = "PARKED"
                        self.seats_taken = 0
                        self.behavior = None

                if self.behavior:
                    self.behavior.execute(self)
                    fuel = f"{self.fuel_level}/{self.fuel_capacity}"
                    self._print(f"   🚙 [{self.name}] @({self.x},{self.y}) | "
                                f"{self.state} | fuel: {fuel} | sightings: {self.sightings}")

            time.sleep(self.DRIVE_SPEED)

    def stop(self):
        self.is_running = False
        event_bus.unsubscribe(Event.ANIMAL_HUNTING, self)
        event_bus.unsubscribe(Event.ANIMAL_DIED, self)

    def depart_tour(self, nocturnal=False):
        tour_type = "NOCTURNAL SPECIAL" if nocturnal else "SAFARI TOUR"
        self._print(f"\n🚙 [{self.name}] {tour_type} departing! Hour {self.current_hour}:00")
        self.sightings = 0
        self.seats_taken = random.randint(max(1, self.seat_capacity // 2), self.seat_capacity)
        self.behavior = PatrolRouteStrategy(self.zone_x, self.zone_y, self.zone_radius)
        self.state = "ON TOUR"

    def depart_long_trip(self, schedule_index, trip):
        self.sightings = 0
        self.seats_taken = random.randint(max(1, self.seat_capacity - 2), self.seat_capacity)
        self.active_long_trip = dict(trip)
        self.behavior = CampingTripStrategy(schedule_index, trip)
        self.state = "CAMPING DAY 1"
        self._print(f"\n⛺ [{self.name}] {trip.get('name', 'Camping Trip')} departing "
                    f"until tick {trip['end_tick']}!")

    def start_refuelling(self):
        self.seats_taken = 0
        self.behavior = RefuelStrategy()

    def needs_refuel(self):
        return self.fuel_level <= self.fuel_low_threshold

    def is_active_tour(self):
        return isinstance(self.behavior, (PatrolRouteStrategy, ChaseStrategy, CampingTripStrategy))

    def _scheduled_long_trip(self):
        for index, trip in enumerate(self.long_trip_schedule):
            if index in self.completed_long_trips:
                continue
            if trip["start_tick"] <= self.current_tick < trip["end_tick"]:
                return index, trip
        return None

    def move_randomly_in_zone(self, zone_x, zone_y, radius):
        if self.fuel_level <= 0:
            self.state = "OUT OF FUEL"
            self.seats_taken = 0
            return

        if not (zone_x - radius <= self.x <= zone_x + radius
                and zone_y - radius <= self.y <= zone_y + radius):
            self.state = "TRAVELLING TO TOUR ZONE"
            self.move_towards(zone_x, zone_y, self.CRUISE_STEP)
            return

        old_x, old_y = self.x, self.y
        self.x = max(zone_x - radius,
                     min(zone_x + radius,
                         self.x + random.randint(-self.PATROL_STEP, self.PATROL_STEP)))
        self.y = max(zone_y - radius,
                     min(zone_y + radius,
                         self.y + random.randint(-self.PATROL_STEP, self.PATROL_STEP)))
        self.x = max(0, min(GRID_WIDTH - 1, self.x))
        self.y = max(0, min(GRID_HEIGHT - 1, self.y))
        self.consume_fuel(old_x, old_y)

    def move_towards(self, target_x, target_y, step):
        if self.fuel_level <= 0 and not isinstance(self.behavior, RefuelStrategy):
            self.state = "OUT OF FUEL"
            self.seats_taken = 0
            return

        old_x, old_y = self.x, self.y
        self.x += self._step_towards(self.x, target_x, step)
        self.y += self._step_towards(self.y, target_y, step)
        self.x = max(0, min(GRID_WIDTH - 1, self.x))
        self.y = max(0, min(GRID_HEIGHT - 1, self.y))
        self.consume_fuel(old_x, old_y)

    def consume_fuel(self, old_x, old_y):
        distance = abs(self.x - old_x) + abs(self.y - old_y)
        if distance:
            burn = max(1, round(distance * self.fuel_burn_rate))
            self.fuel_level = max(0, self.fuel_level - burn)

    def _step_towards(self, current, target, step):
        if current < target:
            return min(step, target - current)
        if current > target:
            return -min(step, current - target)
        return 0

    def _print(self, *args, **kwargs):
        if self.display_output:
            print(*args, **kwargs)
