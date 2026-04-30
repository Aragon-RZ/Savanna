
# engine/weather.py
# ============================================================
# OBSERVER PATTERN — WeatherSystem is a Publisher
# STRATEGY PATTERN — Each weather type is a WeatherEffect
# ============================================================
# WeatherSystem runs as a DAEMON THREAD — it broadcasts
# weather events independently of the main tick loop.
# Animals that are subscribed via EventBus react automatically.
#
# Daemon thread means: when the main engine stops, this
# thread dies automatically — no manual cleanup needed.
# ============================================================

import threading
import random
import time
from utils.events import event_bus, Event, EventListener


# ── STRATEGY PATTERN — Weather Effects ───────────────────────
# Each weather condition is its own strategy object.
# WeatherSystem swaps between them at runtime.

class WeatherEffect:
    """Base strategy — no effect (clear weather)."""
    name = "CLEAR"
    thirst_modifier = 0    # added to thirst each tick
    hunger_modifier = 0    # added to hunger each tick

    def describe(self):
        return "☀️  Clear skies over the savanna."

class DroughtEffect(WeatherEffect):
    """Animals get thirsty 2x faster."""
    name = "DROUGHT"
    thirst_modifier = 2    # +2 extra thirst per tick on top of normal

    def describe(self):
        return "🌵 A drought grips the savanna. Water is scarce!"

class RainEffect(WeatherEffect):
    """Animals thirst drops — rain provides relief."""
    name = "RAIN"
    thirst_modifier = -1   # thirst rises slower during rain

    def describe(self):
        return "🌧️  Rain sweeps across the savanna. Animals find relief."

class StormEffect(WeatherEffect):
    """Dangerous — thirst rises AND hunger rises (animals shelter)."""
    name = "STORM"
    thirst_modifier = 1
    hunger_modifier = 2    # carnivores can't hunt in a storm

    def describe(self):
        return "⛈️  A violent storm rolls in! Animals struggle to survive."


# ── WEATHER SYSTEM (Daemon Thread + Observer Publisher) ──────
class WeatherSystem(threading.Thread):
    """
    Runs as a background daemon thread.
    Every WEATHER_INTERVAL seconds it randomly picks a new
    weather effect and emits a WEATHER_CHANGED event so all
    subscribed animals can react.

    OBSERVER: acts as a Publisher — emits events
    STRATEGY: swaps WeatherEffect objects at runtime
    DAEMON:   dies automatically when main engine stops
    """

    WEATHER_INTERVAL = 20  # seconds between weather changes
    # Weighted pool — clear weather is most common
    WEATHER_POOL = [
        ClearEffect := WeatherEffect,
        DroughtEffect,
        DroughtEffect,   # drought twice as likely as storm
        RainEffect,
        StormEffect,
    ]

    def __init__(self, display_output=True):
        super().__init__()
        self.daemon = True   # ← dies when main thread stops
        self.current_effect = WeatherEffect()   # start clear
        self.display_output = display_output
        self._lock = threading.Lock()
        self._stop_event = threading.Event()

    @property
    def current_weather(self):
        """Thread-safe read of current weather."""
        with self._lock:
            return self.current_effect

    def get_modifiers(self):
        """
        Called by the engine each tick to apply weather effects.
        Returns (thirst_modifier, hunger_modifier).
        """
        with self._lock:
            return (self.current_effect.thirst_modifier,
                    self.current_effect.hunger_modifier)

    def run(self):
        self._print("🌤️  WeatherSystem daemon started.")
        while not self._stop_event.wait(self.WEATHER_INTERVAL):
            self._change_weather()

    def stop(self):
        self._stop_event.set()

    def _print(self, *args, **kwargs):
        if self.display_output:
            print(*args, **kwargs)

    def _change_weather(self):
        """Pick a new random weather — never the same as current."""
        available = [w for w in self.WEATHER_POOL if w is not type(self.current_effect)]
        new_effect = random.choice(available)()

        with self._lock:
            self.current_effect = new_effect

        self._print(f"\n{'='*40}")
        self._print(new_effect.describe())
        self._print(f"{'='*40}\n")

        event_bus.emit(Event.WEATHER_CHANGED, {
            "weather": new_effect.name,
            "effect": new_effect
        })
