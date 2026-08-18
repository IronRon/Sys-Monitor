import re

def explain_cpu(cpu):

    explanations = []

    cores = cpu.get("physical_cores")
    logical = cpu.get("logical_processors")
    l3 = cpu.get("l3_cache_kb")
    name = cpu.get("name") or ""

    parsed = parse_intel_cpu_name(name)

    if cores:
        explanations.append({
            "title": "Physical cores",

            "text": (
                f"This CPU has {cores} physical "
                "cores. A physical core is an "
                "actual hardware execution core "
                "inside the processor."
            ),
        })


    if cores and logical:
        if logical > cores:
            explanations.append({
                "title":
                    "Logical processors",

                "text": (
                    f"Windows sees {logical} "
                    f"logical processors from "
                    f"{cores} physical cores. "
                    "Logical processors are the "
                    "CPU execution targets that "
                    "the Windows scheduler can "
                    "assign threads to."
                ),
            })


    if l3:
        explanations.append({
            "title": "L3 cache",

            "text": (
                f"The processor reports "
                f"{l3 / 1024:.0f} MB of L3 "
                "cache. Cache is very fast "
                "memory located much closer to "
                "the CPU than normal system RAM."
            ),
        })


    # Small family-level interpretation rule.
    if parsed:
        tier = parsed["tier"]
        suffix = parsed["suffix"]

        if tier == "i9":
            explanations.append({
                "title": "Core i9",
                "text": (
                    "Core i9 is part of Intel's higher-"
                    "performance Core product tier. "
                    "The number 9 is a product tier name — "
                    "it does not mean the CPU has nine cores."
                ),
            })

    if "F" in suffix:
        explanations.append({
            "title": "The F suffix",
            "text": (
                "The F suffix identifies an Intel desktop "
                "processor intended to be used with a "
                "separate graphics card rather than relying "
                "on processor-integrated graphics."
            ),
        })

    return explanations


def parse_intel_cpu_name(name):

    if not name:
        return None


    match = re.search(
        r"Core\(TM\)\s+"
        r"(i[3579])-"
        r"(\d+)"
        r"([A-Z]*)",
        name,
        re.IGNORECASE,
    )


    if not match:
        return None


    tier = (
        match
        .group(1)
        .lower()
    )

    model_number = (
        match.group(2)
    )

    suffix = (
        match
        .group(3)
        .upper()
    )


    return {
        "tier":
            tier,

        "model_number":
            model_number,

        "suffix":
            suffix,
    }


def explain_memory(memory):

    modules = memory["modules"]


    explanations = []


    explanations.append({
        "title": "Installed memory",

        "text": (
            f"The computer has "
            f"{memory['module_count']} "
            "physical RAM modules installed."
        ),
    })


    if len(modules) == 2:

        capacities = {
            module["capacity_bytes"]

            for module in modules
        }


        if len(capacities) == 1:

            size = next(iter(capacities))

            explanations.append({
                "title":
                    "Matched memory modules",

                "text": (
                    "Both installed RAM modules "
                    "have the same capacity: "
                    f"{size / (1024 ** 3):.0f} GB "
                    "each."
                ),
            })


    rated_speeds = {
        module["rated_speed_mt_s"]

        for module in modules

        if module["rated_speed_mt_s"]
    }


    configured_speeds = {
        module["configured_speed_mt_s"]

        for module in modules

        if module[
            "configured_speed_mt_s"
        ]
    }


    if (
        len(rated_speeds) == 1
        and
        len(configured_speeds) == 1
    ):

        rated = next(iter(rated_speeds))

        configured = next(iter(
                configured_speeds
            ))


        if configured < rated:

            explanations.append({
                "title":
                    "Rated vs configured speed",

                "text": (
                    f"The DIMMs report a rated "
                    f"speed of {rated} MT/s, but "
                    f"they are currently configured "
                    f"at {configured} MT/s. "
                    "The rated value describes what "
                    "the module advertises, while "
                    "the configured value describes "
                    "the speed the system is "
                    "currently using."
                ),
            })


    return explanations


def explain_disk(disk):

    explanations = []


    if disk["media_type"] == "SSD":

        explanations.append({
            "title": "Solid-state drive",

            "text": (
                "This is an SSD. SSDs use "
                "non-volatile flash storage "
                "rather than rotating magnetic "
                "platters."
            ),
        })


    if disk["bus_type"] == "NVMe":

        explanations.append({
            "title": "NVMe",

            "text": (
                "This drive uses NVMe, a protocol "
                "designed for solid-state storage "
                "connected through PCI Express."
            ),
        })


    if disk["health"]:

        explanations.append({
            "title": "Drive health",

            "text": (
                f"Windows currently reports the "
                f"physical disk health as "
                f"{disk['health']}."
            ),
        })


    return explanations


def explain_gpu(gpu):
    explanations = []

    explanations.append({
        "title": "Graphics processor",
        "text": (
            "A GPU is a processor designed to execute many "
            "operations in parallel. It is primarily used for "
            "graphics rendering, but GPUs are also useful for "
            "other highly parallel workloads."
        ),
    })

    name = (
        gpu.get("name")
        or ""
    ).lower()

    if "nvidia" in name:
        explanations.append({
            "title": "NVIDIA",
            "text": (
                "NVIDIA is the manufacturer of this graphics "
                "processor. GeForce is NVIDIA's consumer "
                "graphics product family."
            ),
        })

    if "rtx" in name:
        explanations.append({
            "title": "RTX",
            "text": (
                "RTX is part of NVIDIA's GeForce branding for "
                "GPUs that include hardware intended for "
                "features such as accelerated ray tracing and "
                "AI-oriented workloads."
            ),
        })

    if gpu.get("reported_vram_bytes"):
        explanations.append({
            "title": "Reported video memory",
            "text": (
                "Windows reports a video-memory value for this "
                "adapter. Some Windows graphics interfaces may "
                "not report modern GPU VRAM capacity perfectly, "
                "so Sys Monitor labels this as a reported value "
                "rather than assuming it is authoritative."
            ),
        })

    return explanations


def explain_system(system):
    explanations = []

    if system.get("system_type") == "x64-based PC":
        explanations.append({
            "title": "x64-based PC",
            "text": (
                "x64 describes the 64-bit processor and "
                "operating-system architecture used by this PC. "
                "A 64-bit system can work with much larger "
                "address spaces than older 32-bit systems."
            ),
        })

    return explanations

def explain_motherboard(motherboard):
    return [
        {
            "title": "Motherboard",
            "text": (
                "The motherboard is the main circuit board of "
                "the computer. It connects major components such "
                "as the CPU, RAM, storage devices, graphics card "
                "and other peripherals."
            ),
        }
    ]

def explain_bios(bios):
    return [
        {
            "title": "BIOS / firmware",
            "text": (
                "System firmware starts before the operating "
                "system. It initialises hardware and provides "
                "low-level configuration information that "
                "Windows can query."
            ),
        }
    ]