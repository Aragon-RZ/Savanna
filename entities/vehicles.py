"""
Vehicle Classes - Safari vehicles that animals react to

Vehicles:
- Jeep: Open safari vehicle
- SafariVehicle: Covered vehicle for tourists

Animals react to vehicles:
- Flee when vehicle nearby (awareness range)
- Different reaction than predators

Usage:
    jeep = Jeep(1, "Safari Jeep", 5, 5)
    jeep.drive_to(10, 10)  # Move to new location
"""

from entities.base import Entity
import random


class Vehicle(Entity):
    """
    Base class for safari vehicles.
    
    Animals react to vehicles by fleeing within
    a certain range.
    """
    
    def __init__(self, entity_id, name, x=0, y=0):
        super().__init__(entity_id, name, x, y)
        self.driving = False
        self.fuel = 100
    
    def drive_to(self, target_x, target_y):
        """Move toward target location"""
        if self.fuel <= 0:
            return
        
        # Simple movement
        if self.x < target_x:
            self.x += 1
        elif self.x > target_x:
            self.x -= 1
        
        if self.y < target_y:
            self.y += 1
        elif self.y > target_y:
            self.y -= 1
        
        self.fuel -= 0.5


class Jeep(Vehicle):
    """
    Open safari jeep.
    
    Animals know these and flee when nearby.
    Range: 5 tiles (animals can smell/hear jeep)
    """
    
    def __init__(self, entity_id, name, x=0, y=0):
        super().__init__(entity_id, name, x, y)
        self.vehicle_type = "jeep"
        self.awareness_range = 5  # Animals flee at this range
    
    def get_awareness_range(self) -> int:
        """Get how far animals can detect this vehicle"""
        return self.awareness_range


class SafariVehicle(Vehicle):
    """
    Covered safari vehicle.
    
    Quieter than jeep, animals detect at shorter range.
    Range: 3 tiles
    """
    
    def __init__(self, entity_id, name, x=0, y=0):
        super().__init__(entity_id, name, x, y)
        self.vehicle_type = "safari_van"
        self.awareness_range = 3
        self.capacity = 6  # Can carry tourists


class Truck(Vehicle):
    """
    Supply truck.
    
    Brings supplies to the safari area.
    Very loud - animals detect at 7 tiles.
    """
    
    def __init__(self, entity_id, name, x=0, y=0):
        super().__init__(entity_id, name, x, y)
        self.vehicle_type = "truck"
        self.awareness_range = 7
        self.supplies = {"food": 50, "water": 50}
    
    def restock(self):
        """Refill supplies"""
        self.supplies["food"] = 50
        self.supplies["water"] = 50


# ==========================================
# HELPER FUNCTIONS
# ==========================================

def create_jeep(id, name, x=0, y=0) -> Jeep:
    """Create a new jeep"""
    return Jeep(id, name, x, y)

def create_safari_van(id, name, x=0, y=0) -> SafariVehicle:
    """Create a new safari van"""
    return SafariVehicle(id, name, x, y)