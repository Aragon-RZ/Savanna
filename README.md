# 🦁 Savanna: Safari Ecosystem Simulation

## 📖 Project Description
This project is a high-fidelity simulation of a Safari Park ecosystem. [cite_start]In this project, we demonstrate our understanding of parallel computing concepts by creating a simulation using the thread library[cite: 2]. [cite_start]The goal is to simulate a real-world scenario of our choice, leveraging the power of parallelism to improve performance[cite: 3].

## 🛠️ Parallel Computing & Threading Architecture
[cite_start]To ensure proper use of the thread library and parallel programming techniques[cite: 25], we implemented the following architecture:

### 1. The Background Engine (Threaded Heartbeat)
* **Implementation**: The core simulation logic runs on a dedicated background `SimulationEngine` thread.
* [cite_start]**Purpose**: This decouples the simulation's "time" from the main execution thread, highlighting the use of threads and parallelism in our project.

### 2. Resource Management (Locks & Semaphores)
* **Semaphores (Multi-Capacity)**: Used for shared environmental resources like **Watering Holes** and **Safari Vehicles** to manage limited capacity safely across threads.
* **Locks (Mutual Exclusion)**: Utilized for single-occupancy resources such as **Hotel Rooms** and protecting sensitive entity data during simultaneous interactions.
* [cite_start]**Error Handling & Robustness**: Entities use non-blocking acquisition (`blocking=False`) when requesting full resources to prevent thread deadlocks, demonstrating error handling and robustness of the code[cite: 26].

## 🗂️ Project Structure
[cite_start]The codebase is well-structured, well-documented, and follows best practices for parallel programming[cite: 9]. [cite_start]It follows a strict Separation of Concerns architecture to ensure code readability and adherence to coding conventions[cite: 27].

```text
Savanna/
├── main.py                   # Entry point and Thread listener
├── engine/                   # Parallel mechanics
│   ├── builder.py            # World-state factory
│   └── simulation.py         # Threaded Tick loop and Collision logic
├── entities/                 # The moving agents (Actors)
│   ├── base.py               # Foundational Entity class
│   ├── animals.py            # Zebra (Herbivore) & Lion (Carnivore) logic
│   └── humans.py             # Tourist & Staff logic
├── environment/              # Thread-safe data structures
│   ├── hotel.py              # Hotel/Room management (Locks)
│   └── nature.py             # WateringHole/River (Semaphores)
└── utils/                    # Shared configuration
    ├── constants.py          # Global simulation variables
    └── states.py             # Enums for Entity/Environment states
```
## 📈 Development Roadmap & Milestones
This schedule outlines our development milestones:

### Phase 1: Project Proposal

Write a brief proposal outlining the simulation idea, including its real-world relevance.

Provide an initial design plan highlighting parallelism.

### Phase 2: MVP Development & Mid-Project Presentation

Prepare a mid-project presentation showcasing progress, challenges faced, and how we addressed them.

Provide a demo of the running simulation.

Highlight the parallel computing aspects of the code.

### Phase 3: Final Submission & Report

Submit the final version of the simulation.

Include a detailed report covering optimizations, trade-offs, test results, performance metrics, and visualizations.

Document the challenges faced and lessons learned.

## 🚀 Getting Started
```
Create Virtual Environment: python -m venv venv
```
***Activate Environment:***

Mac/Linux: ```source venv/bin/activate```

Windows: ```venv\Scripts\activate```

Run Simulation: ```python main.py```
