
# utils/events.py
# ============================================================
# OBSERVER PATTERN — Event Bus
# ============================================================
# How it works:
#   - EventBus is the single broadcaster (the "Subject")
#   - Any object that wants to react to events implements
#     EventListener and registers on the EventBus
#   - When something happens (animal dies, spot opens),
#     someone calls event_bus.emit() and every registered
#     listener is automatically notified
#
# Why we use it here:
#   Before this, the engine manually looped through every
#   entity to check state changes. Now events fire instantly
#   to exactly the listeners that care — sender and receiver
#   are fully decoupled.
# ============================================================

import threading
from abc import ABC, abstractmethod


# ── EVENT TYPE CONSTANTS ─────────────────────────────────────
class Event:
    ANIMAL_DIED      = "animal_died"       # payload: { "entity": animal, "cause": str }
    ANIMAL_BORN      = "animal_born"       # payload: { "entity": animal, "parent_a": animal, "parent_b": animal }
    WATER_SPOT_FREED = "water_spot_freed"  # payload: { "environment": hole, "freed_by": animal }
    GRAZING_SPOT_FREED = "grazing_spot_freed"  # payload: { "environment": area, "freed_by": animal }
    ANIMAL_HUNTING   = "animal_hunting"    # payload: { "predator": animal, "prey": animal }
    WEATHER_CHANGED  = "weather_changed"   # payload: { "weather": str }
    ANIMAL_DESPERATE = "animal_desperate"  # payload: { "entity": animal }
    ENTITY_ADDED     = "entity_added"      # payload: { "entity": entity }
    ENVIRONMENT_ADDED = "environment_added" # payload: { "environment": component }


# ── LISTENER INTERFACE ───────────────────────────────────────
class EventListener(ABC):
    """
    Any class that wants to react to simulation events
    must implement this interface and register on the EventBus.
    """
    @abstractmethod
    def on_event(self, event_type: str, payload: dict):
        pass


# ── EVENT BUS ────────────────────────────────────────────────
class EventBus:
    """
    Central broadcaster for the whole simulation.
    Keeps a registry of listeners per event type.
    """

    def __init__(self):
        self._listeners: dict[str, list] = {}
        self._lock = threading.RLock()

    def subscribe(self, event_type: str, listener: EventListener):
        """Register a listener to be called when event_type fires."""
        with self._lock:
            if event_type not in self._listeners:
                self._listeners[event_type] = []
            if listener not in self._listeners[event_type]:
                self._listeners[event_type].append(listener)

    def unsubscribe(self, event_type: str, listener: EventListener):
        """Remove a listener (e.g. when an entity dies)."""
        with self._lock:
            if event_type in self._listeners:
                self._listeners[event_type] = [
                    l for l in self._listeners[event_type] if l is not listener
                ]

    def emit(self, event_type: str, payload: dict = None):
        """
        Fire an event. Every subscribed listener is notified immediately.
        """
        if payload is None:
            payload = {}
        with self._lock:
            listeners = list(self._listeners.get(event_type, []))
        for listener in listeners:
            listener.on_event(event_type, payload)


# ── GLOBAL SINGLETON ─────────────────────────────────────────
# One shared bus for the whole simulation.
# Import anywhere with:  from utils.events import event_bus, Event
event_bus = EventBus()
