Architecture has now grown nicely

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
