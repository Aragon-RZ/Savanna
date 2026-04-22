"""
Drinking State - Animal is at the watering hole drinking

This state represents an animal actively drinking water.
The animal remains stationary and reduces thirst level.
"""

from .base import AnimalState


class DrinkingState(AnimalState):
    """
    The DRINKING state represents an animal consuming water.
    
    When an animal reaches the watering hole and acquires a spot,
    they enter this state. Their thirst decreases each tick until
    fully quenched, then they return to wandering.
    """
    
    def enter(self):
        """Log when starting to drink"""
        self.animal.state = "DRINKING"
        print(f"💧 {self.animal.name} started drinking at the watering hole!")
    
    def update(self, current_hour: int, entities: list):
        """
        Reduce thirst while drinking.
        
        Thirst decreases by 25 per tick. Once thirst reaches 0,
        the animal is fully quenched and returns to wandering.
        """
        from .wandering import WanderingState
        
        # Reduce thirst while drinking
        self.animal.thirst -= 25
        
        # Check if fully quenched
        if self.animal.thirst <= 0:
            self.animal.thirst = 0
            print(f"✅ {self.animal.name} finished drinking.")
            self.transition_to(WanderingState(self.animal))
        
        # If thirst still high, keep drinking
    
    def exit(self):
        """
        Called when leaving drinking state (e.g., forced to leave).
        The environment will handle releasing the spot.
        """
        pass