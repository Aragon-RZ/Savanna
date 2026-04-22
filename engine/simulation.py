

import time
import threading
from collections import defaultdict
from utils.constants import TICK_RATE, TICKS_PER_DAY, SUNRISE_HOUR, SUNSET_HOUR, MAX_THIRST, MAX_HUNGER
from utils.colors import Colors

class SimulationEngine(threading.Thread):
    def __init__(self, max_ticks=50):
        super().__init__()
        self.tick_count = 0 #tracks how many ticks have passed 
        self.max_ticks = max_ticks
        self.is_running = False #controls wether the simulaition loop is running 
        self.entities = [] #all animals / entities in the simulaiton 
        self.environments = []
        self.food_manager = None  # NEW: Food manager reference
        
        # Stats tracking
        self.stats = {
            'births': 0,
            'deaths': 0,
            'entities_by_species': defaultdict(int),
            'initial_population': 0,
        }

    def add_entity(self, entity):
        self.entities.append(entity)
        species = entity.__class__.__name__
        self.stats['entities_by_species'][species] += 1
        
    def add_environment(self, environment):
        self.environments.append(environment)
    
    def set_food_manager(self, food_manager):
        """Set the food manager for this simulation"""
        self.food_manager = food_manager
    
    def set_reproduction_manager(self, reproduction_manager):
        """Set the reproduction manager for this simulation"""
        self.reproduction_manager = reproduction_manager
    
    def _count_current_population(self):
        """Count living entities by species"""
        population = defaultdict(int)
        for entity in self.entities:
            if entity.is_alive:
                species = entity.__class__.__name__
                population[species] += 1
        return population
    
    def _print_population_summary(self):
        """Print current population statistics"""
        population = self._count_current_population()
        total = sum(population.values())
        print(f"   📊 Population: {total} | ", end="")
        species_strs = [f"{species}: {count}" for species, count in sorted(population.items())]
        print(" | ".join(species_strs))

    def run(self):
        try:
            self.is_running = True
            self.stats['initial_population'] = len([e for e in self.entities if e.is_alive])
            
            print("\n" + "="*60)
            print("🌍 SAFARI SIMULATION ENGINE STARTED")
            print(f"   Initial Population: {self.stats['initial_population']}")
            print(f"   Max Duration: {self.max_ticks} ticks")
            print("="*60 + "\n")
            
            while self.is_running:
                self.tick_count += 1 #move time forward 
                
                # --- DAY/NIGHT CLOCK ---
                current_hour = self.tick_count % TICKS_PER_DAY
                
                if current_hour == SUNRISE_HOUR:
                    print("\n🌅 The sun is rising over the savanna...")
                elif current_hour == SUNSET_HOUR:
                    print("\n🌇 The sun is setting. It is getting dark...")

                print(f"--- ⏰ Tick {self.tick_count} | Hour: {current_hour}:00 ---")
                
                # NEW: Regrow food sources
                if self.food_manager:
                    self.food_manager.regrow_all()
                
                # NEW: Update reproduction cooldowns
                if hasattr(self, 'reproduction_manager') and self.reproduction_manager:
                    self.reproduction_manager.tick_cooldowns()
                
                # 1. Update entities
                for entity in self.entities:
                    if entity.is_alive:
                        # Store current tick for logging
                        if hasattr(entity, 'current_tick'):
                            entity.current_tick = self.tick_count
                        
                        entity.update(current_hour, self.entities)  #Update the animal (pass time + all entities for interactions like hunting)
                       
                        
                        # --- Colorize the State ---
                        if entity.state == "DEAD":
                            c_state = Colors.dead(entity.state)
                        elif entity.state == "DESPERATE":  # <--- NEW Desperation state!
                            c_state = Colors.desperate(entity.state)
                        elif entity.state == "SLEEPING":
                            c_state = f"{Colors.MAGENTA}{entity.state}{Colors.RESET}"
                        elif entity.state == "SEEKING_WATER":
                            c_state = f"{Colors.CYAN}{entity.state}{Colors.RESET}"
                        elif entity.state == "DRINKING":
                            c_state = f"{Colors.BLUE}{entity.state}{Colors.RESET}"
                        elif entity.state == "EATING":  # NEW: Eating state color
                            c_state = f"{Colors.GREEN}{entity.state}{Colors.RESET}"
                        elif entity.state == "HUNTING":
                            c_state = f"{Colors.RED}{entity.state}{Colors.RESET}"
                        elif entity.state == "FLEEING":
                            c_state = f"{Colors.RED}{entity.state}{Colors.RESET}"
                        elif entity.state == "MATING":
                            c_state = f"{Colors.MAGENTA}{entity.state}{Colors.RESET}"
                        else:
                            c_state = f"{Colors.GREEN}{entity.state}{Colors.RESET}"

                        # --- Build the Status String with Progress Bars ---
                        status_parts = [f"State: {c_state}"]
                        
                        if hasattr(entity, "thirst"):
                            # Injecting the visual Thirst bar!
                            bar = Colors.bar(entity.thirst, MAX_THIRST)
                            status_parts.insert(0, f"Thirst: {bar} {entity.thirst}")
                            
                        if hasattr(entity, "hunger"):
                            # Injecting the visual Hunger bar!
                            bar = Colors.bar(entity.hunger, MAX_HUNGER)
                            status_parts.insert(0, f"Hunger: {bar} {entity.hunger}")
                            
                        print(f"   [{Colors.state(entity.name)} {entity.id}] @({entity.x}, {entity.y}) | " + " | ".join(status_parts))

                    # 2. Handle Environment Interactions
                    for env in self.environments:
                        # Check if animal finished drinking
                        if entity.state != "DRINKING" and entity in getattr(env, 'current_drinkers', []):
                            env.finish_drinking(entity)

                        # Check if animal wants to drink and is at the right location
                        if entity.state in ["SEEKING_WATER", "WAITING_IN_LINE"]:
                            if entity.x == env.x and entity.y == env.y:
                                env.try_to_drink(entity)
                    
                    # NEW: Handle food interactions for herbivores
                    if entity.state == "EATING" and hasattr(entity, "target_food"):
                        # Eating state handles food in the state itself
                        pass

                # Print population summary every 10 ticks
                if self.tick_count % 10 == 0:
                    self._print_population_summary()
                
                # 3. Stop condition
                if self.tick_count >= self.max_ticks:
                    self.is_running = False
                    break
                    
                # 4. Wait for next tick
                time.sleep(TICK_RATE)
                
            # Simulation finished - print final summary
            self._print_final_summary()
            
        except Exception as e:
            print(f"\n❌ ERROR in simulation: {str(e)}")
            import traceback
            traceback.print_exc()
            self.is_running = False
            raise
    
    def _print_final_summary(self):
        """Print comprehensive simulation summary at the end"""
        from engine.database_utils import DatabaseRecorder
        
        final_population = self._count_current_population()
        total_final = sum(final_population.values())
        total_dead = len([e for e in self.entities if not e.is_alive])
        
        # Record simulation run metadata
        DatabaseRecorder.record_simulation_run(
            max_ticks=self.max_ticks,
            initial_population=self.stats['initial_population'],
            final_population=total_final,
            total_deaths=total_dead,
            total_births=total_final - self.stats['initial_population'] + total_dead
        )
        
        print("\n" + "="*60)
        print("🛑 SIMULATION COMPLETE")
        print("="*60)
        print(f"\n📈 FINAL STATISTICS:")
        print(f"   Duration: {self.tick_count} ticks")
        print(f"   Initial Population: {self.stats['initial_population']}")
        print(f"   Final Population: {total_final}")
        print(f"   Deaths: {total_dead}")
        print(f"\n🦁 POPULATION BY SPECIES:")
        for species in sorted(final_population.keys()):
            count = final_population[species]
            print(f"   {species}: {count}")
        
        print("\n📊 RESOURCES:")
        if self.food_manager and hasattr(self.food_manager, 'sources'):
            total_grass = sum(s.quantity for s in self.food_manager.sources)
            print(f"   Total Grass Available: {total_grass} units")
            print(f"   Grass Patches: {len(self.food_manager.sources)}")
        
        print("="*60 + "\n")
    
    def _validate_entities(self):
        """Validate entity state - catch and log anomalies"""
        anomalies = []
        for entity in self.entities:
            if not hasattr(entity, 'is_alive'):
                anomalies.append(f"Entity {entity.id} missing is_alive attribute")
            elif entity.is_alive and not hasattr(entity, 'hunger'):
                anomalies.append(f"Living entity {entity.id} missing hunger attribute")
            elif entity.is_alive and not hasattr(entity, 'thirst'):
                anomalies.append(f"Living entity {entity.id} missing thirst attribute")
        
        if anomalies:
            print(f"⚠️  Validation warnings ({len(anomalies)}):")
            for msg in anomalies[:5]:  # Show first 5
                print(f"   - {msg}")
            if len(anomalies) > 5:
                print(f"   ... and {len(anomalies) - 5} more")
        
        return len(anomalies) == 0