
# environment/nature.py
# ============================================================
# WateringHole — now uses COMPOSITE + OBSERVER
# ============================================================
# Changes from original:
#   - Extends EnvironmentComponent (Composite leaf node)
#   - Emits Event.WATER_SPOT_FREED via EventBus (Observer)
#     so waiting animals are notified automatically
#   - update() now owns the "finished drinking" logic that
#     used to be scattered inside simulation.py
# ============================================================

import threading
from environment.base import EnvironmentComponent
from utils.events import event_bus, Event


class WateringHole(EnvironmentComponent):
    """
    A shared natural resource with limited simultaneous capacity.

    COMPOSITE : is a leaf node — lives inside a SavannaZone.
    OBSERVER  : emits WATER_SPOT_FREED when a spot opens up.
    THREADING : Semaphore controls concurrent access.
    """

    def __init__(self, name: str, x: int, y: int, capacity: int = 3):
        super().__init__(name, x, y)
        self.capacity = capacity
        self.spots = threading.Semaphore(capacity)  # core parallelism mechanism
        self.current_drinkers: list = []
        self.display_output = True

    # ── COMPOSITE INTERFACE ──────────────────────────────────

    def update(self, tick: int, entities: list):
        """
        Called every tick by the engine or parent SavannaZone.
        Handles finished drinkers and lets waiting animals in.
        This logic used to live in simulation.py — now it
        belongs to the environment itself.
        """
        # Check if any current drinker has finished
        for entity in list(self.current_drinkers):
            if entity.state != "DRINKING":
                self.finish_drinking(entity)

        # Let in any entity waiting at our location
        for entity in entities:
            if entity.is_alive and entity.state in ["SEEKING_WATER", "WAITING_IN_LINE"]:
                if entity.x == self.x and entity.y == self.y:
                    self.try_to_drink(entity)

    def status(self) -> str:
        drinker_names = ", ".join(e.name for e in self.current_drinkers) or "none"
        free = self.capacity - len(self.current_drinkers)
        return (f"💧 {self.name} | Capacity: {self.capacity} | "
                f"Drinking: {len(self.current_drinkers)} ({drinker_names}) | "
                f"Free spots: {free}")

    # ── WATERING HOLE LOGIC ──────────────────────────────────

    def try_to_drink(self, entity) -> bool:
        """
        Non-blocking attempt to give entity a drinking spot.
        Returns True if successful, False if animal must wait.
        """
        if entity in self.current_drinkers:
            return True  # already drinking

        if self.spots.acquire(blocking=False):
            entity.state = "DRINKING"
            self.current_drinkers.append(entity)
            self._print(f"💧 {entity.name} found a spot and started drinking at {self.name}!")
            return True
        else:
            entity.state = "SEEKING_WATER"  # keep moving, try again next tick
            self._print(f"⏳ {entity.name} is waiting in line. {self.name} is full.")
            return False

    def finish_drinking(self, entity):
        """
        Remove entity and release the semaphore spot.
        OBSERVER: emits WATER_SPOT_FREED so any subscribed
        waiting animal can immediately attempt to drink.
        """
        if entity in self.current_drinkers:
            self.current_drinkers.remove(entity)
            self.spots.release()
            self._print(f"✅ {entity.name} finished drinking and freed a spot at {self.name}.")

            # 🔔 Notify all observers that a spot opened up
            event_bus.emit(Event.WATER_SPOT_FREED, {
                "environment": self,
                "freed_by": entity
            })

    def _print(self, *args, **kwargs):
        if self.display_output:
            print(*args, **kwargs)


class GrazingArea(EnvironmentComponent):
    """
    A natural feeding ground where herbivores can graze.

    COMPOSITE : is a leaf node — lives inside a SavannaZone.
    OBSERVER  : emits GRAZING_SPOT_AVAILABLE when space opens.
    THREADING : Semaphore controls concurrent grazing.
    """

    def __init__(self, name: str, x: int, y: int, capacity: int = 5):
        super().__init__(name, x, y)
        self.capacity = capacity
        self.spots = threading.Semaphore(capacity)
        self.current_grazers: list = []
        self.display_output = True

    def update(self, tick: int, entities: list):
        """
        Called every tick. Handles finished grazers and lets
        waiting herbivores in.
        """
        # Check if any grazer has finished eating
        for entity in list(self.current_grazers):
            if entity.state != "GRAZING":
                self.finish_grazing(entity)

        # Let in any herbivore at our location wanting to graze
        for entity in entities:
            if entity.is_alive and entity.state in ["SEEKING_FOOD", "WAITING_TO_GRAZE"]:
                if entity.x == self.x and entity.y == self.y:
                    self.try_to_graze(entity)

    def status(self) -> str:
        grazer_names = ", ".join(e.name for e in self.current_grazers) or "none"
        free = self.capacity - len(self.current_grazers)
        return (f"🌾 {self.name} | Capacity: {self.capacity} | "
                f"Grazing: {len(self.current_grazers)} ({grazer_names}) | "
                f"Free spots: {free}")

    def try_to_graze(self, entity) -> bool:
        """
        Non-blocking attempt to give entity a grazing spot.
        Returns True if successful, False if animal must wait.
        """
        if entity in self.current_grazers:
            return True  # already grazing

        if self.spots.acquire(blocking=False):
            entity.state = "GRAZING"
            self.current_grazers.append(entity)
            self._print(f"🌾 {entity.name} found grass and started grazing at {self.name}!")
            return True
        else:
            entity.state = "SEEKING_FOOD"  # keep moving
            self._print(f"⏳ {entity.name} waiting to graze. {self.name} is crowded.")
            return False

    def finish_grazing(self, entity):
        """
        Remove entity and release the semaphore spot.
        Reduces entity hunger as reward for grazing.
        """
        if entity in self.current_grazers:
            self.current_grazers.remove(entity)
            self.spots.release()
            entity.hunger = max(0, entity.hunger - 15)  # reduce hunger
            self._print(f"✅ {entity.name} finished grazing at {self.name}.")

            # Notify observers
            event_bus.emit(Event.GRAZING_SPOT_FREED, {
                "environment": self,
                "freed_by": entity
            })

    def _print(self, *args, **kwargs):
        if self.display_output:
            print(*args, **kwargs)


class InsectivoreFeedingGround(EnvironmentComponent):
    """
    Feeding ground for insectivores. It behaves like a shared food
    resource so multiple insectivores can feed without blocking the
    whole simulation.
    """

    def __init__(self, name: str, x: int, y: int, capacity: int = 5):
        super().__init__(name, x, y)
        self.capacity = capacity
        self.spots = threading.Semaphore(capacity)
        self.current_feeders: list = []
        self.display_output = True

    def update(self, tick: int, entities: list):
        for entity in list(self.current_feeders):
            if entity.state != "FORAGING":
                self.finish_feeding(entity)

        for entity in entities:
            if entity.is_alive and entity.state in ["SEEKING_INSECTS", "WAITING_TO_FORAGE"]:
                if entity.x == self.x and entity.y == self.y:
                    self.try_to_feed(entity)

    def status(self) -> str:
        feeder_names = ", ".join(e.name for e in self.current_feeders) or "none"
        free = self.capacity - len(self.current_feeders)
        return (f"{self.name} | Insectivore capacity: {self.capacity} | "
                f"Feeding: {len(self.current_feeders)} ({feeder_names}) | "
                f"Free spots: {free}")

    def try_to_feed(self, entity) -> bool:
        if entity in self.current_feeders:
            return True

        if self.spots.acquire(blocking=False):
            entity.state = "FORAGING"
            self.current_feeders.append(entity)
            self._print(f"{entity.name} started foraging at {self.name}.")
            return True

        entity.state = "WAITING_TO_FORAGE"
        self._print(f"{entity.name} is waiting to forage at {self.name}.")
        return False

    def finish_feeding(self, entity):
        if entity in self.current_feeders:
            self.current_feeders.remove(entity)
            self.spots.release()
            entity.hunger = max(0, entity.hunger - 25)
            self._print(f"{entity.name} finished foraging at {self.name}.")

            event_bus.emit(Event.GRAZING_SPOT_FREED, {
                "environment": self,
                "freed_by": entity
            })

    def _print(self, *args, **kwargs):
        if self.display_output:
            print(*args, **kwargs)


class River(EnvironmentComponent):
    """
    A river running across the savanna. Multiple animals can
    drink from it simultaneously (high capacity).

    COMPOSITE : is a leaf node — lives inside a SavannaZone.
    OBSERVER  : emits WATER_SPOT_FREED when space opens.
    """

    def __init__(self, name: str, x: int, y: int, capacity: int = 10,
                 path_points=None):
        super().__init__(name, x, y)
        self.capacity = capacity
        self.spots = threading.Semaphore(capacity)
        self.current_drinkers: list = []
        self.path_points = path_points or [
            (max(0, x - 18), 0),
            (max(0, x - 10), max(0, y - 22)),
            (x, y),
            (min(99, x + 12), min(99, y + 24)),
            (min(99, x + 20), 99),
        ]
        self.display_output = True

    def update(self, tick: int, entities: list):
        """
        Called every tick. Handles finished drinkers and lets
        waiting animals drink from the river.
        """
        # Check if any drinker has finished
        for entity in list(self.current_drinkers):
            if entity.state != "DRINKING":
                self.finish_drinking(entity)

        # Let in any entity at our location wanting water
        for entity in entities:
            if entity.is_alive and entity.state in ["SEEKING_WATER", "WAITING_IN_LINE"]:
                if self.contains_location(entity.x, entity.y):
                    self.try_to_drink(entity)

    def status(self) -> str:
        drinker_names = ", ".join(e.name for e in self.current_drinkers) or "none"
        free = self.capacity - len(self.current_drinkers)
        return (f"🌊 {self.name} | Capacity: {self.capacity} | "
                f"Drinking: {len(self.current_drinkers)} ({drinker_names}) | "
                f"Free spots: {free}")

    def try_to_drink(self, entity) -> bool:
        """
        Non-blocking attempt to give entity a drinking spot.
        Returns True if successful, False if animal must wait.
        """
        if entity in self.current_drinkers:
            return True  # already drinking

        if self.spots.acquire(blocking=False):
            entity.state = "DRINKING"
            self.current_drinkers.append(entity)
            self._print(f"🌊 {entity.name} found the river and started drinking at {self.name}!")
            return True
        else:
            entity.state = "SEEKING_WATER"
            self._print(f"⏳ {entity.name} waiting at the river. {self.name} is busy.")
            return False

    def finish_drinking(self, entity):
        """
        Remove entity and release the semaphore spot.
        """
        if entity in self.current_drinkers:
            self.current_drinkers.remove(entity)
            self.spots.release()
            self._print(f"✅ {entity.name} finished drinking from {self.name}.")

            event_bus.emit(Event.WATER_SPOT_FREED, {
                "environment": self,
                "freed_by": entity
            })

    def _print(self, *args, **kwargs):
        if self.display_output:
            print(*args, **kwargs)

    def contains_location(self, x: int, y: int) -> bool:
        return any(abs(px - x) + abs(py - y) <= 1 for px, py in self.path_points)


class LandObject(EnvironmentComponent):
    """Static map object used by the UI and future mechanics."""

    land_type = "land"

    def __init__(self, name: str, x: int, y: int):
        super().__init__(name, x, y)
        self.display_output = True

    def update(self, tick: int, entities: list):
        pass

    def status(self) -> str:
        return f"{self.name} | {self.land_type} @ ({self.x}, {self.y})"


class RangerStation(LandObject):
    land_type = "ranger_station"


class SafariStation(LandObject):
    land_type = "safari_station"


class TemporaryRangerCamp(LandObject):
    land_type = "temporary_ranger_camp"

    def __init__(self, name: str, x: int, y: int, zone_id: str,
                 expires_at_tick: int):
        super().__init__(name, x, y)
        self.zone_id = zone_id
        self.expires_at_tick = expires_at_tick

    def status(self) -> str:
        return (f"{self.name} | temporary camp for zone {self.zone_id} "
                f"until tick {self.expires_at_tick} @ ({self.x}, {self.y})")
