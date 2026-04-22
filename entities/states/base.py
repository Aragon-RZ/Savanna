"""
Base State Class - Foundation of the State Pattern

This abstract base class defines the interface that all concrete states
must implement. Each state encapsulates behavior specific to that state.

State Pattern Key Concepts:
1. Each state is a separate class with its own behavior
2. The entity (Animal) holds a reference to its current state
3. States can transition to other states
4. States delegate complex behavior to Strategy objects
"""

from abc import ABC, abstractmethod


class AnimalState(ABC):
    """
    Abstract base class for all animal states.
    
    The State Pattern replaces complex if/else chains with polymorphism.
    Instead of: if state == "WANDERING": do_wander()
    We use: self.state.update() which calls WanderingState.update()
    
    Attributes:
        animal: Reference to the animal entity that owns this state
        
    Methods:
        enter(): Called when entering this state
        exit(): Called when leaving this state  
        update(): Main behavior for this state (called each tick)
        transition_to(): Helper to switch to a new state
    """
    
    def __init__(self, animal):
        """
        Initialize state with reference to owning animal.
        
        Args:
            animal: The Animal entity that owns this state
        """
        self.animal = animal
    
    @property
    def name(self) -> str:
        """Returns the name of this state class for debugging/logging"""
        return self.__class__.__name__.replace("State", "")
    
    def enter(self):
        """
        Called automatically when animal enters this state.
        Override to perform entry actions (logging, initializing values, etc.)
        """
        pass
    
    def exit(self):
        """
        Called automatically when animal leaves this state.
        Override to perform cleanup actions (releasing resources, etc.)
        """
        pass
    
    @abstractmethod
    def update(self, current_hour: int, entities: list):
        """
        Main behavior executed each simulation tick while in this state.
        
        This is where the core logic of the state lives. The animal
        delegates all behavior to this method.
        
        Args:
            current_hour: Current time in simulation (0-23)
            entities: List of all entities in simulation (for interactions)
        """
        pass
    
    def transition_to(self, new_state: 'AnimalState'):
        """
        Cleanly transition from this state to a new state.
        
        Handles the exit/entry lifecycle automatically.
        OBSERVER PATTERN: Emits state change event.
        
        Args:
            new_state: The new AnimalState to transition to
        """
        old_state_name = self.name
        self.exit()
        self.animal._state = new_state
        new_state.enter()
        
        # OBSERVER PATTERN: Emit state changed event
        try:
            from engine.events import EventManager, EventType
            EventManager.emit(EventType.STATE_CHANGED, {
                'entity': self.animal,
                'old_state': old_state_name,
                'new_state': new_state.name
            })
        except ImportError:
            pass  # Events module not yet loaded
    
    def _check_survival(self) -> bool:
        """
        Check if animal has died from thirst/hunger.
        
        Returns:
            True if animal is still alive, False if died
        """
        from utils.constants import MAX_THIRST, MAX_HUNGER
        
        if self.animal.thirst >= MAX_THIRST:
            self.animal.die("Extreme Thirst")
            return False
        if self.animal.hunger >= MAX_HUNGER:
            self.animal.die("Starvation")
            return False
        return True
