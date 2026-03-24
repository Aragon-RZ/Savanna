# Savanna
Savanna simulation for school final project.

## Safari Ecosystem Simulation

An agent-based Python simulation of a safari park. The current MVP models thirsty zebras competing for a watering hole while a hungry lion hunts nearby on the same tick-based map.

## Project Overview

The simulation currently focuses on two interacting systems:

1. Wildlife survival, movement, drinking, and hunting.
2. Shared-resource coordination through the watering hole semaphore.

## Core Mechanics

* **Tick-Based Time Engine:** The simulation advances in discrete ticks instead of depending on real-time updates from each entity.
* **State Machines:** Entities transition through states such as `WANDERING`, `SEEKING_WATER`, `WAITING_IN_LINE`, `DRINKING`, `HUNTING`, and `EATING`.
* **Resource Management:** Watering-hole capacity is controlled with a semaphore so multiple animals can drink without blocking the whole simulation.

## Project Structure

```text
Savanna/
├── main.py                   # Entry point
├── engine/
│   ├── builder.py            # Builds the default world
│   ├── simulation.py         # Tick loop and interaction orchestration
│   └── weather.py            # Placeholder for future weather logic
├── entities/
│   ├── base.py               # Shared entity movement and identity logic
│   ├── animals.py            # Zebra and Lion behavior
│   ├── humans.py             # Placeholder for human actors
│   └── vehicles.py           # Placeholder for vehicles
├── environment/
│   ├── base.py               # Placeholder for environment primitives
│   ├── hotel.py              # Placeholder for hotel logic
│   └── nature.py             # Watering hole logic
└── utils/
    ├── constants.py          # Simulation constants
    └── states.py             # Placeholder for shared enums/state helpers
```

## Running

From the repository root:

```bash
cd Savanna
python3 main.py
```
