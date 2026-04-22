"""
SQLite Database Manager for Safari Simulation

This module provides SQLite database connection and operations
for logging simulation events, entities, and analytics.

Database Schema:
- species: Animal species definitions
- entities: All entities in simulation
- events_log: All events (state changes, actions)
- food_sources: Food patches in environment
- births: Birth records
- deaths: Death records
- weather_log: Weather/season records
- simulation_run: Simulation metadata
- population_snapshots: Population over time
- behavior_stats: State distribution over time

Usage:
    from engine.database import DatabaseManager
    
    # Initialize database
    DatabaseManager.initialize()
    
    # Log events
    DatabaseManager.log_event(tick=1, entity_id=1, event_type="STATE_CHANGED", details="WANDERING")
    
    # Query data
    population = DatabaseManager.get_population_snapshot(tick=1)
"""

import sqlite3
import json
import os
from datetime import datetime
from typing import Optional, List, Dict, Any


SAFARI_DB = "savanna_simulation.db"


class DatabaseManager:
    """
    Singleton database manager for Safari Simulation.
    
    Provides:
    - Database initialization and schema creation
    - CRUD operations for entities
    - Event logging
    - Query methods for analytics
    """
    
    _connection: Optional[sqlite3.Connection] = None
    
    @classmethod
    def get_connection(cls) -> sqlite3.Connection:
        """Get or create database connection"""
        if cls._connection is None:
            cls._connection = sqlite3.connect(SAFARI_DB)
            cls._connection.row_factory = sqlite3.Row
        return cls._connection
    
    @classmethod
    def initialize(cls, db_path: str = SAFARI_DB):
        """
        Initialize database with schema.
        
        Creates all tables if they don't exist.
        
        Args:
            db_path: Path to SQLite database file
        """
        # Remove existing database for fresh start (optional - comment out to preserve data)
        # if os.path.exists(db_path):
        #     os.remove(db_path)
        
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # ==========================================
        # SPECIES TABLE
        # ==========================================
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS species (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                is_diurnal INTEGER DEFAULT 1,
                is_herd INTEGER DEFAULT 1,
                diet TEXT DEFAULT 'herbivore',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # ==========================================
        # ENTITIES TABLE
        # ==========================================
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS entities (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                entity_id INTEGER NOT NULL,
                species_id INTEGER,
                name TEXT NOT NULL,
                x INTEGER DEFAULT 0,
                y INTEGER DEFAULT 0,
                thirst INTEGER DEFAULT 0,
                hunger INTEGER DEFAULT 0,
                state TEXT DEFAULT 'IDLE',
                birth_tick INTEGER DEFAULT 0,
                death_tick INTEGER,
                is_alive INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (species_id) REFERENCES species(id)
            )
        """)
        
        # ==========================================
        # EVENTS LOG TABLE
        # ==========================================
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS events_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tick INTEGER NOT NULL,
                entity_id INTEGER,
                event_type TEXT NOT NULL,
                details TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # ==========================================
        # FOOD SOURCES TABLE
        # ==========================================
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS food_sources (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                x INTEGER NOT NULL,
                y INTEGER NOT NULL,
                food_type TEXT NOT NULL,
                quantity INTEGER DEFAULT 100,
                max_quantity INTEGER DEFAULT 100,
                regrow_rate INTEGER DEFAULT 5,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # ==========================================
        # BIRTHS TABLE
        # ==========================================
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS births (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                parent1_id INTEGER,
                parent2_id INTEGER,
                offspring_id INTEGER,
                tick INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (parent1_id) REFERENCES entities(id),
                FOREIGN KEY (parent2_id) REFERENCES entities(id),
                FOREIGN KEY (offspring_id) REFERENCES entities(id)
            )
        """)
        
        # ==========================================
        # DEATHS TABLE
        # ==========================================
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS deaths (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                entity_id INTEGER NOT NULL,
                cause TEXT NOT NULL,
                tick INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (entity_id) REFERENCES entities(id)
            )
        """)
        
        # ==========================================
        # WEATHER LOG TABLE
        # ==========================================
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS weather_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tick INTEGER NOT NULL,
                season TEXT NOT NULL,
                temperature REAL DEFAULT 25.0,
                water_multiplier REAL DEFAULT 1.0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # ==========================================
        # SIMULATION RUN TABLE
        # ==========================================
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS simulation_run (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                start_tick INTEGER DEFAULT 0,
                end_tick INTEGER,
                config_json TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # ==========================================
        # POPULATION SNAPSHOTS TABLE
        # ==========================================
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS population_snapshots (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tick INTEGER NOT NULL,
                species TEXT NOT NULL,
                count INTEGER DEFAULT 0,
                avg_thirst REAL DEFAULT 0.0,
                avg_hunger REAL DEFAULT 0.0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # ==========================================
        # BEHAVIOR STATS TABLE
        # ==========================================
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS behavior_stats (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tick INTEGER NOT NULL,
                state TEXT NOT NULL,
                count INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # ==========================================
        # SEED SPECIES DATA
        # ==========================================
        species_data = [
            ('Zebra', 1, 1, 'herbivore'),
            ('Elephant', 1, 1, 'herbivore'),
            ('Lion', 1, 0, 'carnivore'),
            ('Leopard', 0, 0, 'carnivore'),
            ('BushBaby', 0, 1, 'insectivore'),
            ('Ostrich', 1, 1, 'herbivore'),
            ('Cheetah', 1, 0, 'carnivore'),
        ]
        
        cursor.executemany("""
            INSERT OR IGNORE INTO species (name, is_diurnal, is_herd, diet)
            VALUES (?, ?, ?, ?)
        """, species_data)
        
        conn.commit()
        conn.close()
        
        print(f"✅ Database initialized: {db_path}")
    
    @classmethod
    def log_event(cls, tick: int, entity_id: Optional[int], event_type: str, details: str = ""):
        """
        Log an event to the database.
        
        Args:
            tick: Current simulation tick
            entity_id: ID of entity (if applicable)
            event_type: Type of event (STATE_CHANGED, ENTITY_ATE, etc.)
            details: Additional event details
        """
        conn = cls.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO events_log (tick, entity_id, event_type, details)
            VALUES (?, ?, ?, ?)
        """, (tick, entity_id, event_type, details))
        conn.commit()
    
    @classmethod
    def log_entity(cls, entity_id: int, name: str, species_id: int, 
                   x: int, y: int, birth_tick: int):
        """
        Log a new entity to the database.
        
        Args:
            entity_id: Unique entity ID
            name: Entity name
            species_id: Species from species table
            x: X position
            y: Y position
            birth_tick: Tick when entity was born/spawned
        """
        conn = cls.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO entities (entity_id, species_id, name, x, y, birth_tick)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (entity_id, species_id, name, x, y, birth_tick))
        conn.commit()
    
    @classmethod
    def update_entity(cls, entity_id: int, x: int, y: int, 
                     thirst: int, hunger: int, state: str):
        """
        Update entity position and stats.
        
        Args:
            entity_id: Entity ID
            x: New X position
            y: New Y position
            thirst: Current thirst level
            hunger: Current hunger level
            state: Current state
        """
        conn = cls.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE entities 
            SET x = ?, y = ?, thirst = ?, hunger = ?, state = ?
            WHERE entity_id = ?
        """, (x, y, thirst, hunger, state, entity_id))
        conn.commit()
    
    @classmethod
    def log_death(cls, entity_id: int, cause: str, tick: int):
        """
        Log entity death.
        
        Args:
            entity_id: ID of dead entity
            cause: Reason for death
            tick: Current tick
        """
        conn = cls.get_connection()
        cursor = conn.cursor()
        
        # Update entity as dead
        cursor.execute("""
            UPDATE entities 
            SET is_alive = 0, death_tick = ?
            WHERE entity_id = ?
        """, (tick, entity_id))
        
        # Log death
        cursor.execute("""
            INSERT INTO deaths (entity_id, cause, tick)
            VALUES (?, ?, ?)
        """, (entity_id, cause, tick))
        
        conn.commit()
    
    @classmethod
    def log_food_source(cls, x: int, y: int, food_type: str, 
                       quantity: int, max_quantity: int, regrow_rate: int):
        """
        Log a food source to database.
        
        Args:
            x: X position
            y: Y position
            food_type: Type of food (GRASS, BERRY, etc.)
            quantity: Current quantity
            max_quantity: Maximum quantity
            regrow_rate: Ticks to regrow
        """
        conn = cls.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO food_sources (x, y, food_type, quantity, max_quantity, regrow_rate)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (x, y, food_type, quantity, max_quantity, regrow_rate))
        conn.commit()
    
    @classmethod
    def update_food_source(cls, food_id: int, quantity: int):
        """Update food source quantity"""
        conn = cls.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE food_sources SET quantity = ? WHERE id = ?
        """, (quantity, food_id))
        conn.commit()
    
    @classmethod
    def log_population_snapshot(cls, tick: int, species_stats: Dict[str, Dict]):
        """
        Log population snapshot for analysis.
        
        Args:
            tick: Current tick
            species_stats: Dict of species -> {count, avg_thirst, avg_hunger}
        """
        conn = cls.get_connection()
        cursor = conn.cursor()
        
        for species, stats in species_stats.items():
            cursor.execute("""
                INSERT INTO population_snapshots (tick, species, count, avg_thirst, avg_hunger)
                VALUES (?, ?, ?, ?, ?)
            """, (tick, species, stats['count'], stats['avg_thirst'], stats['avg_hunger']))
        
        conn.commit()
    
    @classmethod
    def log_behavior_stats(cls, tick: int, state_stats: Dict[str, int]):
        """
        Log state distribution for analysis.
        
        Args:
            tick: Current tick
            state_stats: Dict of state -> count
        """
        conn = cls.get_connection()
        cursor = conn.cursor()
        
        for state, count in state_stats.items():
            cursor.execute("""
                INSERT INTO behavior_stats (tick, state, count)
                VALUES (?, ?, ?)
            """, (tick, state, count))
        
        conn.commit()
    
    @classmethod
    def get_population_by_species(cls) -> List[Dict]:
        """Get current population counts by species"""
        conn = cls.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT species, COUNT(*) as count
            FROM entities
            WHERE is_alive = 1
            GROUP BY species
        """)
        return [dict(row) for row in cursor.fetchall()]
    
    @classmethod
    def get_death_causes(cls) -> List[Dict]:
        """Get death causes statistics"""
        conn = cls.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT cause, COUNT(*) as count
            FROM deaths
            GROUP BY cause
            ORDER BY count DESC
        """)
        return [dict(row) for row in cursor.fetchall()]
    
    @classmethod
    def export_to_csv(cls, output_dir: str = "exports"):
        """
        Export all tables to CSV files.
        
        Args:
            output_dir: Directory to save CSV files
        """
        import csv
        os.makedirs(output_dir, exist_ok=True)
        
        conn = cls.get_connection()
        cursor = conn.cursor()
        
        tables = [
            'species', 'entities', 'events_log', 'food_sources',
            'births', 'deaths', 'weather_log', 
            'population_snapshots', 'behavior_stats'
        ]
        
        for table in tables:
            cursor.execute(f"SELECT * FROM {table}")
            rows = cursor.fetchall()
            
            if rows:
                filename = f"{output_dir}/{table}.csv"
                with open(filename, 'w', newline='') as f:
                    writer = csv.writer(f)
                    writer.writerow([desc[0] for desc in cursor.description])
                    writer.writerows(rows)
                print(f"✅ Exported: {filename}")
    
    @classmethod
    def close(cls):
        """Close database connection"""
        if cls._connection:
            cls._connection.close()
            cls._connection = None


# ==========================================
# CONVENIENCE FUNCTIONS
# ==========================================

def get_species_id(species_name: str) -> int:
    """Get species ID by name"""
    conn = DatabaseManager.get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM species WHERE name = ?", (species_name,))
    result = cursor.fetchone()
    return result[0] if result else None


def get_all_species() -> List[str]:
    """Get all species names"""
    conn = DatabaseManager.get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM species")
    return [row[0] for row in cursor.fetchall()]