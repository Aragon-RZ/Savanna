# environment/base.py
# ============================================================
# COMPOSITE PATTERN — Environment Tree
# ============================================================
# How it works:
#   - EnvironmentComponent is the shared interface
#   - WateringHole / Hotel etc. are LEAVES — do real work
#   - SavannaZone is the COMPOSITE — holds children and
#     delegates update() / status() down to all of them
#   - The engine calls root.update(tick, entities) and the
#     whole tree updates itself recursively
#
# Why we use it here:
#   Before this, environments was a flat list the engine
#   looped manually. Now you can add an entire zone (e.g.
#   WaterZone with 3 holes + a Hotel) as ONE object and
#   the engine never needs to change.
#
#   Tree the builder will construct:
#       Savanna          (SavannaZone)
#       └── WaterZone    (SavannaZone)
#           └── Oasis    (WateringHole)  ← leaf
# ============================================================

from abc import ABC, abstractmethod


# ── COMPONENT INTERFACE ──────────────────────────────────────
class EnvironmentComponent(ABC):
    """
    Shared interface for both individual environment objects
    (leaves) and groups of them (composites).
    The engine only ever depends on this interface.
    """

    def __init__(self, name: str, x: int = 0, y: int = 0):
        self.name = name
        self.x = x
        self.y = y

    @abstractmethod
    def update(self, tick: int, entities: list):
        """Called every tick by the engine or parent zone."""
        pass

    @abstractmethod
    def status(self) -> str:
        """Returns a one-line human-readable summary."""
        pass

    def __str__(self):
        return f"[{self.__class__.__name__}] {self.name} @ ({self.x}, {self.y})"


# ── COMPOSITE NODE ───────────────────────────────────────────
class SavannaZone(EnvironmentComponent):
    """
    A named zone grouping multiple environment components.
    Delegates all calls to its children transparently.
    The engine treats this exactly like a single leaf node.
    """

    def __init__(self, name: str):
        super().__init__(name, x=0, y=0)
        self._children: list[EnvironmentComponent] = []

    def add(self, component: EnvironmentComponent):
        """Add a child (leaf or composite). Chainable."""
        self._children.append(component)
        return self  # allows: zone.add(oasis).add(hotel)

    def remove(self, component: EnvironmentComponent):
        self._children = [c for c in self._children if c is not component]

    def get_all_leaves(self) -> list:
        """Flatten the whole tree and return every leaf."""
        leaves = []
        for child in self._children:
            if isinstance(child, SavannaZone):
                leaves.extend(child.get_all_leaves())
            else:
                leaves.append(child)
        return leaves

    def update(self, tick: int, entities: list):
        for child in self._children:
            child.update(tick, entities)

    def status(self) -> str:
        lines = [f"📍 Zone: {self.name} ({len(self._children)} components)"]
        for child in self._children:
            lines.append(f"   └─ {child.status()}")
        return "\n".join(lines)