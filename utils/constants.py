# utils/constants.py

# Time Settings
TICK_RATE = 1.0  # 1 real second = 1 simulation tick. (Lower this later to speed up time)
TICK_RATE = 0.5  # Speed up simulation (0.5 seconds per tick)
TICKS_PER_DAY = 24
SUNRISE_HOUR = 6   # 6:00 AM
SUNSET_HOUR = 18   # 6:00 PM

# Map Settings
GRID_WIDTH = 100
GRID_HEIGHT = 100

# Survival Caps
MAX_THIRST = 100
MAX_HUNGER = 100
THIRST_THRESHOLD = 40  # When animals start looking for water (lowered for faster triggering)
HUNGER_THRESHOLD = 20  # When herbivores start seeking food (lowered for faster triggering)

DESPERATION_THRESHOLD = 85  # When animals panic and break sleep cycles

# Hunger increase rate (different for herbivores)
HERBIVORE_HUNGER_RATE = 2  # Hunger increases faster for herbivores to trigger eating
