"""
Herd Follow Strategy - Following a group of same-species animals

This strategy implements herd behavior where animals
move together as a group.
"""

import random
from ..base import MovementStrategy


class HerdFollowStrategy(MovementStrategy):
    """
    Herd Following Movement Strategy.
    
    The animal follows the center of nearby same-species
    animals. This creates natural herd behavior where
    animals stay together.
    
    Algorithm:
        1. Find all animals of the same type
        2. Calculate the average position (herd center)
        3. Move toward the herd center
        4. Small chance to stray and explore
    """
    
    def can_execute(self, animal, entities: list) -> bool:
        """Check if this animal is a herd animal"""
        return getattr(animal, 'is_herd_animal', True)
    
    def move(self, animal, entities: list, speed_multiplier: int = 1):
        """
        Move toward herd center.
        
        Args:
            animal: The animal to move
            entities: List of all entities (to find herd)
            speed_multiplier: Speed multiplier
        """
        # Find same-species animals that are alive
        friends = [e for e in entities 
                   if type(e) == type(animal) 
                   and e.is_alive 
                   and e.id != animal.id]
        
        # Find nearby friends within range
        nearby_herd = [f for f in friends 
                      if (abs(animal.x - f.x) + abs(animal.y - f.y)) <= 6]
        
        if nearby_herd:
            # Calculate herd center
            avg_x = sum(f.x for f in nearby_herd) / len(nearby_herd)
            avg_y = sum(f.y for f in nearby_herd) / len(nearby_herd)
            
            # 80% chance to follow herd, 20% chance to explore
            if random.random() < 0.8:
                self.seek_target(animal, avg_x, avg_y, speed_multiplier)
            else:
                # Stray and explore
                from .random_walk import RandomWalkStrategy
                RandomWalkStrategy().move(animal, entities, speed_multiplier)
        else:
            # No herd nearby, just wander randomly
            from .random_walk import RandomWalkStrategy
            RandomWalkStrategy().move(animal, entities, speed_multiplier)