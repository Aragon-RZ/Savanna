"""
Seek Target Strategy - Moving toward a specific destination

This strategy moves an animal directly toward a target location.
Used when the animal has a specific goal (like the watering hole).
"""

from ..base import MovementStrategy


class SeekTargetStrategy(MovementStrategy):
    """
    Seek Target Movement Strategy.
    
    The animal moves directly toward a specific target location.
    This is used when the animal has a clear goal.
    
    Use cases:
    - Seeking water when thirsty
    - Seeking shelter
    - Moving to a specific location
    
    Note: This strategy requires the animal to have a 'target_water'
    attribute or be given target coordinates directly.
    """
    
    def can_execute(self, animal, entities: list) -> bool:
        """Always can seek a target if one exists"""
        return hasattr(animal, 'target_water') and animal.target_water is not None
    
    def move(self, animal, entities: list, speed_multiplier: int = 1):
        """
        Move toward the target water source.
        
        Args:
            animal: The animal to move
            entities: List of all entities (unused)
            speed_multiplier: Speed multiplier
        """
        if animal.target_water:
            target = animal.target_water
            self.seek_target(animal, target.x, target.y, speed_multiplier)