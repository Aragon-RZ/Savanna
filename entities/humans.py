
# entities/humans.py
# ============================================================
# OBSERVER PATTERN — Ranger listens to animal events
# STRATEGY PATTERN — Ranger swaps between patrol/respond
# ============================================================
# The Ranger runs on its OWN thread, completely independent
# of the main simulation tick loop. This demonstrates true
# parallelism — the ranger acts concurrently with animals.
#
# OBSERVER: subscribes to ANIMAL_DIED and ANIMAL_DESPERATE
#           events via the EventBus
# STRATEGY: swaps between PatrolStrategy and RespondStrategy
#           at runtime depending on events received
# THREADING: extends threading.Thread, runs independently
# ============================================================

import threading
import time
import random
from utils.events import event_bus, Event, EventListener
from utils.constants import (
    GRID_WIDTH,
    GRID_HEIGHT,
    RANGER_CAMP_STEP,
    RANGER_PATROL_SPEED,
    RANGER_PURSUIT_STEP,
    RANGER_RESPONSE_STEP,
)



# ── STRATEGY PATTERN — Ranger Behaviors ─────────────────────

class RangerStrategy:
    """Base strategy — ranger patrols calmly."""
    def execute(self, ranger):
        ranger.state = "PATROLLING"
        ranger.x = max(0, min(GRID_WIDTH  - 1, ranger.x + random.choice([-1, 0, 1])))
        ranger.y = max(0, min(GRID_HEIGHT - 1, ranger.y + random.choice([-1, 0, 1])))
        ranger.avoid_water_centers()


class CampPatrolStrategy:
    """Ranger patrols around a temporary anti-poaching camp."""
    def __init__(self, camp, radius=5):
        self.camp = camp
        self.radius = radius

    def execute(self, ranger):
        if not ranger.camp_assignment:
            # Camp may have expired while this strategy was active.
            ranger.behavior = RangerStrategy()
            ranger.behavior.execute(ranger)
            return

        ranger.state = f"CAMPING {self.camp.zone_id}"
        distance = abs(ranger.x - self.camp.x) + abs(ranger.y - self.camp.y)
        if distance > self.radius:
            ranger.move_towards(self.camp.x, self.camp.y, RANGER_CAMP_STEP)
        else:
            ranger.x = max(0, min(GRID_WIDTH - 1, ranger.x + random.choice([-1, 0, 1])))
            ranger.y = max(0, min(GRID_HEIGHT - 1, ranger.y + random.choice([-1, 0, 1])))
        ranger.avoid_water_centers()

class RespondStrategy:
    """
    Ranger received a distress event and moves toward
    the location of the animal in need.
    """
    def __init__(self, target_x, target_y, animal_name):
        self.target_x = target_x
        self.target_y = target_y
        self.animal_name = animal_name

    def execute(self, ranger):
        ranger.state = f"RESPONDING to {self.animal_name}"
        ranger.move_towards(self.target_x, self.target_y, RANGER_RESPONSE_STEP)

        # Arrived at scene
        if ranger.x == self.target_x and ranger.y == self.target_y:
            ranger._print(f"🚨  {ranger.name} arrived at scene of {self.animal_name}!")
            ranger.return_to_default_behavior()


class PursuePoacherStrategy:
    """Ranger moves toward a poacher and arrests them at close range."""
    def __init__(self, poacher):
        self.poacher = poacher

    def execute(self, ranger):
        if (not self.poacher
                or getattr(self.poacher, "resolution", None)
                or not getattr(self.poacher, "is_alive", False)):
            ranger.return_to_default_behavior()
            return

        ranger.state = f"PURSUING {self.poacher.name}"
        ranger.move_towards(self.poacher.x, self.poacher.y, RANGER_PURSUIT_STEP)

        # Arrests are intentionally close-range so chases can play out on the map.
        if abs(ranger.x - self.poacher.x) + abs(ranger.y - self.poacher.y) <= 1:
            if hasattr(self.poacher, "arrest"):
                self.poacher.arrest(ranger)
            ranger.return_to_default_behavior()


# ── RANGER (Thread + Observer) ───────────────────────────────

class Ranger(threading.Thread, EventListener):
    """
    A park ranger that patrols the savanna on its own thread
    and responds to animal emergencies.

    THREADING : extends Thread — runs concurrently with engine
    OBSERVER  : extends EventListener — reacts to EventBus events
    STRATEGY  : holds a behavior that swaps at runtime
    """

    PATROL_SPEED = RANGER_PATROL_SPEED  # seconds between ranger moves

    def __init__(self, name: str, x: int, y: int, territory: str = None,
                 display_output: bool = True):
        threading.Thread.__init__(self)
        self.name = name
        self.id = ""      
        self.x = x
        self.y = y
        self.engine_ref = None
        self.target_water = None
        self.territory = territory or ("south" if y >= GRID_HEIGHT // 2 else "north")
        self.display_output = display_output
        self.state = "PATROLLING"
        self.is_alive = True
        self.behavior = RangerStrategy()   # default strategy
        self.camp_assignment = None
        self.is_running = False
        self.daemon = True                 # dies when engine stops
        self._lock = threading.Lock()

        # OBSERVER — subscribe to relevant events
        event_bus.subscribe(Event.ANIMAL_DIED,      self)
        event_bus.subscribe(Event.ANIMAL_DESPERATE, self)
        event_bus.subscribe(Event.POACHER_SPOTTED,  self)

    # ── OBSERVER interface ───────────────────────────────────
    def on_event(self, event_type: str, payload: dict):
        """
        Called automatically by EventBus when an event fires.
        Ranger swaps to RespondStrategy to investigate.
        """
        if event_type == Event.POACHER_SPOTTED:
            poacher = payload.get("poacher")
            assigned_ranger = payload.get("assigned_ranger")
            if not poacher:
                return
            if assigned_ranger and assigned_ranger is not self:
                return

            # If the engine did not nominate a ranger, only the local territory responds.
            event_territory = "south" if poacher.y >= GRID_HEIGHT // 2 else "north"
            if not assigned_ranger and event_territory != self.territory:
                return

            self._print(f"📻  {self.name} received POACHER report: "
                        f"{poacher.name} at ({poacher.x}, {poacher.y})!")
            with self._lock:
                self.behavior = PursuePoacherStrategy(poacher)
            return

        entity = payload.get("entity")
        if not entity:
            return

        event_territory = "south" if entity.y >= GRID_HEIGHT // 2 else "north"
        if event_territory != self.territory:
            return

        if event_type == Event.ANIMAL_DIED:
            self._print(f"📻  {self.name} received DEATH report: "
                        f"{entity.name} at ({entity.x}, {entity.y})!")
            with self._lock:
                if isinstance(self.behavior, PursuePoacherStrategy):
                    return
                self.behavior = RespondStrategy(entity.x, entity.y, entity.name)

        elif event_type == Event.ANIMAL_DESPERATE:
            entity = payload.get("entity")
            if entity:
                dist = abs(entity.x - self.x) + abs(entity.y - self.y)
                if dist <= 15:
                    self._print(f"👁️  {self.name} spotted distressed "
                                f"{entity.name} at ({entity.x}, {entity.y})!")
                    with self._lock:
                        if isinstance(self.behavior, RangerStrategy):
                            self.behavior = RespondStrategy(entity.x, entity.y, entity.name)

    def update(self, current_hour, entities):
        """
        Rangers manage themselves on their own thread.
        This method exists only to satisfy the engine's entity loop.
        """
        pass

    # ── THREAD run loop ──────────────────────────────────────
    def run(self):
        self.is_running = True
        self._print(f"🌿  {self.name} started patrol at ({self.x}, {self.y})")

        while self.is_running:
            if self.engine_ref and self.engine_ref.is_paused():
                time.sleep(0.1)
                continue

            # Behavior swaps happen from event callbacks, so movement runs under a lock.
            with self._lock:
                self.behavior.execute(self)

            self._print(f"   🧑‍🌾 [{self.name}] @({self.x}, {self.y}) | "
                        f"State: {self.state}")

            time.sleep(self.PATROL_SPEED)

    def stop(self):
        self.is_running = False
        event_bus.unsubscribe(Event.ANIMAL_DIED, self)
        event_bus.unsubscribe(Event.ANIMAL_DESPERATE, self)
        event_bus.unsubscribe(Event.POACHER_SPOTTED, self)

    def assign_camp(self, camp):
        with self._lock:
            self.camp_assignment = camp
            # Pursuing a poacher is more urgent than walking to a new camp.
            if not isinstance(self.behavior, PursuePoacherStrategy):
                self.behavior = CampPatrolStrategy(camp)
            self._print(f"⛺  {self.name} is setting a temporary camp at "
                        f"({camp.x}, {camp.y}) for zone {camp.zone_id}.")

    def clear_camp(self, camp):
        with self._lock:
            if self.camp_assignment is not camp:
                return
            self.camp_assignment = None
            if isinstance(self.behavior, CampPatrolStrategy):
                self.behavior = RangerStrategy()

    def return_to_default_behavior(self):
        if self.camp_assignment:
            self.behavior = CampPatrolStrategy(self.camp_assignment)
        else:
            self.behavior = RangerStrategy()

    def move_towards(self, target_x, target_y, step=1):
        self.x += self._step_towards(self.x, target_x, step)
        self.y += self._step_towards(self.y, target_y, step)
        self.x = max(0, min(GRID_WIDTH - 1, self.x))
        self.y = max(0, min(GRID_HEIGHT - 1, self.y))
        self.avoid_water_centers()

    def _step_towards(self, current, target, step):
        if current < target:
            return min(step, target - current)
        if current > target:
            return -min(step, current - target)
        return 0

    def avoid_water_centers(self):
        if not self.target_water:
            return

        waters = self.target_water if isinstance(self.target_water, list) else [self.target_water]
        for water in waters:
            if abs(self.x - water.x) + abs(self.y - water.y) >= 2:
                continue

            dx = self.x - water.x
            dy = self.y - water.y
            if dx == 0 and dy == 0:
                dx = 1
            self.x = max(0, min(GRID_WIDTH - 1, self.x + (1 if dx > 0 else -1)))
            self.y = max(0, min(GRID_HEIGHT - 1, self.y + (1 if dy > 0 else -1)))

    def _print(self, *args, **kwargs):
        if self.display_output:
            print(*args, **kwargs)
