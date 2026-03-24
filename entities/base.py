from utils.constants import GRID_HEIGHT, GRID_WIDTH


class Entity:
    def __init__(self, entity_id, name, x=0, y=0):
        self.id = entity_id
        self.name = name
        self.x = x
        self.y = y
        self.is_alive = True
        self.state = "IDLE"

    def update(self):
        """
        This is the most important method. 
        Every tick, the engine will call this.
        Child classes (like Zebra) will override this with their specific logic.
        """
        pass

    def move_by(self, dx, dy):
        self.x = min(max(self.x + dx, 0), GRID_WIDTH - 1)
        self.y = min(max(self.y + dy, 0), GRID_HEIGHT - 1)

    def step_towards(self, target_x, target_y):
        dx = 0
        dy = 0

        if self.x < target_x:
            dx = 1
        elif self.x > target_x:
            dx = -1

        if self.y < target_y:
            dy = 1
        elif self.y > target_y:
            dy = -1

        self.move_by(dx, dy)

    def __str__(self):
        return f"[{self.name} {self.id}] at ({self.x}, {self.y}) - State: {self.state}"
