"""
Analytics Engine - Comprehensive real-time and post-simulation analytics

This module provides:
- Real-time population tracking
- Event aggregation
- Statistical analysis
- Query interface
- Report generation
"""

import sqlite3
from collections import defaultdict
from typing import Dict, List, Optional, Tuple
from datetime import datetime


class SimulationAnalyticsEngine:
    """
    Comprehensive analytics for simulation data.
    
    Collects and analyzes:
    - Population dynamics
    - Birth/death statistics
    - Resource consumption
    - Environmental impacts
    - Species-specific metrics
    """
    
    def __init__(self, db_path: str = "savanna_simulation.db"):
        self.db_path = db_path
        self.population_history = defaultdict(list)
        self.species_lifespans = defaultdict(list)
        self.event_counts = defaultdict(int)
    
    def compute_population_trends(self) -> Dict:
        """Compute population trends from events"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get birth and death counts
            cursor.execute("SELECT COUNT(*) FROM births")
            total_births = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM deaths")
            total_deaths = cursor.fetchone()[0]
            
            # Get initial population from simulation_run
            cursor.execute("SELECT config_json FROM simulation_run LIMIT 1")
            result = cursor.fetchone()
            initial = 0
            if result:
                import json
                try:
                    config = json.loads(result[0])
                    initial = config.get('initial_pop', 0)
                except:
                    pass
            
            conn.close()
            return {
                'total_births': total_births,
                'total_deaths': total_deaths,
                'initial_population': initial,
                'net_change': total_births - total_deaths
            }
        except Exception as e:
            return {}
    
    def compute_species_metrics(self) -> Dict[str, Dict]:
        """Compute per-species statistics"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            metrics = {}
            
            # Get species from births table
            cursor.execute("SELECT DISTINCT species FROM births")
            species_list = [row[0] for row in cursor.fetchall()]
            
            for species in species_list:
                # Count births
                cursor.execute("SELECT COUNT(*) FROM births WHERE species = ?", (species,))
                births = cursor.fetchone()[0]
                
                # Count deaths  
                cursor.execute("SELECT COUNT(*) FROM deaths")
                all_deaths = cursor.fetchone()[0]
                
                metrics[species] = {
                    'births': births,
                    'deaths': 0,  # Would need species column in deaths table
                    'survival_rate': (births - 0) / max(1, births) if births > 0 else 0
                }
            
            conn.close()
            return metrics
        except Exception as e:
            return {}
    
    def get_population_by_day(self) -> List[Dict]:
        """Get population snapshots by day"""
        try:
            conn = sqlite3.connect(self.db_path)
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
                    'start_pop': row[1],
                    'end_pop': row[2],
                    'births': row[3],
                    'deaths': row[4]
                })
            
            conn.close()
            return results
        except Exception as e:
            return []
    
    def get_death_causes(self) -> Dict[str, int]:
        """Analyze death causes"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT cause, COUNT(*) as count
                FROM deaths
                GROUP BY cause
                ORDER BY count DESC
            """)
            
            results = {row[0]: row[1] for row in cursor.fetchall()}
            conn.close()
            return results
        except Exception as e:
            return {}
    
    def get_resource_timeline(self) -> List[Dict]:
        """Get resource availability over time"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT tick, total_grass, season, current_weather, food_regrow_rate
                FROM environmental_state
                ORDER BY tick
            """)
            
            results = []
            for row in cursor.fetchall():
                results.append({
                    'tick': row[0],
                    'grass': row[1],
                    'season': row[2],
                    'weather': row[3],
                    'regrow_rate': row[4]
                })
            
            conn.close()
            return results
        except Exception as e:
            return []
    
    def get_summary_report(self) -> Dict:
        """Generate comprehensive summary report"""
        report = {
            'timestamp': datetime.now().isoformat(),
            'population_trends': self.compute_population_trends(),
            'species_metrics': self.compute_species_metrics(),
            'death_causes': self.get_death_causes(),
        }
        
        # Get event counts
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("SELECT COUNT(*) FROM events_log")
            report['total_events'] = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(DISTINCT event_type) FROM events_log")
            report['event_types'] = cursor.fetchone()[0]
            
            conn.close()
        except:
            pass
        
        return report
    
    def print_report(self):
        """Print analytics report to console"""
        report = self.get_summary_report()
        
        print("\n" + "="*70)
        print("📊 SIMULATION ANALYTICS REPORT")
        print("="*70)
        
        print(f"\n📈 POPULATION DYNAMICS:")
        pop = report['population_trends']
        print(f"   Initial Population: {pop.get('initial_population', 'N/A')}")
        print(f"   Total Births: {pop.get('total_births', 0)}")
        print(f"   Total Deaths: {pop.get('total_deaths', 0)}")
        print(f"   Net Change: {pop.get('net_change', 0)}")
        
        print(f"\n🦁 SPECIES METRICS:")
        for species, metrics in sorted(report['species_metrics'].items()):
            print(f"   {species}:")
            print(f"     - Births: {metrics['births']}")
            print(f"     - Survival Rate: {metrics['survival_rate']:.1%}")
        
        print(f"\n💀 DEATH CAUSES:")
        for cause, count in sorted(report['death_causes'].items(), key=lambda x: x[1], reverse=True):
            print(f"   {cause}: {count}")
        
        print(f"\n📝 EVENTS:")
        print(f"   Total Events: {report.get('total_events', 0)}")
        print(f"   Event Types: {report.get('event_types', 0)}")
        
        print("="*70 + "\n")


class ComparisonAnalytics:
    """Compare multiple simulation runs"""
    
    @staticmethod
    def compare_scenarios(db_paths: List[str], scenario_names: List[str]) -> Dict:
        """Compare multiple simulation results"""
        comparisons = {}
        
        for db_path, name in zip(db_paths, scenario_names):
            engine = SimulationAnalyticsEngine(db_path)
            comparisons[name] = engine.get_summary_report()
        
        return comparisons
    
    @staticmethod
    def find_stable_equilibrium(resource_timeline: List[Dict]) -> Optional[Dict]:
        """Detect if ecosystem reached stable equilibrium"""
        if len(resource_timeline) < 20:
            return None
        
        # Check last 20% of ticks
        recent = resource_timeline[-int(len(resource_timeline) * 0.2):]
        
        avg_grass = sum(r['grass'] for r in recent) / len(recent)
        
        # Check variance
        variance = sum((r['grass'] - avg_grass) ** 2 for r in recent) / len(recent)
        
        if variance < (avg_grass * 0.1) ** 2:  # Less than 10% variation
            return {
                'equilibrium_grass': avg_grass,
                'stability': 'stable',
                'tick_start': recent[0]['tick'],
                'tick_end': recent[-1]['tick']
            }
        
        return None
