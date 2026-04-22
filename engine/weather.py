"""
Weather System - Seasons and environmental effects

This module provides realistic African savanna weather:
- Wet Season (rainy): ~90 days
- Dry Season: ~180 days  
- Short Rains: ~30 days

Effects:
- Drought: Water capacity drops, thirst increases faster
- Rain: Water fills, grass grows faster
- Heat Wave: Extreme thirst

Usage:
    weather = WeatherSystem()
    weather.update(tick)  # Call each tick
    
    season = weather.get_season()  # Current season
    water_multiplier = weather.get_water_multiplier()
"""

from enum import Enum
import random


class Season(Enum):
    """Seasons in the savanna"""
    WET = "wet"           # Rainy season
    DRY = "dry"           # Dry season
    SHORT_RAINS = "short rains"  # Brief rainy period


class WeatherEvent(Enum):
    """Weather events"""
    NONE = "none"
    RAIN = "rain"
    DROUGHT = "drought"
    HEAT_WAVE = "heat_wave"
    STORM = "storm"


class WeatherSystem:
    """
    Manages seasons and weather in the savanna.
    
    Real-world accuracy:
    - Wet season: ~90 ticks (short wet period)
    - Dry season: ~180 ticks (long dry)
    - Short rains: ~30 ticks transition
    
    Season cycle: ~300 ticks total (about 12 days)
    """
    
    def __init__(self):
        """Initialize weather system"""
        self.season = Season.WET
        self.next_season = Season.DRY
        self.season_ticks = 0
        
        # Season durations (realistic)
        self.season_durations = {
            Season.WET: 90,
            Season.DRY: 180,
            Season.SHORT_RAINS: 30,
        }
        
        # Current event
        self.current_event = WeatherEvent.NONE
        
        # Effects multipliers
        self.water_multiplier = 1.0  # Water availability
        self.thirst_rate = 1.0      # Thirst increase rate
        self.food_regrow_rate = 1.0  # Grass regrowth
        
        # Temperature
        self.temperature = 25.0  # Celsius
        
        # Rain chance during wet
        self.rain_chance = 0.3
    
    def update(self, tick: int):
        """
        Update weather each tick.
        
        Args:
            tick: Current tick
        """
        self.season_ticks += 1
        
        # Get current season
        current_duration = self.season_durations[self.season]
        
        # Season transition
        if self.season_ticks >= current_duration:
            self._transition_season()
        
        # Weather events
        self._update_weather_events()
        
        # Update temperature based on season
        self._update_temperature()
        
        # Update multipliers
        self._update_effects()
    
    def _transition_season(self):
        """Transition to next season"""
        self.season_ticks = 0
        
        # Cycle through seasons
        if self.season == Season.WET:
            self.season = Season.DRY
        elif self.season == Season.DRY:
            self.season = Season.SHORT_RAINS
        elif self.season == Season.SHORT_RAINS:
            self.season = Season.WET
        
        print(f"🌡️ Season changed to: {self.season.value.upper()}")
    
    def _update_weather_events(self):
        """Random weather events"""
        # Only during transitions or dry
        if self.season == Season.WET:
            # Chance of rain
            if random.random() < self.rain_chance:
                self.current_event = WeatherEvent.RAIN
            else:
                self.current_event = WeatherEvent.NONE
                
        elif self.season == Season.DRY:
            # Chance of drought
            if random.random() < 0.05:
                self.current_event = WeatherEvent.DROUGHT
            # Chance of heat wave
            elif random.random() < 0.02:
                self.current_event = WeatherEvent.HEAT_WAVE
            else:
                self.current_event = WeatherEvent.NONE
                
        else:
            # Short rains - higher rain chance
            if random.random() < 0.5:
                self.current_event = WeatherEvent.RAIN
            else:
                self.current_event = WeatherEvent.NONE
    
    def _update_temperature(self):
        """Update temperature based on season"""
        if self.season == Season.WET:
            self.temperature = 22.0 + random.uniform(-3, 3)
        elif self.season == Season.DRY:
            self.temperature = 30.0 + random.uniform(-5, 5)
        else:
            self.temperature = 25.0 + random.uniform(-3, 3)
    
    def _update_effects(self):
        """Update effect multipliers based on weather"""
        base_water = 1.0
        base_thirst = 1.0
        base_food = 1.0
        
        # Season effects
        if self.season == Season.WET:
            base_water = 1.5
            base_thirst = 0.8
            base_food = 1.5
        elif self.season == Season.DRY:
            base_water = 0.5
            base_thirst = 1.5
            base_food = 0.5
        
        # Event effects
        if self.current_event == WeatherEvent.DROUGHT:
            base_water = 0.2
            base_thirst = 2.0
            base_food = 0.2
        elif self.current_event == WeatherEvent.HEAT_WAVE:
            base_thirst = 2.5
            base_water = 0.3
        elif self.current_event == WeatherEvent.RAIN:
            base_water = 2.0
            base_thirst = 0.5
        
        self.water_multiplier = base_water
        self.thirst_rate = base_thirst
        self.food_regrow_rate = base_food
    
    def get_season(self) -> Season:
        """Get current season"""
        return self.season
    
    def get_event(self) -> WeatherEvent:
        """Get current weather event"""
        return self.current_event
    
    def get_water_multiplier(self) -> float:
        """Get water availability multiplier"""
        return self.water_multiplier
    
    def get_thirst_multiplier(self) -> float:
        """Get thirst rate multiplier"""
        return self.thirst_rate
    
    def get_food_multiplier(self) -> float:
        """Get grass regrowth multiplier"""
        return self.food_regrow_rate
    
    def describe(self) -> str:
        """Get weather description"""
        parts = [
            f"Season: {self.season.value}",
            f"Temp: {self.temperature:.1f}°C",
        ]
        
        if self.current_event != WeatherEvent.NONE:
            parts.append(f"Event: {self.current_event.value}")
        
        return ", ".join(parts)
    
    def __str__(self):
        return f"Weather({self.season.value}, {self.current_event.value})"


# ==========================================
# CONVENIENCE FUNCTIONS
# ==========================================

def get_current_season(tick: int, wet_duration=90, dry_duration=180, short_duration=30) -> Season:
    """
    Calculate season from tick number.
    
    Args:
        tick: Current tick
        wet_duration: Duration of wet season (default 90)
        dry_duration: Duration of dry season (default 180)
        short_duration: Duration of short rains (default 30)
        
    Returns:
        Current Season
    """
    cycle = wet_duration + dry_duration + short_duration
    position = tick % cycle
    
    if position < wet_duration:
        return Season.WET
    elif position < wet_duration + dry_duration:
        return Season.DRY
    else:
        return Season.SHORT_RAINS