"""
Random Walk Strategy - Unpredictable random movement

This strategy implements random wandering behavior.
The animal moves in random directions each step.
"""

import random
from ..base import MovementStrategy


class RandomWalkStrategy(MovementStrategy):
    """
    Random Walk Movement Strategy.
    
    The animal moves in completely random directions.
    This simulates natural wandering behavior where animals
    explore their environment without specific purpose.
    
    Use cases:
    - Default wandering for non-herd animals
    - Lost animals
    - Exploratory behavior
    
    Algorithm:
        1. Choose random direction from [-1, 0, 1] for X
        2. Choose random direction from [-1, 0, 1] for Y
        3. Apply movement
    """
    
    def can_execute(self, animal, entities: list) -> bool:
        """Random walk is always applicable"""
        return True
    
    def move(self, animal, entities: list, speed_multiplier: int = 1):
        """
        Execute random movement.
        
        Args:
            animal: The animal to move
            entities: List of all entities (unused for random walk)
            speed_multiplier: Number of random steps to take
        """
        for _ in range(speed_multiplier):
            animal.x += random.choice([-1, 0, 1])
            animal.y += random.choice([-1, 0, 1])