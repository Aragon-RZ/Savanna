class Entity:
    def __init__(self, entity_id, name, x=0, y=0):
        self.id = entity_id
        self.name = name
        self.x = x
        self.y = y
        self.is_alive = True
        self.state = "IDLE"

    def update(self, current_hour=0, entities=None):
        pass

    def __str__(self):
        return f"[{self.name} {self.id}] at ({self.x}, {self.y}) - State: {self.state}"