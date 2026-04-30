from entities.base import Entity
from utils.constants import (
    GRID_HEIGHT,
    GRID_WIDTH,
    POACHER_ARREST_RANGE,
    POACHER_FLEE_RANGE,
    POACHER_FLEE_STEP,
    POACHER_POACH_TICKS,
    POACHER_STEP,
)
from utils.events import Event, event_bus


class PoacherStrategy:
    def execute(self, poacher, entities):
        raise NotImplementedError


class PoachStrategy(PoacherStrategy):
    def execute(self, poacher, entities):
        ranger = poacher.nearest_ranger(entities)
        if ranger and poacher.distance_to(ranger) <= POACHER_ARREST_RANGE:
            poacher.arrest(ranger)
            return
        if ranger and poacher.distance_to(ranger) <= POACHER_FLEE_RANGE:
            poacher.behavior = FleeStrategy(ranger)
            poacher.behavior.execute(poacher, entities)
            return

        target = poacher.target
        if not target or not getattr(target, "is_alive", False):
            target = poacher.find_target(entities)
            poacher.target = target

        if not target:
            poacher.behavior = FleeStrategy(ranger)
            poacher.behavior.execute(poacher, entities)
            return

        poacher.state = f"POACHING {target.name}"
        poacher.move_towards(target.x, target.y, POACHER_STEP)

        if poacher.distance_to(target) <= 1:
            poacher.poach_ticks += 1
            if poacher.poach_ticks >= POACHER_POACH_TICKS:
                target.die(f"Poached by {poacher.name}")
                event_bus.emit(Event.POACHING_ATTACK, {
                    "poacher": poacher,
                    "target": target
                })
                poacher.behavior = FleeStrategy(ranger)
        else:
            poacher.poach_ticks = 0


class FleeStrategy(PoacherStrategy):
    def __init__(self, ranger=None):
        self.ranger = ranger

    def execute(self, poacher, entities):
        ranger = poacher.nearest_ranger(entities) or self.ranger
        if ranger and poacher.distance_to(ranger) <= POACHER_ARREST_RANGE:
            poacher.arrest(ranger)
            return

        poacher.state = "FLEEING"
        exit_x, exit_y = poacher.exit_point
        if ranger and poacher.distance_to(ranger) <= POACHER_FLEE_RANGE:
            dx = poacher.x - ranger.x
            dy = poacher.y - ranger.y
            if dx == 0 and dy == 0:
                dx = poacher.x - exit_x
                dy = poacher.y - exit_y
            poacher.move_by(
                POACHER_FLEE_STEP if dx >= 0 else -POACHER_FLEE_STEP,
                POACHER_FLEE_STEP if dy >= 0 else -POACHER_FLEE_STEP,
            )
        else:
            poacher.move_towards(exit_x, exit_y, POACHER_FLEE_STEP)

        if poacher.at_map_edge():
            poacher.escape()


class Poacher(Entity):
    def __init__(self, entity_id, name, x, y, target=None, zone_id=None,
                 exit_point=None, display_output=True):
        super().__init__(entity_id, name, x, y)
        self.target = target
        self.zone_id = zone_id
        self.exit_point = exit_point or self._nearest_edge_point()
        self.display_output = display_output
        self.behavior = PoachStrategy()
        self.state = "INFILTRATING"
        self.poach_ticks = 0
        self.resolution = None

    def update(self, current_hour=0, entities=None):
        if self.resolution:
            return
        self.behavior.execute(self, entities or [])

    def arrest(self, ranger):
        if self.resolution:
            return
        self.resolution = "arrested"
        self.is_alive = False
        self.state = "ARRESTED"
        self.ticks_dead = 0
        self._print(f"{self.name} was arrested by {getattr(ranger, 'name', 'a ranger')}.")
        event_bus.emit(Event.POACHER_ARRESTED, {
            "poacher": self,
            "ranger": ranger
        })

    def escape(self):
        if self.resolution:
            return
        self.resolution = "escaped"
        self.is_alive = False
        self.state = "ESCAPED"
        self.ticks_dead = 0
        self._print(f"{self.name} escaped the reserve.")
        event_bus.emit(Event.POACHER_ESCAPED, {"poacher": self})

    def find_target(self, entities):
        prey = [
            entity for entity in entities
            if getattr(entity, "is_alive", False)
            and hasattr(entity, "thirst")
            and entity.__class__.__name__ not in {"Lion", "Cheetah", "Leopard"}
        ]
        if not prey:
            return None
        return min(prey, key=lambda entity: self.distance_to(entity))

    def nearest_ranger(self, entities):
        rangers = [
            entity for entity in entities
            if getattr(entity, "is_alive", False)
            and entity.__class__.__name__ == "Ranger"
        ]
        if not rangers:
            return None
        return min(rangers, key=lambda ranger: self.distance_to(ranger))

    def distance_to(self, entity):
        return abs(self.x - entity.x) + abs(self.y - entity.y)

    def move_towards(self, target_x, target_y, step=1):
        self.x += self._step_towards(self.x, target_x, step)
        self.y += self._step_towards(self.y, target_y, step)
        self._clamp_position()

    def move_by(self, dx, dy):
        self.x += dx
        self.y += dy
        self._clamp_position()

    def at_map_edge(self):
        return self.x in {0, GRID_WIDTH - 1} or self.y in {0, GRID_HEIGHT - 1}

    def _nearest_edge_point(self):
        candidates = [
            (0, self.y),
            (GRID_WIDTH - 1, self.y),
            (self.x, 0),
            (self.x, GRID_HEIGHT - 1),
        ]
        return min(candidates, key=lambda point: abs(point[0] - self.x) + abs(point[1] - self.y))

    def _step_towards(self, current, target, step):
        if current < target:
            return min(step, target - current)
        if current > target:
            return -min(step, current - target)
        return 0

    def _clamp_position(self):
        self.x = max(0, min(GRID_WIDTH - 1, self.x))
        self.y = max(0, min(GRID_HEIGHT - 1, self.y))

    def _print(self, *args, **kwargs):
        if self.display_output:
            print(*args, **kwargs)
