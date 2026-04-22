"""
Human Classes - Safari guides, tourists, and vets

This module provides human elements that interact with animals:
- SafariGuide: Can feed/water animals
- Tourist: Observes (passive, data collection)
- Vet: Can heal injured/sick animals
- Jeep: Vehicle that animals flee from
- SafariVehicle: Carries tourists

Usage:
    guide = SafariGuide(1, "Guide John")
    guide.feed_animal(hungry_zebra)
    
    tourist = Tourist(2, "Tourist Alice")
    tourist.take_photo(animal)
"""

from entities.base import Entity


class SafariGuide(Entity):
    """
    Safari guide - can interact with animals positively.
    
    Actions:
    - Feed animals (reduces hunger)
    - Give water (reduces thirst)
    - Rescue desperate animals
    """
    
    def __init__(self, entity_id, name, x=0, y=0):
        super().__init__(entity_id, name, x, y)
        self.role = "guide"
        self.food_supply = 50  # Can carry food for feeding
        self.water_supply = 50  # Can carry water
    
    def feed_animal(self, animal) -> bool:
        """
        Feed an animal.
        
        Args:
            animal: Animal to feed
            
        Returns:
            True if successful
        """
        if self.food_supply <= 0:
            return False
        
        if hasattr(animal, 'hunger'):
            # Reduce hunger
            feed_amount = min(30, animal.hunger, self.food_supply)
            animal.hunger = max(0, animal.hunger - feed_amount)
            self.food_supply -= feed_amount
            print(f"🍎 {self.name} fed {animal.name} ({feed_amount} food)")
            return True
        return False
    
    def give_water(self, animal) -> bool:
        """
        Give water to an animal.
        
        Args:
            animal: Animal to water
            
        Returns:
            True if successful
        """
        if self.water_supply <= 0:
            return False
        
        if hasattr(animal, 'thirst'):
            # Reduce thirst
            water_amount = min(30, animal.thirst, self.water_supply)
            animal.thirst = max(0, animal.thirst - water_amount)
            self.water_supply -= water_amount
            print(f"💧 {self.name} gave water to {animal.name} ({water_amount} water)")
            return True
        return False
    
    def rescue(self, animal) -> bool:
        """
        Rescue a desperate animal.
        
        Args:
            animal: Animal in desperate state
            
        Returns:
            True if successful
        """
        if not hasattr(animal, 'state'):
            return False
        
        if animal.state == "DESPERATE":
            # Reset survival stats
            animal.thirst = max(0, animal.thirst - 50)
            animal.hunger = max(0, animal.hunger - 50)
            animal.state = "WANDERING"
            print(f"🆘 {self.name} rescued {animal.name}!")
            return True
        return False
    
    def update(self, current_hour=0, entities=None):
        """Guide updates - find animals to help"""
        # Guides don't move much, they wait for animals to come
        pass


class Tourist(Entity):
    """
    Tourist - passive observer.
    
    Actions:
    - Take photos (data collection)
    - Watch animals (observation)
    - Generate revenue (simulation metric)
    """
    
    def __init__(self, entity_id, name, x=0, y=0):
        super().__init__(entity_id, name, x, y)
        self.role = "tourist"
        self.photos_taken = 0
        self.satisfaction = 100
    
    def take_photo(self, animal) -> bool:
        """
        Take a photo of an animal.
        
        Args:
            animal: Animal to photograph
            
        Returns:
            True if successful
        """
        if not animal.is_alive:
            return False
        
        self.photos_taken += 1
        
        # Log the observation
        try:
            from engine.database import DatabaseManager
            DatabaseManager.log_event(
                tick=0,  # Would be current tick
                entity_id=self.id,
                event_type="TOURIST_PHOTO",
                details=f"animal={animal.name}, species={type(animal).__name__}"
            )
        except:
            pass
        
        return True
    
    def observe(self, animals: list) -> int:
        """
        Observe nearby animals.
        
        Args:
            animals: List of all animals
            
        Returns:
            Number of animals observed
        """
        observed = 0
        for animal in animals:
            dist = abs(self.x - animal.x) + abs(self.y - animal.y)
            if dist <= 10:  # Observation range
                observed += 1
        return observed


class Vet(Entity):
    """
    Veterinarian - can heal animals.
    
    Actions:
    - Treat injuries
    - Cure illness
    - Vaccinate (prevent disease)
    """
    
    def __init__(self, entity_id, name, x=0, y=0):
        super().__init__(entity_id, name, x, y)
        self.role = "vet"
        self.medical_supply = 30
    
    def treat(self, animal) -> bool:
        """
        Treat an animal's injuries.
        
        Args:
            animal: Animal to treat
            
        Returns:
            True if successful
        """
        if self.medical_supply <= 0:
            return False
        
        if hasattr(animal, 'is_injured') and animal.is_injured:
            animal.is_injured = False
            self.medical_supply -= 10
            print(f"💊 {self.name} treated {animal.name}")
            return True
        return False
    
    def cure_illness(self, animal) -> bool:
        """
        Cure an animal's illness.
        
        Args:
            animal: Sick animal
            
        Returns:
            True if successful
        """
        if self.medical_supply <= 0:
            return False
        
        if hasattr(animal, 'is_sick') and animal.is_sick:
            animal.is_sick = False
            self.medical_supply -= 10
            print(f"💉 {self.name} cured {animal.name}")
            return True
        return False


# ==========================================
# HUMAN TYPES - Convenience classes
# ==========================================

class SafariGuideMale(SafariGuide):
    def __init__(self, entity_id, name):
        super().__init__(entity_id, name, gender="male")

class SafariGuideFemale(SafariGuide):
    def __init__(self, entity_id, name):
        super().__init__(entity_id, name, gender="female")

class TouristFamily(Tourist):
    """Tourist family group"""
    def __init__(self, entity_id, name):
        super().__init__(entity_id, name)
        self.group_size = random.randint(2, 5)
    
    def __str__(self):
        return f"TouristFamily({self.group_size} people)"