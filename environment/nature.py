

#### WATERING HOLE ####

# environment/nature.py
import threading

class WateringHole:
    def __init__(self, name, x, y, capacity=3):
        self.name = name
        self.x = x
        self.y = y
        self.capacity = capacity
        
        # A Semaphore allows multiple animals to use the resource up to the 'capacity' limit
        self.spots = threading.Semaphore(capacity)
        
        # Keep track of who is currently drinking (helpful for debugging)
        self.current_drinkers = []

    def try_to_drink(self, entity):
        """
        Called by the Engine when an animal reaches the water's coordinates.
        """
        # If they are already drinking, do nothing
        if entity in self.current_drinkers:
            return True

        # blocking=False is crucial! It means "If full, return False immediately."
        # If we didn't use this, the whole simulation would pause and wait.
        if self.spots.acquire(blocking=False):
            entity.state = "DRINKING"
            self.current_drinkers.append(entity)
            print(f"💧 {entity.name} found a spot and started drinking at {self.name}!")
            return True
        else:
            entity.state = "WAITING_IN_LINE"
            print(f"⏳ {entity.name} is waiting in line. The {self.name} is full.")
            return False

    def finish_drinking(self, entity):
        """
        Called by the Engine when an animal's thirst reaches 0.
        """
        if entity in self.current_drinkers:
            self.current_drinkers.remove(entity)
            self.spots.release()  # Free up the semaphore spot!
            print(f"✅ {entity.name} finished drinking and freed up a spot.")