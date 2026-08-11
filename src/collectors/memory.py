import psutil
# Notice we're returning raw bytes. 
# Don't convert them to GB inside the collector.
# That's a useful design decision:
# Collector
#     ↓
# raw data

# Presentation layer
#     ↓
# MB / GB / percentages / formatting

def get_memory_usage():
    memory = psutil.virtual_memory()

    return {
        "percent": memory.percent,
        "total": memory.total,
        "available": memory.available,
        "used": memory.used,
    }