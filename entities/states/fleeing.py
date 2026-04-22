"""
Fleeing State - Animal is escaping from a predator

This state handles the fleeing behavior of prey animals.
The animal moves in the opposite direction of the threat.
"""

from .base import AnimalState


class FleeingState(AnimalState):
    """
    The FLEEING state represents a prey animal escaping a predator.
    
    When a prey animal spots a predator within danger range,
    they enter this state and flee in the opposite direction.
    
    The fleeing continues until:
    1. Predator is out of range (escaped)
    2. Predator catches the animal (death)
    """
    
    def enter(self):
        """Log when starting to flee"""
        self.animal.state = "FLEEING"
        print(f"💨 {self.animal.name} spotted a predator and is FLEEING!")
    
    def update(self, current_hour: int, entities: list):
        """
        Flee from nearest predator.
        
        Uses flee strategy to move in opposite direction of threat.
        If predator is far enough away, return to wandering.
        """
        from utils.colors import Colors
        from .wandering import WanderingState
        
        # Find nearby predators - check for carnivores by attribute
        # Carnivores have hunting_strategy attribute
        predators = [e for e in entities 
                    if e.is_alive
                    and hasattr(e, 'hunting_strategy')]  # Has hunting = is carnivore
        
        closest_predator = None
        closest_dist = 999
        
        for p in predators:
            dist = abs(self.animal.x - p.x) + abs(self.animal.y - p.y)
            if dist <= 6:  # Still in danger zone
                if dist < closest_dist:
                    closest_dist = dist
                    closest_predator = p
        
        # If no predator nearby, we've escaped
        if not closest_predator or closest_dist > 6:
            if closest_predator:  # Was being chased, now escaped
                print(f"🏃 {self.animal.name} has escaped the danger!")
                # OBSERVER PATTERN: Emit entity fled event
                try:
                    from engine.events import EventManager, EventType
                    EventManager.emit(EventType.ENTITY_FLED, {
                        'entity': self.animal,
                        'predator': closest_predator.name
                    })
                except ImportError:
                    pass
            self.transition_to(WanderingState(self.animal))
            return
        else:
            # Just spotted a predator
            try:
                from engine.events import EventManager, EventType
                EventManager.emit(EventType.PREDATOR_SPOTTED, {
                    'entity': self.animal,
                    'predator': closest_predator.name
                })
            except ImportError:
                pass
        
        # Flee using strategy - moves in opposite direction of predator
        self.animal.movement_strategy.flee(self.animal, closest_predator)
    
    def exit(self):
        """Nothing special to clean up"""
        pass