"""
Base Strategy Classes - Foundation of the Strategy Pattern

This module defines the abstract base classes that all concrete
strategies must implement.

Strategy Pattern Key Concepts:
1. Each strategy is a separate class with a common interface
2. Entities hold a reference to strategy objects
3. Strategies are interchangeable at runtime
4. Strategies encapsulate specific algorithms
"""

from abc import ABC, abstractmethod


class MovementStrategy(ABC):
    """
    Abstract base class for all movement behaviors.
    
    The Strategy Pattern allows different movement algorithms to be
    swapped without changing the entity using them.
    
    All movement strategies must implement:
    - move(): Execute one step of movement
    - can_execute(): Check if this strategy can be used
    
    Optional methods for specialized movement:
    - seek_target(): Move toward specific coordinates
    - flee(): Move away from a threat
    """
    
    @abstractmethod
    def move(self, animal, entities: list, speed_multiplier: int = 1):
        """
        Execute one step of movement.
        
        Args:
            animal: The animal entity to move
            entities: List of all entities (for context)
            speed_multiplier: Speed multiplier (default 1)
        """
        pass
    
    @abstractmethod
    def can_execute(self, animal, entities: list) -> bool:
        """
        Check if this strategy can/should be executed.
        
        Args:
            animal: The animal entity
            entities: List of all entities
            
        Returns:
            True if this strategy is applicable in current context
        """
        pass
    
    def seek_target(self, animal, target_x: int, target_y: int, 
                   speed_multiplier: int = 1):
        """
        Move toward a specific target position.
        
        Default implementation: Simple step toward target.
        Override for specialized seeking behavior.
        
        Args:
            animal: The animal entity to move
            target_x: Target X coordinate
            target_y: Target Y coordinate
            speed_multiplier: Speed multiplier
        """
        # Move one step toward target in each axis
        steps = speed_multiplier
        
        for _ in range(steps):
            if animal.x < target_x:
                animal.x += 1
            elif animal.x > target_x:
                animal.x -= 1
            
            if animal.y < target_y:
                animal.y += 1
            elif animal.y > target_y:
                animal.y -= 1
            
            # Stop if reached target
            if animal.x == target_x and animal.y == target_y:
                break
    
    def flee(self, animal, threat, speed_multiplier: int = 1):
        """
        Move in opposite direction of a threat.
        
        Default implementation: Move away from threat position.
        Override for specialized fleeing behavior.
        
        Args:
            animal: The animal entity to move
            threat: The threat entity to flee from
            speed_multiplier: Speed multiplier
        """
        steps = speed_multiplier
        
        for _ in range(steps):
            # Move in opposite direction of threat
            if animal.x < threat.x:
                animal.x -= 1
            elif animal.x > threat.x:
                animal.x += 1
            
            if animal.y < threat.y:
                animal.y -= 1
            elif animal.y > threat.y:
                animal.y += 1


class HuntingStrategy(ABC):
    """
    Abstract base class for hunting behaviors.
    
    Carnivores use different hunting strategies. This allows
    for varied predator behavior without complex if/else logic.
    
    All hunting strategies must implement:
    - select_target(): Choose which prey to pursue
    - hunt(): Execute the hunt (move toward prey)
    """
    
    @abstractmethod
    def select_target(self, predator, prey_list: list):
        """
        Select the best prey to hunt from available targets.
        
        Args:
            predator: The carnivore doing the hunting
            prey_list: List of potential prey entities
            
        Returns:
            The chosen prey entity, or None if no suitable target
        """
        pass
    
    @abstractmethod
    def hunt(self, predator, prey):
        """
        Execute the hunt - move toward the selected prey.
        
        Args:
            predator: The carnivore doing the hunting
            prey: The prey entity being targeted
        """
        pass