"""
Food Sources - Grass patches and food management for the savanna

This module provides food sources that herbivores can eat from.
Food sources:
- GrassPatch: Main food source, regrows over time
- BerryBush: Optional food with different nutrition

Classes:
- FoodType: Enum for different food types
- FoodSource: Base class for all food sources
- GrassPatch: Regrows grass for herbivores
- BerryBush: Berry food source
- FoodManager: Manages all food sources in simulation

Usage:
    from environment.food import GrassPatch, FoodManager
    
    # Create food sources
    grass = GrassPatch(x=5, y=5)
    
    # Animal eats
    if grass.consume(10):
        print("Yum! Got 10 food")
    
    # Grass regrows
    grass.regrow()
"""

from enum import Enum
from typing import List, Optional
import random


class FoodType(Enum):
    """
    Types of food available in the savanna.
    
    Each food type has different nutritional value and regrow rates.
    """
    GRASS = "grass"
    BERRIES = "berries"
    LEAVES = "leaves"
    ACACIA = "acacia"  # Trees (for giraffes)


class FoodSource:
    """
    Base class for all food sources.
    
    A food source is a location where animals can consume food.
    Food sources have:
    - Position (x, y)
    - Food type
    - Current quantity
    - Maximum capacity
    - Regrowth rate
    
    Attributes:
        id: Unique identifier
        x: X coordinate
        y: Y coordinate
        food_type: Type of food
        quantity: Current food amount
        max_quantity: Maximum food capacity
        regrow_rate: How fast food regrows per tick
    """
    
    _id_counter = 0
    
    def __init__(self, x: int, y: int, food_type: FoodType, 
                 max_quantity: int = 100, regrow_rate: int = 5):
        """
        Initialize a food source.
        
        Args:
            x: X coordinate
            y: Y coordinate
            food_type: Type of food
            max_quantity: Maximum food capacity
            regrow_rate: Ticks to fully regrow
        """
        FoodSource._id_counter += 1
        self.id = FoodSource._id_counter
        self.x = x
        self.y = y
        self.food_type = food_type
        self.quantity = max_quantity
        self.max_quantity = max_quantity
        self.regrow_rate = regrow_rate
        self.regrow_counter = 0
    
    def consume(self, amount: int = 10) -> bool:
        """
        Try to consume food from this source.
        
        Args:
            amount: Amount of food to consume
            
        Returns:
            True if successful, False if not enough food
        """
        if self.quantity >= amount:
            self.quantity -= amount
            return True
        return False
    
    def regrow(self):
        """
        Regrow food over time.
        
        Food regrows incrementally each tick. When enough
        accumulates, quantity increases.
        """
        if self.quantity < self.max_quantity:
            self.regrow_counter += 1
            if self.regrow_counter >= self.regrow_rate:
                # Time to regrow some food
                regrow_amount = max(1, self.max_quantity // 10)  # 10% of max
                self.quantity = min(self.max_quantity, self.quantity + regrow_amount)
                self.regrow_counter = 0
    
    @property
    def is_depleted(self) -> bool:
        """Check if food source is empty"""
        return self.quantity <= 0
    
    @property
    def fullness(self) -> float:
        """Get fullness as percentage 0-100"""
        return (self.quantity / self.max_quantity) * 100 if self.max_quantity > 0 else 0
    
    def __str__(self):
        return f"FoodSource({self.food_type.value} @({self.x},{self.y}) {self.fullness:.0f}%)"


class GrassPatch(FoodSource):
    """
    Grass patch - primary food source for herbivores.
    
    Grass is the main food for herbivores like zebras, elephants, etc.
    It regrows over time, creating a sustainable food source.
    
    Characteristics:
    - Regrows relatively fast (5 ticks)
    - Can support multiple animals
    - Depletes when overgrazed
    
    Nutritional Value:
    - Base nutrition: 10 hunger removed per consume
    """
    
    def __init__(self, x: int, y: int, max_quantity: int = 50):
        """
        Create a grass patch.
        
        Args:
            x: X coordinate
            y: Y coordinate
            max_quantity: How much grass the patch can hold
        """
        super().__init__(
            x=x, 
            y=y, 
            food_type=FoodType.GRASS,
            max_quantity=max_quantity,
            regrow_rate=5  # Regrows every 5 ticks
        )
        self.nutrition = 10  # Hunger removed per consume
    
    def graze(self, amount: int = 10) -> int:
        """
        Animals graze on the grass.
        
        Args:
            amount: How much grass to eat
            
        Returns:
            Actual amount consumed
        """
        consumed = min(amount, self.quantity)
        self.quantity -= consumed
        return consumed


class BerryBush(FoodSource):
    """
    Berry bush - supplementary food source.
    
    Berries provide additional nutrition but are less common
    than grass. They regrow slower but provide more nutrition.
    
    Characteristics:
    - Higher nutrition per berry
    - Slower regrowth
    - Smaller capacity
    """
    
    def __init__(self, x: int, y: int):
        super().__init__(
            x=x,
            y=y,
            food_type=FoodType.BERRIES,
            max_quantity=30,
            regrow_rate=10  # Slower than grass
        )
        self.nutrition = 15  # More nutrition than grass
    
    def harvest(self, amount: int = 5) -> int:
        """Harvest berries from bush"""
        consumed = min(amount, self.quantity)
        self.quantity -= consumed
        return consumed


class FoodManager:
    """
    Manager for all food sources in the simulation.
    
    The FoodManager maintains a list of all food sources and
    provides methods to:
    - Add food sources
    - Find nearest food for an entity
    - Tick all food sources (regrowth)
    - Log food statistics
    
    Usage:
        manager = FoodManager()
        manager.add_grass_patch(x=5, y=5)
        manager.add_grass_patch(x=10, y=10)
        
        # In simulation tick
        manager.regrow_all()
        
        # Find food for animal
        nearest = manager.find_nearest_food(animal_x, animal_y)
    """
    
    def __init__(self):
        """Initialize food manager with empty list of sources"""
        self.sources: List[FoodSource] = []
        self._source_id_counter = 0
    
    def add_source(self, source: FoodSource):
        """
        Add a food source to the manager.
        
        Args:
            source: FoodSource instance to add
        """
        self.sources.append(source)
    
    def add_grass_patch(self, x: int, y: int, max_quantity: int = 50) -> GrassPatch:
        """
        Add a grass patch at given location.
        
        Args:
            x: X coordinate
            y: Y coordinate
            max_quantity: Grass capacity
            
        Returns:
            Created GrassPatch instance
        """
        patch = GrassPatch(x, y, max_quantity)
        self.add_source(patch)
        return patch
    
    def add_berry_bush(self, x: int, y: int) -> BerryBush:
        """
        Add a berry bush at given location.
        
        Args:
            x: X coordinate
            y: Y coordinate
            
        Returns:
            Created BerryBush instance
        """
        bush = BerryBush(x, y)
        self.add_source(bush)
        return bush
    
    def add_random_grass(self, count: int, grid_width: int = 100, 
                        grid_height: int = 100, spread: int = 20):
        """
        Add multiple grass patches in random positions.
        
        Useful for setting up initial food distribution.
        
        Args:
            count: Number of grass patches to create
            grid_width: Maximum X coordinate
            grid_height: Maximum Y coordinate
            spread: How spread out patches are from center
        """
        # Distribute around center of map
        center_x = grid_width // 2
        center_y = grid_height // 2
        
        for _ in range(count):
            x = center_x + random.randint(-spread, spread)
            y = center_y + random.randint(-spread, spread)
            self.add_grass_patch(x, y)
    
    def find_nearest_food(self, x: int, y: int, 
                          food_type: Optional[FoodType] = None,
                          max_distance: int = 50) -> Optional[FoodSource]:
        """
        Find nearest non-depleted food source.
        
        Args:
            x: Entity X position
            y: Entity Y position
            food_type: Optional filter for food type
            max_distance: Maximum search distance
            
        Returns:
            Nearest FoodSource or None
        """
        nearest = None
        min_dist = max_distance + 1
        
        for source in self.sources:
            # Skip depleted sources
            if source.is_depleted:
                continue
            
            # Skip wrong food type if specified
            if food_type and source.food_type != food_type:
                continue
            
            # Calculate distance
            dist = abs(source.x - x) + abs(source.y - y)
            
            if dist < min_dist:
                min_dist = dist
                nearest = source
        
        return nearest
    
    def find_food_in_range(self, x: int, y: int, 
                          radius: int = 10) -> List[FoodSource]:
        """
        Find all food sources within a radius.
        
        Args:
            x: Center X position
            y: Center Y position
            radius: Search radius
            
        Returns:
            List of FoodSource in range (excluding depleted)
        """
        found = []
        for source in self.sources:
            if source.is_depleted:
                continue
            dist = abs(source.x - x) + abs(source.y - y)
            if dist <= radius:
                found.append(source)
        return found
    
    def regrow_all(self):
        """Regrow all food sources (call each tick)"""
        for source in self.sources:
            source.regrow()
    
    def get_food_stats(self) -> dict:
        """
        Get statistics about all food sources.
        
        Returns:
            Dict with food statistics
        """
        total = len(self.sources)
        depleted = sum(1 for s in self.sources if s.is_depleted)
        total_quantity = sum(s.quantity for s in self.sources)
        
        by_type = {}
        for source in self.sources:
            ft = source.food_type.value
            if ft not in by_type:
                by_type[ft] = {'count': 0, 'total_quantity': 0}
            by_type[ft]['count'] += 1
            by_type[ft]['total_quantity'] += source.quantity
        
        return {
            'total_sources': total,
            'depleted': depleted,
            'active': total - depleted,
            'total_quantity': total_quantity,
            'by_type': by_type
        }
    
    def __len__(self):
        return len(self.sources)
    
    def __iter__(self):
        return iter(self.sources)
    
    def __str__(self):
        stats = self.get_food_stats()
        return f"FoodManager({stats['active']}/{stats['total_sources']} active, {stats['total_quantity']} total)"