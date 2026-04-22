"""
Flee Strategy - Moving away from a threat

This strategy implements fleeing behavior where the animal
moves in the opposite direction of a threat.
"""

from ..base import MovementStrategy


class FleeStrategy(MovementStrategy):
    """
    Flee Movement Strategy.
    
    The animal moves directly away from a threat (predator).
    This is the opposite direction of the threat's position.
    
    Algorithm:
        1. Calculate direction from animal to threat
        2. Move in the opposite direction
        3. (Optional) Move diagonally for better escape routes
    """
    
    def can_execute(self, animal, entities: list) -> bool:
        """Check if there's a threat nearby"""
        # Check for carnivores by attribute (avoid circular import)
        for e in entities:
            if e.is_alive and hasattr(e, 'hunting_strategy'):
                dist = abs(animal.x - e.x) + abs(animal.y - e.y)
                if dist <= 6:
                    return True
        return False
    
    def move(self, animal, entities: list, speed_multiplier: int = 1):
        """
        Flee from nearest threat.
        
        Args:
            animal: The animal to move
            entities: List of all entities (to find threats)
            speed_multiplier: Speed multiplier
        """
        # Find nearest predator by attribute check
        closest_predator = None
        closest_dist = 999
        
        for e in entities:
            if e.is_alive and hasattr(e, 'hunting_strategy'):
                dist = abs(animal.x - e.x) + abs(animal.y - e.y)
                if dist <= 6 and dist < closest_dist:
                    closest_dist = dist
                    closest_predator = e
        
        if closest_predator:
            # Flee in opposite direction
            self.flee(animal, closest_predator, speed_multiplier)