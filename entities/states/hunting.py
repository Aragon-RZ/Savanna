"""
Hunting State - Carnivore is hunting prey

This state handles the hunting behavior of predator animals.
The carnivore tracks and pursues prey to satisfy hunger.
"""

from .base import AnimalState


class HuntingState(AnimalState):
    """
    The HUNTING state represents a carnivore pursuing prey.
    
    When a carnivore's hunger reaches the threshold, they enter
    this state and actively hunt for prey animals.
    
    Hunting behavior:
    1. Scan for nearby prey
    2. Move toward prey using hunting strategy
    3. Catch and kill prey when in same location
    4. Reset hunger to 0 after feeding
    """
    
    def enter(self):
        """Log when starting to hunt"""
        self.animal.state = "HUNTING"
    
    def update(self, current_hour: int, entities: list):
        """
        Hunt for prey.
        
        Finds nearest prey and chases it using hunting strategy.
        If prey caught (same location), kills and feeds.
        """
        from utils.constants import HUNGER_THRESHOLD
        
        # Check survival
        if not self._check_survival():
            return
        
        # If hunger is below threshold, stop hunting
        if self.animal.hunger < HUNGER_THRESHOLD:
            from .wandering import WanderingState
            self.transition_to(WanderingState(self.animal))
            return
        
        # Find prey (Herbivores and Insectivores)
        # Use class name checking to avoid circular import
        prey_list = [e for e in entities 
                    if e.is_alive 
                    and hasattr(e, 'thirst')  # Has thirst = is animal
                    and not hasattr(e, 'target_water')]  # Carnivores don't have target_water
        
        # More specific check: herbivores have hunger but it's always 0 (grass is everywhere)
        # and they have is_herd_animal attribute
        prey_list = [e for e in entities 
                    if e.is_alive
                    and getattr(e, 'is_herd_animal', False)]  # Herbivores are herd animals
        
        if not prey_list:
            # No prey found - wander randomly
            self.animal.movement_strategy.move(self.animal, entities)
            return
        
        # Find nearest prey using hunting strategy
        target = self.animal.hunting_strategy.select_target(
            self.animal, 
            prey_list
        )
        
        if target:
            # Move toward prey using hunting strategy
            self.animal.hunting_strategy.hunt(self.animal, target)
            
            # Check if caught (same location)
            if (self.animal.x == target.x and 
                self.animal.y == target.y):
                # Kill the prey!
                prey_name = target.name
                target.die(f"Hunted by {self.animal.name}")
                self.animal.hunger = 0
                print(f"🥩 {self.animal.name} feasted on {prey_name}!")
                
                # OBSERVER PATTERN: Emit entity ate event
                try:
                    from engine.events import EventManager, EventType
                    EventManager.emit(EventType.ENTITY_ATE, {
                        'entity': self.animal,
                        'prey': prey_name
                    })
                except ImportError:
                    pass
                
                # Return to wandering
                from .wandering import WanderingState
                self.transition_to(WanderingState(self.animal))
    
    def exit(self):
        """Nothing special to clean up"""
        pass