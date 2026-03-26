

class Entity: #Base class for anything that exists in the simulation. (all animals inherit from this class) 
    def __init__(self, entity_id, name, x=0, y=0):
        self.id = entity_id
        self.name = name
        self.x = x
        self.y = y
        self.is_alive = True
        self.state = "IDLE"

    def update(self, current_hour=0):
        """
        Child classes will override this.
        The Engine passes the current_hour so entities know if it is day or night.
        """
        pass

    def __str__(self):
        return f"[{self.name} {self.id}] at ({self.x}, {self.y}) - State: {self.state}"