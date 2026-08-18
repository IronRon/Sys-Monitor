from datetime import datetime, timezone
import re


def bytes_to_gib(bytes_value):
    if not bytes_value:
        return None

    return bytes_value / (1024 ** 3)


def clean_string(value):
    if value is None:
        return None

    value = str(value).strip()

    if not value:
        return None

    placeholders = {
        "0000",
        "unknown",
        "none",
        "not specified",
        "to be filled by o.e.m.",
        "default string",
    }

    if value.lower() in placeholders:
        return None

    return value


def parse_wmi_date(value):
    """
    Convert PowerShell's JSON representation:

        /Date(1703548800000)/

    into an ISO datetime string.
    """

    if not value:
        return None

    match = re.search(
        r"/Date\((\d+)\)/",
        value,
    )

    if not match:
        return value

    milliseconds = int(
        match.group(1)
    )

    date = datetime.fromtimestamp(
        milliseconds / 1000,
        tz=timezone.utc,
    )

    return date.isoformat()


def normalize_cpu(cpu):

    if not cpu:
        return None

    return {
        "name":
            clean_string(cpu.get("Name")),

        "manufacturer":
            clean_string(
                cpu.get("Manufacturer")
            ),

        "physical_cores":
            cpu.get("NumberOfCores"),

        "logical_processors":
            cpu.get(
                "NumberOfLogicalProcessors"
            ),

        "reported_clock_mhz":
            cpu.get("MaxClockSpeed"),

        "l2_cache_kb":
            cpu.get("L2CacheSize"),

        "l3_cache_kb":
            cpu.get("L3CacheSize"),
    }


def normalize_gpu(gpu):

    return {
        "name":
            clean_string(gpu.get("Name")),

        "video_processor":
            clean_string(
                gpu.get("VideoProcessor")
            ),

        "driver_version":
            clean_string(
                gpu.get("DriverVersion")
            ),

        # Keep this raw value, but explicitly
        # mark it as Windows-reported because
        # this field is not always reliable.
        "reported_vram_bytes":
            gpu.get("AdapterRAM"),
    }


def normalize_memory_module(module):

    return {
        "manufacturer":
            clean_string(
                module.get("Manufacturer")
            ),

        "part_number":
            clean_string(
                module.get("PartNumber")
            ),

        "capacity_bytes":
            module.get("Capacity"),

        "rated_speed_mt_s":
            module.get("Speed"),

        "configured_speed_mt_s":
            module.get(
                "ConfiguredClockSpeed"
            ),

        "slot":
            clean_string(
                module.get("DeviceLocator")
            ),
    }


def normalize_disk(disk):

    return {
        "name":
            (
                clean_string(
                    disk.get("FriendlyName")
                )
                or
                clean_string(
                    disk.get("Model")
                )
            ),

        "manufacturer":
            clean_string(
                disk.get("Manufacturer")
            ),

        "model":
            clean_string(
                disk.get("Model")
            ),

        "media_type":
            clean_string(
                disk.get("MediaType")
            ),

        "bus_type":
            clean_string(
                disk.get("BusType")
            ),

        "health":
            clean_string(
                disk.get("HealthStatus")
            ),

        "size_bytes":
            disk.get("Size"),
    }


def normalize_hardware(raw):

    memory_modules = [
        normalize_memory_module(module)

        for module
        in raw.get("memory", [])
    ]


    return {

        "system": {
            "manufacturer":
                clean_string(
                    raw["system"].get(
                        "Manufacturer"
                    )
                ),

            "model":
                clean_string(
                    raw["system"].get(
                        "Model"
                    )
                ),

            "system_type":
                clean_string(
                    raw["system"].get(
                        "SystemType"
                    )
                ),

            "total_memory_bytes":
                raw["system"].get(
                    "TotalPhysicalMemory"
                ),
        },


        "cpu":
            normalize_cpu(
                raw.get("cpu")
            ),


        "gpus": [
            normalize_gpu(gpu)

            for gpu
            in raw.get("gpus", [])
        ],


        "memory": {
            "module_count":
                len(memory_modules),

            "modules":
                memory_modules,

            "total_capacity_bytes":
                sum(
                    (
                        module[
                            "capacity_bytes"
                        ]
                        or 0
                    )

                    for module
                    in memory_modules
                ),
        },


        "motherboard": {
            "manufacturer":
                clean_string(
                    raw["motherboard"].get(
                        "Manufacturer"
                    )
                ),

            "product":
                clean_string(
                    raw["motherboard"].get(
                        "Product"
                    )
                ),

            "version":
                clean_string(
                    raw["motherboard"].get(
                        "Version"
                    )
                ),
        },


        "bios": {
            "manufacturer":
                clean_string(
                    raw["bios"].get(
                        "Manufacturer"
                    )
                ),

            "version":
                clean_string(
                    raw["bios"].get(
                        "SMBIOSBIOSVersion"
                    )
                ),

            "release_date":
                parse_wmi_date(
                    raw["bios"].get(
                        "ReleaseDate"
                    )
                ),
        },


        "disks": [
            normalize_disk(disk)

            for disk
            in raw.get("disks", [])
        ],
    }