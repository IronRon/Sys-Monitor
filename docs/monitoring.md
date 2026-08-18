# Monitoring Layer

The monitoring layer sits between the low-level system collectors and the interfaces that display the information.

Its main responsibility is:

> Take raw system measurements, combine them into a consistent snapshot, calculate values that depend on time, and retain recent snapshots for later use.

The monitoring layer currently contains:

```text
src/monitoring/
├── __init__.py
├── sampler.py
└── history.py
```

The two main components are:

* `SystemSampler`
* `MonitorHistory`

---

# Overview

The collectors answer questions such as:

```text
What are the current CPU counters?

How many bytes has the disk read since boot?

How many bytes has the network received?

How much RAM is currently available?

Which processes currently exist?
```

These raw values are useful, but some of them are not yet directly suitable for displaying to a user.

For example:

```text
Network bytes received:
2,173,832,073
```

does not tell us the current download speed.

To calculate a rate such as:

```text
3.2 MB/s
```

we need to compare measurements taken at different points in time.

That is the job of the monitoring layer.

---

# Monitoring Architecture

```mermaid
flowchart TD
    CPU[CPU Collector]
    Memory[Memory Collector]
    Disk[Disk Collector]
    Network[Network Collector]
    Processes[Process Collector]

    CPU --> Sampler[SystemSampler]
    Memory --> Sampler
    Disk --> Sampler
    Network --> Sampler
    Processes --> Sampler

    Sampler --> Sample[System Sample]

    Sample --> History[MonitorHistory]

    Sample --> Terminal[Terminal Monitor]
    History --> Terminal

    Sample --> Web[Django Monitoring Service]
    History --> Web
```

The important separation is:

```text
Collectors
    ↓
retrieve raw information

SystemSampler
    ↓
combine + calculate

MonitorHistory
    ↓
retain recent samples

Interfaces
    ↓
display the information
```

---

# Why Have a Separate Monitoring Layer?

Without a monitoring layer, `monitor.py` or the Django views would need to contain logic such as:

```python
current_network = get_network_usage()

download_speed = (
    current_network["bytes_received"]
    - previous_network["bytes_received"]
) / elapsed_seconds
```

The same calculations would eventually be duplicated in multiple interfaces.

Instead:

```text
Terminal
        \
         \
          → SystemSampler
         /
Dashboard
```

Both interfaces can use the same monitoring logic.

This helps maintain **separation of concerns**.

Each layer has a specific purpose:

| Layer        | Responsibility                            |
| ------------ | ----------------------------------------- |
| Collectors   | Retrieve raw operating-system information |
| Monitoring   | Turn measurements into meaningful samples |
| Presentation | Display those samples to a user           |

---

# `SystemSampler`

File:

```text
src/monitoring/sampler.py
```

The `SystemSampler` is the central component of the monitoring layer.

A simplified structure is:

```python
class SystemSampler:
    def __init__(self):
        self.previous_disk = None
        self.previous_network = None

    def prime(self):
        ...

    def sample(self, elapsed_seconds):
        ...
```

The class has two main responsibilities:

1. Establish the initial measurement baselines.
2. Produce complete system samples.

---

# Why Is `SystemSampler` a Class?

A normal function is often sufficient when an operation does not need to remember anything.

For example:

```python
def get_memory_usage():
    ...
```

can simply retrieve memory and return it.

The sampler is different.

It needs to remember:

```text
previous disk counters
previous network counters
```

between calls.

For example:

```text
Sample 1
read_bytes = 10,000

Sample 2
read_bytes = 15,000
```

To calculate the change during Sample 2, the sampler must still know the value from Sample 1.

This means the sampler contains **state**.

An object is a natural way to represent this:

```text
SystemSampler instance
│
├── previous_disk
├── previous_network
│
├── prime()
└── sample()
```

---

# State

In programming, **state** means information that persists between operations.

For the sampler:

```python
self.previous_disk
```

and:

```python
self.previous_network
```

are state.

Their values change as new samples are taken.

For example:

```text
Initial state

previous_network
    ↓
2,000,000 bytes
```

After the next measurement:

```text
current_network
    ↓
2,500,000 bytes

difference
    ↓
500,000 bytes

then:

previous_network
    ↓
becomes 2,500,000
```

This allows the next measurement to be compared against the newest baseline.

---

# Priming

Before normal monitoring starts, the sampler calls:

```python
sampler.prime()
```

Priming means:

> Take initial measurements that will act as baselines for later calculations.

Some metrics cannot produce useful results from only one observation.

CPU percentages and throughput measurements are examples.

---

# CPU Priming

The project uses non-blocking CPU measurement:

```python
psutil.cpu_percent(interval=None)
```

and:

```python
psutil.cpu_percent(
    interval=None,
    percpu=True
)
```

These functions calculate CPU utilisation by comparing CPU times against an earlier observation.

The first call does not yet have a useful previous observation.

The sampler therefore performs an initial call and ignores its result.

Conceptually:

```text
Time A
│
├── read CPU counters
└── remember them

        time passes

Time B
│
├── read CPU counters again
├── compare against Time A
└── calculate CPU percentage
```

The first measurement is therefore a **baseline**, not a displayed sample.

---

# Process CPU Priming

Individual process CPU percentages behave similarly.

Before normal monitoring begins, the project calls:

```python
prime_process_cpu()
```

This loops over currently running processes and performs an initial CPU measurement.

Conceptually:

```text
chrome.exe
    ↓
remember current CPU time

Code.exe
    ↓
remember current CPU time

Discord.exe
    ↓
remember current CPU time
```

Later calls can compare how much CPU time each process consumed since the previous observation.

Processes created after the initial prime may initially have no meaningful previous measurement.

That is acceptable because later samples establish the necessary baseline.

---

# Disk Priming

Disk throughput is calculated using cumulative disk I/O counters.

During `prime()`:

```python
self.previous_disk = get_disk_usage()
```

This records the starting values.

Example:

```text
read_bytes:
480,000,000,000

write_bytes:
310,000,000,000
```

These counters continue increasing as the computer performs disk activity.

---

# Network Priming

The same principle applies to network activity:

```python
self.previous_network = get_network_usage()
```

Example baseline:

```text
bytes_received:
2,000,000,000

bytes_sent:
300,000,000
```

The next sample can compare new values against these counters.

---

# Snapshot vs Rate

An important distinction in monitoring is the difference between a **snapshot value** and a **rate**.

## Snapshot

Some values can be meaningfully read immediately:

```text
RAM usage: 48%

Disk capacity used: 92%

Running processes: 287
```

These describe the system at approximately one moment.

---

## Rate

Other values describe change over time:

```text
Download: 5 MB/s

Disk read: 20 MB/s

Disk write: 3 MB/s
```

A rate requires at least:

```text
starting value
ending value
elapsed time
```

The sampler is responsible for converting cumulative counters into rates.

---

# Cumulative Counters

Disk and network I/O values are currently obtained as cumulative counters.

Imagine a counter that begins at system boot:

```text
System boots

bytes_received = 0
```

As network traffic arrives:

```text
after 1 minute
bytes_received = 50,000,000

after 10 minutes
bytes_received = 700,000,000

after 1 hour
bytes_received = 4,200,000,000
```

The number does not represent current speed.

It represents:

> How many bytes have been received since the counter began.

To determine current throughput, the sampler calculates the **difference between samples**.

---

# Calculating a Rate

Suppose the network collector reports:

```text
First sample:
2,000,000,000 bytes received
```

Later:

```text
Second sample:
2,010,000,000 bytes received
```

The difference is:

```text
10,000,000 bytes
```

If one second elapsed:

```text
10,000,000 bytes
----------------
1 second
```

gives approximately:

```text
10,000,000 bytes per second
```

The general idea is:

```text
current counter - previous counter
----------------------------------
elapsed time
```

This pattern is used by Sys Monitor for:

* disk reads
* disk writes
* network downloads
* network uploads

---

# Disk Read Throughput

The sampler calculates:

```python
disk_read_speed = (
    disk["read_bytes"]
    - self.previous_disk["read_bytes"]
) / elapsed_seconds
```

The result is stored in:

```text
bytes per second
```

For example:

```text
13,500,000 bytes/s
```

The presentation layer may later convert this into:

```text
12.87 MB/s
```

---

# Disk Write Throughput

Disk write speed uses the same calculation:

```python
disk_write_speed = (
    disk["write_bytes"]
    - self.previous_disk["write_bytes"]
) / elapsed_seconds
```

This represents how quickly data was written to storage during the measured interval.

---

# Network Download Throughput

Download speed is calculated from:

```python
network["bytes_received"]
```

The sampler performs:

```python
download_speed = (
    network["bytes_received"]
    - self.previous_network["bytes_received"]
) / elapsed_seconds
```

The result is measured in:

```text
bytes per second
```

---

# Network Upload Throughput

Upload speed is calculated using:

```python
network["bytes_sent"]
```

The sampler performs:

```python
upload_speed = (
    network["bytes_sent"]
    - self.previous_network["bytes_sent"]
) / elapsed_seconds
```

---

# Why Not Assume Exactly One Second?

The monitor currently aims to take approximately one sample per second.

It would be tempting to write:

```python
speed = byte_difference / 1
```

However, the real interval may not be exactly:

```text
1.000 seconds
```

The application itself takes time to:

* enumerate processes
* read system counters
* calculate results
* print terminal output
* handle web requests
* perform Python operations

The actual interval might instead be:

```text
1.034 seconds
```

or:

```text
1.121 seconds
```

Using a fixed divisor of `1` would therefore introduce measurement error.

---

# Measuring Actual Elapsed Time

The terminal monitor uses:

```python
time.perf_counter()
```

Example:

```python
previous_time = time.perf_counter()
```

Later:

```python
current_time = time.perf_counter()

elapsed_seconds = (
    current_time - previous_time
)
```

The actual duration is then supplied to:

```python
sampler.sample(
    elapsed_seconds=elapsed_seconds
)
```

---

# Why `perf_counter()`?

Python provides several ways of working with time.

The project uses:

```python
time.perf_counter()
```

for measuring elapsed durations.

This is different from asking:

```text
What time is it?
```

For example:

```python
datetime.now()
```

is useful for producing:

```text
2026-08-12 20:30:14
```

But for measuring how much time passed between two operations, a performance counter is more appropriate.

Conceptually:

```text
datetime.now()
    ↓
wall-clock timestamp

time.perf_counter()
    ↓
elapsed-time measurement
```

We use both, but for different purposes.

---

# Timestamp vs Timing

Each generated system sample includes:

```python
"timestamp": datetime.now()
```

This answers:

> When was this sample taken?

For example:

```text
20:43:21
```

The sampler also receives:

```python
elapsed_seconds
```

which answers:

> How much time passed since the previous sample?

These values serve different purposes.

```text
Timestamp
    ↓
useful for graphs and logs

Elapsed time
    ↓
useful for rate calculations
```

---

# Taking a Sample

Once the sampler has been primed, the normal sampling operation looks roughly like this:

```text
Call CPU collector
       ↓
Call memory collector
       ↓
Call disk collector
       ↓
Call network collector
       ↓
Call process collector
       ↓
Calculate disk rates
       ↓
Calculate network rates
       ↓
Rank processes
       ↓
Create system sample
       ↓
Update previous counters
       ↓
Return sample
```

---

# Sample Structure

The sampler combines the collector results into one common object.

A simplified sample looks like:

```python
{
    "timestamp": ...,

    "cpu": {
        "percent": ...,
        "per_cpu_percent": ...,
        "physical_cores": ...,
        "logical_processors": ...
    },

    "memory": {
        "percent": ...,
        "total_bytes": ...,
        "used_bytes": ...,
        "available_bytes": ...
    },

    "disk": {
        "percent": ...,
        "total_bytes": ...,
        "used_bytes": ...,
        "free_bytes": ...,
        "read_bytes_per_second": ...,
        "write_bytes_per_second": ...
    },

    "network": {
        "download_bytes_per_second": ...,
        "upload_bytes_per_second": ...
    },

    "processes": {
        "count": ...,
        "top_cpu": ...,
        "top_memory": ...
    }
}
```

This sample becomes the main data structure shared between the monitoring engine and the application's interfaces.

The CPU portion now carries both per-logical-processor utilisation and the physical/logical processor counts. The dashboard uses these values directly to build the logical-processor visualisation.

---

# Why Use One Common Sample?

Without a common structure, each interface might separately request:

```text
CPU
memory
disk
network
processes
```

and perform its own calculations.

Instead:

```text
Collectors
    ↓
SystemSampler
    ↓
one complete sample
    ↓
┌───────────────┬────────────────┐
│               │                │
Terminal     Django API      Future storage
```

This gives the project a stable internal representation of a system measurement.

---

# Raw Values vs Presentation Values

The sampler usually stores resource quantities using base units such as:

```text
bytes

bytes per second

percentages
```

It does not generally format them as:

```text
15.3 GB

4.2 MB/s

"48% used"
```

That formatting belongs to the presentation layer.

For example:

```text
Sampler:

16445685760 bytes
        ↓

Terminal:
15.32 GB
        ↓

Web dashboard:
15.3 GB
```

The underlying measurement remains the same.

---

# Process Rankings

The process collector returns information about all accessible running processes.

The sampler then asks for:

```python
get_top_cpu_processes(
    processes,
    limit=5
)
```

and:

```python
get_top_memory_processes(
    processes,
    limit=5
)
```

The current web sampler keeps both forms of process data in the **latest** sample:

- `top_cpu` and `top_memory` for the overview dashboard
- `items` containing the complete process list for `/api/processes/`

Processes are therefore collected once per sampling cycle and shared by both APIs. The complete process list is deliberately omitted from each rolling-history entry so that hundreds of process objects are not duplicated 60 times.

---


# Shared Process Sampling

The earlier `ProcessService` has been removed. Both the Overview and Processes pages now read from one shared `BackgroundMonitoringService`.

```text
BackgroundMonitoringService
        │
        ├── latest sample
        │      ├── top CPU / RAM processes
        │      └── complete process list
        │
        ├── /api/system/
        └── /api/processes/
```

This avoids taking a second process CPU measurement whenever `/api/processes/` is requested and gives both pages a consistent view of the same sampling cycle.

---

# Updating Previous Counters

After the sample has been calculated:

```python
self.previous_disk = disk
self.previous_network = network
```

This is an important step.

The current sample becomes the baseline for the next sample.

Conceptually:

```text
Sample 1
     ↓
previous

Sample 2
     ↓
compare with Sample 1
     ↓
Sample 2 becomes previous

Sample 3
     ↓
compare with Sample 2
     ↓
Sample 3 becomes previous
```

This creates a continuous chain of measurements.

---

# Sampling Timeline

A simplified monitoring session looks like:

```mermaid
sequenceDiagram
    participant App
    participant Sampler
    participant Collectors
    participant History

    App->>Sampler: prime()
    Sampler->>Collectors: Initial CPU/disk/network readings
    Collectors-->>Sampler: Baselines

    Note over App,Sampler: Time passes

    App->>Sampler: sample(elapsed_seconds)
    Sampler->>Collectors: Retrieve current data
    Collectors-->>Sampler: Current values
    Sampler->>Sampler: Calculate rates
    Sampler-->>App: Complete sample

    App->>History: add(sample)

    Note over App,Sampler: Time passes

    App->>Sampler: sample(elapsed_seconds)
    Sampler->>Collectors: Retrieve current data
    Collectors-->>Sampler: Current values
    Sampler->>Sampler: Compare against previous counters
    Sampler-->>App: Complete sample

    App->>History: add(sample)
```

---

# `MonitorHistory`

File:

```text
src/monitoring/history.py
```

The second main component of the monitoring layer is:

```python
MonitorHistory
```

Its responsibility is:

> Store a limited number of recent system samples.

It does not collect system data itself.

---

# Why Store History?

A single sample tells us:

```text
CPU right now:
17%
```

But monitoring becomes much more useful when we can see change over time:

```text
20:00:01    8%
20:00:02   10%
20:00:03   14%
20:00:04   72%
20:00:05   84%
20:00:06   22%
```

This allows us to identify:

* spikes
* trends
* sustained resource usage
* periods of inactivity
* relationships between metrics

History is therefore required for graphs and later performance analysis.

---

# `deque`

`MonitorHistory` currently uses:

```python
from collections import deque
```

and creates:

```python
deque(maxlen=60)
```

A `deque` is a double-ended queue.

It supports efficient addition and removal of items from either end.

For Sys Monitor, the particularly useful feature is:

```python
maxlen=60
```

which creates a **bounded deque**.

---

# Bounded History

Suppose the deque can contain five values:

```text
maxlen = 5
```

After five samples:

```text
[1, 2, 3, 4, 5]
```

Add sample 6:

```text
[2, 3, 4, 5, 6]
```

Sample 1 is removed automatically.

Add sample 7:

```text
[3, 4, 5, 6, 7]
```

The history therefore behaves as a rolling window.

---

# Why 60 Samples?

The current application uses:

```python
HISTORY_SIZE = 60
```

and aims for approximately:

```text
1 sample per second
```

Therefore:

```text
60 samples
×
approximately 1 second
=
approximately 60 seconds
```

This gives us a useful short-term live performance graph.

The choice of 60 is not a technical requirement.

It is simply appropriate for the current dashboard.

Future interfaces could use:

```text
60 seconds

5 minutes

1 hour

24 hours

7 days
```

depending on how history is stored.

---

# MonitorHistory Interface

The history class currently provides a small interface.

## Add a sample

```python
history.add(sample)
```

Appends the newest measurement.

---

## Retrieve all retained samples

```python
history.get_all()
```

Returns the current history.

This is useful for:

* charts
* APIs
* debugging

---

## Retrieve the newest sample

```python
history.latest()
```

Returns the most recently stored measurement.

If no samples have been collected yet:

```python
None
```

is returned.

---

## Get history length

The class implements:

```python
__len__()
```

which allows:

```python
len(history)
```

For example:

```text
History: 34 / 60 samples
```

---

# Why Wrap `deque` in a Class?

We could directly write:

```python
history = deque(maxlen=60)
```

throughout the project.

Instead, the project uses:

```python
MonitorHistory
```

This creates an abstraction around history storage.

The rest of the application knows:

```python
history.add(sample)

history.get_all()

history.latest()
```

but does not need to know that the implementation currently uses a deque.

This gives us flexibility.

---

# Future History Implementations

Today:

```text
MonitorHistory
    ↓
deque
    ↓
RAM only
```

Later we could introduce:

```text
Monitoring repository
    ↓
SQLite
```

or:

```text
Monitoring repository
    ↓
PostgreSQL
```

without requiring every consumer to understand the database implementation.

Eventually the application may distinguish:

```text
Live history
    ↓
small in-memory rolling buffer

Persistent history
    ↓
database
```

For example:

```text
last 60 seconds
    ↓
RAM deque

last 30 days
    ↓
database
```

---

# Why Keep History in Memory for Now?

The first dashboard only needs a small amount of recent data.

A database would introduce additional complexity:

* database models
* migrations
* writes every second
* retention policies
* aggregation
* cleanup
* storage growth

For the current learning stage:

```python
deque(maxlen=60)
```

is:

* simple
* fast
* bounded
* easy to understand

It gives us enough functionality to build live graphs before introducing persistent monitoring.

---

# Memory Usage of History

A bounded history also prevents unlimited memory growth.

Without a limit:

```text
1 sample
2 samples
100 samples
10,000 samples
1,000,000 samples
...
```

The application would continuously consume additional RAM.

With:

```python
maxlen=60
```

the number of retained samples never exceeds 60.

Therefore the memory requirement remains approximately constant.

This is an example of a **fixed-size rolling buffer**.

---

# Rolling Buffer

The history structure can be thought of as a window moving through time.

```text
Earlier:

[01][02][03][04][05]

          ↓ time

Later:

[02][03][04][05][06]

          ↓ time

Later:

[03][04][05][06][07]
```

The window always contains only the newest observations.

This pattern is common in:

* monitoring software
* streaming systems
* signal processing
* telemetry
* real-time charts
* moving-average calculations

---

# Monitor Loop

The terminal monitor currently controls the sampling schedule.

A simplified version is:

```python
sampler = SystemSampler()
history = MonitorHistory(max_samples=60)

sampler.prime()

previous_time = time.perf_counter()

while True:
    time.sleep(1)

    current_time = time.perf_counter()

    elapsed_seconds = (
        current_time - previous_time
    )

    sample = sampler.sample(
        elapsed_seconds
    )

    history.add(sample)

    print_sample(
        sample,
        history
    )

    previous_time = current_time
```

This loop coordinates:

```text
timing
sampling
history
presentation
```

but the monitoring calculations themselves remain inside the monitoring classes.

---

# Why Does the Main Loop Control Timing?

The CPU collector could use:

```python
psutil.cpu_percent(interval=1)
```

which would block for one second.

Instead the project uses non-blocking measurements and lets the outer application control timing.

This provides more flexibility.

The application can eventually change:

```text
1 second
```

to:

```text
500 milliseconds
```

or:

```text
5 seconds
```

without embedding timing delays inside individual collectors.

It also prevents different collectors from introducing their own independent waits.

---

# Blocking vs Non-Blocking Sampling

A blocking approach might look like:

```text
CPU collector
    ↓
wait 1 second
    ↓
return CPU

memory collector
    ↓
return memory

disk collector
    ↓
return disk
```

The CPU collector controls the timing of the whole cycle.

Our design is closer to:

```text
Monitoring loop
    ↓
wait until next sample
    ↓
call all collectors
    ↓
return immediately
```

The outer monitoring system therefore owns the sampling schedule.

---

# Graceful Shutdown

The terminal monitor runs continuously until the user stops it.

Pressing:

```text
Ctrl + C
```

causes Python to raise:

```python
KeyboardInterrupt
```

The monitor handles it:

```python
try:
    while True:
        ...

except KeyboardInterrupt:
    print("Stopping...")

finally:
    print("Monitor stopped cleanly.")
```

Without this handling, Python would normally display a traceback.

The graceful structure also gives us a place for future cleanup operations.

Possible future cleanup might include:

* flushing samples to disk
* closing database connections
* stopping worker threads
* closing files
* shutting down network connections

---

# Sampling and the Web Dashboard

The same concepts are also used by the Django interface.

The dashboard does not directly call:

```python
psutil.cpu_percent()
```

Instead:

```text
Django
   ↓
BackgroundMonitoringService
   ↓
SystemSampler
   ↓
Collectors
```

The result is returned through:

```text
/api/system/
```

The web interface therefore benefits from exactly the same monitoring calculations used by the terminal application.

---

# Current Django Sampling Behaviour

The Django web monitor now uses a **background sampling thread** rather than browser-request-driven collection.

```text
                   Background thread
                         │
                    wait ~1 second
                         ↓
                    SystemSampler
                         ↓
              latest sample + history
                         │
              ┌──────────┴──────────┐
              ▼                     ▼
       /api/system/          /api/processes/
              │                     │
              ▼                     ▼
        Overview page          Processes page
```

Only the background worker calls `SystemSampler.sample()`. HTTP requests now read already-collected data. Closing the browser therefore stops frontend polling but **does not stop monitoring** while the Django Python process remains alive.

---

# Background Monitoring Thread

`BackgroundMonitoringService.start()` primes the sampler and creates a Python `threading.Thread` whose target is the service's `_run()` method. The loop waits for roughly one sampling interval, takes one complete sample, stores it as `latest_sample`, and appends a smaller copy to `MonitorHistory`.

The worker is created with `daemon=True`. A daemon thread does not keep the Python process alive by itself; however, graceful shutdown is handled separately using a stop event and `join()`.

```text
Django process
│
├── HTTP request handling
│
└── sys-monitor-sampler thread
      ├── wait
      ├── sample
      ├── publish latest sample
      └── repeat
```

---

# Thread Events and Shutdown

The service uses two `threading.Event` objects:

- `_ready_event` indicates that at least one useful sample has been produced.
- `_stop_event` tells the worker to stop.

The sampling loop waits with `_stop_event.wait(sample_interval)` instead of a plain `time.sleep()`. This means a shutdown request can wake the worker immediately rather than waiting for the full interval.

`stop()` sets the stop event and then calls `thread.join(timeout=2)`, allowing the calling thread to wait briefly for the sampler to finish. `atexit.register(monitoring_service.stop)` requests this graceful shutdown during normal interpreter exit. `daemon=True` remains a final safety net so the worker cannot keep Python alive indefinitely.

---

# Thread Safety

`SystemSampler` contains mutable state:

```text
previous disk counters
previous network counters
```

`MonitorHistory` also changes as samples are added.

This means concurrent access must be handled carefully.

The background worker writes shared monitoring state while Django request threads read it. The service protects this state with a `threading.RLock()`.

```text
Background worker              API request
       │                           │
       ├── acquire lock            │
       ├── publish sample          │ waits briefly
       └── release lock            │
                                   ├── acquire lock
                                   ├── copy latest data
                                   └── release lock
```

The API receives deep copies of the latest sample/history so it can serialize them without holding the lock for the entire HTTP response. The `SystemSampler` itself remains focused on measurement rather than providing its own concurrency layer.

---

# Design Decision: Collector vs Sampler

One important architectural rule is:

> Collectors retrieve values. The sampler interprets values across time.

For example:

## Network collector

Returns:

```text
bytes_received
bytes_sent
```

## Sampler

Calculates:

```text
download bytes per second
upload bytes per second
```

This separation is deliberate.

The collector does not know:

* when the previous sample happened
* what the sampling interval is
* how history is stored

The sampler does.

---

# Design Decision: Sampler vs History

Similarly:

> The sampler creates samples. History stores samples.

The sampler does not need to know whether we retain:

```text
10 samples
60 samples
10,000 samples
```

It simply returns a result.

`MonitorHistory` decides how many samples to retain.

This gives us:

```text
SystemSampler
      ↓
one sample

MonitorHistory
      ↓
many samples
```

---

# Design Decision: Monitoring vs Presentation

The monitoring layer should not decide how data looks.

It should not produce strings such as:

```text
"CPU usage is 14.8%"

"Download is 3.42 MB/s"

"RAM is 15.3 GB"
```

Instead it returns values such as:

```python
14.8

3586129.2

16445685760
```

The presentation layer decides whether those become:

```text
14.8%

3.42 MB/s

15.3 GB
```

This allows different interfaces to format the same information differently.

---

# Current Monitoring Flow

The complete current monitoring flow is:

```mermaid
flowchart TD
    Timer[Sampling Trigger]

    Timer --> Sampler[SystemSampler]

    Sampler --> CPU[CPU Collector]
    Sampler --> RAM[Memory Collector]
    Sampler --> Disk[Disk Collector]
    Sampler --> Net[Network Collector]
    Sampler --> Proc[Process Collector]

    CPU --> Raw[Raw Measurements]
    RAM --> Raw
    Disk --> Raw
    Net --> Raw
    Proc --> Raw

    Raw --> Calc[Rate Calculations + Combination]

    Calc --> Sample[System Sample]

    Sample --> History[MonitorHistory]

    Sample --> Interface[Presentation Layer]
    History --> Interface
```

---

# Data Transformation

One of the main jobs of the monitoring layer is transforming data.

For example:

```text
RAW NETWORK COUNTERS

previous:
2,000,000,000 bytes

current:
2,010,000,000 bytes

elapsed:
1.02 seconds

        ↓

MONITORING CALCULATION

10,000,000 / 1.02

        ↓

9,803,921 bytes/sec

        ↓

PRESENTATION

9.35 MB/s
```

Each layer performs a different transformation.

---

# Current Limitations

The monitoring layer is still intentionally simple.

Current limitations include:

* the background worker currently runs inside the Django Python process rather than as a separate Windows service/process
* history is stored only in memory
* only 60 recent samples are retained
* samples disappear when the application stops
* no database persistence
* no configurable sampling interval through the UI
* no long-term aggregation
* no moving averages
* no anomaly detection
* no event correlation
* no historical process tracking
* no persistence of process start/stop events
* no sampling performance statistics
* no automatic handling of suspended/resumed system time

---

# Possible Future Monitoring Features

Future monitoring logic may include:

## Persistent History

Store samples in a database.

Possible periods:

```text
last hour
last day
last week
last month
```

---

## Aggregation

Instead of storing every one-second sample forever:

```text
1-second data
    ↓
aggregate

1-minute averages
    ↓
aggregate

1-hour averages
```

This reduces storage requirements.

---

## Spike Detection

Example:

```text
Normal CPU:
10–25%

Sudden sample:
96%

        ↓

CPU spike detected
```

---

## Sustained Load Detection

Rather than reacting to one high measurement:

```text
CPU > 90%
for 30 seconds
```

could trigger an event.

---

## Memory Leak Detection

A process whose memory usage continually grows:

```text
100 MB
120 MB
145 MB
180 MB
240 MB
...
```

could be identified as potentially leaking memory.

---

## Correlation

The monitor could later answer questions such as:

```text
CPU spike
    +
disk activity spike
    +
specific process CPU spike
        ↓

Likely cause:
process X
```

This would move the project from simple monitoring toward performance diagnosis.

---

# Future Monitoring Architecture

The current background thread already separates sampling from browser requests. A later production-style version may move that worker into a separate process/service and add persistent storage:

```mermaid
flowchart TD
    Windows[Windows]

    Windows --> Collectors[Collectors]

    Collectors --> Worker[Background Monitoring Worker]

    Worker --> Live[Live Rolling Buffer]
    Worker --> DB[(Historical Database)]
    Worker --> Analyzer[Performance Analyzer]

    Live --> API[Django API]
    DB --> API
    Analyzer --> API

    API --> Dashboard[Web Dashboard]
```

In this model:

* monitoring remains independent of browser requests
* the worker can survive or restart independently of Django
* history can survive application restarts
* analytics can operate independently of the UI

---

# Learning Concepts Covered

The monitoring layer introduces several important programming and computer-science concepts.

## Sampling

Observing a system repeatedly at intervals.

---

## Time Series

A collection of measurements ordered by time.

Example:

```text
time        CPU
20:01:01    10%
20:01:02    14%
20:01:03    29%
```

---

## Rate of Change

Calculating how quickly a cumulative value changes.

Used for:

* disk throughput
* network throughput

---

## State

Remembering information between operations.

Examples:

```text
previous disk counters
previous network counters
```

---

## Rolling Buffer

Keeping only the newest fixed number of observations.

Implemented using:

```python
deque(maxlen=60)
```

---

## Separation of Concerns

Keeping:

```text
data retrieval

data interpretation

data storage

presentation
```

in separate components.

---

## Abstraction

The rest of the application asks:

```python
sampler.sample(...)
```

without needing to know every individual psutil call underneath it.

---

## Concurrency

Multiple requests may attempt to access shared monitoring state.

The Django service currently controls this using a lock.

---

## Monotonic / Elapsed-Time Measurement

Using an elapsed-time-oriented clock such as:

```python
time.perf_counter()
```

for performance measurements rather than relying on wall-clock timestamps.

---

# Summary

The collector layer asks:

> What values does Windows expose right now?

The monitoring layer asks:

> What do those measurements mean when compared over time?

`SystemSampler` combines raw collector information, calculates time-based rates, ranks process usage, and produces one consistent system snapshot.

`MonitorHistory` retains a bounded rolling window of those snapshots.

Together they form the reusable monitoring engine shared by the terminal application and Django dashboard.

The next documentation layer, `architecture.md`, will step back from individual classes and describe how all major project components communicate from Windows system information through to the terminal and browser interfaces.
