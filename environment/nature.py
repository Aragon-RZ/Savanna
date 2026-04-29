
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
            print(f"💧 {entity.name} found a spot and started drinking at {self.name}!")
            return True
        else:
            entity.state = "SEEKING_WATER"  # keep moving, try again next tick
            print(f"⏳ {entity.name} is waiting in line. {self.name} is full.")
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
            print(f"✅ {entity.name} finished drinking and freed a spot at {self.name}.")

            # 🔔 Notify all observers that a spot opened up
            event_bus.emit(Event.WATER_SPOT_FREED, {
                "environment": self,
                "freed_by": entity
            })