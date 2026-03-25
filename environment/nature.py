# environment/nature.py
import threading

class WateringHole:
    def __init__(self, name, x, y, capacity=3):
        self.name = name
        self.x = x
        self.y = y
        self.capacity = capacity
        self.spots = threading.Semaphore(capacity)
        self.current_drinkers = []

    def try_to_drink(self, entity):
        if entity in self.current_drinkers:
            return True

        # Non-blocking acquire!
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
        if entity in self.current_drinkers:
            self.current_drinkers.remove(entity)
            self.spots.release()
            print(f"✅ {entity.name} finished drinking and freed up a spot.")