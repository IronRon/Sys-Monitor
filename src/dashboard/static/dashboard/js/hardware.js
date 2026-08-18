const loading =
    document.getElementById(
        "hardware-loading"
    );

const errorPanel =
    document.getElementById(
        "hardware-error"
    );

const errorMessage =
    document.getElementById(
        "hardware-error-message"
    );

const content =
    document.getElementById(
        "hardware-content"
    );


function bytesToGiB(bytes) {

    if (
        bytes === null
        ||
        bytes === undefined
    ) {
        return null;
    }

    return bytes / (1024 ** 3);
}


function formatGiB(bytes, decimals = 1) {

    const gib =
        bytesToGiB(bytes);

    if (gib === null) {
        return "Not reported";
    }

    return `${gib.toFixed(decimals)} GB`;
}


function formatStorage(bytes) {

    if (!bytes) {
        return "Unknown capacity";
    }

    const decimalTB =
        bytes / 1_000_000_000_000;

    if (decimalTB >= 0.9) {

        return `${decimalTB.toFixed(2)} TB`;
    }

    return `${(
        bytes / 1_000_000_000
    ).toFixed(0)} GB`;
}


function formatCache(kb) {

    if (!kb) {
        return "Not reported";
    }

    if (kb >= 1024) {

        return `${(
            kb / 1024
        ).toFixed(1)} MB`;
    }

    return `${kb} KB`;
}


function formatClock(mhz) {

    if (!mhz) {
        return "Not reported";
    }

    return `${(
        mhz / 1000
    ).toFixed(2)} GHz`;
}


function displayValue(value) {

    if (
        value === null
        ||
        value === undefined
        ||
        value === ""
    ) {
        return "Not reported";
    }

    return value;
}


function compactCpuName(name) {

    if (!name) {
        return "Unknown CPU";
    }

    return name
        .replace(
            /Intel\(R\)\s*/i,
            ""
        )
        .replace(
            /Core\(TM\)\s*/i,
            "Core "
        )
        .replace(
            /\s+CPU\s+@\s+.+$/i,
            ""
        )
        .trim();
}


function getCpuChipData(name) {

    if (!name) {
        return {
            tier: "CPU",
            model: "Unknown",
        };
    }

    const match =
        name.match(
            /(i[3579])-(\d+[A-Z]*)/i
        );


    if (!match) {

        return {
            tier: "CPU",
            model:
                compactCpuName(name),
        };
    }


    return {
        tier:
            match[1].toUpperCase(),

        model:
            match[2].toUpperCase(),
    };
}


function createExplanationCard(
    explanation
) {

    const card =
        document.createElement(
            "article"
        );

    card.className =
        "explanation-card";


    const title =
        document.createElement("h3");

    title.textContent =
        explanation.title;


    const text =
        document.createElement("p");

    text.textContent =
        explanation.text;


    card.append(
        title,
        text
    );


    return card;
}


function renderExplanations(
    container,
    explanations
) {

    container.innerHTML = "";


    explanations.forEach(
        (explanation) => {

            container.appendChild(
                createExplanationCard(
                    explanation
                )
            );
        }
    );
}


function renderHero(hardware) {

    const {
        system,
        cpu,
        gpus,
        memory,
        disks,
    } = hardware;


    document
        .getElementById(
            "system-model"
        )
        .textContent =
        displayValue(system.model);


    document
        .getElementById(
            "system-manufacturer"
        )
        .textContent =
        displayValue(
            system.manufacturer
        );


    document
        .getElementById(
            "system-type"
        )
        .textContent =
        displayValue(
            system.system_type
        );


    document
        .getElementById(
            "summary-cpu"
        )
        .textContent =
        compactCpuName(
            cpu.name
        );


    document
        .getElementById(
            "summary-cpu-detail"
        )
        .textContent =
        `${cpu.physical_cores} cores · `
        +
        `${cpu.logical_processors} logical`;


    const primaryGpu =
        gpus[0];


    document
        .getElementById(
            "summary-gpu"
        )
        .textContent =
        primaryGpu
            ? primaryGpu.name
            : "No GPU reported";


    document
        .getElementById(
            "summary-gpu-detail"
        )
        .textContent =
        primaryGpu
            ? `Driver ${primaryGpu.driver_version}`
            : "--";


    document
        .getElementById(
            "summary-memory"
        )
        .textContent =
        formatGiB(
            memory.total_capacity_bytes,
            0
        );


    document
        .getElementById(
            "summary-memory-detail"
        )
        .textContent =
        `${memory.module_count} physical modules`;


    const primaryDisk =
        disks[0];


    document
        .getElementById(
            "summary-storage"
        )
        .textContent =
        primaryDisk
            ? formatStorage(
                primaryDisk.size_bytes
            )
            : "No disk reported";


    document
        .getElementById(
            "summary-storage-detail"
        )
        .textContent =
        primaryDisk
            ? `${primaryDisk.media_type} · ${primaryDisk.bus_type}`
            : "--";
}


function renderCpu(
    cpu,
    explanations
) {

    const chip =
        getCpuChipData(
            cpu.name
        );


    document
        .getElementById(
            "cpu-name"
        )
        .textContent =
        compactCpuName(
            cpu.name
        );


    document
        .getElementById(
            "cpu-manufacturer"
        )
        .textContent =
        displayValue(
            cpu.manufacturer
        );


    document
        .getElementById(
            "cpu-chip-name"
        )
        .textContent =
        chip.tier;


    document
        .getElementById(
            "cpu-chip-model"
        )
        .textContent =
        chip.model;


    document
        .getElementById(
            "cpu-cores"
        )
        .textContent =
        cpu.physical_cores;


    document
        .getElementById(
            "cpu-logical"
        )
        .textContent =
        cpu.logical_processors;


    document
        .getElementById(
            "cpu-clock"
        )
        .textContent =
        formatClock(
            cpu.reported_clock_mhz
        );


    document
        .getElementById(
            "cpu-l3"
        )
        .textContent =
        formatCache(
            cpu.l3_cache_kb
        );


    document
        .getElementById(
            "cpu-l2"
        )
        .textContent =
        formatCache(
            cpu.l2_cache_kb
        );


    renderExplanations(
        document.getElementById(
            "cpu-explanations"
        ),
        explanations
    );
}


function renderGpu(gpus) {

    const container =
        document.getElementById(
            "gpu-grid"
        );


    container.innerHTML = "";


    gpus.forEach(
        (gpu, index) => {

            const card =
                document.createElement(
                    "article"
                );

            card.className =
                "gpu-card";


            const visual =
                document.createElement(
                    "div"
                );

            visual.className =
                "gpu-visual";

            visual.textContent =
                gpu.name
                    ?.toLowerCase()
                    .includes("nvidia")
                    ? "NVIDIA"
                    : "GPU";


            const info =
                document.createElement(
                    "div"
                );

            info.className =
                "gpu-info";


            const title =
                document.createElement(
                    "h3"
                );

            title.textContent =
                displayValue(
                    gpu.name
                );


            const specs =
                document.createElement(
                    "div"
                );

            specs.className =
                "spec-list";


            const specValues = [
                {
                    label:
                        "Video Processor",

                    value:
                        gpu.video_processor,
                },

                {
                    label:
                        "Driver Version",

                    value:
                        gpu.driver_version,
                },

                {
                    label:
                        "Windows-reported VRAM",

                    value:
                        formatGiB(
                            gpu.reported_vram_bytes,
                            2
                        ),
                },
            ];


            specValues.forEach(
                (spec) => {

                    const item =
                        document.createElement(
                            "div"
                        );

                    const label =
                        document.createElement(
                            "span"
                        );

                    const value =
                        document.createElement(
                            "strong"
                        );


                    label.textContent =
                        spec.label;

                    value.textContent =
                        displayValue(
                            spec.value
                        );


                    item.append(
                        label,
                        value
                    );

                    specs.appendChild(
                        item
                    );
                }
            );


            info.append(
                title,
                specs
            );


            card.append(
                visual,
                info
            );


            container.appendChild(
                card
            );
        }
    );
}


function renderMemory(
    memory,
    explanations
) {

    document
        .getElementById(
            "memory-total"
        )
        .textContent =
        formatGiB(
            memory.total_capacity_bytes,
            0
        );


    document
        .getElementById(
            "memory-module-summary"
        )
        .textContent =
        `${memory.module_count} physical RAM module`
        +
        (
            memory.module_count === 1
                ? ""
                : "s"
        );


    const container =
        document.getElementById(
            "memory-modules"
        );


    container.innerHTML = "";


    memory.modules.forEach(
        (module) => {

            const card =
                document.createElement(
                    "article"
                );

            card.className =
                "memory-module";


            const header =
                document.createElement(
                    "div"
                );

            header.className =
                "memory-module-header";


            const slot =
                document.createElement(
                    "span"
                );

            slot.className =
                "memory-slot";

            slot.textContent =
                displayValue(
                    module.slot
                );


            const capacity =
                document.createElement(
                    "strong"
                );

            capacity.className =
                "memory-capacity";

            capacity.textContent =
                formatGiB(
                    module.capacity_bytes,
                    0
                );


            header.append(
                slot,
                capacity
            );


            const speeds =
                document.createElement(
                    "div"
                );

            speeds.className =
                "memory-speed-grid";


            speeds.innerHTML = `
                <div>
                    <span>Rated</span>
                    <strong>
                        ${module.rated_speed_mt_s
                ?? "--"
                } MT/s
                    </strong>
                </div>

                <div>
                    <span>Configured</span>
                    <strong>
                        ${module.configured_speed_mt_s
                ?? "--"
                } MT/s
                    </strong>
                </div>
            `;


            card.append(
                header,
                speeds
            );


            container.appendChild(
                card
            );
        }
    );


    renderExplanations(
        document.getElementById(
            "memory-explanations"
        ),
        explanations
    );
}


function findDiskExplanations(
    disk,
    index,
    diskExplanations
) {

    return (
        diskExplanations.find(
            (entry) =>
                entry.disk_index === index
        )
            ? diskExplanations.find(
                (entry) =>
                    entry.disk_index === index
            ).items
            : []
    );
}


function renderDisks(
    disks,
    diskExplanations
) {

    const container =
        document.getElementById(
            "disk-grid"
        );


    container.innerHTML = "";


    disks.forEach(
        (disk, index) => {

            const card =
                document.createElement(
                    "article"
                );

            card.className =
                "disk-card";


            const top =
                document.createElement(
                    "div"
                );

            top.className =
                "disk-top";


            const name =
                document.createElement(
                    "h3"
                );

            name.className =
                "disk-name";

            name.textContent =
                displayValue(
                    disk.name
                );


            const tags =
                document.createElement(
                    "div"
                );

            tags.className =
                "disk-tags";


            [
                disk.media_type,
                disk.bus_type,
                disk.health,
            ]
                .filter(Boolean)
                .forEach(
                    (value) => {

                        const tag =
                            document.createElement(
                                "span"
                            );

                        tag.className =
                            "disk-tag";


                        if (
                            value
                                .toLowerCase()
                            === "healthy"
                        ) {

                            tag.classList.add(
                                "healthy"
                            );
                        }


                        tag.textContent =
                            value;


                        tags.appendChild(
                            tag
                        );
                    }
                );


            top.append(
                name,
                tags
            );


            const capacity =
                document.createElement(
                    "div"
                );

            capacity.className =
                "disk-capacity";


            const capacityValue =
                document.createElement(
                    "strong"
                );

            capacityValue.textContent =
                formatStorage(
                    disk.size_bytes
                );


            const capacityLabel =
                document.createElement(
                    "span"
                );

            capacityLabel.textContent =
                "physical capacity";


            capacity.append(
                capacityValue,
                capacityLabel
            );


            const explanations =
                document.createElement(
                    "div"
                );

            explanations.className =
                "disk-explanations";


            findDiskExplanations(
                disk,
                index,
                diskExplanations
            )
                .forEach(
                    (explanation) => {

                        explanations.appendChild(
                            createExplanationCard(
                                explanation
                            )
                        );
                    }
                );


            card.append(
                top,
                capacity,
                explanations
            );


            container.appendChild(
                card
            );
        }
    );
}


function renderPlatform(
    system,
    motherboard,
    bios
) {

    document
        .getElementById(
            "motherboard-product"
        )
        .textContent =
        displayValue(
            motherboard.product
        );


    document
        .getElementById(
            "motherboard-manufacturer"
        )
        .textContent =
        displayValue(
            motherboard.manufacturer
        );


    document
        .getElementById(
            "motherboard-version"
        )
        .textContent =
        displayValue(
            motherboard.version
        );


    document
        .getElementById(
            "bios-version"
        )
        .textContent =
        displayValue(
            bios.version
        );


    document
        .getElementById(
            "bios-manufacturer"
        )
        .textContent =
        displayValue(
            bios.manufacturer
        );


    const biosDate =
        bios.release_date
            ? new Date(
                bios.release_date
            )
            : null;


    document
        .getElementById(
            "bios-date"
        )
        .textContent =
        biosDate
            ? biosDate.toLocaleDateString()
            : "Not reported";


    document
        .getElementById(
            "platform-type"
        )
        .textContent =
        displayValue(
            system.system_type
        );


    document
        .getElementById(
            "platform-model"
        )
        .textContent =
        displayValue(
            system.model
        );


    document
        .getElementById(
            "platform-memory"
        )
        .textContent =
        formatGiB(
            system.total_memory_bytes,
            1
        );
}


function renderHardware(data) {

    const hardware =
        data.hardware;

    const explanations =
        data.explanations;


    renderHero(
        hardware
    );


    renderCpu(
        hardware.cpu,
        explanations.cpu || []
    );


    renderGpu(
        hardware.gpus || []
    );


    renderMemory(
        hardware.memory,
        explanations.memory || []
    );


    renderDisks(
        hardware.disks || [],
        explanations.disks || []
    );


    renderPlatform(
        hardware.system,
        hardware.motherboard,
        hardware.bios
    );
}


async function fetchHardware() {

    try {

        const response =
            await fetch(
                "/api/hardware/"
            );


        if (!response.ok) {

            throw new Error(
                `HTTP ${response.status}`
            );
        }


        const data =
            await response.json();


        renderHardware(
            data
        );


        loading.classList.add(
            "hidden"
        );


        content.classList.remove(
            "hidden"
        );

    }

    catch (error) {

        console.error(
            "Failed to retrieve hardware:",
            error
        );


        loading.classList.add(
            "hidden"
        );


        errorPanel.classList.remove(
            "hidden"
        );


        errorMessage.textContent =
            error.message;
    }
}


fetchHardware();