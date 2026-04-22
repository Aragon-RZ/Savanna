"""
Strategy Pattern Module - Swappable behavioral algorithms

This module implements the STRATEGY PATTERN where behaviors are 
encapsulated in separate classes that can be swapped at runtime.

The Strategy Pattern allows:
- Different movement algorithms for different animal types
- Swapping behaviors without changing the entity
- Adding new behaviors without modifying existing code

Structure:
- base.py: Abstract base classes for strategies
- movement/: Different movement algorithms
  - random_walk.py: Random wandering
  - herd_follow.py: Following the herd
  - seek_target.py: Moving toward a specific target
  - flee.py: Running away from threats
- hunting/: Hunting algorithms for carnivores
  - simple_chase.py: Direct chase
  - ambush.py: Strategic ambush

Usage:
    animal.movement_strategy = RandomWalkStrategy()
    animal.movement_strategy.move(animal, entities)
"""

from abc import ABC, abstractmethod

# Export base classes for easy importing
from .movement.random_walk import RandomWalkStrategy
from .movement.herd_follow import HerdFollowStrategy
from .movement.seek_target import SeekTargetStrategy
from .movement.flee import FleeStrategy
from .hunting.simple_chase import SimpleChaseStrategy


# Default strategy mappings
DEFAULT_MOVEMENT = RandomWalkStrategy
DEFAULT_HUNTING = SimpleChaseStrategy