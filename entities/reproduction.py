"""
Reproduction System - Mating and offspring creation

This module handles animal reproduction in the savanna.
When two compatible animals are near each other and healthy,
they can produce offspring.

Classes:
- ReproductionManager: Manages mating attempts
- MatingState: Animals in the process of mating
- Offspring: New baby animal

Reproduction Rules:
- Must be same species
- Both must be healthy (hunger/thirst < threshold)
- Must be near each other
- Cooldown between offspring (prevents infinite population)
- Max offspring per parent pair

Usage:
    rep_mgr = ReproductionManager()
    rep_mgr.try_mate(animal1, animal2)
"""

from typing import Optional, List
import random


class ReproductionManager:
    """
    Manages reproduction attempts between animals.
    
    Tracks:
    - Who is seeking a mate
    - Cooldowns per animal
    - Successful matings
    
    Cooldown:
    - Animals need time between offspring
    - Prevents population explosion
    """
    
    def __init__(self):
        """Initialize reproduction manager"""
        self.seeking_mate: List = []  # Animals seeking mates
        self.cooldowns: dict = {}  # animal_id -> tick when available again
        self.cooldown_ticks = 100  # Ticks between offspring
    
    def register_seeking(self, animal):
        """Animal registers as seeking a mate"""
        if animal not in self.seeking_mate:
            self.seeking_mate.append(animal)
    
    def unregister_seeking(self, animal):
        """Animal stops seeking a mate"""
        if animal in self.seeking_mate:
            self.seeking_mate.remove(animal)
    
    def can_reproduce(self, animal) -> bool:
        """Check if animal can reproduce"""
        from utils.constants import HUNGER_THRESHOLD, THIRST_THRESHOLD
        
        # Check cooldown
        if animal.id in self.cooldowns:
            return False
        
        # Check health - must be well-fed and hydrated
        if animal.hunger >= HUNGER_THRESHOLD:
            return False
        if animal.thirst >= THIRST_THRESHOLD:
            return False
        
        return True
    
    def try_mate(self, animal1, animal2) -> Optional['Offspring']:
        """
        Attempt to mate two animals.
        
        Args:
            animal1: First animal
            animal2: Second animal
            
        Returns:
            Offspring if successful, None otherwise
        """
        # Must be same species
        if type(animal1) != type(animal2):
            return None
        
        # Both must want to reproduce
        if not self.can_reproduce(animal1) or not self.can_reproduce(animal2):
            return None
        
        # Must be close enough
        dist = abs(animal1.x - animal2.x) + abs(animal1.y - animal2.y)
        if dist > 2:
            return None
        
        # Success! Create offspring
        offspring = self._create_offspring(animal1, animal2)
        
        # Set cooldowns
        self.cooldowns[animal1.id] = self.cooldown_ticks
        self.cooldowns[animal2.id] = self.cooldown_ticks
        
        # Unregister from seeking
        self.unregister_seeking(animal1)
        self.unregister_seeking(animal2)
        
        return offspring
    
    def _create_offspring(self, parent1, parent2):
        """Create offspring from two parents"""
        # Create baby near parents
        new_id = max(parent1.id, parent2.id) + 100  # Unique ID
        
        # Same species as parents
        species = type(parent1).__name__
        
        # Find the class and create instance
        from entities.animals import (
            Zebra, Elephant, Lion, Leopard, 
            BushBaby, Ostrich, Cheetah
        )
        
        species_map = {
            'Zebra': Zebra,
            'Elephant': Elephant,
            'Lion': Lion,
            'Leopard': Leopard,
            'BushBaby': BushBaby,
            'Ostrich': Ostrich,
            'Cheetah': Cheetah,
        }
        
        animal_class = species_map.get(species)
        if animal_class:
            # Spawn near parents
            x = (parent1.x + parent2.x) // 2
            y = (parent1.y + parent2.y) // 2
            
            baby = animal_class(new_id, f"Baby{species}", x, y)
            return baby
        
        return None
    
    def tick_cooldowns(self):
        """Reduce cooldowns each tick"""
        to_remove = []
        for animal_id, ticks in self.cooldowns.items():
            self.cooldowns[animal_id] = ticks - 1
            if self.cooldowns[animal_id] <= 0:
                to_remove.append(animal_id)
        
        for animal_id in to_remove:
            del self.cooldowns[animal_id]


class Offspring:
    """
    Represents a new baby animal.
    
    Inherits traits from parents but starts small.
    """
    
    def __init__(self, parent_species, name, x, y):
        self.parent_species = parent_species
        self.name = name
        self.x = x
        self.y = y
    
    def __str__(self):
        return f"Offspring({self.parent_species})"