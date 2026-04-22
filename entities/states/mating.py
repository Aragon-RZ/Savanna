"""
Mating State - Animals reproducing

When two compatible animals are near each other and healthy,
they enter this state to mate and produce offspring.

State Transitions:
- WANDERING → MATING (mate found nearby)
- MATING → WANDERING (mating complete)
"""

from .base import AnimalState


class MatingState(AnimalState):
    """
    The MATING state represents two animals reproducing.
    
    When animals mate:
    1. They stay near each other for a few ticks
    2. Offspring is created
    3. Both go on cooldown
    4. Return to wandering
    """
    
    def __init__(self, animal, partner):
        super().__init__(animal)
        self.partner = partner  # The mate
    
    def enter(self):
        """Log when starting to mate"""
        # Set directly on _state instead of using property setter
        self.animal._state = self
        print(f"💕 {self.animal.name} is mating with {self.partner.name}")
    
    def update(self, current_hour: int, entities: list):
        """
        Attempt to mate.
        
        In this simplified version, mating happens instantly.
        In a more complex version, would take multiple ticks.
        """
        from .wandering import WanderingState
        
        # Simple: immediate mating
        # Try to create offspring via reproduction manager
        rep_mgr = getattr(self.animal, 'reproduction_manager', None)
        
        if rep_mgr:
            baby = rep_mgr.try_mate(self.animal, self.partner)
            
            if baby:
                print(f"💕 New baby {baby.name} born!")
                
                # Add baby to simulation
                sim = getattr(self.animal, 'simulation', None)
                if sim:
                    sim.add_entity(baby)
                    
                    # Log birth to database
                    try:
                        from engine.database_utils import DatabaseRecorder
                        current_tick = getattr(self.animal, 'current_tick', 0)
                        DatabaseRecorder.record_birth(
                            entity_id=baby.id,
                            parent_ids=[self.animal.id, self.partner.id],
                            species=type(baby).__name__,
                            tick=current_tick
                        )
                        # Also log event
                        from engine.database import DatabaseManager
                        DatabaseManager.log_event(
                            tick=current_tick,
                            entity_id=baby.id,
                            event_type="ENTITY_BORN",
                            details=f"parents={self.animal.id},{self.partner.id}"
                        )
                    except Exception as e:
                        pass  # Silently fail if database logging not available
        
        # Return to wandering
        self.transition_to(WanderingState(self.animal))
    
    def exit(self):
        """Clean up after mating"""
        pass