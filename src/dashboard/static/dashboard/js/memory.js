const memoryRing =
    document.getElementById(
        "memory-ring"
    );

const memoryPercent =
    document.getElementById(
        "memory-percent"
    );

const memoryTotal =
    document.getElementById(
        "memory-total"
    );

const memoryUsed =
    document.getElementById(
        "memory-used"
    );

const memoryAvailable =
    document.getElementById(
        "memory-available"
    );

const pagefilePercent =
    document.getElementById(
        "pagefile-percent"
    );

const pagefileDetail =
    document.getElementById(
        "pagefile-detail"
    );

const usedBar =
    document.getElementById(
        "memory-used-bar"
    );

const availableBar =
    document.getElementById(
        "memory-available-bar"
    );

const breakdownUsed =
    document.getElementById(
        "breakdown-used"
    );

const breakdownAvailable =
    document.getElementById(
        "breakdown-available"
    );

const processBody =
    document.getElementById(
        "memory-process-body"
    );

const ramModules =
    document.getElementById(
        "ram-modules"
    );

const sampleCount =
    document.getElementById(
        "memory-sample-count"
    );

const lastUpdated =
    document.getElementById(
        "memory-last-updated"
    );


function bytesToGiB(bytes) {

    return bytes / (1024 ** 3);
}


function formatGiB(
    bytes,
    decimals = 1
) {

    return `${bytesToGiB(
        bytes
    ).toFixed(decimals)} GB`;
}


/* Chart */

const memoryChart =
    new Chart(
        document.getElementById(
            "memory-chart"
        ),
        {
            type: "line",

            data: {
                labels: [],

                datasets: [
                    {
                        label:
                            "In Use",

                        data: [],

                        borderWidth: 2,

                        tension: 0.3,

                        pointRadius: 0,

                        fill: false,
                    },

                    {
                        label:
                            "Available",

                        data: [],

                        borderWidth: 2,

                        tension: 0.3,

                        pointRadius: 0,

                        fill: false,
                    },
                ],
            },

            options: {
                responsive: true,

                maintainAspectRatio:
                    false,

                animation: false,

                interaction: {
                    mode: "index",
                    intersect: false,
                },

                scales: {
                    y: {
                        beginAtZero: true,

                        title: {
                            display: true,
                            text: "GB",
                        },
                    },

                    x: {
                        ticks: {
                            maxTicksLimit: 8,
                        },
                    },
                },
            },
        }
    );


function updateOverview(memory) {

    const percent =
        memory.percent;

    const angle =
        percent * 3.6;


    memoryRing.style.setProperty(
        "--memory-angle",
        `${angle}deg`
    );


    memoryPercent.textContent =
        `${percent.toFixed(1)}%`;


    memoryTotal.textContent =
        formatGiB(
            memory.total_bytes,
            1
        );


    memoryUsed.textContent =
        formatGiB(
            memory.in_use_bytes,
            1
        );


    memoryAvailable.textContent =
        formatGiB(
            memory.available_bytes,
            1
        );


    pagefilePercent.textContent =
        `${memory.pagefile.percent
            .toFixed(1)}%`;


    pagefileDetail.textContent =
        `${formatGiB(
            memory.pagefile.used_bytes
        )} used / `
        +
        `${formatGiB(
            memory.pagefile.total_bytes
        )}`;


    usedBar.style.width =
        `${percent}%`;


    availableBar.style.width =
        `${100 - percent}%`;


    breakdownUsed.textContent =
        formatGiB(
            memory.in_use_bytes
        );


    breakdownAvailable.textContent =
        formatGiB(
            memory.available_bytes
        );
}


function updateChart(history) {

    memoryChart.data.labels =
        history.map(
            sample => {

                const date =
                    new Date(
                        sample.timestamp
                    );

                return date
                    .toLocaleTimeString(
                        [],
                        {
                            hour12: false,
                        }
                    );
            }
        );


    memoryChart
        .data
        .datasets[0]
        .data =
        history.map(
            sample =>
                bytesToGiB(
                    sample.in_use_bytes
                )
        );


    memoryChart
        .data
        .datasets[1]
        .data =
        history.map(
            sample =>
                bytesToGiB(
                    sample.available_bytes
                )
        );


    memoryChart.update();


    sampleCount.textContent =
        `${history.length} / 60 samples`;
}


function renderProcesses(
    processes,
    totalMemory
) {

    processBody.innerHTML = "";


    const largest =
        processes.length
            ? processes[0]
                .memory_bytes
            : 1;


    processes.forEach(
        (process) => {

            const row =
                document.createElement(
                    "tr"
                );


            const percentage =
                (
                    process.memory_bytes
                    /
                    totalMemory
                )
                * 100;


            const relative =
                (
                    process.memory_bytes
                    /
                    largest
                )
                * 100;


            row.innerHTML = `
                <td class="memory-process-name">
                    ${process.name}
                </td>

                <td class="memory-process-pid">
                    ${process.pid}
                </td>

                <td class="memory-process-number">
                    ${formatGiB(
                process.memory_bytes,
                2
            )}
                </td>

                <td class="memory-process-number">
                    ${percentage.toFixed(2)}%
                </td>

                <td>
                    <div class="process-memory-track">

                        <div
                            class="process-memory-fill"
                            style="
                                width:
                                ${relative}%
                            "
                        >
                        </div>

                    </div>
                </td>
            `;


            processBody.appendChild(
                row
            );
        }
    );
}


function renderHardwareMemory(
    memory
) {

    ramModules.innerHTML = "";


    memory.modules.forEach(
        module => {

            const card =
                document.createElement(
                    "article"
                );


            card.className =
                "ram-module";


            card.innerHTML = `
                <div class="ram-module-top">

                    <span class="ram-module-slot">
                        ${module.slot}
                    </span>

                    <strong
                        class="ram-module-capacity"
                    >
                        ${formatGiB(
                module.capacity_bytes,
                0
            )}
                    </strong>

                </div>


                <div class="ram-module-speeds">

                    <span>
                        Rated
                        <strong>
                            ${module.rated_speed_mt_s}
                            MT/s
                        </strong>
                    </span>


                    <span>
                        Configured
                        <strong>
                            ${module.configured_speed_mt_s}
                            MT/s
                        </strong>
                    </span>

                </div>
            `;


            ramModules.appendChild(
                card
            );
        }
    );
}


async function fetchHardwareMemory() {

    try {

        const response =
            await fetch(
                "/api/hardware/"
            );


        if (!response.ok) {
            return;
        }


        const data =
            await response.json();


        renderHardwareMemory(
            data.hardware.memory
        );

    }

    catch (error) {

        console.error(
            "Unable to retrieve RAM hardware:",
            error
        );
    }
}


async function fetchMemory() {

    try {

        const response =
            await fetch(
                "/api/memory/"
            );


        if (!response.ok) {

            throw new Error(
                `HTTP ${response.status}`
            );
        }


        const data =
            await response.json();


        updateOverview(
            data.memory
        );


        updateChart(
            data.history
        );


        renderProcesses(
            data.top_processes,
            data.memory.total_bytes
        );


        const timestamp =
            new Date(
                data.timestamp
            );


        lastUpdated.textContent =
            `Updated `
            +
            timestamp
                .toLocaleTimeString();

    }

    catch (error) {

        console.error(
            "Unable to retrieve memory data:",
            error
        );


        lastUpdated.textContent =
            "Unable to retrieve memory data";
    }

    finally {

        setTimeout(
            fetchMemory,
            1000
        );
    }
}


fetchHardwareMemory();

fetchMemory();