"""
Desperate State - Animal is critically low on survival needs

This is an emergency state when an animal's thirst or hunger
reaches the desperation threshold. The animal will do anything
to survive, ignoring normal behavioral patterns.
"""

from .base import AnimalState
from utils.constants import DESPERATION_THRESHOLD


class DesperateState(AnimalState):
    """
    The DESPERATE state represents an animal in crisis.
    
    When thirst or hunger exceeds DESPERATION_THRESHOLD, the animal
    enters this emergency state. Normal rules are suspended - the
    animal will:
    - Wake up from sleep immediately
    - Ignore herd behavior
    - Prioritize survival above all else
    
    This state continues until the animal finds water/food
    or dies from exhaustion.
    """
    
    def enter(self):
        """Log when entering desperate state"""
        self.animal.state = "DESPERATE"
        print(f"⚠️ {self.animal.name} is DESPERATE! Critical survival situation!")
    
    def update(self, current_hour: int, entities: list):
        """
        Emergency survival behavior.
        
        Prioritizes finding water/food above all else.
        Animal becomes highly aggressive in seeking resources.
        """
        from .wandering import WanderingState
        from .seeking_water import SeekingWaterState
        from .hunting import HuntingState
        from utils.constants import MAX_THIRST, MAX_HUNGER, HUNGER_THRESHOLD
        
        # Check survival
        if not self._check_survival():
            return
        
        # Check if no longer desperate
        is_still_desperate = (self.animal.thirst >= DESPERATION_THRESHOLD or 
                             self.hunger >= DESPERATION_THRESHOLD)
        
        if not is_still_desperate:
            self.transition_to(WanderingState(self.animal))
            return
        
        # DESPERATE BEHAVIOR: Emergency response
        
        # Priority 1: Thirst (more critical than hunger)
        if self.animal.thirst >= DESPERATION_THRESHOLD:
            if self.animal.target_water:
                # Move frantically toward water
                target = self.animal.target_water
                self.animal.movement_strategy.seek_target(
                    self.animal, 
                    target.x, 
                    target.y,
                    speed_multiplier=2  # Move faster when desperate
                )
                # Update state to reflect seeking
                if self.animal.x == target.x and self.animal.y == target.y:
                    self.animal.state = "SEEKING_WATER"
            return
        
        # Priority 2: Hunger (for carnivores)
        from entities.animals import Carnivore
        if isinstance(self.animal, Carnivore):
            if self.animal.hunger >= DESPERATION_THRESHOLD:
                # Hunt aggressively
                self.transition_to(HuntingState(self.animal))
                return
        
        # If herbivore with hunger desperate, just move randomly fast
        self.animal.movement_strategy.move(self.animal, entities, speed_multiplier=2)
    
    def exit(self):
        """Log when recovering from desperate state"""
        print(f"✅ {self.animal.name} is no longer desperate!")