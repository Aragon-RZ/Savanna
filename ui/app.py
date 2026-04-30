import random
import queue
import time
import tkinter as tk
from tkinter import ttk

from engine.builder import POPULATION_PROFILE, SafariBuilder
from environment.nature import (
    GrazingArea,
    InsectivoreFeedingGround,
    RangerStation,
    SafariStation,
    WateringHole,
)
from entities.animals import (
    Antelope,
    Buffalo,
    BushBaby,
    Cheetah,
    Elephant,
    Giraffe,
    Herbivore,
    Insectivore,
    Leopard,
    Lion,
    Meerkat,
    Ostrich,
    Pangolin,
    Rhino,
    Zebra,
)
from entities.humans import Ranger
from entities.vehicles import SafariJeep
from utils.constants import GRID_HEIGHT, GRID_WIDTH
from utils.events import Event, EventListener, event_bus


EVENT_TYPES = [
    Event.ANIMAL_DIED,
    Event.ANIMAL_BORN,
    Event.POACHER_SPOTTED,
    Event.POACHER_ARRESTED,
    Event.POACHER_ESCAPED,
    Event.POACHING_ATTACK,
    Event.RANGER_CAMP_CREATED,
    Event.RANGER_CAMP_EXPIRED,
    Event.WATER_SPOT_FREED,
    Event.GRAZING_SPOT_FREED,
    Event.ANIMAL_HUNTING,
    Event.WEATHER_CHANGED,
    Event.ANIMAL_DESPERATE,
    Event.ENTITY_ADDED,
    Event.ENVIRONMENT_ADDED,
]

ANIMAL_TYPES = {
    "Zebra": Zebra,
    "Elephant": Elephant,
    "Giraffe": Giraffe,
    "Buffalo": Buffalo,
    "Rhino": Rhino,
    "Antelope": Antelope,
    "Ostrich": Ostrich,
    "Meerkat": Meerkat,
    "BushBaby": BushBaby,
    "Pangolin": Pangolin,
    "Lion": Lion,
    "Leopard": Leopard,
    "Cheetah": Cheetah,
}

LAND_OBJECT_TYPES = [
    "WateringHole",
    "GrazingArea",
    "InsectivoreFeedingGround",
    "RangerStation",
    "SafariStation",
]

OBJECT_TYPES = list(ANIMAL_TYPES) + ["Ranger", "SafariJeep"] + LAND_OBJECT_TYPES


class UiEventCollector(EventListener):
    def __init__(self, event_queue):
        self.event_queue = event_queue

    def on_event(self, event_type: str, payload: dict):
        self.event_queue.put((time.strftime("%H:%M:%S"), self._format(event_type, payload)))

    def _format(self, event_type, payload):
        if event_type == Event.ANIMAL_DIED:
            entity = payload.get("entity")
            cause = payload.get("cause", "unknown")
            return f"Death: {getattr(entity, 'name', 'Unknown')} ({cause})"

        if event_type == Event.ANIMAL_BORN:
            entity = payload.get("entity")
            parent_a = payload.get("parent_a")
            parent_b = payload.get("parent_b")
            return (
                f"Birth: {getattr(entity, 'name', 'New animal')} "
                f"from {getattr(parent_a, 'name', 'parent')} and "
                f"{getattr(parent_b, 'name', 'parent')}"
            )

        if event_type == Event.POACHER_SPOTTED:
            poacher = payload.get("poacher")
            target = payload.get("target")
            zone_id = payload.get("zone_id")
            return (
                f"Poacher: {getattr(poacher, 'name', 'Unknown')} "
                f"entered zone {zone_id} near {getattr(target, 'name', 'wildlife')}"
            )

        if event_type == Event.POACHER_ARRESTED:
            poacher = payload.get("poacher")
            ranger = payload.get("ranger")
            return (
                f"Arrest: {getattr(ranger, 'name', 'Ranger')} stopped "
                f"{getattr(poacher, 'name', 'poacher')}"
            )

        if event_type == Event.POACHER_ESCAPED:
            poacher = payload.get("poacher")
            return f"Escape: {getattr(poacher, 'name', 'Poacher')} left the reserve"

        if event_type == Event.POACHING_ATTACK:
            poacher = payload.get("poacher")
            target = payload.get("target")
            return (
                f"Poaching: {getattr(poacher, 'name', 'Poacher')} killed "
                f"{getattr(target, 'name', 'wildlife')}"
            )

        if event_type == Event.RANGER_CAMP_CREATED:
            camp = payload.get("camp")
            ranger = payload.get("ranger")
            return (
                f"Camp: {getattr(ranger, 'name', 'A ranger')} set "
                f"{getattr(camp, 'name', 'temporary camp')}"
            )

        if event_type == Event.RANGER_CAMP_EXPIRED:
            camp = payload.get("camp")
            return f"Camp expired: {getattr(camp, 'name', 'temporary camp')}"

        if event_type == Event.ANIMAL_HUNTING:
            predator = payload.get("predator")
            prey = payload.get("prey")
            return (
                f"Hunt: {getattr(predator, 'name', 'Predator')} "
                f"caught {getattr(prey, 'name', 'prey')}"
            )

        if event_type == Event.ANIMAL_DESPERATE:
            entity = payload.get("entity")
            return f"Distress: {getattr(entity, 'name', 'Unknown')} needs attention"

        if event_type == Event.WATER_SPOT_FREED:
            environment = payload.get("environment")
            freed_by = payload.get("freed_by")
            return (
                f"Water: {getattr(environment, 'name', 'Watering hole')} "
                f"freed by {getattr(freed_by, 'name', 'an animal')}"
            )

        if event_type == Event.GRAZING_SPOT_FREED:
            environment = payload.get("environment")
            freed_by = payload.get("freed_by")
            label = "Forage" if hasattr(environment, "current_feeders") else "Grazing"
            return (
                f"{label}: {getattr(environment, 'name', 'Feeding area')} "
                f"freed by {getattr(freed_by, 'name', 'an animal')}"
            )

        if event_type == Event.WEATHER_CHANGED:
            return f"Weather: {payload.get('weather', 'UNKNOWN')}"

        if event_type == Event.ENTITY_ADDED:
            entity = payload.get("entity")
            return f"Added: {getattr(entity, 'name', 'Entity')}"

        if event_type == Event.ENVIRONMENT_ADDED:
            environment = payload.get("environment")
            return f"Placed: {getattr(environment, 'name', 'Map object')}"

        return event_type


class SavannaApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Savanna Simulation")
        self.geometry("1180x760")
        self.minsize(980, 640)

        self.engine = None
        self.engine_started = False
        self.last_snapshot = None
        self.event_queue = queue.Queue()
        self.event_collector = None

        self.max_ticks_var = tk.IntVar(value=240)
        self.speed_var = tk.DoubleVar(value=0.30)
        self.speed_text = tk.StringVar(value="0.30 s/tick")
        self.object_type_var = tk.StringVar(value="Zebra")
        self.object_count_var = tk.IntVar(value=1)
        self.object_x_var = tk.IntVar(value=50)
        self.object_y_var = tk.IntVar(value=50)
        self.random_position_var = tk.BooleanVar(value=True)
        self.cursor_place_var = tk.BooleanVar(value=False)
        self.populate_scale_var = tk.IntVar(value=1)
        self.summary_vars = {}

        self._configure_style()
        self._build_layout()
        self._new_engine()

        self.protocol("WM_DELETE_WINDOW", self._on_close)
        self.after(120, self._refresh)

    def _configure_style(self):
        style = ttk.Style(self)
        style.configure("Toolbar.TFrame", padding=8)
        style.configure("Metric.TLabel", padding=(0, 2))
        style.configure("Title.TLabel", font=("Helvetica", 15, "bold"))
        style.configure("Section.TLabel", font=("Helvetica", 12, "bold"))
        style.configure("Small.TLabel", font=("Helvetica", 10))

    def _build_layout(self):
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)

        toolbar = ttk.Frame(self, style="Toolbar.TFrame")
        toolbar.grid(row=0, column=0, sticky="ew")
        toolbar.columnconfigure(10, weight=1)

        self.start_button = ttk.Button(toolbar, text="Start", width=10, command=self._start)
        self.pause_button = ttk.Button(toolbar, text="Pause", width=10, command=self._pause_resume)
        self.stop_button = ttk.Button(toolbar, text="Stop", width=10, command=self._stop)
        self.reset_button = ttk.Button(toolbar, text="Reset", width=10, command=self._reset)

        self.start_button.grid(row=0, column=0, padx=(0, 6))
        self.pause_button.grid(row=0, column=1, padx=6)
        self.stop_button.grid(row=0, column=2, padx=6)
        self.reset_button.grid(row=0, column=3, padx=6)

        ttk.Label(toolbar, text="Ticks").grid(row=0, column=4, padx=(20, 6))
        ttk.Spinbox(
            toolbar,
            from_=24,
            to=2000,
            increment=24,
            width=7,
            textvariable=self.max_ticks_var,
            command=self._reset
        ).grid(row=0, column=5, padx=(0, 12))

        ttk.Label(toolbar, text="Speed").grid(row=0, column=6, padx=(10, 6))
        speed = ttk.Scale(
            toolbar,
            from_=0.05,
            to=1.50,
            variable=self.speed_var,
            command=self._on_speed_change
        )
        speed.grid(row=0, column=7, sticky="ew", padx=(0, 8))
        ttk.Label(toolbar, textvariable=self.speed_text, width=10).grid(row=0, column=8)

        ttk.Label(toolbar, text="Savanna Simulation", style="Title.TLabel").grid(
            row=0, column=10, sticky="e"
        )

        body = ttk.PanedWindow(self, orient=tk.HORIZONTAL)
        body.grid(row=1, column=0, sticky="nsew")

        map_frame = ttk.Frame(body, padding=(10, 10, 8, 10))
        map_frame.columnconfigure(0, weight=1)
        map_frame.rowconfigure(0, weight=1)
        body.add(map_frame, weight=3)

        self.map_canvas = tk.Canvas(
            map_frame,
            background="#eef5df",
            highlightthickness=1,
            highlightbackground="#9eaa8a"
        )
        self.map_canvas.grid(row=0, column=0, sticky="nsew")
        self.map_canvas.bind("<Configure>", lambda _event: self._render_last_snapshot())
        self.map_canvas.bind("<Button-1>", self._on_map_click)

        side = ttk.Frame(body, padding=(8, 10, 10, 10))
        side.columnconfigure(0, weight=1)
        side.rowconfigure(0, weight=1)
        body.add(side, weight=2)

        self.side_tabs = ttk.Notebook(side)
        self.side_tabs.grid(row=0, column=0, sticky="nsew")

        overview_tab = ttk.Frame(self.side_tabs, padding=8)
        resources_tab = ttk.Frame(self.side_tabs, padding=8)
        entities_tab = ttk.Frame(self.side_tabs, padding=8)
        events_tab = ttk.Frame(self.side_tabs, padding=8)
        controls_tab = ttk.Frame(self.side_tabs, padding=8)
        self.side_tabs.add(overview_tab, text="Overview")
        self.side_tabs.add(resources_tab, text="Resources")
        self.side_tabs.add(entities_tab, text="Entities")
        self.side_tabs.add(events_tab, text="Events")
        self.side_tabs.add(controls_tab, text="Add")

        overview_tab.columnconfigure(0, weight=1)
        overview_tab.rowconfigure(2, weight=1)

        metrics = ttk.LabelFrame(overview_tab, text="Status", padding=10)
        metrics.grid(row=0, column=0, sticky="ew")
        metric_keys = [
            "Run",
            "Tick",
            "Hour",
            "Weather",
            "Entities",
            "Alive",
            "Vehicles",
            "Long trips",
            "Herbivores",
            "Carnivores",
            "Insectivores",
            "Avg thirst",
            "Avg hunger",
            "Births",
            "Deaths",
            "Births tick",
            "Deaths tick",
            "Poachers active",
            "Poacher spawns",
            "Arrests",
            "Escapes",
            "Poached",
            "Temp camps",
            "Camps made",
            "Water spots",
            "Grazing spots",
            "Insect spots",
            "Buildings",
        ]
        split_at = (len(metric_keys) + 1) // 2
        for index, key in enumerate(metric_keys):
            column_offset = 0 if index < split_at else 2
            row = index if index < split_at else index - split_at
            ttk.Label(metrics, text=key, style="Metric.TLabel").grid(
                row=row, column=column_offset, sticky="w", padx=(0, 6)
            )
            var = tk.StringVar(value="-")
            self.summary_vars[key] = var
            ttk.Label(metrics, textvariable=var, style="Metric.TLabel").grid(
                row=row, column=column_offset + 1, sticky="e", padx=(0, 14)
            )
        metrics.columnconfigure(1, weight=1)
        metrics.columnconfigure(3, weight=1)

        species_box = ttk.LabelFrame(overview_tab, text="Active Species", padding=8)
        species_box.grid(row=1, column=0, sticky="nsew", pady=(10, 0))
        species_box.columnconfigure(0, weight=1)
        species_box.rowconfigure(0, weight=1)
        self.species_table = ttk.Treeview(
            species_box,
            columns=("species", "count"),
            show="headings",
            height=6
        )
        self.species_table.heading("species", text="Species")
        self.species_table.heading("count", text="Count")
        self.species_table.column("species", width=180, anchor="w", stretch=True)
        self.species_table.column("count", width=70, anchor="e", stretch=False)
        self.species_table.grid(row=0, column=0, sticky="nsew")
        species_scroll = ttk.Scrollbar(species_box, orient=tk.VERTICAL, command=self.species_table.yview)
        species_scroll.grid(row=0, column=1, sticky="ns")
        self.species_table.configure(yscrollcommand=species_scroll.set)

        breakdown_box = ttk.LabelFrame(overview_tab, text="Engine Details", padding=8)
        breakdown_box.grid(row=2, column=0, sticky="nsew", pady=(10, 0))
        breakdown_box.columnconfigure(0, weight=1)
        breakdown_box.rowconfigure(0, weight=1)
        self.breakdown_table = ttk.Treeview(
            breakdown_box,
            columns=("metric", "value"),
            show="headings",
            height=7
        )
        self.breakdown_table.heading("metric", text="Metric")
        self.breakdown_table.heading("value", text="Value")
        self.breakdown_table.column("metric", width=150, anchor="w", stretch=True)
        self.breakdown_table.column("value", width=150, anchor="w", stretch=True)
        self.breakdown_table.grid(row=0, column=0, sticky="nsew")
        breakdown_scroll = ttk.Scrollbar(breakdown_box, orient=tk.VERTICAL, command=self.breakdown_table.yview)
        breakdown_scroll.grid(row=0, column=1, sticky="ns")
        self.breakdown_table.configure(yscrollcommand=breakdown_scroll.set)

        resources_tab.columnconfigure(0, weight=1)
        resources_tab.rowconfigure(1, weight=1)
        resources_tab.rowconfigure(3, weight=1)
        ttk.Label(resources_tab, text="Shared Resources", style="Section.TLabel").grid(
            row=0, column=0, sticky="w", pady=(0, 6)
        )
        resource_wrap = ttk.Frame(resources_tab)
        resource_wrap.grid(row=1, column=0, sticky="nsew")
        resource_wrap.columnconfigure(0, weight=1)
        resource_wrap.rowconfigure(0, weight=1)
        self.resource_table = ttk.Treeview(
            resource_wrap,
            columns=("kind", "name", "use", "free", "occupants"),
            show="headings",
            height=10
        )
        for column, heading, width, anchor in [
            ("kind", "Kind", 88, "w"),
            ("name", "Name", 150, "w"),
            ("use", "Use", 70, "e"),
            ("free", "Free", 56, "e"),
            ("occupants", "Occupants", 180, "w"),
        ]:
            self.resource_table.heading(column, text=heading)
            self.resource_table.column(column, width=width, anchor=anchor, stretch=True)
        self.resource_table.grid(row=0, column=0, sticky="nsew")
        resource_scroll = ttk.Scrollbar(resource_wrap, orient=tk.VERTICAL, command=self.resource_table.yview)
        resource_scroll.grid(row=0, column=1, sticky="ns")
        self.resource_table.configure(yscrollcommand=resource_scroll.set)

        ttk.Label(resources_tab, text="Buildings & Camps", style="Section.TLabel").grid(
            row=2, column=0, sticky="w", pady=(12, 6)
        )
        land_wrap = ttk.Frame(resources_tab)
        land_wrap.grid(row=3, column=0, sticky="nsew")
        land_wrap.columnconfigure(0, weight=1)
        land_wrap.rowconfigure(0, weight=1)
        self.land_table = ttk.Treeview(
            land_wrap,
            columns=("kind", "name", "pos", "details"),
            show="headings",
            height=7
        )
        for column, heading, width, anchor in [
            ("kind", "Kind", 110, "w"),
            ("name", "Name", 160, "w"),
            ("pos", "Pos", 70, "w"),
            ("details", "Details", 180, "w"),
        ]:
            self.land_table.heading(column, text=heading)
            self.land_table.column(column, width=width, anchor=anchor, stretch=True)
        self.land_table.grid(row=0, column=0, sticky="nsew")
        land_scroll = ttk.Scrollbar(land_wrap, orient=tk.VERTICAL, command=self.land_table.yview)
        land_scroll.grid(row=0, column=1, sticky="ns")
        self.land_table.configure(yscrollcommand=land_scroll.set)

        entities_tab.columnconfigure(0, weight=1)
        entities_tab.rowconfigure(0, weight=1)
        entity_wrap = ttk.Frame(entities_tab)
        entity_wrap.grid(row=0, column=0, sticky="nsew")
        entity_wrap.columnconfigure(0, weight=1)
        entity_wrap.rowconfigure(0, weight=1)
        self.entity_table = ttk.Treeview(
            entity_wrap,
            columns=("name", "species", "state", "pos", "needs", "details"),
            show="headings",
            height=18
        )
        for column, heading, width, anchor in [
            ("name", "Name", 130, "w"),
            ("species", "Type", 92, "w"),
            ("state", "State", 140, "w"),
            ("pos", "Pos", 62, "w"),
            ("needs", "Needs", 116, "w"),
            ("details", "Details", 190, "w"),
        ]:
            self.entity_table.heading(column, text=heading)
            self.entity_table.column(column, width=width, anchor=anchor, stretch=True)
        self.entity_table.grid(row=0, column=0, sticky="nsew")
        entity_scroll_y = ttk.Scrollbar(entity_wrap, orient=tk.VERTICAL, command=self.entity_table.yview)
        entity_scroll_y.grid(row=0, column=1, sticky="ns")
        entity_scroll_x = ttk.Scrollbar(entity_wrap, orient=tk.HORIZONTAL, command=self.entity_table.xview)
        entity_scroll_x.grid(row=1, column=0, sticky="ew")
        self.entity_table.configure(
            yscrollcommand=entity_scroll_y.set,
            xscrollcommand=entity_scroll_x.set
        )

        events_tab.columnconfigure(0, weight=1)
        events_tab.rowconfigure(0, weight=1)
        events_wrap = ttk.Frame(events_tab)
        events_wrap.grid(row=0, column=0, sticky="nsew")
        events_wrap.columnconfigure(0, weight=1)
        events_wrap.rowconfigure(0, weight=1)
        self.events_list = tk.Listbox(
            events_wrap,
            height=18,
            activestyle="none",
            background="#fbfbf7",
            foreground="#243018",
            selectbackground="#dfe8c9",
            selectforeground="#1f2a18",
            highlightthickness=1,
            highlightbackground="#c4c9b8",
            font=("Helvetica", 10)
        )
        self.events_list.grid(row=0, column=0, sticky="nsew")
        events_scroll_y = ttk.Scrollbar(events_wrap, orient=tk.VERTICAL, command=self.events_list.yview)
        events_scroll_y.grid(row=0, column=1, sticky="ns")
        events_scroll_x = ttk.Scrollbar(events_wrap, orient=tk.HORIZONTAL, command=self.events_list.xview)
        events_scroll_x.grid(row=1, column=0, sticky="ew")
        self.events_list.configure(
            yscrollcommand=events_scroll_y.set,
            xscrollcommand=events_scroll_x.set
        )

        controls_tab.columnconfigure(0, weight=1)
        spawner = ttk.LabelFrame(controls_tab, text="Add Object", padding=10)
        spawner.grid(row=0, column=0, sticky="ew")
        spawner.columnconfigure(1, weight=1)
        spawner.columnconfigure(3, weight=1)

        ttk.Label(spawner, text="Type").grid(row=0, column=0, sticky="w")
        object_type = ttk.Combobox(
            spawner,
            textvariable=self.object_type_var,
            values=OBJECT_TYPES,
            state="readonly",
            width=14
        )
        object_type.grid(row=0, column=1, columnspan=3, sticky="ew", padx=(8, 0))

        ttk.Label(spawner, text="Count").grid(row=1, column=0, sticky="w", pady=(8, 0))
        ttk.Spinbox(
            spawner,
            from_=1,
            to=500,
            width=6,
            textvariable=self.object_count_var
        ).grid(row=1, column=1, sticky="ew", padx=(8, 8), pady=(8, 0))

        ttk.Checkbutton(
            spawner,
            text="Random",
            variable=self.random_position_var
        ).grid(row=1, column=2, sticky="w", pady=(8, 0))

        ttk.Checkbutton(
            spawner,
            text="Cursor",
            variable=self.cursor_place_var
        ).grid(row=1, column=3, sticky="e", pady=(8, 0))

        ttk.Label(spawner, text="X").grid(row=2, column=0, sticky="w", pady=(8, 0))
        ttk.Spinbox(
            spawner,
            from_=0,
            to=GRID_WIDTH - 1,
            width=6,
            textvariable=self.object_x_var
        ).grid(row=2, column=1, sticky="ew", padx=(8, 8), pady=(8, 0))

        ttk.Label(spawner, text="Y").grid(row=2, column=2, sticky="w", pady=(8, 0))
        ttk.Spinbox(
            spawner,
            from_=0,
            to=GRID_HEIGHT - 1,
            width=6,
            textvariable=self.object_y_var
        ).grid(row=2, column=3, sticky="ew", padx=(8, 0), pady=(8, 0))

        ttk.Button(spawner, text="Add", command=self._add_objects).grid(
            row=3, column=0, columnspan=2, sticky="ew", pady=(10, 0), padx=(0, 6)
        )
        ttk.Spinbox(
            spawner,
            from_=1,
            to=5,
            width=4,
            textvariable=self.populate_scale_var
        ).grid(row=3, column=2, sticky="ew", pady=(10, 0), padx=(0, 6))
        ttk.Button(spawner, text="Populate", command=self._populate_more).grid(
            row=3, column=3, sticky="ew", pady=(10, 0)
        )

    def _new_engine(self):
        self._detach_event_collector()
        self.event_queue = queue.Queue()

        builder = SafariBuilder(
            max_ticks=self.max_ticks_var.get(),
            logger_enabled=False,
            display_output=False,
            tick_rate=self.speed_var.get(),
            auto_start_workers=False
        )
        self.engine = (
            builder.build_environment()
            
            .add_population_profile(scale=1)
            .add_rangers(4)
            .add_jeeps(4)
            .get_engine()
        )
        self.engine_started = False
        self._attach_event_collector()
        self._append_event("UI", "World ready")
        self._render_snapshot(self.engine.snapshot())
        self._update_buttons()

    def _attach_event_collector(self):
        self.event_collector = UiEventCollector(self.event_queue)
        for event_type in EVENT_TYPES:
            event_bus.subscribe(event_type, self.event_collector)

    def _detach_event_collector(self):
        if not self.event_collector:
            return
        for event_type in EVENT_TYPES:
            event_bus.unsubscribe(event_type, self.event_collector)
        self.event_collector = None

    def _start(self):
        if not self.engine:
            self._new_engine()
        elif self.engine.ident is not None and not self.engine.is_alive():
            self._new_engine()

        self.engine.tick_rate = self.speed_var.get()
        self.engine.start()
        self.engine_started = True
        self._append_event("UI", "Simulation started")
        self._update_buttons()

    def _pause_resume(self):
        if not self.engine or not self.engine.is_alive():
            return
        if self.engine.is_paused():
            self.engine.resume()
            self._append_event("UI", "Simulation resumed")
        else:
            self.engine.pause()
            self._append_event("UI", "Simulation paused")
        self._update_buttons()

    def _stop(self):
        self._stop_engine()
        self._append_event("UI", "Simulation stopped")
        self._update_buttons()

    def _reset(self):
        self._stop_engine()
        self.events_list.delete(0, tk.END)
        self._new_engine()

    def _add_objects(self):
        self._ensure_editable_engine()
        object_type = self.object_type_var.get()
        count = self._bounded_int(self.object_count_var, 1, 1, 500)

        for _ in range(count):
            x, y = self._selected_position()
            self._place_object(object_type, x, y)

        self._append_event("UI", f"Queued {count} {object_type}")
        self._render_snapshot(self.engine.snapshot())

    def _place_object(self, object_type, x, y):
        if object_type in LAND_OBJECT_TYPES:
            environment = self._create_land_object(object_type, x, y)
            self.engine.add_environment_component(environment)
            self._refresh_animal_targets()
            return environment

        entity = self._create_object(object_type, x, y)
        self.engine.add_entity(entity)
        return entity

    def _populate_more(self):
        self._ensure_editable_engine()
        scale = self._bounded_int(self.populate_scale_var, 1, 1, 5)
        added = 0

        for animal_class, base_name, count, start_x, start_y in POPULATION_PROFILE:
            for _ in range(count * scale):
                x = self._clamp(start_x + random.randint(-8, 8), GRID_WIDTH)
                y = self._clamp(start_y + random.randint(-8, 8), GRID_HEIGHT)
                animal = self._create_animal(animal_class, base_name, x, y)
                self.engine.add_entity(animal)
                added += 1

        self._append_event("UI", f"Populated {added} animals")
        self._render_snapshot(self.engine.snapshot())

    def _ensure_editable_engine(self):
        if not self.engine:
            self._new_engine()
            return
        if self.engine.ident is not None and not self.engine.is_alive():
            self._new_engine()

    def _create_object(self, object_type, x, y):
        if object_type in ANIMAL_TYPES:
            return self._create_animal(ANIMAL_TYPES[object_type], object_type, x, y)

        name = self._next_name(object_type)
        if object_type == "Ranger":
            territory = "south" if y >= GRID_HEIGHT // 2 else "north"
            ranger = Ranger(
                name=name,
                x=x,
                y=y,
                territory=territory,
                display_output=False
            )
            ranger.target_water = self.engine.water_sources()
            ranger.engine_ref = self.engine
            return ranger

        jeep = SafariJeep(
            name=name,
            x=x,
            y=y,
            zone_x=x,
            zone_y=y,
            zone_radius=14,
            display_output=False
        )
        jeep.engine_ref = self.engine
        jeep.known_entities = self.engine.entities
        return jeep

    def _create_land_object(self, object_type, x, y):
        name = self._next_environment_name(object_type)
        if object_type == "WateringHole":
            obj = WateringHole(name=name, x=x, y=y, capacity=7)
        elif object_type == "GrazingArea":
            obj = GrazingArea(name=name, x=x, y=y, capacity=10)
        elif object_type == "InsectivoreFeedingGround":
            obj = InsectivoreFeedingGround(name=name, x=x, y=y, capacity=8)
        elif object_type == "RangerStation":
            obj = RangerStation(name, x, y)
        else:
            obj = SafariStation(name, x, y)

        obj.display_output = False
        return obj

    def _create_animal(self, animal_class, base_name, x, y):
        animal = animal_class(self.engine.next_entity_id(), self._next_name(base_name), x, y)
        self._configure_animal_targets(animal)
        animal.display_output = False
        return animal

    def _configure_animal_targets(self, animal):
        animal.target_water = self.engine.water_sources()
        if isinstance(animal, Insectivore):
            animal.target_insects = self.engine.insect_food_sources()
        elif isinstance(animal, Herbivore):
            animal.target_food = self.engine.grazing_sources()

    def _refresh_animal_targets(self):
        for entity in self.engine.entities:
            if hasattr(entity, "thirst"):
                self._configure_animal_targets(entity)
            elif isinstance(entity, Ranger):
                entity.target_water = self.engine.water_sources()

    def _selected_position(self):
        if self.random_position_var.get():
            return (
                random.randint(0, GRID_WIDTH - 1),
                random.randint(0, GRID_HEIGHT - 1)
            )
        return (
            self._clamp(self._bounded_int(self.object_x_var, 50, 0, GRID_WIDTH - 1), GRID_WIDTH),
            self._clamp(self._bounded_int(self.object_y_var, 50, 0, GRID_HEIGHT - 1), GRID_HEIGHT),
        )

    def _on_map_click(self, event):
        x, y = self._grid_from_canvas(event.x, event.y)
        self.object_x_var.set(x)
        self.object_y_var.set(y)
        self.random_position_var.set(False)

        if not self.cursor_place_var.get():
            return

        self._ensure_editable_engine()
        object_type = self.object_type_var.get()
        self._place_object(object_type, x, y)
        self._append_event("UI", f"Placed {object_type} at {x},{y}")
        self._render_snapshot(self.engine.snapshot())

    def _grid_from_canvas(self, pixel_x, pixel_y):
        width, height, pad, map_width, map_height = self._map_geometry()
        clamped_x = max(pad, min(width - pad, pixel_x))
        clamped_y = max(pad, min(height - pad, pixel_y))
        grid_x = round(((clamped_x - pad) / max(map_width, 1)) * (GRID_WIDTH - 1))
        grid_y = round(((clamped_y - pad) / max(map_height, 1)) * (GRID_HEIGHT - 1))
        return self._clamp(grid_x, GRID_WIDTH), self._clamp(grid_y, GRID_HEIGHT)

    def _next_name(self, base_name):
        prefix = f"{base_name} "
        highest = 0
        for entity in self.engine.entities:
            name = getattr(entity, "name", "")
            if name.startswith(prefix):
                suffix = name[len(prefix):]
                if suffix.isdigit():
                    highest = max(highest, int(suffix))
        return f"{base_name} {highest + 1}"

    def _next_environment_name(self, base_name):
        prefix = f"{base_name} "
        highest = 0
        snapshot = self.engine.snapshot()
        objects = (
            snapshot.get("water_holes", [])
            + snapshot.get("grazing_areas", [])
            + snapshot.get("insect_feeding_grounds", [])
            + snapshot.get("land_objects", [])
        )
        for item in objects:
            name = item.get("name", "")
            if name.startswith(prefix):
                suffix = name[len(prefix):]
                if suffix.isdigit():
                    highest = max(highest, int(suffix))
        return f"{base_name} {highest + 1}"

    def _bounded_int(self, variable, default, minimum, maximum):
        try:
            value = int(variable.get())
        except (tk.TclError, ValueError):
            value = default
        value = max(minimum, min(maximum, value))
        variable.set(value)
        return value

    def _clamp(self, value, limit):
        return max(0, min(limit - 1, int(value)))

    def _stop_engine(self):
        if not self.engine:
            return
        self.engine.stop()
        if self.engine.is_alive():
            self.engine.join(timeout=1.0)
        self.engine_started = False

    def _on_speed_change(self, value):
        speed = float(value)
        self.speed_text.set(f"{speed:.2f} s/tick")
        if self.engine:
            self.engine.tick_rate = speed

    def _refresh(self):
        self._drain_events()
        if self.engine:
            self._render_snapshot(self.engine.snapshot())
            self._update_buttons()
        self.after(120, self._refresh)

    def _drain_events(self):
        while True:
            try:
                timestamp, message = self.event_queue.get_nowait()
            except queue.Empty:
                break
            self._append_event(timestamp, message)

    def _append_event(self, prefix, message):
        self.events_list.insert(tk.END, f"{prefix}  {message}")
        while self.events_list.size() > 120:
            self.events_list.delete(0)
        self.events_list.see(tk.END)

    def _render_snapshot(self, snapshot):
        self.last_snapshot = snapshot
        self._render_summary(snapshot)
        self._render_species(snapshot["summary"].get("active_species", {}))
        self._render_breakdown(snapshot)
        self._render_resources(snapshot)
        self._render_entities(snapshot["entities"])
        self._render_map(snapshot)

    def _render_last_snapshot(self):
        if self.last_snapshot:
            self._render_map(self.last_snapshot)

    def _render_summary(self, snapshot):
        summary = snapshot["summary"]
        status = "Running" if snapshot["is_running"] else "Stopped"
        if snapshot["is_running"] and snapshot["is_paused"]:
            status = "Paused"

        water = self._resource_total(snapshot.get("water_holes", []), "drinkers")
        grazing = self._resource_total(snapshot.get("grazing_areas", []), "grazers")
        insect_food = self._resource_total(
            snapshot.get("insect_feeding_grounds", []),
            "feeders"
        )
        vehicles = [
            entity for entity in snapshot["entities"]
            if entity["category"] == "vehicle"
        ]
        scheduled_trips = sum(len(v.get("scheduled_long_trips") or []) for v in vehicles)
        completed_trips = sum(v.get("completed_long_trips", 0) for v in vehicles)

        values = {
            "Run": status,
            "Tick": f"{snapshot['tick']} / {snapshot['max_ticks']}",
            "Hour": f"{snapshot['hour']}:00",
            "Weather": snapshot["weather"],
            "Entities": str(summary["total_entities"]),
            "Alive": str(summary["alive_total"]),
            "Vehicles": str(summary.get("vehicles_total", len(vehicles))),
            "Long trips": (
                f"{summary.get('active_long_trips', 0)} active / "
                f"{completed_trips}/{scheduled_trips} done"
            ),
            "Herbivores": str(summary["alive_herbivores"]),
            "Carnivores": str(summary["alive_carnivores"]),
            "Insectivores": str(summary["alive_insectivores"]),
            "Avg thirst": str(summary["avg_thirst"]),
            "Avg hunger": str(summary["avg_hunger"]),
            "Births": str(summary.get("births_total", 0)),
            "Deaths": str(summary.get("deaths_total", 0)),
            "Births tick": str(summary.get("births_this_tick", 0)),
            "Deaths tick": str(summary.get("deaths_this_tick", 0)),
            "Poachers active": str(summary.get("active_poachers", 0)),
            "Poacher spawns": str(summary.get("poacher_spawns_total", 0)),
            "Arrests": str(summary.get("poachers_arrested_total", 0)),
            "Escapes": str(summary.get("poachers_escaped_total", 0)),
            "Poached": str(summary.get("poached_animals_total", 0)),
            "Temp camps": str(summary.get("temporary_camps", 0)),
            "Camps made": str(summary.get("temporary_camps_created", 0)),
            "Water spots": water,
            "Grazing spots": grazing,
            "Insect spots": insect_food,
            "Buildings": str(len(snapshot.get("land_objects", []))),
        }
        for key, value in values.items():
            if key in self.summary_vars:
                self.summary_vars[key].set(value)

    def _resource_total(self, items, used_key):
        if not items:
            return "none"
        used = sum(item.get(used_key, 0) for item in items)
        capacity = sum(item.get("capacity", 0) for item in items)
        return f"{used}/{capacity}"

    def _render_breakdown(self, snapshot):
        self.breakdown_table.delete(*self.breakdown_table.get_children())
        summary = snapshot["summary"]
        rows = [
            ("Births by species", self._format_counts(summary.get("births_by_species", {}))),
            ("Deaths by species", self._format_counts(summary.get("deaths_by_species", {}))),
            ("Deaths by cause", self._format_counts(summary.get("deaths_by_cause", {}))),
            ("Poacher zones", self._format_counts(summary.get("poacher_incidents_by_zone", {}))),
        ]

        for entity in snapshot["entities"]:
            if entity["category"] != "vehicle":
                continue
            for trip in entity.get("scheduled_long_trips") or []:
                label = f"{entity['name']} trip"
                value = (
                    f"{trip.get('name', 'Camping')} "
                    f"{trip.get('start_tick')}->{trip.get('end_tick')}"
                )
                rows.append((label, value))

        for metric, value in rows:
            self.breakdown_table.insert("", tk.END, values=(metric, value))

    def _format_counts(self, counts):
        if not counts:
            return "-"
        return ", ".join(f"{key}: {value}" for key, value in counts.items())

    def _render_resources(self, snapshot):
        self.resource_table.delete(*self.resource_table.get_children())
        self.land_table.delete(*self.land_table.get_children())

        for hole in snapshot.get("water_holes", []):
            kind = "River" if hole.get("kind") == "River" else "Water"
            self.resource_table.insert("", tk.END, values=(
                kind,
                hole["name"],
                f"{hole['drinkers']}/{hole['capacity']}",
                hole["free_spots"],
                ", ".join(hole.get("drinker_names") or []) or "-",
            ))

        for area in snapshot.get("grazing_areas", []):
            self.resource_table.insert("", tk.END, values=(
                "Grazing",
                area["name"],
                f"{area['grazers']}/{area['capacity']}",
                area["free_spots"],
                ", ".join(area.get("grazer_names") or []) or "-",
            ))

        for area in snapshot.get("insect_feeding_grounds", []):
            self.resource_table.insert("", tk.END, values=(
                "Insects",
                area["name"],
                f"{area['feeders']}/{area['capacity']}",
                area["free_spots"],
                ", ".join(area.get("feeder_names") or []) or "-",
            ))

        for land_object in snapshot.get("land_objects", []):
            land_type = land_object.get("land_type", "land").replace("_", " ").title()
            details = "-"
            if land_object.get("land_type") == "temporary_ranger_camp":
                details = (
                    f"zone {land_object.get('zone_id')} "
                    f"until tick {land_object.get('expires_at_tick')}"
                )
            self.land_table.insert("", tk.END, values=(
                land_type,
                land_object["name"],
                f"{land_object['x']},{land_object['y']}",
                details,
            ))

    def _render_entities(self, entities):
        self.entity_table.delete(*self.entity_table.get_children())
        ordered = sorted(entities, key=lambda e: (e["category"], e["species"], str(e["id"])))
        for entity in ordered:
            needs = self._entity_needs(entity)
            details = self._entity_details(entity)
            pos = f"{entity['x']},{entity['y']}"
            self.entity_table.insert(
                "",
                tk.END,
                values=(entity["name"], entity["species"], entity["state"], pos, needs, details)
            )

    def _entity_needs(self, entity):
        if entity["thirst"] is not None and entity["hunger"] is not None:
            return f"T{entity['thirst']} H{entity['hunger']}"
        if entity["seat_capacity"] is not None:
            seats = f"Riders {entity['seats_taken']}/{entity['seat_capacity']}"
            if entity["fuel_capacity"] is not None:
                seats += f" Fuel {entity['fuel_level']}/{entity['fuel_capacity']}"
            return seats
        return "-"

    def _entity_details(self, entity):
        if entity["category"] == "vehicle":
            if entity.get("active_trip_name"):
                return (
                    f"{entity['active_trip_name']} to "
                    f"{entity.get('trip_camp_x')},{entity.get('trip_camp_y')} "
                    f"until {entity.get('trip_end_tick')}"
                )
            scheduled = len(entity.get("scheduled_long_trips") or [])
            completed = entity.get("completed_long_trips", 0)
            return f"Camping trips {completed}/{scheduled}"
        if entity["category"] == "ranger":
            return f"Territory {entity.get('territory') or '-'}"
        if entity["category"] == "poacher":
            return f"Zone {entity.get('zone_id') or '-'} {entity.get('resolution') or 'active'}"
        if entity.get("death_cause"):
            return entity["death_cause"]
        return "-"

    def _render_species(self, species_counts):
        self.species_table.delete(*self.species_table.get_children())
        for species, count in species_counts.items():
            self.species_table.insert("", tk.END, values=(species, count))

    def _render_map(self, snapshot):
        canvas = self.map_canvas
        canvas.delete("all")

        width, height, pad, map_width, map_height = self._map_geometry()

        canvas.create_rectangle(
            pad, pad, width - pad, height - pad,
            fill="#eef5df",
            outline="#9eaa8a"
        )

        for step in range(0, GRID_WIDTH + 1, 10):
            x = self._sx(step, pad, map_width)
            canvas.create_line(x, pad, x, height - pad, fill="#d7dfc8")
        for step in range(0, GRID_HEIGHT + 1, 10):
            y = self._sy(step, pad, map_height)
            canvas.create_line(pad, y, width - pad, y, fill="#d7dfc8")

        mid_y = self._sy(GRID_HEIGHT / 2, pad, map_height)
        canvas.create_line(pad, mid_y, width - pad, mid_y, fill="#778a62", dash=(5, 4))

        for hole in snapshot["water_holes"]:
            if hole.get("kind") == "River":
                self._draw_river(canvas, hole, pad, map_width, map_height)

        for hole in snapshot["water_holes"]:
            if hole.get("kind") != "River":
                self._draw_water_hole(canvas, hole, pad, map_width, map_height)

        # Draw grazing areas
        for area in snapshot.get("grazing_areas", []):
            self._draw_grazing_area(canvas, area, pad, map_width, map_height)

        for area in snapshot.get("insect_feeding_grounds", []):
            self._draw_insect_feeding_ground(canvas, area, pad, map_width, map_height)

        for land_object in snapshot.get("land_objects", []):
            self._draw_land_object(canvas, land_object, pad, map_width, map_height)

        for entity in snapshot["entities"]:
            self._draw_entity(canvas, entity, pad, map_width, map_height)

        self._draw_weather_badge(canvas, snapshot, pad)

    def _map_geometry(self):
        canvas = self.map_canvas
        width = max(canvas.winfo_width(), 400)
        height = max(canvas.winfo_height(), 400)
        pad = 18
        return width, height, pad, width - pad * 2, height - pad * 2

    def _draw_weather_badge(self, canvas, snapshot, pad):
        weather = snapshot.get("weather", "CLEAR")
        emoji = {
            "CLEAR": "☀️",
            "RAIN": "🌧️",
            "DROUGHT": "🌵",
            "STORM": "⛈️",
        }.get(weather, "🌤️")
        text_id = canvas.create_text(
            pad + 10,
            pad + 9,
            text=f"{emoji} {weather.title()}",
            anchor="nw",
            fill="#243018",
            font=("Helvetica", 13, "bold")
        )
        bbox = canvas.bbox(text_id)
        if bbox:
            background = canvas.create_rectangle(
                bbox[0] - 7, bbox[1] - 4,
                bbox[2] + 7, bbox[3] + 4,
                fill="#fbfbf2",
                outline="#a4ad8e"
            )
            canvas.tag_lower(background, text_id)

    def _sx(self, value, pad, map_width):
        return pad + (float(value) / max(GRID_WIDTH - 1, 1)) * map_width

    def _sy(self, value, pad, map_height):
        return pad + (float(value) / max(GRID_HEIGHT - 1, 1)) * map_height

    def _draw_river(self, canvas, river, pad, map_width, map_height):
        path = river.get("path_points") or []
        points = []
        for grid_x, grid_y in path:
            points.extend([
                self._sx(grid_x, pad, map_width),
                self._sy(grid_y, pad, map_height),
            ])
        if len(points) < 4:
            return

        line_options = {
            "smooth": True,
            "capstyle": tk.ROUND,
            "joinstyle": tk.ROUND,
        }
        canvas.create_line(*points, fill="#c8f1ff", width=22, **line_options)
        canvas.create_line(*points, fill="#63c4e4", width=15, **line_options)
        canvas.create_line(*points, fill="#2384b5", width=5, **line_options)

        x = self._sx(river["x"], pad, map_width)
        y = self._sy(river["y"], pad, map_height)
        canvas.create_text(
            x + 14, y - 16,
            text=river["name"],
            anchor="w",
            fill="#16506c",
            font=("Helvetica", 10, "bold")
        )

    def _draw_water_hole(self, canvas, hole, pad, map_width, map_height):
        x = self._sx(hole["x"], pad, map_width)
        y = self._sy(hole["y"], pad, map_height)
        radius = 11
        canvas.create_oval(
            x - radius, y - radius, x + radius, y + radius,
            fill="#4aa3df",
            outline="#1e6f9f",
            width=2
        )
        canvas.create_text(
            x + 16, y,
            text=hole["name"],
            anchor="w",
            fill="#1e4f6d",
            font=("Helvetica", 10, "bold")
        )

    def _draw_insect_feeding_ground(self, canvas, area, pad, map_width, map_height):
        x = self._sx(area["x"], pad, map_width)
        y = self._sy(area["y"], pad, map_height)
        radius_x = 18
        radius_y = 10
        canvas.create_oval(
            x - radius_x, y - radius_y, x + radius_x, y + radius_y,
            fill="#d8b86a",
            outline="#8f6b21",
            width=2
        )
        for dx, dy in [(-7, -2), (0, 3), (7, -1)]:
            canvas.create_oval(
                x + dx - 2, y + dy - 2, x + dx + 2, y + dy + 2,
                fill="#654716",
                outline=""
            )
        canvas.create_text(
            x + radius_x + 6, y,
            text=area["name"],
            anchor="w",
            fill="#5c4218",
            font=("Helvetica", 10, "bold")
        )

    def _draw_land_object(self, canvas, land_object, pad, map_width, map_height):
        x = self._sx(land_object["x"], pad, map_width)
        y = self._sy(land_object["y"], pad, map_height)
        land_type = land_object.get("land_type", "land")
        if land_type == "ranger_station":
            fill, outline, roof, label = "#35614a", "#183425", "#244c38", "R"
        elif land_type == "temporary_ranger_camp":
            fill, outline, roof, label = "#4f6f54", "#1f3422", "#6f8b52", "C"
        else:
            fill, outline, roof, label = "#c78b42", "#6a4318", "#9c6027", "S"

        width = 20
        height = 16
        canvas.create_polygon(
            x - width / 2 - 2, y - height / 2,
            x, y - height / 2 - 10,
            x + width / 2 + 2, y - height / 2,
            fill=roof,
            outline=outline,
            width=2
        )
        canvas.create_rectangle(
            x - width / 2, y - height / 2,
            x + width / 2, y + height / 2,
            fill=fill,
            outline=outline,
            width=2
        )
        canvas.create_text(x, y, text=label, fill="#ffffff", font=("Helvetica", 9, "bold"))
        canvas.create_text(
            x + width / 2 + 7, y,
            text=self._land_object_label(land_object),
            anchor="w",
            fill=outline,
            font=("Helvetica", 10, "bold")
        )

    def _land_object_label(self, land_object):
        if land_object.get("land_type") != "temporary_ranger_camp":
            return land_object["name"]
        expires = land_object.get("expires_at_tick")
        suffix = f" until {expires}" if expires is not None else ""
        return f"{land_object['name']}{suffix}"

    def _draw_grazing_area(self, canvas, area, pad, map_width, map_height):
        x = self._sx(area["x"], pad, map_width)
        y = self._sy(area["y"], pad, map_height)
        radius_x = 20
        radius_y = 12
        canvas.create_oval(
            x - radius_x, y - radius_y, x + radius_x, y + radius_y,
            fill="#b7e29a",
            outline="#5a9f54",
            width=2
        )
        canvas.create_text(
            x + radius_x + 6, y,
            text=area["name"],
            anchor="w",
            fill="#2f5b2a",
            font=("Helvetica", 10, "bold")
        )

    def _draw_entity(self, canvas, entity, pad, map_width, map_height):
        x = self._sx(entity["x"], pad, map_width)
        y = self._sy(entity["y"], pad, map_height)
        category = entity["category"]
        state = entity["state"]

        palette = {
            "herbivore": ("#5a9f54", "#244d22"),
            "insectivore": ("#8a6fd1", "#40306f"),
            "carnivore": ("#d35a3a", "#682416"),
            "ranger": ("#214f3a", "#0e2118"),
            "vehicle": ("#e8b342", "#684600"),
            "poacher": ("#2b2b2b", "#000000"),
            "other": ("#6f7278", "#33363a"),
        }
        fill, outline = palette.get(category, palette["other"])
        if category == "vehicle" and entity.get("active_trip_name"):
            fill, outline = "#f08a3a", "#7a3d13"
        if not entity["is_alive"] or state == "DEAD":
            ticks_dead = entity.get("ticks_dead", 0)
            max_decay = 30
            if ticks_dead >= max_decay:
                return

            decay_ratio = ticks_dead / max_decay
            size = max(1, int(6 * (1 - decay_ratio)))
            grey_value = int(150 + 80 * decay_ratio)
            grey = f"#{grey_value:02x}{grey_value:02x}{grey_value:02x}"
            canvas.create_oval(
                x - size, y - size, x + size, y + size,
                fill=grey,
                outline="#aaaaaa",
                width=1
            )
            return

        size = 6
        if category in {"ranger", "vehicle"}:
            size = 8
        if category == "carnivore":
            canvas.create_polygon(
                x, y - size - 2,
                x - size - 2, y + size,
                x + size + 2, y + size,
                fill=fill,
                outline=outline,
                width=2
            )
        elif category == "poacher":
            canvas.create_polygon(
                x, y - size - 2,
                x + size + 2, y,
                x, y + size + 2,
                x - size - 2, y,
                fill=fill,
                outline=outline,
                width=2
            )
        elif category == "vehicle":
            canvas.create_rectangle(
                x - size - 2, y - size, x + size + 2, y + size,
                fill=fill,
                outline=outline,
                width=2
            )
        else:
            canvas.create_oval(
                x - size, y - size, x + size, y + size,
                fill=fill,
                outline=outline,
                width=2
            )

        label = entity["species"][:1]
        if category == "ranger":
            label = "R"
        elif category == "vehicle":
            label = "J"
        elif category == "poacher":
            label = "P"
        canvas.create_text(x, y, text=label, fill="#ffffff", font=("Helvetica", 8, "bold"))

        if category == "vehicle" and entity.get("seat_capacity") is not None:
            riders = f"{entity.get('seats_taken', 0)}/{entity.get('seat_capacity', 0)}"
            text_id = canvas.create_text(
                x,
                y + size + 11,
                text=riders,
                fill="#3f2b00",
                font=("Helvetica", 8, "bold")
            )
            bbox = canvas.bbox(text_id)
            if bbox:
                background = canvas.create_rectangle(
                    bbox[0] - 3, bbox[1] - 1,
                    bbox[2] + 3, bbox[3] + 1,
                    fill="#fff8df",
                    outline="#d7b45c"
                )
                canvas.tag_lower(background, text_id)

    def _update_buttons(self):
        running = bool(self.engine and self.engine.is_alive())
        self.start_button.configure(state=tk.DISABLED if running else tk.NORMAL)
        self.pause_button.configure(state=tk.NORMAL if running else tk.DISABLED)
        self.stop_button.configure(state=tk.NORMAL if running else tk.DISABLED)
        if running and self.engine.is_paused():
            self.pause_button.configure(text="Resume")
        else:
            self.pause_button.configure(text="Pause")

    def _on_close(self):
        self._stop_engine()
        self._detach_event_collector()
        self.destroy()


def main():
    app = SavannaApp()
    app.mainloop()


if __name__ == "__main__":
    main()
