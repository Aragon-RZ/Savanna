"""
Simple Chase Strategy - Direct pursuit of prey

This is the most basic hunting strategy where the predator
directly chases the nearest prey.
"""

from ..base import HuntingStrategy


class SimpleChaseStrategy(HuntingStrategy):
    """
    Simple Chase Hunting Strategy.
    
    The predator picks the nearest prey and chases it directly.
    This is a straightforward "run after it" approach.
    
    Use cases:
    - Default hunting behavior
    - Fast predators (Cheetah)
    - Open terrain hunting
    
    Algorithm:
        1. Find all prey within hunting range
        2. Pick the closest one
        3. Move directly toward it
    """
    
    def select_target(self, predator, prey_list: list):
        """
        Select the nearest prey.
        
        Args:
            predator: The carnivore doing the hunting
            prey_list: List of potential prey entities
            
        Returns:
            The nearest prey, or None if no prey available
        """
        if not prey_list:
            return None
        
        # Find nearest prey
        nearest_prey = None
        nearest_dist = 999
        
        for prey in prey_list:
            dist = abs(predator.x - prey.x) + abs(predator.y - prey.y)
            if dist < nearest_dist:
                nearest_dist = dist
                nearest_prey = prey
        
        return nearest_prey
    
    def hunt(self, predator, prey):
        """
        Chase the prey directly.
        
        Moves the predator one step toward the prey's position.
        
        Args:
            predator: The carnivore doing the hunting
            prey: The prey being chased
        """
        # Move toward prey - one step at a time
        if predator.x < prey.x:
            predator.x += 1
        elif predator.x > prey.x:
            predator.x -= 1
        
        if predator.y < prey.y:
            predator.y += 1
        elif predator.y > prey.y:
            predator.y -= 1