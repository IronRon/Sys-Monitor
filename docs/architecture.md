# System Architecture

This document describes the overall software architecture of **Sys Monitor**.

While `collectors.md` explains how individual system resources are collected and `monitoring.md` explains sampling and history, this document focuses on:

* the major application layers
* module boundaries
* dependencies between components
* terminal monitoring flow
* Django dashboard flow
* API data flow
* frontend/backend communication
* the current background-monitoring model

The central architectural goal is:

> Keep system-data collection independent from how that data is displayed.

This allows the same monitoring engine to support multiple interfaces.

---

# High-Level Architecture

At the highest level, Sys Monitor separates operating-system access, collection, monitoring, persistence and presentation. Persistence is a side path from live monitoring rather than something the browser must pass through:

```text
Operating System
      ↓
Collection
      ↓
Monitoring
   ┌──┴──────────────┐
   ↓                 ↓
Presentation     Persistence
                 PostgreSQL
```

In the current application:

```mermaid
flowchart TD
    OS["Windows Operating System"]
    PS["psutil / CIM"]
    C["Collector Layer"]
    M["Monitoring Layer"]
    P["Telemetry Layer"]
    PG[(PostgreSQL)]
    DJ["Django Web Layer"]
    FE["Browser Frontend"]

    OS --> PS
    PS --> C
    C --> M

    M --> DJ
    DJ --> FE

    M --> P
    P --> PG
```

Each layer has a different responsibility.

---

# Application Layers

The current web-monitoring architecture can be divided into several responsibilities:

```text
┌──────────────────────────────────────────────┐
│                PRESENTATION                  │
│                                              │
│           Django + JavaScript + charts       │
└───────────────────────▲──────────────────────┘
                        │
┌───────────────────────┴──────────────────────┐
│               SERVICE / LIVE STATE           │
│                                              │
│        BackgroundMonitoringService           │
└──────────────▲──────────────────┬─────────────┘
               │                  │
┌──────────────┴──────────┐  ┌────▼─────────────┐
│      MONITORING         │  │    PERSISTENCE   │
│                         │  │                  │
│ SystemSampler           │  │ TelemetryWriter  │
│ ProcessSnapshotWorker   │  │ Django ORM       │
│ MonitorHistory          │  │ PostgreSQL       │
└──────────────▲──────────┘  └──────────────────┘
               │
┌──────────────┴───────────────────────────────┐
│                 COLLECTION                  │
│                                             │
│ CPU   Memory   Disk   Network   Processes   │
└───────────────────────▲─────────────────────┘
                        │
┌───────────────────────┴─────────────────────┐
│               SYSTEM ACCESS                 │
│                                             │
│              psutil / CIM                   │
└───────────────────────▲─────────────────────┘
                        │
┌───────────────────────┴─────────────────────┐
│             OPERATING SYSTEM                │
│                                             │
│                  Windows                    │
└─────────────────────────────────────────────┘
```

Persistence is intentionally a side path. PostgreSQL does not sit between the collectors and the live dashboard, so a telemetry write problem does not have to stop live monitoring.

# Project Structure

The current project structure is approximately:

```text
Sys_Monitor/
│
├── README.md
├── requirements.txt
│
├── docs/
│   ├── architecture.md
│   ├── collectors.md
│   ├── monitoring.md
│   ├── api.md
│   ├── frontend.md
│   └── concepts.md
│
└── src/
    │
    ├── collectors/
    │   ├── __init__.py
    │   ├── cpu.py
    │   ├── memory.py
    │   ├── disk.py
    │   ├── network.py
    │   ├── processes.py
    │   ├── hardware.py
    │   └── self_monitor.py
    │
    ├── hardware/
    │   ├── __init__.py
    │   ├── normalizer.py
    │   └── explanations.py
    │
    ├── monitoring/
    │   ├── __init__.py
    │   ├── sampler.py
    │   ├── process_worker.py
    │   └── history.py
    │
    ├── telemetry/
    │   ├── __init__.py
    │   ├── models.py
    │   ├── writer.py
    │   └── migrations/
    │
    ├── dashboard/
    │   ├── services.py
    │   ├── views.py
    │   ├── urls.py
    │   │
    │   ├── templates/
    │   │   └── dashboard/
    │   │       ├── _self_overhead.html
    │   │       ├── index.html
    │   │       ├── processes.html
    │   │       ├── hardware.html
    │   │       ├── memory.html
    │   │       ├── disk.html
    │   │       └── network.html
    │   │
    │   └── static/
    │       └── dashboard/
    │           ├── css/
    │           │   ├── dashboard.css
    │           │   ├── processes.css
    │           │   ├── hardware.css
    │           │   ├── memory.css
    │           │   ├── disk.css
    │           │   ├── network.css
    │           │   └── self_overhead.css
    │           └── js/
    │               ├── dashboard.js
    │               ├── processes.js
    │               ├── hardware.js
    │               ├── memory.js
    │               ├── disk.js
    │               ├── network.js
    │               └── self_overhead.js
    │
    ├── config/
    │   ├── settings.py
    │   ├── urls.py
    │   ├── asgi.py
    │   └── wsgi.py
    │
    ├── monitor.py
    ├── process_tree.py
    └── manage.py
```

---

# Module Boundaries

A major goal of the architecture is to keep responsibilities inside clearly defined modules.

```mermaid
flowchart LR
    subgraph Collection["Collection Layer"]
        CPU["cpu.py"]
        MEM["memory.py"]
        DISK["disk.py"]
        NET["network.py"]
        PROC["processes.py"]
        HARDWARE["hardware.py"]
    end

    subgraph Monitoring["Monitoring Layer"]
        SAMPLER["sampler.py"]
        PWORKER["process_worker.py"]
        HISTORY["history.py"]
    end

    subgraph Persistence["Telemetry Layer"]
        MODELS["telemetry/models.py"]
        WRITER["telemetry/writer.py"]
        PG[(PostgreSQL)]
    end

    subgraph Web["Django Layer"]
        SERVICE["BackgroundMonitoringService"]
        HSERVICE["HardwareService"]
        VIEWS["views.py"]
        URLS["urls.py"]
    end

    subgraph Frontend["Browser"]
        HTML["Templates"]
        JS["JavaScript"]
        CSS["CSS"]
        CHART["Chart.js / Cytoscape.js"]
    end

    CPU --> SAMPLER
    MEM --> SAMPLER
    DISK --> SAMPLER
    NET --> SAMPLER

    PROC --> PWORKER

    SAMPLER --> SERVICE
    PWORKER --> SERVICE
    HISTORY --> SERVICE

    SERVICE --> WRITER
    WRITER --> MODELS
    MODELS --> PG

    HARDWARE --> HSERVICE
    SERVICE --> VIEWS
    HSERVICE --> VIEWS
    URLS --> VIEWS
    VIEWS --> HTML
    VIEWS --> JS
    JS --> CHART
```

The dependency direction generally moves upward from Windows access toward application services and presentation.

Important boundaries include:

* collectors do not depend on Django,
* `SystemSampler` does not depend on PostgreSQL,
* `ProcessSnapshotWorker` owns slow process refreshes,
* `TelemetryWriter` receives already-built samples rather than collecting Windows metrics,
* browser code does not know how psutil/CIM retrieve data.

# Dependency Direction

A useful architectural rule for the project is:

> Lower-level monitoring code should not depend on higher-level presentation code.

Good dependency direction:

```text
dashboard
    ↓
monitoring
    ↓
collectors
    ↓
psutil
```

Avoid:

```text
collectors
    ↓
dashboard
```

or:

```text
sampler
    ↓
HTML
```

For example, this is appropriate:

```python
from monitoring.sampler import SystemSampler
```

inside the Django service.

But `sampler.py` should never need:

```python
from django.http import JsonResponse
```

because HTTP is not the sampler's responsibility.

---

# Layer 1 — Windows

At the bottom of the architecture is the operating system.

```mermaid
flowchart TD
    Programs["Running Programs"]
    Kernel["Windows Kernel"]
    Hardware["Hardware"]

    Programs --> Kernel
    Kernel --> Hardware
```

Windows manages resources such as:

* processor scheduling
* memory
* processes
* storage
* networking
* devices

Sys Monitor observes information exposed by the operating system.

The application does not directly control these resources at the current stage.

---

# Layer 2 — psutil

`psutil` acts as the main abstraction between Python and operating-system resource information.

```mermaid
flowchart TD
    App["Sys Monitor Python Code"]
    PS["psutil"]
    Windows["Windows System Interfaces"]

    App --> PS
    PS --> Windows
```

Instead of every module interacting directly with Windows APIs, the collector layer communicates through psutil.

For example:

```text
Sys Monitor
    ↓
psutil.cpu_percent()
    ↓
Windows CPU information
```

---

# Layer 3 — Collectors

Collectors isolate resource-specific retrieval logic.

```mermaid
flowchart TD
    PS["psutil"]

    CPU["CPU Collector"]
    MEM["Memory Collector"]
    DISK["Disk Collector"]
    NET["Network Collector"]
    PROC["Process Collector"]

    PS --> CPU
    PS --> MEM
    PS --> DISK
    PS --> NET
    PS --> PROC
```

Each collector returns Python data.

Example:

```text
CPU collector
    ↓
{
    total_percent,
    per_cpu_percent,
    physical_cores,
    logical_processors
}
```

The collectors are intentionally unaware of:

* terminal formatting
* Django
* HTML
* JavaScript
* Chart.js
* HTTP
* database storage

---

# Layer 4 — Monitoring

The monitoring layer combines fast collector data with independently refreshed process data.

```mermaid
flowchart TD
    CPU["CPU"]
    MEM["Memory"]
    DISK["Disk"]
    NET["Network"]
    PROC["Processes"]

    SAMPLER["SystemSampler"]
    PWORKER["ProcessSnapshotWorker"]
    SERVICE["BackgroundMonitoringService"]

    CPU --> SAMPLER
    MEM --> SAMPLER
    DISK --> SAMPLER
    NET --> SAMPLER

    PROC --> PWORKER

    SAMPLER --> SERVICE
    PWORKER --> SERVICE
    SERVICE --> SNAP["Combined Latest Sample"]
```

The `SystemSampler` now performs the fast operations such as:

* combining CPU, memory, disk and network measurements
* calculating disk throughput
* calculating network throughput
* maintaining previous counter state
* creating timezone-aware timestamps
* measuring fast-sample duration

Process enumeration is deliberately separated into `ProcessSnapshotWorker` because profiling showed that a full process scan can take around 1.5 seconds on the development PC. The service combines the cached process snapshot with the fast system sample without forcing the fast path to wait for another process scan.

# System Sample as an Internal Contract

The combined sample published by `BackgroundMonitoringService` is an important architectural boundary.

Higher-level consumers receive a structure containing:

```text
sample
│
├── timestamp
├── cpu
├── memory
├── disk
├── network
├── processes
└── self_monitor
```

The individual pieces do not all originate from the same worker:

```text
SystemSampler
    → fast CPU/RAM/disk/network/self values

ProcessSnapshotWorker
    → cached process values

BackgroundMonitoringService
    → combines both into the live contract
```

This means the API can keep one stable response structure without requiring every underlying metric to have exactly the same collection cost or refresh cadence.

`TelemetryWriter` also consumes this combined sample, but stores only a compact subset suitable for long-term history.

# System Sample Flow

```mermaid
flowchart LR
    FAST["Fast Collectors"] --> S["SystemSampler"]
    PROC["Process Collector"] --> PW["ProcessSnapshotWorker"]

    S --> SERVICE["BackgroundMonitoringService"]
    PW --> SERVICE

    SERVICE --> SAMPLE["Combined Sample"]

    SAMPLE --> LIVE["Live APIs"]
    SAMPLE --> HISTORY["MonitorHistory"]
    SAMPLE --> WRITER["TelemetryWriter"]
    WRITER --> PG[(PostgreSQL)]
```

The same combined sample can therefore feed both volatile live state and durable telemetry without the database participating in Windows collection.

# History Architecture

The sampler creates individual measurements.

`MonitorHistory` stores multiple measurements.

```mermaid
flowchart LR
    S1["Sample 1"]
    S2["Sample 2"]
    S3["Sample 3"]
    SN["..."]

    HISTORY["MonitorHistory\nmax 60 samples"]

    S1 --> HISTORY
    S2 --> HISTORY
    S3 --> HISTORY
    SN --> HISTORY
```

The distinction is:

```text
SystemSampler
    ↓
creates one snapshot

MonitorHistory
    ↓
retains many snapshots
```

---

# Rolling History

The current history architecture is:

```text
                         newest
                           ↓
[05][06][07][08] ... [63][64]
 ↑
oldest
```

When a new sample arrives:

```text
Before:

[05][06][07] ... [63][64]

New sample:
[65]

After:

[06][07][08] ... [64][65]
```

The oldest sample is automatically discarded.

This keeps memory use bounded.

---

# Persistence Layer — Telemetry and PostgreSQL

Persistent telemetry now forms a parallel path beside the short in-memory live history.

```mermaid
flowchart LR
    SERVICE["BackgroundMonitoringService"]
    LIVE["Latest Sample + MonitorHistory"]
    WRITER["TelemetryWriter"]
    ORM["Django ORM"]
    PG[(PostgreSQL)]

    SERVICE --> LIVE
    SERVICE --> WRITER
    WRITER --> ORM
    ORM --> PG
```

The telemetry app is intentionally separate from collectors and monitoring:

```text
monitoring/
    ↓
produces live data

telemetry/
    ↓
persists selected historical data

dashboard/
    ↓
serves live APIs and pages
```

## Telemetry Models

The current relational model is:

```mermaid
erDiagram
    DEVICE ||--o{ SYSTEM_METRIC_SAMPLE : has
    DEVICE ||--o{ MONITOR_OVERHEAD_SAMPLE : hosts

    DEVICE {
        bigint id
        slug key
        string name
        string device_type
        string hostname
        datetime last_seen_at
    }

    SYSTEM_METRIC_SAMPLE {
        bigint id
        datetime timestamp
        float cpu_percent
        float memory_percent
        bigint memory_in_use_bytes
        float disk_read_bytes_per_second
        float network_download_bytes_per_second
        int process_count
        string top_cpu_process_name
    }

    MONITOR_OVERHEAD_SAMPLE {
        bigint id
        datetime timestamp
        int backend_pid
        float cpu_percent
        bigint memory_bytes
        float sample_duration_ms
    }
```

`Device` provides a stable parent for telemetry. This prevents every row from repeating device identity and also prepares the schema for another device type later.

Both sample tables have a composite index beginning with their device foreign key and timestamp. This matches the expected analytics query pattern:

```text
one device
+ time range
```

## ORM Boundary

Application code normally persists/query data through Django model classes:

```text
Python model operation
        ↓
Django ORM
        ↓
Django PostgreSQL backend
        ↓
Psycopg 3
        ↓
PostgreSQL
```

The ORM is an abstraction over the relational database; PostgreSQL remains the actual persistent store.

## TelemetryWriter

`TelemetryWriter.write_if_due()` receives an already-built monitoring sample. It does not collect Windows metrics itself.

Approximately every five seconds it:

1. resolves/caches the current `Device`,
2. selects compact system metrics,
3. selects the leading CPU and memory process,
4. creates `SystemMetricSample`,
5. creates `MonitorOverheadSample`,
6. updates `Device.last_seen_at`.

The related writes run inside `transaction.atomic()` so they form one database transaction. Database failures are caught at the persistence boundary so the live monitor can continue even when PostgreSQL is temporarily unavailable.

---

# Presentation Layer

The system currently has two separate presentation paths.

```mermaid
flowchart TD
    MON["Monitoring Engine"]

    MON --> CLI["Terminal Interface"]
    MON --> WEB["Web Interface"]

    CLI --> TERM["PowerShell / Terminal"]

    WEB --> DJ["Django"]
    DJ --> BROWSER["Browser"]
```

This demonstrates one of the main advantages of separating monitoring logic from presentation.

---

# Terminal Architecture

The terminal interface is:

```text
src/monitor.py
```

Its responsibility is primarily orchestration and presentation.

---

# Terminal Flow

```mermaid
flowchart TD
    START["Start monitor.py"]

    CREATE["Create SystemSampler<br/>Create MonitorHistory"]

    PRIME["Prime CPU, process,<br/>disk and network state"]

    WAIT["Wait until next sample"]

    SAMPLE["SystemSampler.sample()"]

    HISTORY["history.add(sample)"]

    PRINT["print_sample()"]

    CHECK{"User pressed Ctrl+C?"}

    STOP["Graceful shutdown"]

    START --> CREATE
    CREATE --> PRIME
    PRIME --> WAIT
    WAIT --> SAMPLE
    SAMPLE --> HISTORY
    HISTORY --> PRINT
    PRINT --> CHECK

    CHECK -- No --> WAIT
    CHECK -- Yes --> STOP
```

---

# Terminal Sequence

Another way to view the terminal monitor is as a sequence:

```mermaid
sequenceDiagram
    participant User
    participant Monitor as monitor.py
    participant Sampler as SystemSampler
    participant Collectors
    participant History as MonitorHistory

    User->>Monitor: Run monitor.py

    Monitor->>Sampler: prime()
    Sampler->>Collectors: Read initial counters
    Collectors-->>Sampler: Baseline values

    loop Every sampling cycle
        Monitor->>Monitor: Wait approximately 1 second

        Monitor->>Sampler: sample(elapsed_seconds)

        Sampler->>Collectors: Get current measurements
        Collectors-->>Sampler: Raw data

        Sampler->>Sampler: Calculate rates

        Sampler-->>Monitor: Complete sample

        Monitor->>History: add(sample)

        Monitor->>Monitor: print_sample()
    end

    User->>Monitor: Ctrl+C
    Monitor-->>User: Monitor stopped cleanly
```

---

# Why the Terminal Interface Is Thin

`monitor.py` should not contain detailed psutil logic.

Instead of:

```text
monitor.py
├── calculate CPU
├── calculate network
├── calculate disk
├── process iteration
├── history implementation
└── printing
```

the design is:

```text
monitor.py
├── ask sampler for data
├── add to history
└── print data
```

This keeps the terminal interface replaceable.

---

# Web Architecture

The Django side adds several additional layers because the browser does not directly run the Python monitoring code.

```mermaid
flowchart TD
    Browser["Browser"]

    URL["Django URL Router"]

    View["Django View"]

    Service["BackgroundMonitoringService"]

    Sampler["SystemSampler"]

    Collectors["Collectors"]

    Browser --> URL
    URL --> View
    View --> Service
    Service --> Sampler
    Sampler --> Collectors
```

The result then flows back in the opposite direction.

```mermaid
flowchart BT
    Collectors["Collectors"]
    Sampler["SystemSampler"]
    Service["BackgroundMonitoringService"]
    View["Django View"]
    JSON["JSON Response"]
    JS["dashboard.js"]
    UI["Dashboard UI"]

    Collectors --> Sampler
    Sampler --> Service
    Service --> View
    View --> JSON
    JSON --> JS
    JS --> UI
```

---

# Django Components

The important Django modules currently are:

```text
dashboard/
├── services.py
├── views.py
├── urls.py
├── templates/
└── static/
```

Their responsibilities are different.

---

# `urls.py`

The URL configuration determines:

> Which view should handle this URL?

Current important routes:

```text
/
```

and:

```text
/api/system/
```

Conceptually:

```mermaid
flowchart LR
    REQUEST["Incoming URL"]

    ROUTER["dashboard/urls.py"]

    INDEX["index()"]
    API["system_api()"]

    REQUEST --> ROUTER

    ROUTER -- "/" --> INDEX
    ROUTER -- "/api/system/" --> API
```

---

# `views.py`

The Django views deal with HTTP requests.

The dashboard view:

```text
GET /
    ↓
index()
    ↓
render index.html
```

The API view:

```text
GET /api/system/
    ↓
system_api()
    ↓
BackgroundMonitoringService
    ↓
JSON response
```

The view should remain relatively thin.

It should not know how disk throughput is calculated.

---

# `BackgroundMonitoringService`

`dashboard/services.py` now owns one continuously updated monitoring stream for the web application.

```mermaid
flowchart LR
    WORKER["Background sampler thread"]
    SERVICE["BackgroundMonitoringService"]
    SAMPLER["SystemSampler"]
    HISTORY["MonitorHistory"]
    LATEST["Latest complete sample"]
    API1["/api/system/"]
    API2["/api/processes/"]

    SERVICE --> WORKER
    WORKER --> SAMPLER
    SAMPLER --> LATEST
    WORKER --> HISTORY
    LATEST --> API1
    HISTORY --> API1
    LATEST --> API2
```

The service owns the sampler, history, latest sample, worker thread, lifecycle events and synchronization lock. The complete process list is retained in the latest sample for the Processes API, but historical entries remain smaller.

---

# Why Use a Service Layer?

Without `BackgroundMonitoringService`:

```text
Django View
    ↓
SystemSampler
    ↓
history
    ↓
thread lock
    ↓
timing
    ↓
serialization
```

The view would have too many responsibilities.

With the service:

```text
View
    ↓
get_system_data()
    ↓
Service manages everything else
```

This gives a cleaner HTTP layer.

---

# Service Boundary

```mermaid
flowchart LR
    subgraph Django["HTTP / Django"]
        VIEW["View"]
    end

    subgraph ServiceLayer["Application Service"]
        SERVICE["BackgroundMonitoringService"]
        HSERVICE["HardwareService"]
    end

    subgraph Core["Monitoring Core"]
        SAMPLE["SystemSampler"]
        HISTORY["MonitorHistory"]
    end

    VIEW --> SERVICE
    SERVICE --> SAMPLE
    SERVICE --> HISTORY
```

This is an important boundary.

Django-specific code lives above the monitoring core.

---

# Current API Architecture

The browser retrieves monitoring data from:

```text
/api/system/
```

using an HTTP GET request.

The complete current path is:

```mermaid
flowchart TD
    BROWSER["Browser"]

    FETCH["fetch('/api/system/')"]

    DJANGO["Django"]

    VIEW["system_api()"]

    SERVICE["BackgroundMonitoringService"]

    SAMPLER["SystemSampler"]

    COLLECTORS["Collectors"]

    WINDOWS["Windows"]

    BROWSER --> FETCH
    FETCH --> DJANGO
    DJANGO --> VIEW
    VIEW --> SERVICE
    SERVICE --> SAMPLER
    SAMPLER --> COLLECTORS
    COLLECTORS --> WINDOWS
```

The response travels back:

```mermaid
flowchart TD
    WINDOWS["Windows"]

    COLLECTORS["Collectors"]

    SAMPLER["SystemSampler"]

    SERVICE["BackgroundMonitoringService"]

    SERIALIZE["Serialize Python data"]

    JSON["HTTP JSON Response"]

    JS["dashboard.js"]

    UI["Dashboard"]

    WINDOWS --> COLLECTORS
    COLLECTORS --> SAMPLER
    SAMPLER --> SERVICE
    SERVICE --> SERIALIZE
    SERIALIZE --> JSON
    JSON --> JS
    JS --> UI
```

---

# End-to-End Web Request

Collection and HTTP delivery are now separate flows. The background thread continuously produces samples; browser requests only retrieve the latest published state.

```mermaid
sequenceDiagram
    participant Worker as Background sampler thread
    participant Sampler as SystemSampler
    participant Collectors
    participant Service as BackgroundMonitoringService
    participant JS as dashboard.js
    participant Django as Django API

    loop approximately every 1 second
        Worker->>Sampler: sample(elapsed_seconds)
        Sampler->>Collectors: Read system resources
        Collectors-->>Sampler: Raw measurements
        Sampler-->>Worker: Complete sample
        Worker->>Service: Publish latest sample + history
    end

    JS->>Django: GET /api/system/
    Django->>Service: get_system_data()
    Service-->>Django: Copy of latest data
    Django-->>JS: JSON response
    JS->>JS: Update cards and charts
```

---

# Current Dashboard Presentation

The browser now uses the same `/api/system/` response for several visual components:

```mermaid
flowchart LR
    API["/api/system/"]
    JS["dashboard.js"]

    CARD["Overview Cards"]
    GRAPH["CPU History Graph"]
    CORES["Logical Processor Grid"]
    CPU["Top CPU Table"]
    RAM["Top Memory Table"]

    API --> JS
    JS --> CARD
    JS --> GRAPH
    JS --> CORES
    JS --> CPU
    JS --> RAM
```

The logical-processor grid and process tables are generated dynamically from the arrays returned by the API, so the presentation adapts to the data rather than assuming a fixed number of CPU entries or process rows.

---


# Dedicated Processes Page

The web interface now has a second monitoring page at `/processes/`. It uses a separate JSON endpoint so the main system endpoint does not need to send the complete process list on every overview refresh.

```mermaid
flowchart LR
    PAGE["/processes/"]
    JS["processes.js"]
    API["/api/processes/"]
    SERVICE["BackgroundMonitoringService"]
    LATEST["Latest shared sample"]

    PAGE --> JS
    JS -->|"poll"| API
    API --> SERVICE
    SERVICE --> LATEST
    LATEST --> SERVICE
    SERVICE --> API
    API -->|"flat PID/PPID JSON"| JS
    JS --> TABLE["Sortable / searchable table"]
    JS --> TREE["Expandable process tree"]
```

The API returns a flat list of process objects. `processes.js` uses PID/PPID relationships to build the hierarchy in the browser, so the same data can power both the table and tree views.

---

# Process Graph Architecture

The dedicated Processes page now has three presentations of the same `/api/processes/` data: Table, expandable Tree and interactive Graph. No new backend endpoint was required.

```mermaid
flowchart TD
    API["/api/processes/"] --> JS["processes.js"]
    JS --> TABLE["Table view"]
    JS --> TREE["Expandable tree"]
    JS --> CY["Cytoscape.js graph"]
    CY --> DAGRE["Dagre directed layout"]
    DAGRE --> CANVAS["Interactive process forest"]
```

Each process becomes a Cytoscape node. If its PPID is present in the current process set, JavaScript creates a directed edge from the parent PID to the child PID. Processes whose parents are absent become graph roots, so the result is usually a **forest** containing several independent trees.

The initial layout is calculated by Dagre. Live refreshes then update existing graph elements without automatically rerunning the layout, which preserves the user's pan and zoom position while inspecting the graph.


# Static Hardware Architecture

The Hardware / About My PC feature follows a separate path from the one-second monitoring loop.

```mermaid
flowchart LR
    WIN["Windows CIM / Storage Interfaces"]
    PS["PowerShell"]
    HC["hardware.py"]
    N["normalizer.py"]
    E["explanations.py"]
    HS["HardwareService cache"]
    API["/api/hardware/"]
    JS["hardware.js"]
    UI["About My PC page"]

    WIN --> PS
    PS --> HC
    HC --> N
    N --> HS
    N --> E
    E --> HS
    HS --> API
    API --> JS
    JS --> UI
```

The important distinction is:

```text
BackgroundMonitoringService
    = continuously changing performance telemetry

HardwareService
    = slow-changing hardware identity collected once and cached
```

The explanation layer derives generic educational text from detected properties instead of hard-coding a paragraph for every possible CPU, GPU, RAM or disk model.

---
# Self-Overhead Architecture

Self-monitoring is deliberately integrated with the shared monitoring pipeline.

```mermaid
flowchart TD
    PROC["Python / Django backend process"]
    SELF["SelfMonitorCollector"]
    SAMPLER["SystemSampler"]
    SAMPLE["latest_sample.self_monitor"]
    HISTORY["MonitorHistory self subset"]
    API["GET /api/self/"]
    PARTIAL["_self_overhead.html"]
    JS["self_overhead.js"]
    WIDGET["Floating Sys Monitor Cost widget"]

    PROC --> SELF
    SELF --> SAMPLER
    SAMPLER --> SAMPLE
    SAMPLER --> HISTORY
    SAMPLE --> API
    HISTORY --> API
    API --> JS
    PARTIAL --> WIDGET
    JS --> WIDGET
```

The feature introduces three reusable pieces:

```text
collectors/self_monitor.py
    → process-level backend measurements

/api/self/
    → read-only view of already sampled self-overhead data

_self_overhead.html + self_overhead.css/js
    → reusable widget included by monitoring pages
```

`SystemSampler` remains the single owner of live collection. The self-overhead API therefore does not create another psutil sampling path.

The current measurement boundary is the **Python/Django backend process**. Browser-side rendering is a separate process boundary and is intentionally excluded. This matters especially on the Processes Graph page, where Cytoscape rendering load belongs to the browser rather than the backend.

The self-monitor section also reuses the current Network socket list to count sockets owned by the Sys Monitor PID. This avoids another expensive system-wide socket enumeration.

---

# Dedicated Memory, Disk and Network Pages

The Memory and Disk pages are specialised views over the same background telemetry stream used by the overview dashboard. They do not own new samplers.

```mermaid
flowchart TD
    BG["BackgroundMonitoringService"]
    LATEST["latest_sample"]
    HISTORY["MonitorHistory"]

    BG --> LATEST
    BG --> HISTORY

    LATEST --> MEMAPI["/api/memory/"]
    HISTORY --> MEMAPI
    LATEST --> DISKAPI["/api/disk/"]
    HISTORY --> DISKAPI
    LATEST --> NETAPI["/api/network/"]
    HISTORY --> NETAPI

    HW["HardwareService"] --> HWAPI["/api/hardware/"]
    DNS["HostnameResolver"] --> NETAPI

    MEMAPI --> MEMPAGE["Memory page"]
    HWAPI --> MEMPAGE

    DISKAPI --> DISKPAGE["Disk page"]
    HWAPI --> DISKPAGE

    NETAPI --> NETPAGE["Network page"]
```

The Memory page combines:

```text
live physical-memory + page-file telemetry
        +
60-sample memory history
        +
top memory processes
        +
cached physical DIMM information
```

The Disk page combines:

```text
live C: filesystem capacity
        +
system-wide read/write throughput history
        +
cached physical-drive identity / health
```

The Network page combines:

```text
live system upload/download rates
        +
per-interface counters, addresses and adapter state
        +
current TCP/UDP socket relationships
        +
best-effort reverse-DNS hostname enrichment
```

Connection objects are retained only in the latest sample; the rolling history stores network throughput rates rather than 60 copies of the socket table.

This creates an important architectural distinction: **live resource behaviour** comes from `BackgroundMonitoringService`, **slow optional hostname metadata** comes from `HostnameResolver`, while **what hardware is installed** comes from `HardwareService`.

---

# Browser Architecture

The browser contains three main frontend technologies:

```text
HTML
CSS
JavaScript
```

plus Chart.js.

```mermaid
flowchart TD
    HTML["index.html<br/>Structure"]
    CSS["dashboard.css<br/>Presentation"]
    JS["dashboard.js<br/>Behaviour"]
    CHART["Chart.js<br/>Visualisation"]

    HTML --> PAGE["Dashboard"]
    CSS --> PAGE
    JS --> PAGE
    CHART --> PAGE
```

---

# HTML Responsibility

`index.html` defines the structure of the page.

For example:

```text
Dashboard
├── Header
├── CPU card
├── Memory card
├── Disk card
├── Network card
├── CPU chart
└── Footer
```

The initial values can contain placeholders such as:

```text
--%
```

JavaScript later replaces these values.

---

# CSS Responsibility

`dashboard.css` controls presentation:

```text
layout
spacing
fonts
background
cards
responsive behaviour
```

CSS does not retrieve monitoring data.

---

# JavaScript Responsibility

`dashboard.js` controls the live behaviour.

```mermaid
flowchart TD
    START["Page loaded"]

    FETCH["Fetch /api/system/"]

    JSON["Parse JSON"]

    CARDS["Update metric cards"]

    GRAPH["Update CPU graph"]

    WAIT["Wait ~1 second"]

    START --> FETCH
    FETCH --> JSON
    JSON --> CARDS
    JSON --> GRAPH
    CARDS --> WAIT
    GRAPH --> WAIT
    WAIT --> FETCH
```

---

# Chart.js Boundary

Chart.js is not part of the monitoring engine.

It receives ordinary frontend data and draws it.

```text
Monitoring history
       ↓
JSON
       ↓
dashboard.js
       ↓
labels + values
       ↓
Chart.js
       ↓
Canvas graph
```

For example:

```text
history
│
├── 20:10:01 → 10%
├── 20:10:02 → 14%
└── 20:10:03 → 21%
```

becomes:

```text
labels:
[20:10:01, 20:10:02, 20:10:03]

values:
[10, 14, 21]
```

Chart.js then visualises those arrays.

---

# Frontend/Backend Boundary

One of the most important architectural boundaries is HTTP/JSON.

```mermaid
flowchart LR
    subgraph Backend["Python Backend"]
        MON["Monitoring"]
        DJ["Django"]
    end

    subgraph Boundary["HTTP Boundary"]
        API["JSON API"]
    end

    subgraph Frontend["Browser"]
        JS["JavaScript"]
        UI["HTML / Chart.js"]
    end

    MON --> DJ
    DJ --> API
    API --> JS
    JS --> UI
```

Python does not directly modify browser HTML.

JavaScript does not directly call psutil.

They communicate through JSON.

---

# Why JSON?

JSON provides a language-independent data format.

Python may have:

```python
{
    "cpu": {
        "percent": 14.7
    }
}
```

Django converts it into JSON:

```json
{
    "cpu": {
        "percent": 14.7
    }
}
```

JavaScript then receives an object where it can use:

```javascript
data.cpu.percent
```

This cleanly separates backend and frontend technologies.

---

# Current Background-Monitoring Architecture

The browser no longer determines when measurements are taken. The Django process now contains separate workers for fast system sampling and slower process snapshots.

```mermaid
flowchart TD
    FAST["sys-monitor-sampler<br/>~1 second target"]
    SAMPLER["SystemSampler"]
    PTHREAD["process-snapshot-worker"]
    PCACHE["Cached process snapshot"]
    SERVICE["BackgroundMonitoringService"]
    LATEST["Latest combined sample"]
    HISTORY["60-sample MonitorHistory"]
    WRITER["TelemetryWriter<br/>~5 second persistence"]
    PG[(PostgreSQL)]
    API["Live JSON APIs"]

    FAST --> SAMPLER
    PTHREAD --> PCACHE
    SAMPLER --> SERVICE
    PCACHE --> SERVICE
    SERVICE --> LATEST
    SERVICE --> HISTORY
    SERVICE --> WRITER
    WRITER --> PG
    LATEST --> API
    HISTORY --> API
```

Profiling motivated this separation. Before the process worker, process enumeration dominated the main sample and pushed the effective cadence beyond two seconds. After moving it off the fast path, the main system sampler typically completes in roughly 50–130 ms while process enumeration can continue independently for roughly 1.5 seconds.

## Browser Open or Closed

```text
Django process running
        ↓
background workers running
        ↓
samples continue

Browser open
        ↓
polls APIs and displays latest samples

Browser closed
        ↓
frontend polling stops, but monitoring and telemetry persistence continue
```

Multiple browser clients still read the same shared latest state rather than triggering extra collector passes.

## Worker Lifecycle

Both the fast sampler thread and process snapshot worker are daemon-backed background workers, so they do not keep Python alive by themselves. `BackgroundMonitoringService.stop()` signals the fast sampler to stop, joins it briefly, and also stops the process worker. An `atexit` handler requests this shutdown during normal interpreter exit.

# Restarting Django Loses History

The **live in-memory** history still disappears when Django restarts:

```text
Django running
    ↓
MonitorHistory exists in RAM

Django stops
    ↓
MonitorHistory disappears
```

However, compact telemetry written to PostgreSQL remains durable across restarts.

This creates two intentionally different history stores:

```text
MonitorHistory
    → short live window

PostgreSQL
    → persistent long-term data
```

# Shared Monitoring State

The service owns mutable state such as the latest sample, rolling history, worker lifecycle and sampler counters. A re-entrant lock (`RLock`) protects publication and copying of this state.

```mermaid
sequenceDiagram
    participant Worker as Background worker
    participant Lock
    participant State as Shared state
    participant API as API request

    Worker->>Lock: acquire
    Worker->>State: publish latest sample
    Worker->>Lock: release

    API->>Lock: acquire
    API->>State: copy latest data
    API->>Lock: release
```

The API works with copied data after releasing the lock, keeping contention short.

---

# Current Runtime Components

When the Django dashboard is running, the important runtime components are approximately:

```mermaid
flowchart LR
    subgraph Machine["Windows PC"]
        Django["Django Development Server"]
        Python["Python Monitoring Code"]
        Browser["Web Browser"]

        Django --> Python
        Browser <--> Django
    end
```

Both the web server and monitoring code run locally.

No external server is currently required for the monitoring API.

Chart.js is currently loaded externally through a CDN, but the monitoring data itself stays local.

---

# Terminal vs Web Architecture

The two current interfaces can be compared as:

```text
TERMINAL

Windows
   ↓
psutil
   ↓
Collectors
   ↓
SystemSampler
   ↓
MonitorHistory
   ↓
monitor.py
   ↓
PowerShell


WEB

Windows
   ↓
psutil
   ↓
Collectors
   ↓
SystemSampler
   ↓
MonitorHistory
   ↓
BackgroundMonitoringService
   ↓
Django View
   ↓
JSON
   ↓
dashboard.js
   ↓
Browser
```

The lower layers are reused.

Only the presentation path changes.

---

# Shared Core

This reuse is an important design property:

```mermaid
flowchart TD
    CORE["Shared Monitoring Core"]

    CLI["Terminal"]
    WEB["Django Dashboard"]
    FUTURE["Future Interfaces"]

    CORE --> CLI
    CORE --> WEB
    CORE -.-> FUTURE
```

Possible future interfaces include:

* desktop GUI
* tray application
* command-line queries
* remote API
* mobile dashboard
* other local applications

---

# Separation of Concerns

The architecture follows separation of concerns.

```text
cpu.py
    ↓
knows CPU collection

history.py
    ↓
knows rolling history

sampler.py
    ↓
knows sampling

services.py
    ↓
knows web monitoring lifecycle

views.py
    ↓
knows HTTP

dashboard.js
    ↓
knows browser behaviour

Chart.js
    ↓
knows chart rendering
```

No single module should need to understand every part of the system.

---

# Example: Adding a New Metric

Suppose we later add:

```text
CPU frequency
```

A healthy architecture might require:

```text
1. cpu.py
      ↓
collect frequency

2. sampler.py
      ↓
add it to sample

3. API serialization
      ↓
expose it

4. dashboard.js
      ↓
read it

5. HTML
      ↓
display it
```

We should **not** need to rewrite unrelated disk or network code.

---

# Example: Replacing Chart.js

Suppose the frontend later changes chart library.

Current:

```text
SystemSampler
    ↓
JSON
    ↓
Chart.js
```

Future:

```text
SystemSampler
    ↓
JSON
    ↓
Different chart library
```

The collectors and monitoring code should remain unchanged.

That is one of the benefits of strong boundaries.

---

# Example: Replacing psutil

Similarly, suppose CPU collection later uses Windows Performance Counters.

Current:

```text
cpu.py
    ↓
psutil
```

Future:

```text
cpu.py
    ↓
Windows Performance Counters
```

If the collector continues returning the same structure:

```python
{
    "total_percent": ...,
    "per_cpu_percent": ...
}
```

then the sampler and dashboard may not need significant changes.

This is the benefit of abstraction.

---

# Current Architecture Summary

The complete current system can be represented as:

```mermaid
flowchart TD
    WIN["Windows"]
    PS["psutil / CIM"]

    subgraph Collection["Collection"]
        FASTCOL["CPU / Memory / Disk / Network"]
        PROC["Processes"]
        HW["Static Hardware"]
    end

    subgraph Monitoring["Monitoring"]
        SAMPLER["SystemSampler"]
        PWORKER["ProcessSnapshotWorker"]
        SERVICE["BackgroundMonitoringService"]
        HISTORY["MonitorHistory"]
    end

    subgraph Persistence["Persistence"]
        WRITER["TelemetryWriter"]
        ORM["Django ORM / Psycopg"]
        PG[(PostgreSQL)]
    end

    subgraph Web["Django + Browser"]
        API["Live APIs"]
        UI["Dashboard Pages"]
    end

    WIN --> PS
    PS --> FASTCOL
    PS --> PROC
    WIN --> HW

    FASTCOL --> SAMPLER
    PROC --> PWORKER
    SAMPLER --> SERVICE
    PWORKER --> SERVICE
    SERVICE --> HISTORY

    SERVICE --> API
    HISTORY --> API
    API --> UI

    SERVICE --> WRITER
    WRITER --> ORM
    ORM --> PG
```

The architecture therefore has two history paths:

```text
MonitorHistory
    → short, volatile, high-frequency live UI history

PostgreSQL telemetry
    → compact, durable, lower-frequency historical data
```

# Current Web Data Flow Summary

```mermaid
flowchart LR
    B["Browser"]
    D["Django"]
    MS["BackgroundMonitoringService"]
    SS["SystemSampler"]
    C["Collectors"]
    W["Windows"]

    B -- "GET /api/system/" --> D
    D --> MS
    MS --> SS
    SS --> C
    C --> W

    W --> C
    C --> SS
    SS --> MS
    MS --> D
    D -- "JSON" --> B
```

---

# Architectural Principles

The project currently follows several useful principles.

## Single Responsibility

Modules should have one main reason to change.

---

## Separation of Concerns

System collection, sampling, storage and presentation are kept separate.

---

## Abstraction

Higher layers depend on simple interfaces rather than implementation details.

---

## Reuse

The monitoring engine supports more than one interface.

---

## Bounded State

Live history currently uses a fixed-size rolling buffer.

---

## Explicit Data Flow

Monitoring data moves through known layers rather than relying on hidden global behaviour.

---

## Thin Views

Django views primarily deal with HTTP rather than implementing monitoring calculations.

---

# Current Architectural Limitations

The background sampler removes browser-driven collection, but the design is still intentionally local and lightweight. Important limitations include:

* the worker thread lives inside the Django Python process
* stopping/restarting Django stops the worker and clears in-memory history
* multiple separate Django processes would not share the same latest sample/history
* no message queue exists
* no WebSocket streaming exists
* the browser still polls the APIs to receive updates
* no authentication exists
* PostgreSQL telemetry exists, but no long-term historical query/service layer or analytics API has been built yet

These are appropriate trade-offs for the current local application.

---

# Evolution Path

Current:

```text
Django process
    │
    ├── fast system sampler
    ├── process snapshot worker
    ├── 60-sample live history
    └── TelemetryWriter
             ↓
         PostgreSQL
    │
    └── live APIs
             ↓
         Dashboard
```

The next architectural step is not adding persistence—it now exists. The next step is to build a query/analytics layer over the persisted rows:

```text
PostgreSQL telemetry
        ↓
Telemetry query/service layer
        ↓
aggregates + time ranges
        ↓
analytics API
        ↓
Analytics page
```

A later production-style version could still move monitoring workers outside Django into a dedicated monitor process or Windows service while keeping the collector, telemetry and API boundaries.

# Summary

Sys Monitor currently follows a layered architecture with separate fast, slow and persistent paths:

```text
Windows
    ↓
Collectors
    ├── fast metrics → SystemSampler
    └── processes    → ProcessSnapshotWorker
                         ↓
              BackgroundMonitoringService
                 ├── latest sample
                 ├── MonitorHistory
                 └── TelemetryWriter
                          ↓
                    Django ORM
                          ↓
                     PostgreSQL
```

The terminal interface continues to reuse the monitoring code, while the Django web layer exposes shared live state through JSON APIs.

The most important architectural characteristics are now:

* browser requests do not drive collection,
* expensive process enumeration does not block the fast system sampler,
* short live history and durable historical telemetry have different responsibilities,
* PostgreSQL persistence is isolated from the live monitoring path,
* future analytics can be built as a query layer over existing telemetry rather than changing the collectors.

