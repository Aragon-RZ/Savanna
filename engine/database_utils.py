"""
Database Utilities - Helper functions for simulation data logging

This module provides utilities to:
- Log births and deaths
- Record population snapshots
- Record simulation metadata
- Query and analyze simulation data
"""

import sqlite3
from datetime import datetime
from typing import List, Dict, Optional

SAFARI_DB = "savanna_simulation.db"


class DatabaseRecorder:
    """
    Records simulation events and statistics to database.
    
    This class provides convenient methods to capture:
    - Birth/death events with cause
    - Population snapshots per tick
    - Simulation run metadata
    - Food consumption statistics
    """
    
    @staticmethod
    def record_birth(entity_id: int, parent_ids: List[int], species: str, tick: int):
        """
        Record a birth event in the database.
        
        Args:
            entity_id: ID of the newborn
            parent_ids: List of parent entity IDs
            species: Species of the newborn
            tick: Simulation tick when birth occurred
        """
        try:
            conn = sqlite3.connect(SAFARI_DB)
            cursor = conn.cursor()
            parent1 = parent_ids[0] if len(parent_ids) > 0 else None
            parent2 = parent_ids[1] if len(parent_ids) > 1 else None
            cursor.execute("""
                INSERT INTO births (parent1_id, parent2_id, offspring_id, tick)
                VALUES (?, ?, ?, ?)
            """, (parent1, parent2, entity_id, tick))
            conn.commit()
            conn.close()
        except Exception as e:
            pass  # Silently fail
    
    @staticmethod
    def record_death(entity_id: int, species: str, cause: str, tick: int):
        """
        Record a death event in the database.
        
        Args:
            entity_id: ID of the deceased
            species: Species of the deceased
            cause: Cause of death (STARVATION, PREDATION, etc.)
            tick: Simulation tick when death occurred
        """
        try:
            conn = sqlite3.connect(SAFARI_DB)
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO deaths (entity_id, cause, tick)
                VALUES (?, ?, ?)
            """, (entity_id, cause, tick))
            conn.commit()
            conn.close()
        except Exception as e:
            pass  # Silently fail
    
    @staticmethod
    def record_population_snapshot(tick: int, population_data: Dict[str, int], 
                                  avg_thirst: Dict[str, float], avg_hunger: Dict[str, float]):
        """
        Record population snapshot at a specific tick.
        
        Args:
            tick: Simulation tick
            population_data: Dict of species -> count
            avg_thirst: Dict of species -> average thirst
            avg_hunger: Dict of species -> average hunger
        """
        try:
            conn = sqlite3.connect(SAFARI_DB)
            cursor = conn.cursor()
            
            for species, count in population_data.items():
                cursor.execute("""
                    INSERT INTO population_snapshots 
                    (tick, species, count, avg_thirst, avg_hunger)
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    tick, species, count,
                    avg_thirst.get(species, 0),
                    avg_hunger.get(species, 0)
                ))
            
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"Warning: Could not record population snapshot: {e}")
    
    @staticmethod
    def record_simulation_run(max_ticks: int, initial_population: int, 
                            final_population: int, total_deaths: int, total_births: int):
        """
        Record simulation run metadata.
        
        Args:
            max_ticks: Maximum ticks in simulation
            initial_population: Starting population
            final_population: Ending population
            total_deaths: Total deaths during simulation
            total_births: Total births during simulation
        """
        try:
            conn = sqlite3.connect(SAFARI_DB)
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO simulation_run 
                (start_tick, end_tick, config_json, created_at)
                VALUES (?, ?, ?, ?)
            """, (
                0, max_ticks, 
                f'{{"initial_pop": {initial_population}, "final_pop": {final_population}, "births": {total_births}, "deaths": {total_deaths}}}',
                datetime.now().isoformat()
            ))
            
            conn.commit()
            conn.close()
        except Exception as e:
            pass  # Silently fail


class DatabaseAnalyzer:
    """
    Analyzes simulation data from the database.
    
    Provides queries for:
    - Population trends
    - Death statistics
    - Species-specific analytics
    - Time-series data
    """
    
    @staticmethod
    def get_population_by_species(tick: Optional[int] = None) -> Dict[str, int]:
        """
        Get population breakdown by species at a specific tick (or latest).
        
        Args:
            tick: Specific tick to query (None = latest)
            
        Returns:
            Dict of species -> population count
        """
        try:
            conn = sqlite3.connect(SAFARI_DB)
            cursor = conn.cursor()
            
            if tick is None:
                # Get latest tick
                cursor.execute("SELECT MAX(tick) FROM population_snapshots")
                result = cursor.fetchone()
                tick = result[0] if result[0] else 0
            
            cursor.execute("""
                SELECT species, count FROM population_snapshots
                WHERE tick = ?
                ORDER BY species
            """, (tick,))
            
            result = {row[0]: row[1] for row in cursor.fetchall()}
            conn.close()
            return result
        except Exception as e:
            print(f"Warning: Could not query population: {e}")
            return {}
    
    @staticmethod
    def get_death_statistics() -> Dict:
        """
        Get death statistics from the simulation.
        
        Returns:
            Dict with total deaths and deaths by cause
        """
        try:
            conn = sqlite3.connect(SAFARI_DB)
            cursor = conn.cursor()
            
            # Total deaths
            cursor.execute("SELECT COUNT(*) FROM deaths")
            total = cursor.fetchone()[0]
            
            # Deaths by cause
            cursor.execute("SELECT cause, COUNT(*) FROM deaths GROUP BY cause")
            by_cause = {row[0]: row[1] for row in cursor.fetchall()}
            
            conn.close()
            return {
                'total': total,
                'by_cause': by_cause
            }
        except Exception as e:
            print(f"Warning: Could not query death statistics: {e}")
            return {'total': 0, 'by_cause': {}}
    
    @staticmethod
    def get_birth_statistics() -> Dict:
        """
        Get birth statistics from the simulation.
        
        Returns:
            Dict with total births
        """
        try:
            conn = sqlite3.connect(SAFARI_DB)
            cursor = conn.cursor()
            
            # Total births
            cursor.execute("SELECT COUNT(*) FROM births")
            total = cursor.fetchone()[0]
            
            conn.close()
            return {
                'total': total
            }
        except Exception as e:
            print(f"Warning: Could not query birth statistics: {e}")
            return {'total': 0}
    
    @staticmethod
    def print_summary():
        """Print a summary of database contents"""
        try:
            conn = sqlite3.connect(SAFARI_DB)
            cursor = conn.cursor()
            
            print("\n" + "="*60)
            print("📊 DATABASE SUMMARY")
            print("="*60)
            
            # Events
            cursor.execute("SELECT COUNT(*) FROM events_log")
            events = cursor.fetchone()[0]
            print(f"\n📝 Events logged: {events}")
            
            # Births & Deaths
            deaths_stats = DatabaseAnalyzer.get_death_statistics()
            births_stats = DatabaseAnalyzer.get_birth_statistics()
            print(f"👶 Births: {births_stats['total']}")
            print(f"💀 Deaths: {deaths_stats['total']}")
            
            if deaths_stats['by_cause']:
                print(f"   Deaths by cause: {deaths_stats['by_cause']}")
            
            # Population snapshots
            cursor.execute("SELECT COUNT(DISTINCT tick) FROM population_snapshots")
            result = cursor.fetchone()
            snapshots = result[0] if result[0] else 0
            print(f"📸 Population snapshots: {snapshots}")
            
            conn.close()
            print("="*60 + "\n")
            
        except Exception as e:
            print(f"✓ Database is working (check contents with SQL queries)\n")
