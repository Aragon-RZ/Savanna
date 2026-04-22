"""
Sleeping State - Animal is sleeping based on day/night cycle

The sleeping state manages the diurnal/nocturnal behavior of animals.
Animals will sleep during their inactive hours (day for nocturnal,
night for diurnal) unless they are desperate.
"""

from .base import AnimalState
from utils.constants import SUNRISE_HOUR, SUNSET_HOUR


class SleepingState(AnimalState):
    """
    The SLEEPING state represents an animal resting.
    
    Sleep is driven by the day/night cycle:
    - Diurnal animals (Zebra, Lion): Sleep at night
    - Nocturnal animals (Leopard, BushBaby): Sleep during day
    
    The animal will wake up if:
    - It's their active time (day/night based on is_diurnal)
    - They become desperate (critical thirst/hunger)
    """
    
    def enter(self):
        """Log when animal goes to sleep"""
        self.animal.state = "SLEEPING"
        print(f"💤 {self.animal.name} went to sleep.")
    
    def update(self, current_hour: int, entities: list):
        """
        Check if animal should wake up.
        
        Waking conditions:
        1. It's their active time AND not desperate
        2. They become desperate (emergency wake-up)
        """
        from utils.constants import DESPERATION_THRESHOLD
        from .wandering import WanderingState
        from .desperate import DesperateState
        
        # Check if desperate - emergency wake up
        is_desperate = (self.animal.thirst >= DESPERATION_THRESHOLD or 
                       self.animal.hunger >= DESPERATION_THRESHOLD)
        
        if is_desperate:
            print(f"⚠️ {self.animal.name} woke up in a panic due to extreme thirst/hunger!")
            self.transition_to(DesperateState(self.animal))
            return
        
        # Check if it's time to wake up based on diurnal/nocturnal
        is_daytime = SUNRISE_HOUR <= current_hour < SUNSET_HOUR
        should_be_awake = is_daytime if self.animal.is_diurnal else not is_daytime
        
        if should_be_awake:
            print(f"☀️/🌙 {self.animal.name} woke up.")
            self.transition_to(WanderingState(self.animal))
        
        # Otherwise, stay sleeping (do nothing)
    
    def exit(self):
        """Nothing to clean up when waking"""
        pass