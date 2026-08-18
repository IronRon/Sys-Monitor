# Concepts and Learning Notes

This document is a short glossary of programming, operating-system and software-engineering concepts introduced while building Sys Monitor.

It is intended as a quick reference rather than detailed documentation.

---

# CPU

## CPU

**CPU** stands for Central Processing Unit.

It executes the instructions used by programs and the operating system.

Examples of programs competing for CPU time include:

* Chrome
* Python
* Django
* VS Code
* Windows services
* games

---

## Physical Core

A physical CPU core is an actual hardware processing core inside the CPU.

A CPU may contain many cores, allowing multiple tasks to execute in parallel.

The current development PC reports:

```text
10 physical cores
```

---

## Logical Processor

A logical processor is an execution unit visible to the operating-system scheduler.

Technologies such as Hyper-Threading or SMT can allow a physical core to expose more than one logical processor.

The current PC reports:

```text
10 physical cores
20 logical processors
```

Windows can therefore schedule threads across 20 logical CPUs.

---

## CPU Utilisation

CPU utilisation measures how busy the processor was during a period of time.

Example:

```text
CPU: 18%
```

means approximately 18% of the machine's total CPU capacity was being used during the measured interval.

CPU utilisation is therefore a **time-based measurement**, not a single instantaneous value.

---

# Processes

## Process

A process is a running instance of a program.

For example:

```text
python.exe
chrome.exe
Code.exe
Discord.exe
```

A program exists on disk.

A process exists while that program is running.

---

## PID

**PID** means Process Identifier.

Windows assigns each running process an ID.

Example:

```text
chrome.exe
PID 18320
```

Two processes may have the same executable name but different PIDs.

---

## PPID

**PPID** means Parent Process Identifier.

It identifies the process associated with the parent relationship of another process.

Example:

```text
explorer.exe
PID 4000
    │
    └── chrome.exe
        PID 10000
        PPID 4000
```

PID and PPID values allow us to build process trees.

---

## Process Tree

A process tree shows parent/child relationships between processes.

Example:

```text
explorer.exe
│
├── chrome.exe
│   ├── chrome.exe
│   └── chrome.exe
│
└── Code.exe
    ├── node.exe
    └── python.exe
```

The Processes page now turns these PID/PPID relationships into an interactive expandable tree.

---

## Multi-Process Application

Some applications deliberately use many processes.

Chrome is an example.

Instead of one large `chrome.exe` process, Chrome may have separate processes for:

* browser management
* webpage rendering
* GPU work
* utilities
* networking-related work
* extensions and other isolated tasks

This can improve security, stability and isolation.

---

## Working Set / RSS

A process's **working set** is broadly the memory associated with the process that is currently resident in physical RAM.

psutil exposes this through its resident-memory information.

Sys Monitor currently stores it as:

```text
memory_bytes
```

and later displays it as MB or GB.

---

# Monitoring

## Sampling

Sampling means measuring something repeatedly at intervals.

For example:

```text
21:00:01    CPU 10%
21:00:02    CPU 14%
21:00:03    CPU 28%
21:00:04    CPU 16%
```

Sys Monitor currently aims to take approximately one sample per second.

---

## Sample

A sample is one snapshot of the computer's state.

A Sys Monitor sample currently contains information about:

```text
CPU
memory
disk
network
processes
timestamp
```

---

## Time Series

A time series is a sequence of measurements ordered by time.

Example:

```text
Time        CPU
21:30:01    10%
21:30:02    18%
21:30:03    42%
```

The CPU graph is a visualisation of time-series data.

---

## Priming

Some measurements require a previous observation before they become meaningful.

For example:

```python
psutil.cpu_percent(interval=None)
```

needs an earlier CPU measurement to compare against.

The first call is used to establish that baseline and its result is ignored.

This is referred to in the project as **priming**.

Conceptually:

```text
first measurement
      ↓
remember baseline
      ↓
time passes
      ↓
second measurement
      ↓
calculate change
```

---

## Blocking

A blocking operation prevents the current execution flow from continuing until the operation finishes.

Example:

```python
psutil.cpu_percent(interval=1)
```

approximately means:

```text
measure
↓
wait 1 second
↓
measure again
↓
return
```

The function blocks for that interval.

---

## Non-Blocking

A non-blocking CPU measurement:

```python
psutil.cpu_percent(interval=None)
```

returns immediately by comparing the current counters with a previously recorded observation.

Sys Monitor uses this approach so the overall monitoring loop controls the timing.

---

## Cumulative Counter

A cumulative counter continually increases as activity occurs.

For example:

```text
Network bytes received:

2,000,000,000
2,010,000,000
2,018,000,000
...
```

The number is not the current network speed.

It represents accumulated activity.

Disk and network monitoring both use cumulative counters.

---

## Delta

A **delta** means the difference between two values.

Example:

```text
current bytes:
15,000,000

previous bytes:
10,000,000

delta:
5,000,000
```

Deltas are used to calculate disk and network throughput.

---

## Rate

A rate describes change over time.

For example:

```text
bytes changed
-------------
seconds elapsed
```

can produce:

```text
bytes per second
```

Sys Monitor uses this to calculate:

* disk read speed
* disk write speed
* network download speed
* network upload speed

---

## `perf_counter()`

Python's:

```python
time.perf_counter()
```

is used to measure elapsed time.

This is useful because our sampling interval is not guaranteed to be exactly one second.

For example:

```text
requested delay: 1 second
actual elapsed: 1.047 seconds
```

Using the real elapsed duration improves throughput calculations.

---

# Data Structures

## `deque`

A `deque` is a double-ended queue provided by Python's `collections` module.

Sys Monitor uses:

```python
deque(maxlen=60)
```

to store recent monitoring samples.

---

## Rolling Buffer

A rolling buffer retains only a fixed number of recent values.

Example with a maximum of five:

```text
[1][2][3][4][5]
```

Add `6`:

```text
[2][3][4][5][6]
```

The oldest value is removed automatically.

Sys Monitor currently keeps:

```text
60 samples
```

which gives roughly 60 seconds of history.

---

## State

State is information an object remembers between operations.

`SystemSampler` has state such as:

```text
previous disk counters
previous network counters
```

Without those previous values, it could not calculate rates.

---

# Software Architecture

## Separation of Concerns

Separation of concerns means giving different parts of a program different responsibilities.

Sys Monitor currently separates:

```text
Collectors
    ↓
retrieve data

SystemSampler
    ↓
calculate and combine data

MonitorHistory
    ↓
store recent data

Django
    ↓
serve HTTP

JavaScript
    ↓
update browser

Chart.js
    ↓
draw graphs
```

This prevents one large file from doing everything.

---

## Abstraction

Abstraction hides implementation details behind a simpler interface.

For example:

```python
cpu = get_cpu_usage()
```

allows the sampler to retrieve CPU information without needing to care about every lower-level operation used to obtain it.

Similarly:

```python
sampler.sample(...)
```

allows Django to request a complete system sample without knowing how each metric is calculated.

---

## Layered Architecture

The project currently has approximately:

```text
Windows
   ↓
psutil
   ↓
Collectors
   ↓
Monitoring
   ↓
Services
   ↓
Django / Terminal
   ↓
Frontend
```

Higher layers depend on lower layers.

Lower layers should generally not depend on higher presentation layers.

---

## Service Layer

`BackgroundMonitoringService` is the bridge between Django and the core monitoring system. It also owns the background sampling thread and shared latest sample used by both APIs.

Instead of putting monitoring state and calculations inside a Django view:

```text
View
    ↓
BackgroundMonitoringService
    ↓
SystemSampler
```

The view remains focused on HTTP.

---

# Concurrency

## Concurrency

Concurrency means multiple tasks may make progress during overlapping periods of time.

For example, a web server may receive:

```text
Request A
Request B
```

at almost the same time.

If both access shared monitoring state, they could interfere with one another.

---

## Race Condition

A race condition can occur when the result depends on the timing of multiple operations accessing shared state.

Example:

```text
Request A reads previous counter

Request B reads previous counter

Request A changes counter

Request B changes counter
```

The resulting measurement may be incorrect.

---

## Lock

A lock allows only one operation at a time to access a protected section of shared state.

Sys Monitor currently uses:

```python
threading.Lock()
```

inside `BackgroundMonitoringService`.

Conceptually:

```text
Request A
    ↓
LOCK
    ↓
sample
    ↓
UNLOCK
         ↓
      Request B
         ↓
        LOCK
```

---

# Background Execution

## Thread

A **thread** is one flow of execution inside a process. Sys Monitor's Django process now has a background sampler thread that can collect system data while Django also handles HTTP requests.

```text
Python / Django process
├── request handling
└── background sampler thread
```

---

## Daemon Thread

The sampler thread is created with:

```python
daemon=True
```

A daemon thread does not keep the Python interpreter alive after all non-daemon work has finished. It is a safety net, not the main graceful-shutdown mechanism.

---

## `threading.Event`

An `Event` is a thread-safe flag that one thread can set and another can wait for. Sys Monitor uses a ready event to signal that the first useful sample exists and a stop event to wake and terminate the worker.

---

## `join()`

Calling `thread.join()` means the current thread waits for another thread to finish. During shutdown, Sys Monitor signals the sampler to stop and then waits briefly for it to exit.

---

## `atexit`

Python's `atexit` mechanism registers functions to run during normal interpreter shutdown. Sys Monitor registers the monitoring service's `stop()` method so Ctrl+C / normal server shutdown can request a clean worker exit.

---

## Background Sampling

Background sampling means measurements are produced independently of browser requests.

```text
background worker
    ↓
sample every ~1 second
    ↓
latest shared state
    ↓
APIs read that state
```

The browser can close while sampling continues as long as the Django Python process remains running.

---

# Web Concepts

## HTTP

HTTP is the protocol used for communication between the browser and Django.

For example:

```text
GET /api/system/
```

asks Django for system monitoring information.

---

## API

An **API** is an interface through which software components communicate.

Sys Monitor currently exposes:

```text
/api/system/
```

The frontend can request monitoring data without needing direct access to Python or psutil.

---

## JSON

JSON is a text-based data format used to exchange structured information.

Example:

```json
{
    "cpu": {
        "percent": 14.7
    }
}
```

Django sends JSON.

JavaScript receives it.

---

## Serialization

Serialization means converting an in-memory object into a format that can be transmitted or stored.

For example:

```text
Python datetime
      ↓
serialization
      ↓
"2026-08-12T21:30:04"
```

The API serializes Python monitoring values before returning them as JSON.

---

## Polling

Polling means repeatedly requesting new information.

The dashboard currently does:

```text
GET /api/system/
      ↓
receive data
      ↓
wait
      ↓
GET /api/system/
      ↓
...
```

approximately once per second.

---

## Request-Driven Monitoring

An earlier version of Sys Monitor took new samples when `/api/system/` or `/api/processes/` was requested. That design has now been replaced by background sampling. It remains useful as a comparison:

```text
old:
request → collect → respond

current:
background collect → publish latest state
request → read → respond
```

---

## DOM

DOM stands for:

**Document Object Model**

The browser represents the HTML page as a tree of objects.

JavaScript can find and modify these objects.

Example:

```javascript
document.getElementById("cpu-value")
```

finds the CPU value element.

---

## `textContent`

JavaScript can change text displayed on the page:

```javascript
cpuValue.textContent = "14.7%";
```

The browser then updates the visible dashboard.

---

## `async` / `await`

HTTP requests take time.

JavaScript uses:

```javascript
async
```

and:

```javascript
await
```

to work with operations that complete later.

For example:

```javascript
const response =
    await fetch("/api/system/");
```

The function waits for the response while the browser remains responsive.

---

## `fetch()`

`fetch()` is the browser API currently used to make HTTP requests.

Example:

```javascript
fetch("/api/system/")
```

communicates with Django.

---

## `.map()`

JavaScript's `.map()` transforms every item in an array into a new value.

Example:

```javascript
[
    {cpu: 10},
    {cpu: 20},
    {cpu: 30}
]
```

can become:

```javascript
[10, 20, 30]
```

This is used to turn API history objects into Chart.js data arrays.

---


## Dynamic DOM Generation

JavaScript can create HTML elements at runtime instead of requiring every element to be written in the original template.

Sys Monitor now uses this for the logical-processor grid and process-table rows:

```text
API data
   ↓
JavaScript loop
   ↓
createElement()
   ↓
appendChild()
   ↓
new DOM elements
```

---

## Data-Driven UI

A data-driven UI creates its visible elements from the data it receives.

For example:

```text
8 logical processors  →  8 CPU items
20 logical processors → 20 CPU items
```

The dashboard therefore adapts to the machine instead of hard-coding a fixed number of CPUs.

---


## `Map`

A JavaScript `Map` stores key/value pairs and provides fast lookup by key. The Processes page uses a map such as:

```text
PID → process object
```

so a process's `ppid` can quickly be used to find its parent while constructing the tree.

---

## `Set`

A JavaScript `Set` stores unique values. The Processes page uses a set of expanded PIDs so open tree branches can remain open when fresh process data is rendered.

---

## Filtering and Sorting

Filtering selects only items that match a condition, while sorting changes their order. The Processes table uses both: search filters the process array, and clicking a column header changes the sort key and direction.

---

## `<details>` and `<summary>`

HTML `<details>` and `<summary>` elements provide built-in expandable/collapsible content. Sys Monitor uses them for process-tree nodes instead of implementing all expand/collapse behaviour from scratch.

---

## Frontend State

Frontend state is information the browser remembers while the page is running. The Processes page keeps state such as the latest process list, current sort column/direction and expanded tree PIDs.

---

# Chart.js

Chart.js is the frontend charting library currently used by Sys Monitor.

It receives data such as:

```text
timestamps:
[21:00:01, 21:00:02, 21:00:03]

CPU values:
[10, 18, 25]
```

and draws the values as a graph inside an HTML:

```html
<canvas>
```

Chart.js does not collect or calculate CPU information.

It only visualises data supplied by the application.

---

## Graph / Node / Edge

A graph is a data structure made from **nodes** and **edges**. In the process graph, each running process is a node and each parent-to-child PID relationship is a directed edge.

---

## Directed Graph

A directed graph has edges with a direction. Sys Monitor draws process relationships as:

```text
parent PID -> child PID
```

---

## Process Forest

A forest is a collection of separate trees. The process graph may have several roots because some process parents are not present or accessible in the current process list.

---

## Cytoscape.js

Cytoscape.js is the frontend graph visualisation library used by the Processes Graph view. It stores and renders nodes and edges and provides interactions such as pan, zoom, selection and styling.

---

## Graph Layout Algorithm

A graph layout algorithm calculates positions for nodes so relationships are easier to understand visually. Sys Monitor uses the Dagre extension for the initial directed process-tree layout.

---

## Dagre

Dagre is a directed graph layout algorithm. In Sys Monitor it arranges parent processes above child processes in a top-to-bottom hierarchy.

---

## Topology

Graph topology describes which nodes and edges exist and how they are connected. The Processes page compares PID/PPID topology between refreshes so it can detect when processes start, stop or change relationships without moving the entire graph every second.

---

## Pan and Zoom

Panning moves the graph viewport across a larger graph space. Zooming changes the scale. Together they let the process graph behave like a large navigable canvas even when the complete process forest cannot fit on screen.

---

# Backend vs Frontend

The **backend** currently consists mainly of Python and Django.

It handles:

```text
system collection
sampling
history
API responses
```

The **frontend** runs in the browser.

It handles:

```text
display
formatting
interaction
charts
```

The boundary between them is:

```text
JSON over HTTP
```

---

# Raw Data vs Presentation

An important design idea introduced in the project is keeping raw values separate from how they are displayed.

For example, the backend provides:

```text
16445685760 bytes
```

The frontend may display:

```text
15.3 GB
```

Similarly:

```text
3364992 bytes/sec
```

may become:

```text
3.21 MB/s
```

This allows different interfaces to format the same data differently.

---


# Memory and Storage Concepts

## Available Memory

Available memory estimates how much physical memory Windows can make available to applications without immediately needing to page memory out. It is more useful than looking only at a raw `free` value because operating systems deliberately use RAM for caches and other reclaimable purposes.

## Page File

A page file is disk-backed storage used by Windows as part of virtual-memory and committed-memory management. Sys Monitor displays page-file usage separately from physical RAM because page-file capacity and RAM utilisation are related but are not the same measurement.

## Paging

Paging is the movement/management of memory in fixed-size pages. If memory pressure requires data to be backed by slower storage, page-file activity can become relevant. Physical RAM remains much faster than disk-backed storage.

## Caching

Operating systems can use otherwise idle RAM to cache useful data. Cached memory may still be reclaimable when applications need memory, which is why "used" RAM does not automatically mean memory is being wasted.

## Filesystem / Volume

A filesystem organises files and directories on a storage volume. In the current Disk page, the C: percentage describes how much of that filesystem's capacity is occupied.

## Physical Drive

A physical drive is the actual SSD or HDD hardware. One physical drive may contain multiple partitions or volumes. Sys Monitor therefore gets live C: capacity from the disk collector but gets the drive model, SSD/NVMe type and health from the separate hardware service.

## Capacity vs Activity

Disk capacity and disk activity are different measurements:

```text
capacity
    → how full the storage is

activity / throughput
    → how much data is being read or written now
```

A disk can be nearly full but idle, or mostly empty while processing heavy I/O.

## Read and Write Throughput

A disk **read** transfers data from persistent storage so it can be used by the system. A **write** stores data persistently. Sys Monitor calculates current read/write throughput from changes in cumulative disk I/O counters divided by elapsed time.

## MB vs MiB

Decimal and binary byte units are slightly different:

```text
1 MB  = 1,000,000 bytes
1 MiB = 1,048,576 bytes
```

Sys Monitor currently performs many conversions using powers of 1024 while the UI often uses familiar `MB` / `GB` labels. A stricter future UI could label those values as MiB/GiB.

---

# Network Concepts

## Network Interface

A network interface is an adapter or software endpoint through which the operating system can send and receive network traffic. Examples include Ethernet, Wi-Fi, loopback, VPN and virtual adapters. Sys Monitor now calculates throughput separately for each detected interface.

## IP Address

An IP address identifies a network endpoint. IPv4 commonly uses dotted decimal addresses such as `192.168.1.20`; IPv6 uses a larger hexadecimal address space.

## Port

A port is a numeric endpoint within an IP host. An IP address identifies the machine/interface while the port helps identify the particular network service or socket endpoint.

## Socket

A socket is an operating-system networking endpoint owned by a process or the system. Sys Monitor uses socket information to associate PIDs with local/remote addresses and connection states.

## TCP

TCP is a connection-oriented transport protocol that provides reliable, ordered delivery. TCP sockets move through states such as `LISTEN`, `SYN_SENT`, `ESTABLISHED` and `TIME_WAIT`.

## UDP

UDP is a datagram-oriented transport protocol. It does not establish the same persistent connection state as TCP, so a UDP socket may have no remote endpoint and no TCP-style `ESTABLISHED` state.

## Local and Remote Endpoint

A connection can be described by two endpoints:

```text
local IP : local port
        ↕
remote IP : remote port
```

The local endpoint belongs to this PC. The remote endpoint belongs to the other side of the communication when one exists.

## DNS and Reverse DNS

DNS normally resolves a hostname to an IP address. **Reverse DNS** attempts the opposite: given an IP address, find a hostname associated with it. Reverse-DNS results are optional metadata and are not guaranteed to exist.

## Asynchronous Enrichment

Sys Monitor does not block the Network API while waiting for reverse-DNS lookups. Unknown IPs are scheduled for resolution in a small background thread pool, while the API immediately returns the raw IP address. A later refresh can include the hostname if resolution succeeded.

## MTU

MTU means **Maximum Transmission Unit**. It describes the largest packet size, in bytes, that an interface can transmit without needing fragmentation at that interface layer.

## Link Speed vs Throughput

An interface may report a link speed such as `1000 Mbps`. This is not the same thing as current application throughput.

```text
link speed
    → negotiated/theoretical interface link capacity

current throughput
    → how many bytes are actually moving per second now
```

## Connection Inspection vs Packet Capture

The current Network page inspects operating-system **sockets/connections**. It does not yet capture individual packets or decode HTTP/TLS application payloads. Packet capture is a separate, higher-frequency monitoring problem and will require a dedicated capture worker rather than the one-second `SystemSampler`.

---

# Hardware Identification Concepts

## Static vs Live Data

Not every piece of system information needs the same sampling strategy. CPU utilisation and network throughput change continuously, while a CPU model or motherboard model rarely changes during a program run.

Sys Monitor therefore separates:

```text
live telemetry
    → background sampling

static hardware identity
    → collect once + cache
```

## CIM

CIM stands for **Common Information Model**. Windows exposes structured management information about components such as processors, memory, video controllers, systems, motherboards and firmware. The hardware collector asks PowerShell to query this information and return it as JSON.

## Normalisation

Normalisation converts source-specific data into the application's own consistent representation.

For example:

```text
Windows: NumberOfLogicalProcessors
        ↓
Sys Monitor: logical_processors
```

The hardware normalizer also cleans placeholder firmware values and parses dates into a consistent format.

## Caching

Caching means keeping a previously computed or retrieved result so it can be reused without repeating the expensive operation. `HardwareService` caches the discovered hardware because motherboard, BIOS, RAM-module and CPU-model information does not need to be queried once per second.

## Data Provenance

Data provenance means keeping track of where a value came from and how trustworthy it is. Monitoring software should not imply more certainty than the source provides.

For example, Sys Monitor labels a GPU value as:

```text
Windows-reported VRAM
```

instead of assuming the value is always an authoritative manufacturer specification.

## Property-Driven Explanation

The hardware explanation engine generates educational text from detected properties rather than storing a paragraph for every possible hardware model.

Examples:

- `logical_processors > physical_cores` can explain logical CPU scheduling targets
- two equal-size DIMMs can explain matched memory modules
- `media_type = SSD` can explain solid-state storage
- `bus_type = NVMe` can explain NVMe

This keeps the teaching layer reusable across different PCs.

---
# Documentation Concepts

## Markdown

Markdown is a lightweight text format that uses simple characters to describe document structure.

For example:

```markdown
# Heading

**Bold text**

- list item
```

is easier to write and maintain than manually writing all of the equivalent HTML.

Sys Monitor keeps its technical documentation in `.md` files inside:

```text
docs/
```

---

## Source of Truth

A **source of truth** is the main authoritative copy of some information.

For the documentation feature:

```text
docs/*.md
```

are the source of truth.

The Django documentation pages are generated from these files rather than storing a second manually maintained copy of the same content in HTML templates.

---

## Markdown Renderer

A Markdown renderer converts Markdown text into another format, usually HTML.

Sys Monitor uses the Python `markdown` package.

Conceptually:

```text
# CPU
    ↓
Markdown renderer
    ↓
<h1>CPU</h1>
```

The browser understands the generated HTML, not the original Markdown syntax.

---

## Dynamic Route

A dynamic route contains part of the URL as a variable rather than defining every possible URL separately.

Instead of writing one Django route for every documentation page:

```text
/docs/collectors/
/docs/monitoring/
/docs/architecture/
```

Sys Monitor uses one pattern:

```python
path(
    "<slug:slug>/",
    views.docs_page,
    name="page",
)
```

The variable part is passed to the Django view.

---

## Slug

A **slug** is a short URL-friendly identifier.

Examples:

```text
collectors
monitoring
architecture
frontend
```

In Django:

```text
<slug:slug>
```

contains two different uses of the word `slug`:

```text
<converter:variable_name>
```

Therefore:

```text
<slug:slug>
   │    │
   │    └── Python argument name
   │
   └── Django URL converter
```

For:

```text
/docs/architecture/
```

Django extracts:

```python
slug = "architecture"
```

and calls the documentation view with that value.

The variable could have been given another name:

```python
path(
    "<slug:page_name>/",
    views.docs_page,
)
```

which would require the view to accept `page_name` instead.

---

## Path Converter

A Django path converter controls what kind of URL text is accepted and converts it into a value passed to the view.

Examples include:

```text
<int:id>
<slug:slug>
<str:name>
```

The documentation route uses the `slug` converter because documentation names such as `architecture` and `frontend` are URL-friendly identifiers.

---

## Documentation Registry / Whitelist

Sys Monitor stores the allowed documentation pages in `DOC_PAGES`.

For example:

```python
DOC_PAGES = {
    "architecture": {
        "title": "Architecture",
        "filename": "architecture.md",
    },
}
```

The slug selects an entry from this registry.

This serves two purposes:

1. It provides metadata for navigation and page titles.
2. It prevents arbitrary URL values from being treated directly as file paths.

Only files deliberately registered by the application are exposed as documentation pages.

---

## Template Inheritance

Django template inheritance allows multiple pages to share one common layout.

The documentation site uses:

```text
base.html
    ↓
shared sidebar, page shell and static files

index.html / page.html
    ↓
page-specific content
```

A child template uses:

```django
{% extends "documentation/base.html" %}
```

and fills named blocks defined by the base template.

This prevents duplicated navigation and layout HTML across every documentation page.

---

## `safe` Template Filter

Django normally escapes HTML values before displaying them.

This protects pages from accidentally rendering potentially dangerous HTML.

The Markdown renderer deliberately produces HTML, so the documentation template uses:

```django
{{ content_html|safe }}
```

This tells Django to render the generated HTML rather than display the HTML tags as text.

This is appropriate here because the Markdown files are trusted project files. It should not be blindly used with untrusted user input.

---

## Mermaid

Mermaid is a JavaScript diagramming library that converts text definitions into diagrams.

Example source:

```text
flowchart LR
    A --> B
```

can be rendered as a graphical flowchart.

Sys Monitor stores Mermaid definitions inside Markdown code fences.

Python-Markdown turns the fenced block into HTML code, and the browser-side Mermaid library performs the second step that turns the diagram text into SVG graphics.

```text
Markdown
    ↓
Python-Markdown
    ↓
HTML code block
    ↓
Mermaid.js
    ↓
SVG diagram
```

---

## CDN

A **CDN** — Content Delivery Network — hosts files that a web page can load over the internet.

The current project loads libraries such as Chart.js and Mermaid from a CDN instead of storing their JavaScript files directly inside the project.

This is convenient during development, but it also means those libraries may require internet access when first loaded.

---

# Key Ideas Learned So Far

The main new ideas introduced by the project so far include:

* CPU cores vs logical processors
* processes
* PID and PPID
* process trees
* process working sets
* CPU utilisation
* sampling
* priming
* blocking vs non-blocking operations
* cumulative counters
* deltas
* rates
* elapsed-time measurement
* application state
* rolling buffers
* `deque`
* layered architecture
* separation of concerns
* abstraction
* service layers
* concurrency
* race conditions
* locks
* APIs
* HTTP
* JSON
* serialization
* polling
* request-driven vs background monitoring
* threads and daemon threads
* `threading.Event`
* `join()`
* `atexit` cleanup
* the DOM
* asynchronous JavaScript
* `fetch()`
* `.map()`
* dynamic DOM generation
* data-driven UI
* JavaScript `Map` and `Set`
* filtering and sorting
* HTML `<details>` / `<summary>`
* frontend state
* Chart.js
* graphs, nodes and directed edges
* process forests
* Cytoscape.js
* graph layout algorithms and Dagre
* graph topology
* pan and zoom interaction
* frontend/backend separation
* network interfaces and per-interface counters
* IPv4 and IPv6 addresses
* ports and sockets
* TCP vs UDP
* TCP connection states
* local vs remote endpoints
* DNS and reverse DNS
* asynchronous hostname enrichment
* MTU and link speed
* connection inspection vs packet capture
* Markdown
* Markdown rendering
* dynamic Django routes
* slugs and path converters
* documentation registries
* template inheritance
* Django's `safe` template filter
* Mermaid diagrams
* CDNs
* source-of-truth documentation
* available vs used physical memory
* page files and paging
* memory caching
* filesystem/volume vs physical drive
* disk capacity vs disk activity
* read/write throughput
* MB/GB vs MiB/GiB unit conventions
* static vs live system data
* Windows CIM hardware discovery
* hardware-data normalisation
* caching
* data provenance and measurement uncertainty
* property-driven hardware explanations

These concepts will continue to become more concrete as Sys Monitor grows.
