# utils/constants.py

# Time Settings
TICK_RATE = 1.0  # 1 real second = 1 simulation tick. (Lower this later to speed up time)
TICKS_PER_DAY = 24
SUNRISE_HOUR = 6   # 6:00 AM
SUNSET_HOUR = 18   # 6:00 P

# Map Settings
GRID_WIDTH = 100
GRID_HEIGHT = 100

# Survival Caps
MAX_THIRST = 100
MAX_HUNGER = 100
THIRST_THRESHOLD = 45  # When animals start looking for water
HUNGER_THRESHOLD = 40  # When animals start looking for food
CARNIVORE_HUNT_THRESHOLD = 70  # When carnivores start actively hunting

DESPERATION_THRESHOLD = 80  # When animals panic and break sleep cycles
