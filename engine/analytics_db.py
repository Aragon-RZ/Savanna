"""
Enhanced Database Schema - Environmental state tracking and analytics

This module extends the database with tables for:
- Environmental state per tick (grass levels, water, weather)
- Resource events (regrowth, depletion)
- Daily aggregates (population, births, deaths per day)
- Species statistics (aggregate analytics)
- Herd dynamics (grouping patterns)
"""

import sqlite3
from typing import Dict, List, Optional


class EnhancedSchema:
    """Creates enhanced database tables for comprehensive analytics"""
    
    @staticmethod
    def create_tables(db_path: str = "savanna_simulation.db"):
        """
        Create all enhanced schema tables.
        
        New tables:
        - environmental_state: Per-tick environmental conditions
        - resource_events: When resources grow/deplete
        - daily_aggregates: Daily summaries
        - species_statistics: Per-species aggregate stats
        - herd_dynamics: Population grouping patterns
        """
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # ==========================================
        # ENVIRONMENTAL STATE TABLE
        # ==========================================
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS environmental_state (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tick INTEGER NOT NULL,
                season TEXT NOT NULL,
                current_weather TEXT NOT NULL,
                temperature REAL DEFAULT 25.0,
                total_grass INTEGER DEFAULT 0,
                total_water INTEGER DEFAULT 0,
                water_multiplier REAL DEFAULT 1.0,
                food_regrow_rate REAL DEFAULT 1.0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # ==========================================
        # RESOURCE EVENTS TABLE
        # ==========================================
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS resource_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tick INTEGER NOT NULL,
                resource_type TEXT NOT NULL,
                event_type TEXT NOT NULL,
                location_x INTEGER,
                location_y INTEGER,
                amount INTEGER,
                reason TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # ==========================================
        # DAILY AGGREGATES TABLE
        # ==========================================
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS daily_aggregates (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                day INTEGER NOT NULL,
                population_start INTEGER DEFAULT 0,
                population_end INTEGER DEFAULT 0,
                births INTEGER DEFAULT 0,
                deaths INTEGER DEFAULT 0,
                avg_hunger REAL DEFAULT 0,
                avg_thirst REAL DEFAULT 0,
                total_food_consumed INTEGER DEFAULT 0,
                total_water_consumed INTEGER DEFAULT 0,
                predation_events INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # ==========================================
        # SPECIES STATISTICS TABLE
        # ==========================================
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS species_statistics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                species TEXT NOT NULL,
                total_born INTEGER DEFAULT 0,
                total_died INTEGER DEFAULT 0,
                avg_lifespan REAL DEFAULT 0,
                peak_population INTEGER DEFAULT 0,
                extinction_risk TEXT DEFAULT 'low',
                primary_diet TEXT,
                nocturnal BOOLEAN DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(species)
            )
        """)
        
        # ==========================================
        # HERD DYNAMICS TABLE
        # ==========================================
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS herd_dynamics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tick INTEGER NOT NULL,
                species TEXT NOT NULL,
                herd_size INTEGER DEFAULT 0,
                avg_herd_proximity REAL DEFAULT 0,
                predator_nearby BOOLEAN DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        conn.commit()
        conn.close()
        print("✅ Enhanced database schema created")


class EnvironmentalStateRecorder:
    """Records environmental state per tick"""
    
    @staticmethod
    def record_state(tick: int, season: str, weather: str, temperature: float,
                    total_grass: int, total_water: int, water_mult: float,
                    food_regrow: float, db_path: str = "savanna_simulation.db"):
        """Record environmental state for a tick"""
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO environmental_state
                (tick, season, current_weather, temperature, total_grass, total_water,
                 water_multiplier, food_regrow_rate)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (tick, season, weather, temperature, total_grass, total_water, water_mult, food_regrow))
            conn.commit()
            conn.close()
        except Exception as e:
            pass  # Silently fail


class ResourceEventRecorder:
    """Records resource events (regrowth, depletion, consumption)"""
    
    @staticmethod
    def record_event(tick: int, resource_type: str, event_type: str,
                    x: Optional[int] = None, y: Optional[int] = None,
                    amount: Optional[int] = None, reason: str = "",
                    db_path: str = "savanna_simulation.db"):
        """Record a resource event"""
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO resource_events
                (tick, resource_type, event_type, location_x, location_y, amount, reason)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (tick, resource_type, event_type, x, y, amount, reason))
            conn.commit()
            conn.close()
        except Exception as e:
            pass  # Silently fail


class DailyAggregateRecorder:
    """Records daily summary statistics"""
    
    @staticmethod
    def record_day(day: int, pop_start: int, pop_end: int, births: int, deaths: int,
                  avg_hunger: float, avg_thirst: float, food_consumed: int,
                  water_consumed: int, predation: int,
                  db_path: str = "savanna_simulation.db"):
        """Record daily aggregate statistics"""
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO daily_aggregates
                (day, population_start, population_end, births, deaths, avg_hunger,
                 avg_thirst, total_food_consumed, total_water_consumed, predation_events)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (day, pop_start, pop_end, births, deaths, avg_hunger,
                  avg_thirst, food_consumed, water_consumed, predation))
            conn.commit()
            conn.close()
        except Exception as e:
            pass  # Silently fail


class SpeciesStatisticsRecorder:
    """Records aggregate statistics per species"""
    
    @staticmethod
    def update_species_stats(species: str, births: int, deaths: int,
                            avg_lifespan: float, peak_pop: int,
                            extinction_risk: str = "low",
                            primary_diet: str = "omnivore",
                            nocturnal: bool = False,
                            db_path: str = "savanna_simulation.db"):
        """Update or create species statistics"""
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO species_statistics
                (species, total_born, total_died, avg_lifespan, peak_population,
                 extinction_risk, primary_diet, nocturnal)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (species, births, deaths, avg_lifespan, peak_pop,
                  extinction_risk, primary_diet, nocturnal))
            conn.commit()
            conn.close()
        except Exception as e:
            pass  # Silently fail


class HerdDynamicsRecorder:
    """Records herd grouping patterns and dynamics"""
    
    @staticmethod
    def record_herd(tick: int, species: str, herd_size: int, avg_proximity: float,
                   predator_nearby: bool = False,
                   db_path: str = "savanna_simulation.db"):
        """Record herd dynamics snapshot"""
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO herd_dynamics
                (tick, species, herd_size, avg_herd_proximity, predator_nearby)
                VALUES (?, ?, ?, ?, ?)
            """, (tick, species, herd_size, avg_proximity, int(predator_nearby)))
            conn.commit()
            conn.close()
        except Exception as e:
            pass  # Silently fail


class AnalyticsQueries:
    """Pre-built analytics queries"""
    
    @staticmethod
    def get_population_trend(db_path: str = "savanna_simulation.db") -> List[Dict]:
        """Get population trends over time"""
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute("""
                SELECT day, population_start, population_end, births, deaths
                FROM daily_aggregates
                ORDER BY day
            """)
            results = []
            for row in cursor.fetchall():
                results.append({
                    'day': row[0],
                    'pop_start': row[1],
                    'pop_end': row[2],
                    'births': row[3],
                    'deaths': row[4]
                })
            conn.close()
            return results
        except Exception as e:
            return []
    
    @staticmethod
    def get_extinction_risks(db_path: str = "savanna_simulation.db") -> Dict:
        """Get extinction risk by species"""
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute("""
                SELECT species, extinction_risk, peak_population
                FROM species_statistics
                ORDER BY species
            """)
            results = {row[0]: {'risk': row[1], 'peak': row[2]} for row in cursor.fetchall()}
            conn.close()
            return results
        except Exception as e:
            return {}
    
    @staticmethod
    def get_resource_availability(db_path: str = "savanna_simulation.db") -> Dict:
        """Get resource availability summary"""
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute("""
                SELECT season, AVG(total_grass) as avg_grass, AVG(total_water) as avg_water
                FROM environmental_state
                GROUP BY season
            """)
            results = {row[0]: {'grass': row[1], 'water': row[2]} for row in cursor.fetchall()}
            conn.close()
            return results
        except Exception as e:
            return {}
