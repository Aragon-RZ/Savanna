 
import threading

class WateringHole:
    def __init__(self, name, x, y, capacity=3): #(default capacity if not stated in watering hole creation)
        self.name = name #name of wateringhole for dsiplay 
        self.x = x
        self.y = y
        self.capacity = capacity
        self.spots = threading.Semaphore(capacity) #semaphore for access control
        self.current_drinkers = [] #keeps track of animals currently drinking 

    def try_to_drink(self, entity):
        if entity in self.current_drinkers:
            return True #if animal currenltly drinking, do nothing 

        # Non-blocking acquire- to not block entire simulaition
        if self.spots.acquire(blocking=False):
            entity.state = "DRINKING"
            self.current_drinkers.append(entity)
            print(f"💧 {entity.name} found a spot and started drinking at {self.name}!")
            return True
        else:
            #no spots available, animal waits
            entity.state = "WAITING_IN_LINE"
            print(f"⏳ {entity.name} is waiting in line. The {self.name} is full.")
            return False

    def finish_drinking(self, entity):
        if entity in self.current_drinkers:
            self.current_drinkers.remove(entity)
            self.spots.release() #free up spot for another animal 
            print(f"✅ {entity.name} finished drinking and freed up a spot.")