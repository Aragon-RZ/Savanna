class Entity:
    def __init__(self, entity_id, name, x=0, y=0):
        self.id = entity_id
        self.name = name
        self.x = x #x coordinate 
        self.y = y
        self.is_alive = True
        self.state = "IDLE"    # Current state (e.g., IDLE, WANDERING, DRINKING, etc.)

    def update(self, current_hour=0, entities=None):
        pass #meant to be overridden by child classes (like Animal). Each specific entity defines its own behavior here.

    def __str__(self): # Defines how the entity is displayed when printed.
        return f"[{self.name} {self.id}] at ({self.x}, {self.y}) - State: {self.state}"