"""
State Pattern Module - Manages animal behavioral states

This module implements the STATE PATTERN where each state is represented
as a separate class. This replaces string-based state management with
object-oriented state objects.

Structure:
- base.py: Abstract base class for all states
- idle.py: IDLE state (no specific action)
- sleeping.py: SLEEPING state (diurnal/nocturnal driven)
- wandering.py: WANDERING state (exploring)
- seeking_water.py: SEEKING_WATER state (looking for water)
- drinking.py: DRINKING state (at watering hole)
- eating.py: EATING state (consuming food)
- fleeing.py: FLEEING state (escaping predator)
- hunting.py: HUNTING state (carnivores hunting prey)
- desperate.py: DESPERATE state (critical hunger/thirst)

Usage:
    from entities.states import WanderingState
    
    animal.set_state(WanderingState(animal))
    animal.update()  # State automatically calls its own update()
"""

from .idle import IdleState
from .sleeping import SleepingState
from .wandering import WanderingState
from .seeking_water import SeekingWaterState
from .drinking import DrinkingState
from .eating import EatingState
from .fleeing import FleeingState
from .hunting import HuntingState
from .desperate import DesperateState
# Note: MatingState requires a partner, so not in STATE_MAP (use direct instantiation)

# Mapping from state names to state classes for backward compatibility
STATE_MAP = {
    "IDLE": IdleState,
    "SLEEPING": SleepingState,
    "WANDERING": WanderingState,
    "SEEKING_WATER": SeekingWaterState,
    "DRINKING": DrinkingState,
    "EATING": EatingState,
    "FLEEING": FleeingState,
    "HUNTING": HuntingState,
    "DESPERATE": DesperateState,
    "MATING": None,  # Requires partner, use direct instantiation
    "WAITING_IN_LINE": SeekingWaterState,  # Reuse SeekingWater for waiting
}


def get_state_by_name(state_name: str, animal):
    """
    Factory function to create a state object from a string name.
    
    Args:
        state_name: String name of the state (e.g., "WANDERING")
        animal: The animal entity that owns this state
        
    Returns:
        An instance of the corresponding State class
    """
    state_class = STATE_MAP.get(state_name.upper(), IdleState)
    return state_class(animal)
