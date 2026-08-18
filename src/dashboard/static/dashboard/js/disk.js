const diskPercent =
    document.getElementById(
        "disk-percent"
    );

const diskUsed =
    document.getElementById(
        "disk-used"
    );

const diskFree =
    document.getElementById(
        "disk-free"
    );

const diskTotal =
    document.getElementById(
        "disk-total"
    );

const diskRead =
    document.getElementById(
        "disk-read"
    );

const diskWrite =
    document.getElementById(
        "disk-write"
    );

const capacityUsedBar =
    document.getElementById(
        "capacity-used-bar"
    );

const capacityExample =
    document.getElementById(
        "capacity-example"
    );

const diskSampleCount =
    document.getElementById(
        "disk-sample-count"
    );

const diskLastUpdated =
    document.getElementById(
        "disk-last-updated"
    );

const physicalDiskGrid =
    document.getElementById(
        "physical-disk-grid"
    );


function bytesToGiB(bytes) {

    return bytes / (1024 ** 3);
}


function bytesToMiB(bytes) {

    return bytes / (1024 ** 2);
}


function formatCapacity(bytes) {

    const gib =
        bytesToGiB(bytes);

    if (gib >= 900) {

        return `${(
            bytes
            /
            1_000_000_000_000
        ).toFixed(2)} TB`;
    }

    return `${gib.toFixed(1)} GB`;
}


function formatThroughput(
    bytesPerSecond
) {

    const mib =
        bytesToMiB(
            bytesPerSecond
        );


    if (mib >= 1) {

        return `${mib.toFixed(2)} MB/s`;
    }


    const kib =
        bytesPerSecond / 1024;


    if (kib >= 1) {

        return `${kib.toFixed(1)} KB/s`;
    }


    return `${bytesPerSecond.toFixed(0)} B/s`;
}


/* Chart */

const diskChart =
    new Chart(
        document.getElementById(
            "disk-chart"
        ),
        {
            type: "line",

            data: {
                labels: [],

                datasets: [
                    {
                        label:
                            "Read",

                        data: [],

                        borderWidth: 2,

                        tension: 0.3,

                        pointRadius: 0,

                        fill: false,
                    },

                    {
                        label:
                            "Write",

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
                            text: "MB/s",
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


function updateOverview(disk) {

    diskPercent.textContent =
        `${disk.percent.toFixed(1)}%`;


    diskUsed.textContent =
        formatCapacity(
            disk.used_bytes
        );


    diskFree.textContent =
        formatCapacity(
            disk.free_bytes
        );


    diskTotal.textContent =
        formatCapacity(
            disk.total_bytes
        );


    diskRead.textContent =
        formatThroughput(
            disk.read_bytes_per_second
        );


    diskWrite.textContent =
        formatThroughput(
            disk.write_bytes_per_second
        );


    capacityUsedBar.style.width =
        `${disk.percent}%`;


    capacityExample.textContent =
        `${disk.percent.toFixed(1)}%`;
}


function updateChart(history) {

    diskChart.data.labels =
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


    diskChart
        .data
        .datasets[0]
        .data =
        history.map(
            sample =>
                bytesToMiB(
                    sample
                        .read_bytes_per_second
                )
        );


    diskChart
        .data
        .datasets[1]
        .data =
        history.map(
            sample =>
                bytesToMiB(
                    sample
                        .write_bytes_per_second
                )
        );


    diskChart.update();


    diskSampleCount.textContent =
        `${history.length} / 60 samples`;
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
        document.createElement(
            "h4"
        );

    title.textContent =
        explanation.title;


    const text =
        document.createElement(
            "p"
        );

    text.textContent =
        explanation.text;


    card.append(
        title,
        text
    );


    return card;
}


function findDiskExplanation(
    index,
    explanations
) {

    return explanations.find(
        item =>
            item.disk_index
            === index
    );
}


function renderHardwareDisks(
    disks,
    explanations
) {

    physicalDiskGrid.innerHTML =
        "";


    disks.forEach(
        (disk, index) => {

            const card =
                document.createElement(
                    "article"
                );

            card.className =
                "physical-disk";


            const top =
                document.createElement(
                    "div"
                );

            top.className =
                "physical-disk-top";


            const name =
                document.createElement(
                    "h3"
                );

            name.textContent =
                disk.name
                ?? "Unknown disk";


            const tags =
                document.createElement(
                    "div"
                );

            tags.className =
                "physical-disk-tags";


            [
                disk.media_type,
                disk.bus_type,
                disk.health,
            ]
                .filter(Boolean)
                .forEach(
                    value => {

                        const tag =
                            document.createElement(
                                "span"
                            );

                        tag.className =
                            "physical-disk-tag";


                        if (
                            value.toLowerCase()
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
                "physical-disk-capacity";

            capacity.textContent =
                formatCapacity(
                    disk.size_bytes
                );


            const explanationArea =
                document.createElement(
                    "div"
                );

            explanationArea.className =
                "physical-disk-explanations";


            const explanation =
                findDiskExplanation(
                    index,
                    explanations
                );


            if (explanation) {

                explanation.items.forEach(
                    item => {

                        explanationArea.appendChild(
                            createExplanationCard(
                                item
                            )
                        );
                    }
                );
            }


            card.append(
                top,
                capacity,
                explanationArea
            );


            physicalDiskGrid.appendChild(
                card
            );
        }
    );
}


async function fetchHardwareDisks() {

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


        renderHardwareDisks(
            data.hardware.disks,
            data.explanations.disks
            ?? []
        );

    }

    catch (error) {

        console.error(
            "Unable to retrieve disk hardware:",
            error
        );
    }
}


async function fetchDisk() {

    try {

        const response =
            await fetch(
                "/api/disk/"
            );


        if (!response.ok) {

            throw new Error(
                `HTTP ${response.status}`
            );
        }


        const data =
            await response.json();


        updateOverview(
            data.disk
        );


        updateChart(
            data.history
        );


        const timestamp =
            new Date(
                data.timestamp
            );


        diskLastUpdated.textContent =
            `Updated `
            +
            timestamp
                .toLocaleTimeString();

    }

    catch (error) {

        console.error(
            "Unable to retrieve disk data:",
            error
        );


        diskLastUpdated.textContent =
            "Unable to retrieve disk data";
    }

    finally {

        setTimeout(
            fetchDisk,
            1000
        );
    }
}


fetchHardwareDisks();

fetchDisk();