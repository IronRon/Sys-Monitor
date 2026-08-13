const cpuValue = document.getElementById("cpu-value");

const memoryValue =
    document.getElementById("memory-value");

const memoryDetail =
    document.getElementById("memory-detail");

const diskValue =
    document.getElementById("disk-value");

const diskDetail =
    document.getElementById("disk-detail");

const networkValue =
    document.getElementById("network-value");

const networkDetail =
    document.getElementById("network-detail");

const sampleCount =
    document.getElementById("sample-count");

const lastUpdated =
    document.getElementById("last-updated");

const cpuCoreGrid =
    document.getElementById("cpu-core-grid");

const cpuCoreSummary =
    document.getElementById("cpu-core-summary");

const topCpuProcesses =
    document.getElementById("top-cpu-processes");

const topMemoryProcesses =
    document.getElementById("top-memory-processes");


function bytesToGB(bytes) {
    return bytes / (1024 ** 3);
}


function bytesToMB(bytes) {
    return bytes / (1024 ** 2);
}


const cpuChart = new Chart(
    document.getElementById("cpu-chart"),
    {
        type: "line",

        data: {
            labels: [],

            datasets: [
                {
                    label: "CPU %",
                    data: [],
                    borderWidth: 2,
                    tension: 0.25,
                    pointRadius: 0,
                    fill: true,
                },
            ],
        },

        options: {
            responsive: true,
            maintainAspectRatio: false,
            animation: false,

            interaction: {
                intersect: false,
                mode: "index",
            },

            plugins: {
                legend: {
                    display: false,
                },
            },

            scales: {
                x: {
                    grid: {
                        display: false,
                    },

                    ticks: {
                        maxTicksLimit: 10,
                    },
                },

                y: {
                    min: 0,
                    max: 100,

                    ticks: {
                        callback: function (value) {
                            return `${value}%`;
                        },
                    },
                },
            },
        },
    }
);


function updateCards(data) {

    cpuValue.textContent =
        `${data.cpu.percent.toFixed(1)}%`;


    memoryValue.textContent =
        `${data.memory.percent.toFixed(1)}%`;

    memoryDetail.textContent =
        `${bytesToGB(
            data.memory.used_bytes
        ).toFixed(1)} GB used / `
        +
        `${bytesToGB(
            data.memory.total_bytes
        ).toFixed(1)} GB`;


    diskValue.textContent =
        `${data.disk.percent.toFixed(1)}%`;

    diskDetail.textContent =
        `Read `
        +
        `${bytesToMB(
            data.disk.read_bytes_per_second
        ).toFixed(2)} MB/s`
        +
        ` • Write `
        +
        `${bytesToMB(
            data.disk.write_bytes_per_second
        ).toFixed(2)} MB/s`;


    networkValue.textContent =
        `↓ `
        +
        `${bytesToMB(
            data.network.download_bytes_per_second
        ).toFixed(2)} MB/s`;

    networkDetail.textContent =
        `↑ `
        +
        `${bytesToMB(
            data.network.upload_bytes_per_second
        ).toFixed(2)} MB/s`;
}


function updateCpuChart(history) {

    cpuChart.data.labels =
        history.map((sample) => {

            const date =
                new Date(sample.timestamp);

            return date.toLocaleTimeString(
                [],
                {
                    hour: "2-digit",
                    minute: "2-digit",
                    second: "2-digit",
                }
            );
        });


    cpuChart.data.datasets[0].data =
        history.map(
            (sample) => sample.cpu_percent
        );


    cpuChart.update();
}

function updateCpuCores(cpu) {

    cpuCoreGrid.innerHTML = "";

    cpuCoreSummary.textContent =
        `${cpu.physical_cores} physical / `
        +
        `${cpu.logical_processors} logical`;


    cpu.per_cpu_percent.forEach(
        (percent, index) => {

            const core =
                document.createElement("div");

            core.classList.add("cpu-core");


            core.innerHTML = `
                <div class="cpu-core-header">

                    <span>
                        CPU ${index}
                    </span>

                    <strong>
                        ${percent.toFixed(1)}%
                    </strong>

                </div>

                <div class="cpu-core-track">

                    <div
                        class="cpu-core-fill"
                        style="width: ${percent}%"
                    ></div>

                </div>
            `;


            cpuCoreGrid.appendChild(core);
        }
    );
}

function updateTopCpuProcesses(processes) {

    topCpuProcesses.innerHTML = "";


    processes.forEach((process) => {

        const row =
            document.createElement("tr");


        row.innerHTML = `
            <td class="process-name">
                ${process.name}
            </td>

            <td class="process-pid">
                ${process.pid}
            </td>

            <td class="process-value">
                ${process.cpu_percent.toFixed(2)}%
            </td>
        `;


        topCpuProcesses.appendChild(row);
    });
}

function updateTopMemoryProcesses(processes) {

    topMemoryProcesses.innerHTML = "";


    processes.forEach((process) => {

        const row =
            document.createElement("tr");


        row.innerHTML = `
            <td class="process-name">
                ${process.name}
            </td>

            <td class="process-pid">
                ${process.pid}
            </td>

            <td class="process-value">
                ${bytesToMB(
                    process.memory_bytes
                ).toFixed(1)} MB
            </td>
        `;


        topMemoryProcesses.appendChild(row);
    });
}


async function fetchSystemData() {

    try {

        const response =
            await fetch("/api/system/");

        if (!response.ok) {
            throw new Error(
                `HTTP ${response.status}`
            );
        }

        const data =
            await response.json();


        updateCards(data);

        updateCpuChart(data.history);

        updateCpuCores(
            data.cpu
        );

        updateTopCpuProcesses(
            data.processes.top_cpu
        );

        updateTopMemoryProcesses(
            data.processes.top_memory
        );


        sampleCount.textContent =
            `${data.history.length} / 60`;


        const updated =
            new Date(data.timestamp);

        lastUpdated.textContent =
            `Updated `
            +
            updated.toLocaleTimeString();

    }
    catch (error) {

        console.error(
            "Failed to retrieve system data:",
            error
        );

        lastUpdated.textContent =
            "Unable to retrieve system data";
    }

    finally {

        setTimeout(
            fetchSystemData,
            1000
        );
    }
}


fetchSystemData();