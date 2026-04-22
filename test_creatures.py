"""
Test Creatures - Diverse simulation for testing patterns

This script creates a diverse population of creatures to test
all four design patterns: State, Strategy, Observer, and Decorator.

Test Scenarios:
1. Herd behavior: Zebras moving together
2. Predator-prey: Lions hunting zebras
3. Nocturnal animals: Leopards and BushBabies
4. State transitions: Animals getting thirsty, sleeping
5. Decorator effects: Speed boosts, injuries
"""

import sys
sys.path.insert(0, '.')

from engine.builder import SafariBuilder
from engine.events import EventManager, EventType, ConsoleLogger, StatisticsTracker
from entities.animals import Zebra, Elephant, Lion, Leopard, BushBaby, Ostrich, Cheetah
from entities.components import SpeedBoostDecorator, InjuredDecorator, BuffDecorator


def test_herd_behavior():
    """Test: Herd of zebras staying together"""
    print("\n" + "="*50)
    print("TEST 1: HERD BEHAVIOR")
    print("="*50)
    
    EventManager.clear()
    logger = ConsoleLogger(verbose=False)
    tracker = StatisticsTracker()
    EventManager.subscribe('*', logger)
    EventManager.subscribe('*', tracker)
    
    builder = SafariBuilder(max_ticks=20)
    engine = (builder.build_environment()
                    .add_zebras(8)  # Big herd
                    .get_engine())
    engine.start()
    engine.join()
    
    print(f"\nHerd Stats: {tracker.stats['state_changes']} state changes")


def test_predator_prey():
    """Test: Lion hunting zebra"""
    print("\n" + "="*50)
    print("TEST 2: PREDATOR vs PREY")
    print("="*50)
    
    EventManager.clear()
    logger = ConsoleLogger(verbose=True)
    tracker = StatisticsTracker()
    EventManager.subscribe('*', logger)
    EventManager.subscribe('*', tracker)
    
    # Build environment using method chaining (returns builder)
    builder = SafariBuilder(max_ticks=30).build_environment()
    
    # Get engine to add custom animals
    engine = builder.get_engine()
    
    # Spawn zebra and lion close to each other
    zebra = Zebra(1, "TestZebra", 0, 0)
    zebra.target_water = builder.water
    engine.add_entity(zebra)
    
    lion = Lion(2, "TestLion", 1, 1)  # Close!
    lion.target_water = builder.water
    engine.add_entity(lion)
    
    engine.max_ticks = 30
    engine.start()
    engine.join()
    
    print(f"\nPredator Stats - Born: {tracker.stats['total_born']}, Died: {tracker.stats['total_died']}")
    print(tracker.get_summary())


def test_nocturnal():
    """Test: Nocturnal animals"""
    print("\n" + "="*50)
    print("TEST 3: NOCTURNAL ANIMALS")
    print("="*50)
    
    EventManager.clear()
    logger = ConsoleLogger(verbose=False)
    tracker = StatisticsTracker()
    EventManager.subscribe('*', logger)
    EventManager.subscribe('*', tracker)
    
    builder = SafariBuilder(max_ticks=50)
    engine = (builder.build_environment()
                    .add_zebras(3)  # Diurnal
                    .add_leopards(2)  # Nocturnal
                    .add_bushbabies(3)  # Nocturnal
                    .get_engine())
    engine.start()
    engine.join()
    
    print(f"\nNocturnal Stats - State changes: {tracker.stats['state_changes']}")


def test_decorators():
    """Test: Decorator patterns"""
    print("\n" + "="*50)
    print("TEST 4: DECORATOR PATTERNS")
    print("="*50)
    
    # Create base creatures
    zebra = Zebra(1, "NormalZebra", 5, 5)
    lion = Lion(2, "NormalLion", 0, 0)
    
    # Apply decorators
    fast_zebra = SpeedBoostDecorator(zebra, multiplier=3.0)
    injured_lion = InjuredDecorator(lion, severity=0.7)
    
    print(f"Original Zebra: {zebra.name}")
    print(f"Fast Zebra: {fast_zebra.name}")
    print(f"Injured Lion: {injured_lion.name}")
    
    # Test movement
    print("\nMovement test (5 ticks):")
    for i in range(5):
        fast_zebra.move()
        injured_lion.move()
        print(f"  Tick {i+1}: FastZebra @({fast_zebra.x}, {fast_zebra.y}), InjuredLion @({injured_lion.x}, {injured_lion.y})")
    
    # Test stacking decorators
    print("\nStacked decorators:")
    super_lion = SpeedBoostDecorator(InjuredDecorator(Lion(3, "SuperLion", 0, 0)))
    print(f"Stacked: {super_lion.name}")


def test_all_patterns():
    """Test: All patterns combined"""
    print("\n" + "="*50)
    print("TEST 5: ALL PATTERNS COMBINED")
    print("="*50)
    
    EventManager.clear()
    logger = ConsoleLogger(verbose=True)
    tracker = StatisticsTracker()
    EventManager.subscribe('*', logger)
    EventManager.subscribe('*', tracker)
    
    builder = SafariBuilder(max_ticks=25)
    engine = (builder.build_environment()
                    .add_zebras(5)
                    .add_elephants(2)
                    .add_lions(2)
                    .add_leopards(1)
                    .add_bushbabies(2)
                    .get_engine())
    engine.start()
    engine.join()
    
    print("\n" + "="*50)
    print("FINAL STATISTICS")
    print("="*50)
    print(tracker.get_summary())


if __name__ == "__main__":
    # Run all tests sequentially
    print("="*50)
    print("RUNNING ALL TESTS")
    print("="*50)
    
    test_herd_behavior()
    test_predator_prey()
    test_nocturnal()
    test_decorators()
    test_all_patterns()
    
    print("\n" + "="*50)
    print("✅ ALL TESTS COMPLETE")
    print("="*50)