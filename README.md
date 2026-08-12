# Sys_Monitor

Lightweight Windows system monitor that samples system metrics (CPU, memory, disk, network, processes) once per second, keeps a 60-second history, and prints a terminal UI. Built on psutil.

## Quickstart

Prerequisites:
- Python 3.8+
- psutil

Install and run:
```powershell
pip install -r requirements.txt
python -m src.monitor
```

## Architecture (overview)

### Project layout (src):

monitor.py — terminal UI / entry point
process_tree.py — helper for process hierarchy
collectors/
cpu.py
memory.py
disk.py
network.py
processes.py
monitoring/
sampler.py — combines measurements, computes rates
history.py — stores recent snapshots

| Component      | Responsibility                       |
| -------------- | ------------------------------------ |
| `cpu.py`       | Read CPU information                 |
| `memory.py`    | Read RAM information                 |
| `disk.py`      | Read disk counters                   |
| `network.py`   | Read network counters                |
| `processes.py` | Read/rank processes                  |
| `sampler.py`   | Combine everything into one snapshot |
| `history.py`   | Store recent snapshots               |
| `monitor.py`   | Terminal UI                          |



We started here:

Windows
   ↓
psutil
   ↓
print numbers

Now we have:

                       WINDOWS
                          │
                          ▼
                       psutil
                          │
         ┌────────────────┼────────────────┐
         │                │                │
         ▼                ▼                ▼
       CPU             Memory           Processes
         │                │                │
         │                │         ┌──────┴───────┐
         │                │         ▼              ▼
         │                │     CPU ranking    RAM ranking
         │                │
         └────────────────┼────────────────┐
                          ▼
                      monitor.py
                          │
                 one sample / second
                          │
                          ▼
                   deque(maxlen=60)
                          │
                          ▼
                    60 sec history
                          │
               ┌──────────┴──────────┐
               ▼                     ▼
           terminal               future UI
                                    │
                               live graphs


SystemSampler
│
├── previous_disk
├── previous_network
│
├── prime()
│
└── sample()


collectors/
│
├── cpu.py
├── memory.py
├── disk.py
├── network.py
└── processes.py
        │
        │ raw measurements
        ▼
monitoring/
│
├── sampler.py
│      │
│      └── combines measurements
│          + calculates rates
│
└── history.py
       │
       └── stores samples
              │
              ▼
monitor.py
│
└── displays terminal output


### Sample schema (per-sample keys)
sample
│
├── timestamp
│
├── cpu
│   ├── percent
│   └── per_cpu_percent
│
├── memory
│   ├── percent
│   ├── total_bytes
│   ├── used_bytes
│   └── available_bytes
│
├── disk
│   ├── percent
│   ├── read_bytes_per_second
│   └── write_bytes_per_second
│
├── network
│   ├── download_bytes_per_second
│   └── upload_bytes_per_second
│
└── processes
    ├── count
    ├── top_cpu
    └── top_memory


                            WINDOWS
                               │
                               ▼
                             psutil
                               │
              ┌────────────────┼───────────────┐
              ▼                ▼               ▼
             CPU             Disk           Processes
              │                │               │
              └────────────────┼───────────────┘
                               ▼
                         SystemSampler
                               │
                               ▼
                       MonitoringService
                         │           │
                         ▼           ▼
                    latest data    history
                         │           │
                         └─────┬─────┘
                               ▼
                         Django view
                               │
                               ▼
                         /api/system/
                               │
                              JSON
                               │
                               ▼
                         JavaScript
                               │
                 ┌─────────────┴────────────┐
                 ▼                          ▼
            metric cards                Chart.js
                                            │
                                            ▼
                                      CPU history