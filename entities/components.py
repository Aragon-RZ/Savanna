"""
Decorator Pattern Module - Adding modifiers to entities dynamically

This module implements the DECORATOR PATTERN which allows adding
behavioral modifiers to entities at runtime without changing
their class hierarchy.

Decorator Pattern Key Concepts:
- Component: The base interface (Entity) that can be decorated
- Concrete Component: The actual entity (Animal)
- Decorator: Base class that wraps a component
- Concrete Decorator: Specific modifiers (SpeedBoost, Injured, etc.)

Available Decorators:
- SpeedBoost: Increases movement speed
- Injured: Reduces speed and other abilities
- Buff: General stat enhancement
- StaminaBoost: Extends time before fatigue
- ScentCovered: Reduces predator detection range

Usage:
    # Wrap an animal with a decorator
    from entities.components import SpeedBoost, InjuredDecorator
    
    fast_zebra = SpeedBoost(zebra)
    injured_lion = InjuredDecorator(lion)
    
    # Use the decorated animal normally
    fast_zebra.move()  # Moves faster
    
    # Decorators can stack
    turbo_zebra = SpeedBoost(InjuredDecorator(zebra))  # Fast but injured
"""

from abc import ABC, abstractmethod


class EntityComponent(ABC):
    """
    Abstract base class for entity decorators.
    
    This defines the interface that all decorators must implement.
    Decorators wrap an Entity and modify its behavior.
    
    The Decorator Pattern:
        Component (Entity)
            ↓
        ConcreteComponent (Animal)
            ↓
        Decorator (EntityDecorator)
            ↓
        ConcreteDecorator (SpeedBoost, Injured, etc.)
    
    Attributes:
        wrapped: The entity being decorated
    """
    
    @abstractmethod
    def __init__(self, wrapped):
        """
        Initialize the decorator with an entity to wrap.
        
        Args:
            wrapped: The Entity to wrap
        """
        self.wrapped = wrapped
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Get the decorated name"""
        pass
    
    @property
    @abstractmethod
    def x(self) -> int:
        """Get X position"""
        pass
    
    @x.setter
    @abstractmethod
    def x(self, value: int):
        """Set X position"""
        pass
    
    @property
    @abstractmethod
    def y(self) -> int:
        """Get Y position"""
        pass
    
    @y.setter
    @abstractmethod
    def y(self, value: int):
        """Set Y position"""
        pass
    
    @abstractmethod
    def move(self, entities: list = None, speed_multiplier: int = 1):
        """
        Execute movement with the decorator applied.
        
        Args:
            entities: List of all entities
            speed_multiplier: Base speed multiplier
        """
        pass


class SpeedBoostDecorator(EntityComponent):
    """
    Decorator that increases movement speed.
    
    This decorator wraps an animal and doubles its movement
    speed, allowing it to move multiple steps per tick.
    
    Use cases:
    - Fast prey escaping predators
    - predators in chase mode
    - Animals under adrenaline
    """
    
    def __init__(self, wrapped, multiplier: float = 2.0):
        """
        Initialize the speed boost decorator.
        
        Args:
            wrapped: The Entity to wrap
            multiplier: Speed multiplier (default 2.0)
        """
        super().__init__(wrapped)
        self._multiplier = multiplier
    
    @property
    def name(self) -> str:
        return f"[FAST] {self.wrapped.name}"
    
    @property
    def x(self) -> int:
        return self.wrapped.x
    
    @x.setter
    def x(self, value: int):
        self.wrapped.x = value
    
    @property
    def y(self) -> int:
        return self.wrapped.y
    
    @y.setter
    def y(self, value: int):
        self.wrapped.y = value
    
    def move(self, entities: list = None, speed_multiplier: int = 1):
        """Move with increased speed"""
        actual_multiplier = int(speed_multiplier * self._multiplier)
        self.wrapped.movement_strategy.move(self.wrapped, entities or [], actual_multiplier)
    
    def get_speed(self) -> float:
        """Get the current speed multiplier"""
        return self._multiplier


class InjuredDecorator(EntityComponent):
    """
    Decorator that represents an injured animal.
    
    Injured animals have reduced speed and visibility range.
    This decorator simulates injury effects.
    
    Effects:
    - Movement speed reduced by 50%
    - Herd detection range reduced
    - Predator awareness reduced
    """
    
    def __init__(self, wrapped, severity: float = 0.5):
        """
        Initialize the injured decorator.
        
        Args:
            wrapped: The Entity to wrap
            severity: Speed multiplier (0.0-1.0, default 0.5)
        """
        super().__init__(wrapped)
        self._severity = severity  # 0.5 = 50% speed
    
    @property
    def name(self) -> str:
        return f"[INJURED] {self.wrapped.name}"
    
    @property
    def x(self) -> int:
        return self.wrapped.x
    
    @x.setter
    def x(self, value: int):
        self.wrapped.x = value
    
    @property
    def y(self) -> int:
        return self.wrapped.y
    
    @y.setter
    def y(self, value: int):
        self.wrapped.y = value
    
    def move(self, entities: list = None, speed_multiplier: int = 1):
        """Move with reduced speed due to injury"""
        actual_multiplier = max(1, int(speed_multiplier * (1 - self._severity)))
        self.wrapped.movement_strategy.move(self.wrapped, entities or [], actual_multiplier)
    
    def get_severity(self) -> float:
        """Get the injury severity"""
        return self._severity


class ScentCoveredDecorator(EntityComponent):
    """
    Decorator that masks an animal's scent.
    
    Animals with this decorator are harder for predators
    to detect, reducing their detection range.
    
    Use cases:
    - Animals hiding
    - Animals in water
    - Animals that rolled in mud
    """
    
    def __init__(self, wrapped, stealth_bonus: float = 0.5):
        """
        Initialize the scent covered decorator.
        
        Args:
            wrapped: The Entity to wrap
            stealth_bonus: Detection range reduction (0.0-1.0)
        """
        super().__init__(wrapped)
        self._stealth_bonus = stealth_bonus
    
    @property
    def name(self) -> str:
        return f"[HIDDEN] {self.wrapped.name}"
    
    @property
    def x(self) -> int:
        return self.wrapped.x
    
    @x.setter
    def x(self, value: int):
        self.wrapped.x = value
    
    @property
    def y(self) -> int:
        return self.wrapped.y
    
    @y.setter
    def y(self, value: int):
        self.wrapped.y = value
    
    def move(self, entities: list = None, speed_multiplier: int = 1):
        """Move normally but with reduced detection"""
        self.wrapped.movement_strategy.move(self.wrapped, entities or [], speed_multiplier)
    
    def get_detection_range(self, base_range: int) -> int:
        """Get reduced detection range"""
        return int(base_range * (1 - self._stealth_bonus))


class BuffDecorator(EntityComponent):
    """
    Decorator that provides general stat buffs.
    
    This is a flexible decorator that can enhance multiple
    attributes of an animal.
    
    Buffable stats:
    - speed: Movement speed multiplier
    - thirst_threshold: Higher thirst tolerance
    - hunger_threshold: Higher hunger tolerance
    - detection_range: Predator detection range
    """
    
    def __init__(self, wrapped, **buffs):
        """
        Initialize the buff decorator.
        
        Args:
            wrapped: The Entity to wrap
            **buffs: Keyword arguments for stat multipliers
                - speed: Speed multiplier
                - thirst_threshold: Thirst tolerance multiplier
                - hunger_threshold: Hunger tolerance multiplier
                - detection_range: Detection range multiplier
        """
        super().__init__(wrapped)
        self._buffs = buffs
    
    @property
    def name(self) -> str:
        return f"[BUFFED] {self.wrapped.name}"
    
    @property
    def x(self) -> int:
        return self.wrapped.x
    
    @x.setter
    def x(self, value: int):
        self.wrapped.x = value
    
    @property
    def y(self) -> int:
        return self.wrapped.y
    
    @y.setter
    def y(self, value: int):
        self.wrapped.y = value
    
    def move(self, entities: list = None, speed_multiplier: int = 1):
        """Move with buffed speed if applicable"""
        speed_buff = self._buffs.get('speed', 1.0)
        actual_multiplier = int(speed_multiplier * speed_buff)
        self.wrapped.movement_strategy.move(self.wrapped, entities or [], actual_multiplier)
    
    def get_buff(self, stat: str, base_value: float) -> float:
        """Get buffed stat value"""
        buff = self._buffs.get(stat, 1.0)
        return base_value * buff


class FatigueDecorator(EntityComponent):
    """
    Decorator that represents a tired animal.
    
    Tired animals have reduced speed and may need
    to rest more frequently.
    
    Effects:
    - Movement speed reduced by 25%
    - Increased sleep need
    """
    
    def __init__(self, wrapped):
        super().__init__(wrapped)
    
    @property
    def name(self) -> str:
        return f"[TIRED] {self.wrapped.name}"
    
    @property
    def x(self) -> int:
        return self.wrapped.x
    
    @x.setter
    def x(self, value: int):
        self.wrapped.x = value
    
    @property
    def y(self) -> int:
        return self.wrapped.y
    
    @y.setter
    def y(self, value: int):
        self.wrapped.y = value
    
    def move(self, entities: list = None, speed_multiplier: int = 1):
        """Move with reduced speed due to fatigue"""
        actual_multiplier = max(1, int(speed_multiplier * 0.75))
        self.wrapped.movement_strategy.move(self.wrapped, entities or [], actual_multiplier)


# Factory function for creating decorators
def create_decorator(entity, decorator_type: str, **kwargs) -> EntityComponent:
    """
    Factory function to create a decorator.
    
    Args:
        entity: The entity to decorate
        decorator_type: Type of decorator ("speed_boost", "injured", etc.)
        **kwargs: Additional arguments for the decorator
        
    Returns:
        The decorated entity
    """
    decorators = {
        'speed_boost': SpeedBoostDecorator,
        'injured': InjuredDecorator,
        'scent_covered': ScentCoveredDecorator,
        'buff': BuffDecorator,
        'fatigue': FatigueDecorator,
    }
    
    decorator_class = decorators.get(decorator_type.lower())
    if decorator_class:
        return decorator_class(entity, **kwargs)
    return entity