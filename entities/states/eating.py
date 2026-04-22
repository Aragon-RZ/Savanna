"""
Eating State - Herbivore consuming food

When an herbivore reaches a food source (GrassPatch), it enters
this state to consume food and reduce hunger.

State Transitions:
- WANDERING → EATING (at food source with food available)
- EATING → WANDERING (finished eating or food depleted)

Behavior:
- Consume food from the food source each tick
- Reduce hunger level
- Stay at food source until hunger is low
- Leave if food is depleted
"""

from .base import AnimalState


class EatingState(AnimalState):
    """
    The EATING state represents an animal consuming food.
    
    When an animal reaches a food source and is hungry,
    they enter this state and eat until:
    1. Hunger is reduced to 0 (or low threshold)
    2. Food source is depleted
    3. Interrupted by predator (transition to FLEEING)
    """
    
    def enter(self):
        """Log when starting to eat"""
        self.animal.state = "EATING"
        if self.animal.target_food:
            print(f"🌿 {self.animal.name} started eating at food source @({self.animal.target_food.x}, {self.animal.target_food.y})")
    
    def update(self, current_hour: int, entities: list):
        """
        Eat food from the food source.
        
        Each tick:
        1. Check if food is still available
        2. Consume food (reduce food source quantity)
        3. Reduce animal hunger
        4. If full or food depleted, return to wandering
        """
        from .wandering import WanderingState
        from utils.constants import HUNGER_THRESHOLD
        
        # Check if we still have food source
        if not self.animal.target_food:
            self.transition_to(WanderingState(self.animal))
            return
        
        food_source = self.animal.target_food
        
        # Check if food source depleted
        if food_source.is_depleted:
            print(f"❌ {self.animal.name} - food source depleted!")
            self.animal.target_food = None
            self.transition_to(WanderingState(self.animal))
            return
        
        # Consume food
        consume_amount = 10
        consumed = food_source.consume(consume_amount)
        
        if consumed:
            # Reduce hunger
            self.animal.hunger = max(0, self.animal.hunger - consumed)
            print(f"🌿 {self.animal.name} ate grass ({consumed} units), hunger now {self.animal.hunger}")
            
            # Log to database
            try:
                from engine.database import DatabaseManager
                DatabaseManager.log_event(
                    tick=getattr(self.animal, 'current_tick', 0),
                    entity_id=self.animal.id,
                    event_type="ENTITY_ATE",
                    details=f"consumed={consumed}"
                )
            except ImportError:
                pass
        else:
            # Couldn't consume (depleted during eat)
            print(f"❌ {self.animal.name} - couldn't eat!")
        
        # Check if hunger is satisfied (below threshold)
        if self.animal.hunger < HUNGER_THRESHOLD:
            print(f"✅ {self.animal.name} finished eating!")
            self.animal.target_food = None
            self.transition_to(WanderingState(self.animal))
            return
        
        # Still hungry, stay at food source
        # (Animal stays in EATING state for next tick)
    
    def exit(self):
        """Clean up when leaving eating state"""
        # Could trigger additional behavior here
        pass