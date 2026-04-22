"""
Idle State - Animal is idle with no specific action

This is the default/starting state for all entities.
It serves as a placeholder before the animal enters a meaningful state.
"""

from .base import AnimalState


class IdleState(AnimalState):
    """
    The IDLE state represents an animal at rest with no specific task.
    
    This is typically the initial state when an animal is created,
    before the simulation assigns them a proper behavioral state.
    
    Behavior:
        - Does nothing specific
        - Animal remains stationary
        - Will transition to WANDERING or SLEEPING on first update
    """
    
    def enter(self):
        """Set state name when entering"""
        self.animal.state = "IDLE"
    
    def update(self, current_hour: int, entities: list):
        """
        Idle animals immediately transition to wandering.
        
        On first tick, they start exploring the savanna.
        """
        from .wandering import WanderingState
        self.transition_to(WanderingState(self.animal))
    
    def exit(self):
        """Nothing to clean up when leaving idle"""
        pass