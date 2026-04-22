"""
Seeking Water State - Animal is moving toward watering hole

This state handles the behavior of animals seeking water when thirsty.
The animal will move toward the target water source.
"""

from .base import AnimalState


class SeekingWaterState(AnimalState):
    """
    The SEEKING_WATER state represents an animal traveling to water.
    
    When an animal's thirst reaches the threshold, they enter this state
    and move toward the watering hole. Upon arrival, they either:
    - Start drinking if space available
    - Wait in line if full
    """
    
    def enter(self):
        """Log when starting to seek water"""
        self.animal.state = "SEEKING_WATER"
    
    def update(self, current_hour: int, entities: list):
        """
        Move toward the water source.
        
        If we have reached the water source, attempt to start drinking.
        If no space, we wait in line (handled by environment).
        """
        from utils.constants import MAX_THIRST
        from .drinking import DrinkingState
        
        # Check survival
        if not self._check_survival():
            return
        
        # Check if we're at the water source
        if self.animal.target_water:
            water = self.animal.target_water
            if self.animal.x == water.x and self.animal.y == water.y:
                # We're at the water - environment handles drinking logic
                # This state just waits
                return
        
        # Move toward water source using strategy
        if self.animal.target_water:
            target = self.animal.target_water
            self.animal.movement_strategy.seek_target(
                self.animal, 
                target.x, 
                target.y
            )
    
    def exit(self):
        """Clean up if needed"""
        pass