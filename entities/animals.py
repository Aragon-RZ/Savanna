"""
Animal Classes - Fauna of the Savanna

This module contains all animal types in the simulation.

Design Patterns Used:
1. STATE PATTERN: Each animal delegates behavior to a State object
   - States encapsulate behavioral logic
   - Animals transition between states
   - States handle entry/exit actions
   
2. STRATEGY PATTERN: Movement and hunting use strategy objects
   - movement_strategy: How the animal moves
   - hunting_strategy: How carnivores hunt (only for carnivores)

State Transitions:
    IDLE → WANDERING (initial update)
    WANDERING → SLEEPING (inactive hours)
    WANDERING → SEEKING_WATER (thirst threshold)
    SEEKING_WATER → DRINKING (at water source)
    DRINKING → WANDERING (finished drinking)
    WANDERING → FLEEING (predator spotted)
    FLEEING → WANDERING (escaped)
    WANDERING → HUNTING (carnivore hungry)
    HUNTING → WANDERING (caught prey or gave up)
    ANY → DESPERATE (critical survival)
    DESPERATE → WANDERING (recovered)

Strategy Selection:
    Herbivores: RandomWalkStrategy (default), HerdFollowStrategy (herd animals)
    Carnivores: +HuntingStrategy (SimpleChaseStrategy)
"""

from entities.base import Entity
from utils.constants import (
    THIRST_THRESHOLD, MAX_THIRST, SUNRISE_HOUR, SUNSET_HOUR, 
    MAX_HUNGER, HUNGER_THRESHOLD, DESPERATION_THRESHOLD
)
from utils.colors import Colors
from entities.behaviors.movement.random_walk import RandomWalkStrategy
from entities.behaviors.movement.herd_follow import HerdFollowStrategy
from entities.behaviors.hunting.simple_chase import SimpleChaseStrategy


class Animal(Entity):
    """
    Base class for all animals.
    
    Animals extend Entity with survival needs (thirst, hunger)
    and behavioral properties (is_diurnal, is_herd_animal).
    
    State Pattern Integration:
        - Animals use State objects for all behavior
        - The update() method delegates to current state
        - States handle entry/exit actions
        
    Strategy Pattern Integration:
        - movement_strategy: How the animal moves (default: RandomWalk)
        - hunting_strategy: How carnivores hunt (default: SimpleChase)
        
    Observer Pattern Integration:
        - die() in Entity base class emits ENTITY_DIED event
        - State transitions emit STATE_CHANGED events
    """
    
    def __init__(self, entity_id, name, x, y, is_diurnal=True):
        """
        Initialize an animal.
        
        Args:
            entity_id: Unique identifier
            name: Display name
            x: Starting X position
            y: Starting Y position
            is_diurnal: True for day-active, False for night-active
        """
        super().__init__(entity_id, name, x, y)
        
        # Survival needs
        self.thirst = 0
        self.hunger = 0
        self.target_water = None
        
        # Behavioral properties
        self.is_diurnal = is_diurnal
        
        # STRATEGY PATTERN: Initialize with default strategies
        # These can be changed at runtime for different behaviors
        self.movement_strategy = RandomWalkStrategy()
        self.hunting_strategy = SimpleChaseStrategy()
        
        # OBSERVER PATTERN: Emit birth event
        try:
            from engine.events import EventManager, EventType
            EventManager.emit(EventType.ENTITY_BORN, {
                'entity': self
            })
        except ImportError:
            pass
    
    def update(self, current_hour, entities):
        """
        Update the animal for one simulation tick.
        
        The STATE PATTERN in action:
        1. Check if alive (dead animals don't update)
        2. Increment survival needs
        3. Check for death conditions
        4. Delegate remaining behavior to current state
        
        Args:
            current_hour: Current time in simulation (0-23)
            entities: List of all entities (for interactions)
        """
        if not self.is_alive:
            return
        
        # Increment survival needs
        self.thirst += 2
        # Use class-specific hunger rate if available, else default
        self.hunger += getattr(self, 'hunger_rate', 1)
        
        # Check survival (death from thirst/hunger)
        if self.thirst >= MAX_THIRST:
            self.die("Extreme Thirst")
            return
        if self.hunger >= MAX_HUNGER:
            self.die("Starvation")
            return
        
        # STATE PATTERN: Delegate all behavior to current state
        # The state object handles:
        # - What to do this tick
        # - When to transition to a new state
        super().update(current_hour, entities)
    
    # STRATEGY PATTERN: Helper methods for strategies
    
    def set_movement_strategy(self, strategy):
        """
        Change the animal's movement strategy at runtime.
        
        Usage:
            from entities.behaviors import HerdFollowStrategy
            animal.set_movement_strategy(HerdFollowStrategy())
            
        Args:
            strategy: A MovementStrategy instance
        """
        self.movement_strategy = strategy
    
    def set_hunting_strategy(self, strategy):
        """
        Change the animal's hunting strategy at runtime.
        
        Only applies to carnivores.
        
        Args:
            strategy: A HuntingStrategy instance
        """
        self.hunting_strategy = strategy
    
    def herd(self, herd_animal: bool):
        """
        Enable or disable herd following behavior.
        
        Args:
            herd_animal: True to follow herd, False for solo wandering
        """
        if herd_animal:
            self.movement_strategy = HerdFollowStrategy()
        else:
            self.movement_strategy = RandomWalkStrategy()


class Herbivore(Animal):
    """
    Herbivore base class - animals that eat plants.
    
    Herbivores have the following behavior:
    1. Check for predators (flee if spotted)
    2. Check thirst (seek water if needed)
    3. Check hunger (seek food if hungry)
    4. Follow herd or wander randomly
    
    Food System:
    - Herbivores now actually get hungry and seek food
    - They find GrassPatch via food_manager
    - Can only eat when at food source location
    """
    
    def __init__(self, entity_id, name, x, y, is_diurnal=True, is_herd_animal=True):
        """
        Initialize a herbivore.
        
        Args:
            is_herd_animal: True if this species moves in herds
        """
        super().__init__(entity_id, name, x, y, is_diurnal)
        self.is_herd_animal = is_herd_animal
        self.target_food = None  # Current food source
        self.food_manager = None  # Reference to food manager
        
        # Set default movement strategy based on herd behavior
        if is_herd_animal:
            self.movement_strategy = HerdFollowStrategy()
        else:
            self.movement_strategy = RandomWalkStrategy()
    
    def set_food_manager(self, food_manager):
        """
        Set the food manager for this herbivore.
        
        Called by simulation when setting up the environment.
        
        Args:
            food_manager: FoodManager instance
        """
        self.food_manager = food_manager
    
    def _seek_food(self, entities):
        """
        Find and move toward food source.
        
        Called when herbivore is hungry and needs to eat.
        Looks for nearest GrassPatch with food available.
        """
        if not self.food_manager:
            return False
        
        # If already have target, just move toward it
        if self.target_food:
            if self.target_food.is_depleted:
                # Food source depleted, find new one
                self.target_food = None
            else:
                # Move toward food
                self.movement_strategy.seek_target(
                    self, 
                    self.target_food.x, 
                    self.target_food.y
                )
                # Check if at food source
                if self.x == self.target_food.x and self.y == self.target_food.y:
                    from entities.states import EatingState
                    self.set_state(EatingState(self))
                return True
        
        # Find new food source
        nearest = self.food_manager.find_nearest_food(
            self.x, 
            self.y,
            max_distance=30
        )
        
        if nearest:
            self.target_food = nearest
            # Move toward it
            self.movement_strategy.seek_target(
                self, 
                nearest.x, 
                nearest.y
            )
            # Check if already at food
            if self.x == nearest.x and self.y == nearest.y:
                from entities.states import EatingState
                self.set_state(EatingState(self))
            return True
        
        return False
    
    def update(self, current_hour, entities):
        """
        Update herbivore behavior.
        
        Herbivore-specific logic:
        1. Hunger increases over time (needs food)
        2. Check for predators first (survival priority)
        3. Check hunger and seek food if needed
        4. Let state handle rest of behavior
        """
        if not self.is_alive:
            return
        
        # NOTE: Herbivores now get hungry!
        # Previously: self.hunger = 0 (grass everywhere)
        # Now: Hunger increases naturally in parent.update()
        # Use higher rate to trigger eating behavior more often
        self.hunger_rate = 3  # Herbivores get hungry faster
        
        # Check for desperate predator avoidance
        if self.thirst >= DESPERATION_THRESHOLD:
            from entities.states import DesperateState
            self.set_state(DesperateState(self))
        
        # Delegate to parent (which delegates to state)
        super().update(current_hour, entities)


class Insectivore(Herbivore):
    """
    Insectivore base class - animals that eat insects.
    
    Currently behaves exactly like a herbivore.
    In a more complex simulation, would eat bugs instead of grass.
    """
    pass


class Carnivore(Animal):
    """
    Carnivore base class - animals that eat other animals.
    
    Carnivores have the following behavior:
    1. Prioritize water if thirsty
    2. Hunt if hungry
    3. Wander if not hungry or no prey available
    """
    
    def update(self, current_hour, entities):
        """
        Update carnivore behavior.
        
        Carnivore-specific logic:
        1. If hungry, hunt for prey
        2. If caught prey, feed (reset hunger)
        3. Otherwise, normal animal behavior
        """
        if not self.is_alive:
            return
        
        # Let parent handle base update (which handles state pattern)
        super().update(current_hour, entities)


# ==========================================
# SPECIFIC ANIMAL TYPES
# ==========================================
# Each specific animal inherits from the appropriate base class.
# They can override __init__ to set specific properties.
#
# Diurnal Herbivores (active during day, sleep at night)
class Zebra(Herbivore): pass
class Elephant(Herbivore): pass
class Giraffe(Herbivore): pass
class Buffalo(Herbivore): pass
class Rhino(Herbivore): pass
class Antelope(Herbivore): pass
class Ostrich(Herbivore): pass

# Diurnal Insectivores
class Meerkat(Insectivore): pass

# Diurnal Carnivores (active during day, sleep at night)
class Lion(Carnivore): pass
class Cheetah(Carnivore): pass

# Nocturnal Animals (active during night, sleep during day)
class Leopard(Carnivore):
    def __init__(self, entity_id, name, x, y):
        super().__init__(entity_id, name, x, y, is_diurnal=False)

class BushBaby(Insectivore):
    def __init__(self, entity_id, name, x, y):
        super().__init__(entity_id, name, x, y, is_diurnal=False)

class Pangolin(Insectivore):
    def __init__(self, entity_id, name, x, y):
        super().__init__(entity_id, name, x, y, is_diurnal=False)