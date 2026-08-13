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

const cpuCard = document.getElementById("cpu-card");
const memoryCard = document.getElementById("memory-card");
const diskCard = document.getElementById("disk-card");
const networkCard = document.getElementById("network-card");

const cpuMeter = document.getElementById("cpu-meter");
const memoryMeter = document.getElementById("memory-meter");
const diskMeter = document.getElementById("disk-meter");
const networkMeter = document.getElementById("network-meter");

const cpuState = document.getElementById("cpu-state");
const memoryState = document.getElementById("memory-state");
const diskState = document.getElementById("disk-state");
const networkState = document.getElementById("network-state");


function bytesToGB(bytes) {
    return bytes / (1024 ** 3);
}


function bytesToMB(bytes) {
    return bytes / (1024 ** 2);
}

function getUsageLabel(percent) {
    if (percent < 20) return "Idle";
    if (percent < 45) return "Normal";
    if (percent < 70) return "Busy";
    if (percent < 90) return "High";
    return "Critical";
}

function setMetricVisual(card, meter, stateElement, percent) {
    meter.style.width = `${Math.max(0, Math.min(percent, 100))}%`;
    stateElement.textContent = getUsageLabel(percent);

    const glow =
        percent > 85
            ? "0 0 28px rgba(255, 90, 90, 0.18)"
            : percent > 60
                ? "0 0 22px rgba(255, 180, 50, 0.14)"
                : "0 18px 50px rgba(0, 0, 0, 0.22)";

    card.style.boxShadow = glow;
}

function getCoreHue(percent) {
    if (percent < 20) return 205;   // blue
    if (percent < 40) return 165;   // green-cyan
    if (percent < 60) return 95;    // green/yellow
    if (percent < 80) return 38;    // amber
    return 8;                       // red-orange
}

function getCoreState(percent) {
    if (percent < 15) return "Idle";
    if (percent < 40) return "Active";
    if (percent < 70) return "Busy";
    if (percent < 90) return "Hot";
    return "Maxed";
}

function getCoreSpan(percent) {
    return percent >= 75 ? 2 : 1;
}

function getCoreScale(percent) {
    return (0.85 + (percent / 100) * 0.38).toFixed(2);
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
    const cpuPercent = data.cpu.percent;
    const memoryPercent = data.memory.percent;
    const diskPercent = data.disk.percent;

    const downloadMB =
        bytesToMB(data.network.download_bytes_per_second);

    const uploadMB =
        bytesToMB(data.network.upload_bytes_per_second);

    cpuValue.textContent =
        `${cpuPercent.toFixed(1)}%`;

    memoryValue.textContent =
        `${memoryPercent.toFixed(1)}%`;

    memoryDetail.textContent =
        `${bytesToGB(data.memory.used_bytes).toFixed(1)} GB used / `
        +
        `${bytesToGB(data.memory.total_bytes).toFixed(1)} GB`;

    diskValue.textContent =
        `${diskPercent.toFixed(1)}%`;

    diskDetail.textContent =
        `Read ${bytesToMB(data.disk.read_bytes_per_second).toFixed(2)} MB/s`
        +
        ` • Write ${bytesToMB(data.disk.write_bytes_per_second).toFixed(2)} MB/s`;

    networkValue.textContent =
        `↓ ${downloadMB.toFixed(2)} MB/s`;

    networkDetail.textContent =
        `↑ ${uploadMB.toFixed(2)} MB/s`;

    const networkVisualPercent =
        Math.min(
            100,
            ((downloadMB + uploadMB) / 10) * 100
        );

    setMetricVisual(cpuCard, cpuMeter, cpuState, cpuPercent);
    setMetricVisual(memoryCard, memoryMeter, memoryState, memoryPercent);
    setMetricVisual(diskCard, diskMeter, diskState, diskPercent);
    setMetricVisual(networkCard, networkMeter, networkState, networkVisualPercent);

    networkState.textContent =
        downloadMB + uploadMB > 0.5 ? "Active" : "Quiet";
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

    cpu.per_cpu_percent.forEach((percent, index) => {
        const core = document.createElement("div");

        const hue = getCoreHue(percent);
        const span = getCoreSpan(percent);
        const scale = getCoreScale(percent);
        const state = getCoreState(percent);

        core.classList.add("cpu-core");
        core.style.setProperty("--hue", hue);
        core.style.setProperty("--span", span);
        core.style.setProperty("--scale", scale);

        core.innerHTML = `
            <div class="cpu-core-top">
                <div>
                    <div class="cpu-core-number">CPU ${index}</div>
                    <div class="cpu-core-state">${state}</div>
                </div>
                <div class="cpu-core-percent">${percent.toFixed(1)}%</div>
            </div>

            <div class="cpu-core-icon">
                ▣
            </div>

            <div class="cpu-core-bottom">
                <div class="cpu-core-mini-track">
                    <div
                        class="cpu-core-mini-fill"
                        style="width: ${percent}%"
                    ></div>
                </div>
            </div>
        `;

        cpuCoreGrid.appendChild(core);
    });
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