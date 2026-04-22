"""
Analytics System - Data collection and export

This module provides analytics for the simulation:
- Population statistics over time
- Event summaries
- Data export to CSV/JSON

Usage:
    analytics = SimulationAnalytics()
    analytics.record_snapshot(tick, entities, food_manager)
    
    # At end of simulation
    analytics.export_csv()
    analytics.print_summary()
"""

import json
import csv
import os
from datetime import datetime
from typing import List, Dict


class SimulationAnalytics:
    """
    Collects and analyzes simulation data.
    
    Data collected:
    - Population per species over time
    - State distribution over time
    - Births and deaths
    - Food consumption
    - Weather stats
    """
    
    def __init__(self):
        """Initialize analytics"""
        self.population_snapshots: List[Dict] = []
        self.state_snapshots: List[Dict] = []
        self.births: List[Dict] = []
        self.deaths: List[Dict] = []
        self.food_consumption: List[Dict] = []
        self.weather_snapshots: List[Dict] = []
        
        # Running stats
        self.total_born = 0
        self.total_died = 0
        self.food_eaten = 0
        self.start_time = None
        self.end_time = None
    
    def start(self):
        """Mark simulation start"""
        self.start_time = datetime.now()
    
    def end(self):
        """Mark simulation end"""
        self.end_time = datetime.now()
    
    def record_population(self, tick: int, entities: list):
        """
        Record population snapshot.
        
        Args:
            tick: Current tick
            entities: All entities in simulation
        """
        # Count by species
        species_counts: Dict[str, int] = {}
        species_thirst: Dict[str, List] = {}
        species_hunger: Dict[str, List] = {}
        
        for entity in entities:
            if not entity.is_alive:
                continue
            
            species = type(entity).__name__
            
            # Count
            species_counts[species] = species_counts.get(species, 0) + 1
            
            # Stats
            if hasattr(entity, 'thirst'):
                if species not in species_thirst:
                    species_thirst[species] = []
                species_thirst[species].append(entity.thirst)
            
            if hasattr(entity, 'hunger'):
                if species not in species_hunger:
                    species_hunger[species] = []
                species_hunger[species].append(entity.hunger)
        
        # Calculate averages
        snapshot = {"tick": tick, "counts": {}}
        
        for species, count in species_counts.items():
            avg_thirst = sum(species_thirst[species]) / count if count > 0 else 0
            avg_hunger = sum(species_hunger[species]) / count if count > 0 else 0
            
            snapshot["counts"][species] = {
                "count": count,
                "avg_thirst": avg_thirst,
                "avg_hunger": avg_hunger,
            }
        
        self.population_snapshots.append(snapshot)
    
    def record_states(self, tick: int, entities: list):
        """
        Record state distribution.
        
        Args:
            tick: Current tick
            entities: All entities
        """
        state_counts: Dict[str, int] = {}
        
        for entity in entities:
            if entity.is_alive and hasattr(entity, 'state'):
                state = entity.state
                state_counts[state] = state_counts.get(state, 0) + 1
        
        self.state_snapshots.append({
            "tick": tick,
            "states": state_counts
        })
    
    def record_birth(self, tick: int, species: str):
        """Record a birth"""
        self.births.append({"tick": tick, "species": species})
        self.total_born += 1
    
    def record_death(self, tick: int, species: str, cause: str):
        """Record a death"""
        self.deaths.append({
            "tick": tick,
            "species": species,
            "cause": cause
        })
        self.total_died += 1
    
    def record_food(self, tick: int, amount: int):
        """Record food consumption"""
        self.food_consumption.append({
            "tick": tick,
            "amount": amount
        })
        self.food_eaten += amount
    
    def record_weather(self, tick: int, weather):
        """Record weather snapshot"""
        self.weather_snapshots.append({
            "tick": tick,
            "season": weather.get_season().value,
            "temp": weather.temperature,
            "event": weather.get_event().value,
        })
    
    def get_population_trend(self, species: str) -> List[int]:
        """Get population trend for a species"""
        counts = []
        for snapshot in self.population_snapshots:
            if species in snapshot["counts"]:
                counts.append(snapshot["counts"][species]["count"])
            else:
                counts.append(0)
        return counts
    
    def get_extinction_risk(self) -> Dict[str, str]:
        """Get extinction risk for each species"""
        risk = {}
        
        if not self.population_snapshots:
            return risk
        
        latest = self.population_snapshots[-1]["counts"]
        
        for species, data in latest.items():
            count = data["count"]
            if count == 0:
                risk[species] = "EXTINCT"
            elif count <= 2:
                risk[species] = "CRITICAL"
            elif count <= 5:
                risk[species] = "ENDANGERED"
            else:
                risk[species] = "STABLE"
        
        return risk
    
    def export_json(self, filename: str = "savanna_analysis.json"):
        """
        Export all data to JSON file.
        
        Args:
            filename: Output filename
        """
        data = {
            "simulation": {
                "start_time": str(self.start_time),
                "end_time": str(self.end_time),
            },
            "population": self.population_snapshots,
            "states": self.state_snapshots,
            "births": self.births,
            "deaths": self.deaths,
            "food": {
                "total_eaten": self.food_eaten,
                "consumption": self.food_consumption,
            },
            "weather": self.weather_snapshots,
            "summary": {
                "total_born": self.total_born,
                "total_died": self.total_died,
            }
        }
        
        with open(filename, 'w') as f:
            json.dump(data, f, indent=2)
        
        print(f"✅ Exported to: {filename}")
    
    def export_csv(self, output_dir: str = "exports"):
        """
        Export data to CSV files.
        
        Args:
            output_dir: Directory for output files
        """
        os.makedirs(output_dir, exist_ok=True)
        
        # Population over time
        self._export_population_csv(output_dir)
        
        # Deaths
        self._export_deaths_csv(output_dir)
        
        # Summary
        self._export_summary_txt(output_dir)
        
        print(f"✅ Exported CSVs to: {output_dir}/")
    
    def _export_population_csv(self, output_dir: str):
        """Export population CSV"""
        filename = f"{output_dir}/population.csv"
        
        with open(filename, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(["tick", "species", "count", "avg_thirst", "avg_hunger"])
            
            for snapshot in self.population_snapshots:
                tick = snapshot["tick"]
                for species, data in snapshot["counts"].items():
                    writer.writerow([
                        tick,
                        species,
                        data["count"],
                        f"{data['avg_thirst']:.1f}",
                        f"{data['avg_hunger']:.1f}",
                    ])
    
    def _export_deaths_csv(self, output_dir: str):
        """Export deaths CSV"""
        filename = f"{output_dir}/deaths.csv"
        
        with open(filename, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(["tick", "species", "cause"])
            
            for death in self.deaths:
                writer.writerow([
                    death["tick"],
                    death["species"],
                    death["cause"],
                ])
    
    def _export_summary_txt(self, output_dir: str):
        """Export summary text file"""
        filename = f"{output_dir}/summary.txt"
        
        risk = self.get_extinction_risk()
        
        with open(filename, 'w') as f:
            f.write("="*50 + "\n")
            f.write("SAVANNA SIMULATION SUMMARY\n")
            f.write("="*50 + "\n\n")
            
            f.write(f"Duration: {self.start_time} to {self.end_time}\n\n")
            
            f.write("POPULATION STATISTICS:\n")
            f.write("-"*30 + "\n")
            for species, status in risk.items():
                count = 0
                for snap in self.population_snapshots:
                    if species in snap["counts"]:
                        count = snap["counts"][species]["count"]
                f.write(f"  {species}: {count} ({status})\n")
            
            f.write("\nBIRTHS/DEATHS:\n")
            f.write("-"*30 + "\n")
            f.write(f"  Total Born: {self.total_born}\n")
            f.write(f"  Total Died: {self.total_died}\n")
            
            f.write("\nFOOD CONSUMPTION:\n")
            f.write("-"*30 + "\n")
            f.write(f"  Total Eaten: {self.food_eaten}\n")
            
            f.write("\nEXTINCTION RISK:\n")
            f.write("-"*30 + "\n")
            for species, status in risk.items():
                f.write(f"  {species}: {status}\n")
    
    def print_summary(self):
        """Print summary to console"""
        print("\n" + "="*50)
        print("SIMULATION SUMMARY")
        print("="*50)
        
        print(f"\nBorn: {self.total_born}")
        print(f"Died: {self.total_died}")
        print(f"Food Eaten: {self.food_eaten}")
        
        risk = self.get_extinction_risk()
        print("\nExtinction Risk:")
        for species, status in risk.items():
            print(f"  {species}: {status}")
        
        print("\nPopulation Trends:")
        for species in ["Zebra", "Lion", "Elephant"]:
            trend = self.get_population_trend(species)
            if trend:
                print(f"  {species}: {trend[-1]} ({'+' if trend[-1] > trend[0] else ''}{trend[-1] - trend[0]})")


# ==========================================
# CONVENIENCE FUNCTIONS
# ==========================================

def create_analytics() -> SimulationAnalytics:
    """Create new analytics tracker"""
    return SimulationAnalytics()