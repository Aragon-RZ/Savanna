"""
Base Entity Class - Foundation of all simulation entities

This class provides the basic properties and methods that all
entities (animals, humans, etc.) share.

Changes for State Pattern:
- Added _state reference for State Pattern support
- Added state property for backward compatibility
- Added set_state() method for cleaner state transitions
"""

from entities.states import IdleState


class Entity:
    """
    Base class for all entities in the simulation.
    
    An entity is any object that exists in the savanna simulation.
    This includes animals, humans, and potentially other objects.
    
    Attributes:
        id: Unique identifier for this entity
        name: Display name (e.g., "Zebra 1", "Lion 3")
        x: X coordinate position
        y: Y coordinate position
        is_alive: Whether the entity is alive
        state: Current behavioral state (via State Pattern)
        _state: Internal State object
        
    State Pattern Integration:
        - _state: Holds the actual State object
        - state property: Returns string name for compatibility
        - set_state(): Clean way to transition states
    """
    
    def __init__(self, entity_id, name, x=0, y=0):
        """
        Initialize a new entity.
        
        Args:
            entity_id: Unique ID for this entity
            name: Display name
            x: Initial X coordinate
            y: Initial Y coordinate
        """
        self.id = entity_id
        self.name = name
        self.x = x
        self.y = y
        self.is_alive = True
        
        # STATE PATTERN: Initialize with idle state
        # The entity starts in IDLE state until simulation assigns behavior
        self._state = IdleState(self)
    
    @property
    def state(self) -> str:
        """
        Get the current state name as a string.
        
        This provides backward compatibility with code that checks
        the state as a string (e.g., if entity.state == "WANDERING")
        
        Returns:
            String name of the current state (e.g., "WANDERING")
        """
        if self._state:
            return self._state.name
        return "NONE"
    
    @state.setter
    def state(self, new_state_name: str):
        """
        Set state by name - provides backward compatibility.
        
        Usage: animal.state = "WANDERING"
        
        This converts the string to the appropriate State object.
        For cleaner code, use set_state() instead.
        
        Args:
            new_state_name: Name of the new state (e.g., "WANDERING")
        """
        from entities.states import get_state_by_name
        self._state = get_state_by_name(new_state_name, self)
    
    def set_state(self, new_state):
        """
        Set state directly with a State object.
        
        Preferred method for State Pattern usage.
        
        Usage:
            from entities.states import WanderingState
            animal.set_state(WanderingState(animal))
            
        Args:
            new_state: An AnimalState instance
        """
        self._state.transition_to(new_state)
    
    def update(self, current_hour=0, entities=None):
        """
        Update the entity for one simulation tick.
        
        This method should be overridden by subclasses to implement
        specific behavior. By default, delegates to current state.
        
        Args:
            current_hour: Current time (0-23)
            entities: List of all entities in simulation
        """
        # STATE PATTERN: Delegate to current state
        # The state object handles all behavior
        if self._state:
            self._state.update(current_hour, entities or [])
    
    def __str__(self):
        return f"[{self.name} {self.id}] at ({self.x}, {self.y}) - State: {self.state}"
    
    def die(self, cause: str = "unknown"):
        """
        Mark the entity as dead.
        
        OBSERVER PATTERN: Emits ENTITY_DIED event.
        
        Args:
            cause: Reason for death
        """
        self.is_alive = False
        
        # OBSERVER PATTERN: Emit death event
        try:
            from engine.events import EventManager, EventType
            EventManager.emit(EventType.ENTITY_DIED, {
                'entity': self,
                'cause': cause
            })
        except ImportError:
            pass  # Events module not yet loaded