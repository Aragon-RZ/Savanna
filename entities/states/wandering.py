"""
Wandering State - Animal explores the savanna

The wandering state is the default active state for animals.
They move around looking for resources (water, food) and companions.
"""

from .base import AnimalState
from utils.constants import THIRST_THRESHOLD, DESPERATION_THRESHOLD


class WanderingState(AnimalState):
    """
    The WANDERING state represents an animal exploring the savanna.
    
    This is the main "living" state where animals:
    - Move around using their movement strategy
    - Look for water when thirsty
    - Join herds (for herd animals)
    - React to predators
    
    The actual movement logic is DELEGATED to a Strategy object,
    allowing different movement algorithms without changing this state.
    """
    
    def enter(self):
        """Set state name when starting to wander"""
        self.animal.state = "WANDERING"
    
    def update(self, current_hour: int, entities: list):
        """
        Main wandering behavior - delegates to strategy and checks needs.
        
        Decision hierarchy:
        1. Check survival (death from thirst/hunger)
        2. If desperate, transition to DESPERATE
        3. If thirsty, seek water
        4. If hungry (herbivore), seek food
        5. Otherwise, use movement strategy to wander
        """
        # Check survival first
        if not self._check_survival():
            return
        
        # Check desperation threshold
        if (self.animal.thirst >= DESPERATION_THRESHOLD or 
            self.animal.hunger >= DESPERATION_THRESHOLD):
            from .desperate import DesperateState
            self.transition_to(DesperateState(self.animal))
            return
        
        # Check thirst - seek water if threshold reached
        if self.animal.thirst >= THIRST_THRESHOLD and self.animal.target_water:
            from .seeking_water import SeekingWaterState
            self.transition_to(SeekingWaterState(self.animal))
            return
        
        # NEW: Check hunger for herbivores - seek food if hungry
        from utils.constants import HUNGER_THRESHOLD
        if self.animal.hunger >= HUNGER_THRESHOLD:
            # Check if this is a herbivore (has target_food attribute)
            if hasattr(self.animal, 'target_food') and hasattr(self.animal, 'food_manager'):
                # Try to find and seek food
                if self.animal._seek_food(entities):
                    # Successfully found food, state changed to EATING
                    return
        
        # NEW: Reproduction attempt - check if ready to mate
        # Must have reproduction_manager and be healthy
        if hasattr(self.animal, 'reproduction_manager'):
            rep_mgr = self.animal.reproduction_manager
            if rep_mgr and rep_mgr.can_reproduce(self.animal):
                # Look for a mate nearby
                from entities.animals import Herbivore, Carnivore
                for other in entities:
                    if other == self.animal:
                        continue
                    if not other.is_alive:
                        continue
                    if type(other) != type(self.animal):
                        continue
                    if rep_mgr.can_reproduce(other):
                        # Check distance
                        dist = abs(self.animal.x - other.x) + abs(self.animal.y - other.y)
                        if dist <= 2:
                            # Found a mate! Transition to mating
                            from .mating import MatingState
                            self.transition_to(MatingState(self.animal, other))
                            return
        
        # Delegate actual movement to the animal's movement strategy
        # This is where STRATEGY PATTERN is used - different animals
        # can have different movement algorithms (random, herd, etc.)
        self.animal.movement_strategy.move(self.animal, entities)
    
    def exit(self):
        """Nothing special to clean up"""
        pass