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

This will later become an interactive feature in the Processes dashboard.

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

`MonitoringService` is the bridge between Django and the core monitoring system.

Instead of putting monitoring state and calculations inside a Django view:

```text
View
    ↓
MonitoringService
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

inside `MonitoringService`.

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

The current web monitor creates new samples when the dashboard requests them.

Therefore:

```text
dashboard open
    ↓
requests occur
    ↓
samples occur
```

but:

```text
dashboard closed
    ↓
no requests
    ↓
web sampling stops
```

A later version may introduce background monitoring.

---

# JavaScript Concepts

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
* request-driven monitoring
* the DOM
* asynchronous JavaScript
* `fetch()`
* `.map()`
* Chart.js
* frontend/backend separation

These concepts will continue to become more concrete as Sys Monitor grows.
