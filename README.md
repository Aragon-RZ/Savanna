# Savanna
Savanna simulation for school final project

# 🦁 Safari Ecosystem Simulation

An agent-based, object-oriented simulation of a bustling Safari Park. This project models the complex interactions between wildlife, environments, and human tourists using Python. It features a custom time-tick engine and utilizes concurrent programming concepts (Locks and Semaphores) to manage shared resources.

## 📋 Project Overview

The simulation handles two main ecosystems interacting with each other:
1. **The Natural World:** Animals (Herbivores and Carnivores) managing their survival stats (hunger, thirst) and interacting with the environment.
2. **The Tourism World:** Humans visiting the park, staying in hotels, and booking safari excursions.

### ✨ Core Mechanics
* **Tick-Based Time Engine:** Decouples simulation time from real-time for stable state management.
* **State Machines:** Entities transition between states dynamically (e.g., `WANDERING`, `SEEKING_WATER`, `HUNTING`, `DIRTY`, `CLEAN`).
* **Resource Management:** * **Semaphores:** Manage multi-capacity resources like Watering Holes and Safari Car seats.
  * **Locks:** Manage single-occupancy resources like Hotel Rooms and animal health pools during combat.

## 🗂️ Project Structure

We follow a strict Separation of Concerns architecture to prevent circular dependencies and keep the codebase modular:

```text
safari_sim/
├── main.py                   # Entry point and simulation initializer
├── engine/                   # The core mechanics
│   ├── simulation.py         # Main loop, Tick system, and entity master lists
│   └── weather.py            # Manages seasons and environmental changes
├── entities/                 # The moving agents (Actors)
│   ├── base.py               # Foundational `Entity` class
│   ├── animals.py            # Zebra, Lion, Elephant, etc.
│   ├── humans.py             # Tourist, Guide, Housekeeper
│   └── vehicles.py           # SafariCar
├── environment/              # Stationary locations
│   ├── base.py               # Foundational `Location` class
│   ├── hotel.py              # Hotel and Room management
│   └── nature.py             # Savanna, WateringHole, River
└── utils/                    # Shared helpers
    ├── constants.py          # Global simulation variables (TICK_RATE, MAX_THIRST)
    └── states.py             # Enums for entity and environment states