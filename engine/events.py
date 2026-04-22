"""
Observer Pattern Module - Event system for the simulation

This module implements the OBSERVER PATTERN which allows the simulation
to react to events without tight coupling between entities.

Observer Pattern Key Concepts:
- Subject: Entity that emits events (animals, environment)
- Observer: Objects that react to events
- Event: The actual event data being passed

Events tracked:
- ENTITY_BORN: New entity created
- ENTITY_DIED: Entity died
- STATE_CHANGED: Entity changed state
- ENTITY_DRANK: Entity finished drinking
- ENTITY_ATE: Entity ate (carnivore caught prey)
- ENTITY_FLED: Entity escaped predator
- PREDATOR_SPOTTED: Prey spotted a predator

Usage:
    # Register an observer
    from engine.events import EventManager, EventType
    EventManager.register_observer(my_observer)
    
    # Emit an event
    EventManager.emit(EventType.ENTITY_DIED, {
        'entity': animal,
        'cause': 'Hunted by Lion 1'
    })
"""

from enum import Enum
from typing import Callable, Dict, List, Any
from collections import defaultdict


class EventType(Enum):
    """
    All possible event types in the simulation.
    
    Each enum value represents a type of event that can occur.
    Observers can subscribe to specific events or all events.
    """
    ENTITY_BORN = "entity_born"
    ENTITY_DIED = "entity_died"
    STATE_CHANGED = "state_changed"
    ENTITY_DRANK = "entity_drank"
    ENTITY_ATE = "entity_ate"
    ENTITY_FLED = "entity_fled"
    PREDATOR_SPOTTED = "predator_spotted"
    ENTITY_BORN_THIRSTY = "entity_born_thirsty"
    WATERING_HOLE_EMPTY = "watering_hole_empty"
    WATERING_HOLE_AVAILABLE = "watering_hole_available"


class Event:
    """
    Represents a single event in the simulation.
    
    Attributes:
        type: The EventType of this event
        data: Dictionary of event data (entity, cause, etc.)
        tick: The simulation tick when event occurred
    """
    
    def __init__(self, event_type: EventType, data: Dict[str, Any], tick: int = 0):
        self.type = event_type
        self.data = data
        self.tick = tick
    
    def __repr__(self):
        return f"Event({self.type.value}, tick={self.tick})"


class Observer(Callable):
    """
    Abstract base class for event observers.
    
    Any class that wants to receive events should inherit from this
    and implement the on_event() method.
    
    Usage:
        class MyObserver(Observer):
            def on_event(self, event: Event):
                print(f"Event received: {event.type}")
    """
    
    def on_event(self, event: Event):
        """
        Called when a subscribed event occurs.
        
        Args:
            event: The Event object containing event data
        """
        raise NotImplementedError("Observers must implement on_event()")
    
    def __call__(self, event: Event):
        """Allows observer to be called directly"""
        self.on_event(event)


class EventManager:
    """
    Central event manager implementing the Observer pattern.
    
    This is a singleton that manages all event subscriptions and emissions.
    Any part of the simulation can emit events, and any part can subscribe.
    
    Design:
        - Uses defaultdict to store observers by event type
        - Supports wildcards (*) to receive all events
        - Observers can be functions or callable objects
    
    Usage:
        # Subscribe to specific event
        EventManager.subscribe(EventType.ENTITY_DIED, my_observer)
        
        # Subscribe to all events
        EventManager.subscribe("*", my_observer)
        
        # Emit an event
        EventManager.emit(EventType.ENTITY_DIED, {'entity': animal})
    """
    
    _instance = None
    _observers: Dict[str, List[Observer]] = defaultdict(list)
    _tick: int = 0
    
    def __new__(cls):
        """Singleton pattern - only one EventManager exists"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._observers = defaultdict(list)
            cls._tick = 0
        return cls._instance
    
    @classmethod
    def subscribe(cls, event_type: str, observer: Observer):
        """
        Subscribe an observer to receive events.
        
        Args:
            event_type: EventType value or "*" for all events
            observer: An Observer instance or callable
        """
        if observer not in cls._observers[event_type]:
            cls._observers[event_type].append(observer)
    
    @classmethod
    def unsubscribe(cls, event_type: str, observer: Observer):
        """
        Remove an observer from receiving events.
        
        Args:
            event_type: EventType value or "*" for all events
            observer: The observer to remove
        """
        if observer in cls._observers[event_type]:
            cls._observers[event_type].remove(observer)
    
    @classmethod
    def emit(cls, event_type: EventType, data: Dict[str, Any]):
        """
        Emit an event to all subscribed observers.
        
        Args:
            event_type: The type of event occurring
            data: Dictionary of event data
        """
        event = Event(event_type, data, cls._tick)
        
        # Notify observers subscribed to this specific event
        for observer in cls._observers[event_type.value]:
            try:
                observer.on_event(event)
            except Exception as e:
                print(f"Error in observer {observer}: {e}")
        
        # Notify observers subscribed to all events (*)
        for observer in cls._observers["*"]:
            try:
                observer.on_event(event)
            except Exception as e:
                print(f"Error in observer {observer}: {e}")
    
    @classmethod
    def set_tick(cls, tick: int):
        """Update the current simulation tick"""
        cls._tick = tick
    
    @classmethod
    def clear(cls):
        """Clear all observers (useful for testing)"""
        cls._observers.clear()


class ConsoleLogger(Observer):
    """
    Logs all events to the console with formatting.
    
    This is a built-in observer that provides formatted output
    for all simulation events.
    """
    
    def __init__(self, verbose: bool = True):
        self.verbose = verbose
    
    def on_event(self, event: Event):
        """Log the event to console"""
        if not self.verbose:
            return
        
        entity = event.data.get('entity')
        entity_name = entity.name if entity else "Unknown"
        
        if event.type == EventType.ENTITY_DIED:
            cause = event.data.get('cause', 'unknown')
            print(f"💀 EVENT: {entity_name} died - Cause: {cause}")
        
        elif event.type == EventType.STATE_CHANGED:
            old_state = event.data.get('old_state', 'N/A')
            new_state = event.data.get('new_state', 'N/A')
            print(f"🔄 EVENT: {entity_name} changed state: {old_state} → {new_state}")
        
        elif event.type == EventType.ENTITY_ATE:
            prey = event.data.get('prey')
            print(f"🍖 EVENT: {entity_name} ate {prey}")
        
        elif event.type == EventType.ENTITY_FLED:
            predator = event.data.get('predator')
            print(f"🏃 EVENT: {entity_name} fled from {predator}")
        
        elif event.type == EventType.PREDATOR_SPOTTED:
            predator = event.data.get('predator')
            print(f"⚠️ EVENT: {entity_name} spotted {predator}")


class StatisticsTracker(Observer):
    """
    Tracks simulation statistics.
    
    This observer collects data about the simulation for analysis
    or display purposes.
    """
    
    def __init__(self):
        self.stats = {
            'total_born': 0,
            'total_died': 0,
            'deaths_by_cause': defaultdict(int),
            'state_changes': 0,
            'meals_eaten': 0,
        }
    
    def on_event(self, event: Event):
        """Track the event in statistics"""
        entity = event.data.get('entity')
        entity_name = entity.name if entity else "Unknown"
        
        if event.type == EventType.ENTITY_BORN:
            self.stats['total_born'] += 1
        
        elif event.type == EventType.ENTITY_DIED:
            self.stats['total_died'] += 1
            cause = event.data.get('cause', 'unknown')
            self.stats['deaths_by_cause'][cause] += 1
        
        elif event.type == EventType.STATE_CHANGED:
            self.stats['state_changes'] += 1
        
        elif event.type == EventType.ENTITY_ATE:
            self.stats['meals_eaten'] += 1
    
    def get_summary(self) -> str:
        """Get a summary of tracked statistics"""
        return f"""
=== Simulation Statistics ===
Born: {self.stats['total_born']}
Died: {self.stats['total_died']}
Meals Eaten: {self.stats['meals_eaten']}
State Changes: {self.stats['state_changes']}
Deaths by Cause:
{chr(10).join(f"  - {cause}: {count}" for cause, count in self.stats['deaths_by_cause'].items())}
"""