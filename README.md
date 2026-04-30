# Savanna Safari Ecosystem Simulation

Savanna is a threaded safari-park ecosystem simulation with a live Tkinter UI, autonomous animals, rangers, safari jeeps, weather, poachers, shared resources, and CSV analytics output.

The project models a dynamic reserve where animals search for water and food, predators hunt, poachers create security incidents, rangers respond in parallel, and safari jeeps run tours across the map. It was built to demonstrate operating-systems concepts such as threads, locks, semaphores, background workers, and safe shared-state coordination.

## Features

- Live map UI with start, pause, stop, reset, speed control, object spawning, and cursor placement.
- Threaded `SimulationEngine` that advances time independently from the UI.
- Weather system with clear, rain, drought, and storm effects.
- Animal ecosystem with herbivores, carnivores, insectivores, hunger, thirst, death, hunting, reproduction, and state changes.
- Shared environmental resources: rivers, watering holes, grazing areas, and insectivore feeding grounds.
- Poacher incidents with target selection, escape/arrest outcomes, zone tracking, and temporary ranger camps.
- Ranger threads that patrol, respond to distress events, pursue poachers, and protect temporary camps.
- Safari jeep threads with normal tours, nocturnal tours, fuel, rider counts, sightings, and scheduled multi-day camping expeditions.
- Event log for births, deaths, weather changes, poacher sightings, arrests, escapes, poaching attacks, camp creation, and resource availability.
- CSV logger for analytics and final reporting.

## Running the Project

From the `Savanna/` directory:

```bash
python3 ui_app.py
```

This launches the main Tkinter interface.

You can also run the console simulation:

```bash
python3 main.py
```

No third-party packages are required. The project uses the Python standard library, including `threading`, `tkinter`, `csv`, `random`, and `time`.

## UI Guide

The UI is split into a large map and a tabbed right panel.

- `Overview`: run status, tick, weather, population counts, births/deaths, poacher metrics, resource totals, and jeep trip status.
- `Resources`: detailed water, grazing, insect food, building, and temporary camp information.
- `Entities`: every visible entity with state, position, needs, rider counts, fuel, ranger territory, poacher zone, and jeep trip details.
- `Events`: readable live event stream from the simulation event bus.
- `Add`: spawn animals, rangers, safari jeeps, poachers, and map resources.

The map also shows:

- Weather indicator in the top-left.
- Clean resource names such as `Mara River` or `North Bend Oasis`.
- Jeep rider counts, for example `5/8`.
- Different shapes/colors for herbivores, carnivores, insectivores, rangers, jeeps, and poachers.

## Simulation Model

### Engine

`engine/simulation.py` contains the main simulation thread. Each tick:

1. Advances simulation time.
2. Applies weather effects.
3. Expires temporary ranger camps.
4. Possibly spawns poachers.
5. Updates living entities.
6. Updates environmental resources.
7. Records births, deaths, poacher outcomes, and logger metrics.
8. Stops when `max_ticks` is reached.

### Builder

`engine/builder.py` creates the default world:

- Mara River and multiple watering holes.
- Grazing areas and insectivore feeding grounds.
- Ranger and safari stations.
- A broad animal population profile.
- Rangers and safari jeeps.
- Two scheduled multi-day jeep camping expeditions during the default simulation.

### Weather

`engine/weather.py` runs as a daemon thread. It randomly changes between:

- `CLEAR`
- `RAIN`
- `DROUGHT`
- `STORM`

Weather modifies thirst and hunger pressure on living animals.

## Entities

### Animals

Animals live in `entities/animals.py`.

- Herbivores seek water and grazing areas.
- Insectivores seek water and insect feeding grounds.
- Carnivores hunt prey when hungry.
- Animals can sleep, graze, forage, drink, flee, reproduce, become desperate, or die.

### Rangers

Rangers live in `entities/humans.py`.

Rangers are threaded workers. They patrol independently and react to events from the `EventBus`. They can:

- Respond to distressed animals.
- Investigate animal deaths.
- Pursue poachers.
- Arrest poachers at close range.
- Patrol temporary anti-poaching camps.

Ranger response speed is configured in `utils/constants.py`.

### Safari Jeeps

Jeeps live in `entities/vehicles.py`.

Jeeps are threaded workers. They support:

- Morning tours.
- Afternoon tours.
- Nocturnal tours.
- Fuel usage and refueling.
- Rider counts.
- Wildlife sightings.
- Event chasing when hunts or dramatic deaths happen.
- Scheduled 2-3 day camping expeditions.

### Poachers

Poachers live in `entities/poachers.py`.

Poachers can spawn automatically during the simulation or manually from the UI. They target high-value non-carnivore animals, move toward the target, poach if they remain close long enough, then flee. Rangers can intercept and arrest them.

## Environment

Environment objects live in `environment/nature.py` and use thread-safe resource management.

- `River`
- `WateringHole`
- `GrazingArea`
- `InsectivoreFeedingGround`
- `RangerStation`
- `SafariStation`
- `TemporaryRangerCamp`

Water, grazing, and insect food resources use semaphores to model limited simultaneous access. When a resource spot opens, an event is emitted so waiting entities can react.

## Architecture Patterns

- `Threading`: simulation engine, weather system, rangers, and jeeps run concurrently.
- `Semaphore`: multi-capacity shared resources such as water and food areas.
- `Lock`: protects entity state and event-sensitive behavior.
- `Observer`: `utils/events.py` implements an event bus used by animals, rangers, jeeps, weather, resources, and the UI.
- `Strategy`: rangers, jeeps, poachers, animals, and weather swap behaviors at runtime.
- `Composite`: `environment/base.py` represents the savanna as nested zones and leaves.
- `Builder`: `engine/builder.py` constructs the default simulation world.

## CSV Analytics

`utils/logger.py` writes one CSV row per tick. UI runs now enable logging by default and display the generated CSV path in the Events tab.

CSV files are written to the `Savanna/` directory with timestamped names such as:

```text
simulation_20260430_133642_405013.csv
```

The logger tracks:

- Tick, hour, and weather.
- Total, alive, and dead animals.
- Birth and death counters.
- Animal type counts.
- Hunger and thirst statistics.
- State counts such as sleeping, drinking, grazing, hunting, and fleeing.
- Water, grazing, and insect food utilization.
- Ranger and jeep counts.
- Jeep fuel, occupancy, sightings, and long trips.
- Active poachers, spawns, arrests, escapes, poached animals, and temporary camps.

These files can be loaded into Excel, Google Sheets, Python, or any analytics tool for graphs and final-report analysis.

## Project Structure

```text
Savanna/
├── ui_app.py                  # UI entrypoint
├── main.py                    # Console simulation entrypoint
├── engine/
│   ├── builder.py             # Default world factory
│   ├── simulation.py          # Threaded simulation loop and metrics
│   └── weather.py             # Weather daemon and weather strategies
├── entities/
│   ├── animals.py             # Animal classes and behavior
│   ├── humans.py              # Ranger thread and ranger strategies
│   ├── poachers.py            # Poacher behavior and outcomes
│   └── vehicles.py            # Safari jeep thread and tour strategies
├── environment/
│   ├── base.py                # Composite environment base
│   ├── hotel.py               # Hotel/room resource examples
│   └── nature.py              # Water, food, buildings, and camps
├── ui/
│   └── app.py                 # Tkinter UI
└── utils/
    ├── constants.py           # Tunable simulation settings
    ├── events.py              # Event bus
    ├── logger.py              # CSV analytics logger
    └── states.py              # Shared state definitions
```

## Configuration

Most tunable values are in `utils/constants.py`, including:

- Tick rate and day length.
- Grid dimensions.
- Hunger/thirst thresholds.
- Reproduction timing and limits.
- Poacher spawn chance, speed, flee range, and arrest range.
- Ranger patrol speed and pursuit/response movement.

The UI also lets you adjust max ticks and tick speed before starting or resetting a run.

## Notes

- `ui_app.py` is the recommended entrypoint for demonstrations.
- `main.py` is useful for console-only runs.
- Existing `simulation_*.csv` files are generated output and can be used for analytics examples.
- The simulation is stochastic, so each run will produce slightly different wildlife, poacher, weather, and tour outcomes.
