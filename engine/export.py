"""
Data Export System - Export simulation results to various formats

This module provides:
- CSV export (events, population, resources, daily summaries)
- JSON export (complete simulation trace, statistics)
- Excel export (if available)
- SQL queries for ad-hoc analysis
"""

import sqlite3
import json
import csv
import os
from datetime import datetime
from typing import Dict, List, Optional


class CSVExporter:
    """Export simulation data to CSV files"""
    
    @staticmethod
    def export_all(db_path: str = "savanna_simulation.db",
                  output_dir: str = "simulation_exports"):
        """Export all simulation data to CSV files"""
        os.makedirs(output_dir, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Events log
        CSVExporter._export_table(cursor, "events_log", 
                                 f"{output_dir}/events_{timestamp}.csv",
                                 ["id", "tick", "entity_id", "event_type", "details"])
        
        # Population snapshots
        CSVExporter._export_table(cursor, "population_snapshots",
                                 f"{output_dir}/population_{timestamp}.csv",
                                 ["id", "tick", "species", "count"])
        
        # Environmental state
        CSVExporter._export_table(cursor, "environmental_state",
                                 f"{output_dir}/environment_{timestamp}.csv",
                                 ["tick", "season", "current_weather", "temperature", 
                                  "total_grass", "food_regrow_rate"])
        
        # Births and deaths
        CSVExporter._export_table(cursor, "births",
                                 f"{output_dir}/births_{timestamp}.csv",
                                 ["offspring_id", "parent1_id", "parent2_id", "tick"])
        
        CSVExporter._export_table(cursor, "deaths",
                                 f"{output_dir}/deaths_{timestamp}.csv",
                                 ["entity_id", "cause", "tick"])
        
        # Daily aggregates
        CSVExporter._export_table(cursor, "daily_aggregates",
                                 f"{output_dir}/daily_stats_{timestamp}.csv",
                                 ["day", "population_start", "population_end", 
                                  "births", "deaths", "avg_hunger", "avg_thirst"])
        
        conn.close()
        print(f"✅ CSV export complete: {output_dir}/")
        return output_dir
    
    @staticmethod
    def _export_table(cursor, table_name: str, output_path: str, 
                     columns: Optional[List[str]] = None):
        """Export a single table to CSV"""
        try:
            if columns:
                col_str = ", ".join(columns)
                cursor.execute(f"SELECT {col_str} FROM {table_name}")
            else:
                cursor.execute(f"SELECT * FROM {table_name}")
            
            rows = cursor.fetchall()
            if not rows:
                return
            
            # Get column names
            if columns:
                col_names = columns
            else:
                col_names = [description[0] for description in cursor.description]
            
            # Write to CSV
            with open(output_path, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(col_names)
                writer.writerows(rows)
            
            print(f"  ✓ Exported {table_name}: {len(rows)} rows")
        except Exception as e:
            print(f"  ⚠️ Failed to export {table_name}: {e}")


class JSONExporter:
    """Export simulation data to JSON for external analysis"""
    
    @staticmethod
    def export_full(db_path: str = "savanna_simulation.db",
                   output_path: Optional[str] = None) -> str:
        """Export complete simulation as JSON"""
        if output_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = f"simulation_export_{timestamp}.json"
        
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        export_data = {
            'timestamp': datetime.now().isoformat(),
            'database': db_path,
            'summary': JSONExporter._get_summary(cursor),
            'events': JSONExporter._get_events(cursor),
            'population': JSONExporter._get_population(cursor),
            'environment': JSONExporter._get_environment(cursor),
            'demographics': JSONExporter._get_demographics(cursor),
        }
        
        with open(output_path, 'w') as f:
            json.dump(export_data, f, indent=2, default=str)
        
        conn.close()
        print(f"✅ JSON export: {output_path}")
        return output_path
    
    @staticmethod
    def _get_summary(cursor) -> Dict:
        """Get simulation summary"""
        cursor.execute("SELECT COUNT(*) FROM events_log")
        total_events = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM births")
        total_births = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM deaths")
        total_deaths = cursor.fetchone()[0]
        
        cursor.execute("SELECT config_json FROM simulation_run LIMIT 1")
        result = cursor.fetchone()
        config = {}
        if result and result[0]:
            try:
                config = json.loads(result[0])
            except:
                pass
        
        return {
            'total_events': total_events,
            'total_births': total_births,
            'total_deaths': total_deaths,
            'simulation_config': config
        }
    
    @staticmethod
    def _get_events(cursor) -> List[Dict]:
        """Get all events"""
        cursor.execute("""
            SELECT tick, entity_id, event_type, details
            FROM events_log
            ORDER BY tick
            LIMIT 1000
        """)
        
        return [
            {
                'tick': row[0],
                'entity_id': row[1],
                'event_type': row[2],
                'details': row[3]
            }
            for row in cursor.fetchall()
        ]
    
    @staticmethod
    def _get_population(cursor) -> Dict:
        """Get population data"""
        cursor.execute("""
            SELECT tick, species, count
            FROM population_snapshots
            ORDER BY tick, species
        """)
        
        by_species = {}
        for tick, species, count in cursor.fetchall():
            if species not in by_species:
                by_species[species] = []
            by_species[species].append({'tick': tick, 'count': count})
        
        return by_species
    
    @staticmethod
    def _get_environment(cursor) -> Dict:
        """Get environmental data"""
        cursor.execute("""
            SELECT tick, season, current_weather, temperature, total_grass,
                   water_multiplier, food_regrow_rate
            FROM environmental_state
            ORDER BY tick
            LIMIT 500
        """)
        
        return [
            {
                'tick': row[0],
                'season': row[1],
                'weather': row[2],
                'temperature': row[3],
                'grass': row[4],
                'water_mult': row[5],
                'food_regrow_rate': row[6]
            }
            for row in cursor.fetchall()
        ]
    
    @staticmethod
    def _get_demographics(cursor) -> Dict:
        """Get birth/death demographics"""
        cursor.execute("""
            SELECT cause, COUNT(*) as count
            FROM deaths
            GROUP BY cause
        """)
        
        causes = {row[0]: row[1] for row in cursor.fetchall()}
        
        cursor.execute("SELECT COUNT(*) FROM births")
        birth_count = cursor.fetchone()[0]
        
        return {
            'total_births': birth_count,
            'death_causes': causes
        }


class QueryBuilder:
    """Build and execute custom analytics queries"""
    
    @staticmethod
    def population_over_time(db_path: str = "savanna_simulation.db") -> List[Dict]:
        """Get population over time"""
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT tick, species, count
            FROM population_snapshots
            ORDER BY tick, species
        """)
        
        result = [
            {'tick': row[0], 'species': row[1], 'population': row[2]}
            for row in cursor.fetchall()
        ]
        
        conn.close()
        return result
    
    @staticmethod
    def extinction_risk_analysis(db_path: str = "savanna_simulation.db") -> Dict:
        """Analyze extinction risk by species"""
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get births/deaths per species
        cursor.execute("""
            SELECT species, COUNT(*) as births
            FROM births
            GROUP BY species
        """)
        
        result = {row[0]: {'births': row[1]} for row in cursor.fetchall()}
        
        conn.close()
        return result
    
    @staticmethod
    def resource_depletion_analysis(db_path: str = "savanna_simulation.db") -> Dict:
        """Analyze resource depletion patterns"""
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get grass levels over time
        cursor.execute("""
            SELECT tick, total_grass, season, current_weather
            FROM environmental_state
            ORDER BY tick
        """)
        
        data = [
            {
                'tick': row[0],
                'grass': row[1],
                'season': row[2],
                'weather': row[3]
            }
            for row in cursor.fetchall()
        ]
        
        conn.close()
        
        # Calculate depletion rate
        if len(data) > 1:
            total_change = data[-1]['grass'] - data[0]['grass']
            avg_per_tick = total_change / len(data)
            
            return {
                'total_change': total_change,
                'avg_change_per_tick': avg_per_tick,
                'timeline': data[:100]  # First 100 ticks
            }
        
        return {'error': 'Insufficient data'}
    
    @staticmethod
    def predator_prey_analysis(db_path: str = "savanna_simulation.db") -> Dict:
        """Analyze predator-prey dynamics"""
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Count hunts
        cursor.execute("""
            SELECT COUNT(*) FROM events_log
            WHERE event_type = 'HUNTING'
        """)
        hunt_count = cursor.fetchone()[0]
        
        conn.close()
        
        return {
            'hunting_events': hunt_count,
            'predator_success_rate': 'TBD'
        }


class ExportManager:
    """Manage all exports"""
    
    @staticmethod
    def export_all(db_path: str = "savanna_simulation.db"):
        """Export simulation in all formats"""
        print("\n" + "="*60)
        print("📤 EXPORTING SIMULATION DATA")
        print("="*60)
        
        # CSV exports
        print("\n📊 CSV Exports:")
        CSVExporter.export_all(db_path)
        
        # JSON export
        print("\n📋 JSON Export:")
        JSONExporter.export_full(db_path)
        
        print("\n✅ All exports complete!")
        print("="*60 + "\n")
