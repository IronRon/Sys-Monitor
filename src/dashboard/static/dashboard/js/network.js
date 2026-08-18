let connections = [];


const connectionSearch =
    document.getElementById(
        "connection-search"
    );

const protocolFilter =
    document.getElementById(
        "protocol-filter"
    );

const remoteOnly =
    document.getElementById(
        "remote-only"
    );


function bytesToMB(bytes) {
    return bytes / (1024 ** 2);
}


function formatRate(bytes) {

    const mb = bytesToMB(bytes);

    if (mb >= 1) {
        return `${mb.toFixed(2)} MB/s`;
    }

    return `${(
        bytes / 1024
    ).toFixed(1)} KB/s`;
}


function formatEndpoint(endpoint) {

    if (!endpoint) {
        return "—";
    }

    if (
        endpoint.ip.includes(":")
    ) {
        return (
            `[${endpoint.ip}]:`
            +
            endpoint.port
        );
    }

    return (
        `${endpoint.ip}:`
        +
        endpoint.port
    );
}


const networkChart =
    new Chart(
        document.getElementById(
            "network-chart"
        ),
        {
            type: "line",

            data: {
                labels: [],

                datasets: [
                    {
                        label: "Download",
                        data: [],
                        borderWidth: 2,
                        pointRadius: 0,
                        tension: 0.3,
                    },

                    {
                        label: "Upload",
                        data: [],
                        borderWidth: 2,
                        pointRadius: 0,
                        tension: 0.3,
                    },
                ],
            },

            options: {
                responsive: true,
                maintainAspectRatio: false,
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


function updateChart(history) {

    networkChart.data.labels =
        history.map(
            item =>
                new Date(
                    item.timestamp
                )
                    .toLocaleTimeString(
                        [],
                        {
                            hour12: false,
                        }
                    )
        );


    networkChart
        .data
        .datasets[0]
        .data =
        history.map(
            item =>
                bytesToMB(
                    item
                        .download_bytes_per_second
                )
        );


    networkChart
        .data
        .datasets[1]
        .data =
        history.map(
            item =>
                bytesToMB(
                    item
                        .upload_bytes_per_second
                )
        );


    networkChart.update();


    document
        .getElementById(
            "network-sample-count"
        )
        .textContent =
        `${history.length} / 60 samples`;
}


function renderInterfaces(
    interfaces
) {

    const grid =
        document.getElementById(
            "interface-grid"
        );


    grid.innerHTML = "";


    interfaces.forEach(
        interface => {

            const card =
                document.createElement(
                    "article"
                );

            card.className =
                "interface-card";


            const addresses =
                interface.addresses
                    .map(
                        address => `
                        <div>
                            <span>
                                ${address.family}
                            </span>

                            <strong>
                                ${address.address}
                            </strong>
                        </div>
                    `
                    )
                    .join("");


            card.innerHTML = `
                <div class="interface-top">

                    <h3>
                        ${interface.name}
                    </h3>

                    <span
                        class="
                            interface-state
                            ${interface.is_up
                    ? "up"
                    : "down"
                }
                        "
                    >
                        ${interface.is_up
                    ? "UP"
                    : "DOWN"
                }
                    </span>

                </div>

                <div class="interface-stats">

                    <span>
                        Link
                        <strong>
                            ${interface.speed_mbps
                || "?"
                }
                            Mbps
                        </strong>
                    </span>

                    <span>
                        MTU
                        <strong>
                            ${interface.mtu ?? "?"}
                        </strong>
                    </span>

                    <span>
                        ↓
                        <strong>
                            ${formatRate(
                    interface
                        .download_bytes_per_second
                )}
                        </strong>
                    </span>

                    <span>
                        ↑
                        <strong>
                            ${formatRate(
                    interface
                        .upload_bytes_per_second
                )}
                        </strong>
                    </span>

                </div>

                <div class="interface-addresses">
                    ${addresses}
                </div>
            `;


            grid.appendChild(card);
        }
    );
}


function getFilteredConnections() {

    const query =
        connectionSearch.value
            .trim()
            .toLowerCase();


    const protocol =
        protocolFilter.value;


    return connections.filter(
        connection => {

            if (
                protocol !== "ALL"
                &&
                connection.protocol
                !== protocol
            ) {
                return false;
            }


            if (
                remoteOnly.checked
                &&
                !connection.remote
            ) {
                return false;
            }


            if (!query) {
                return true;
            }


            const searchable = [
                connection.process_name,
                connection.pid,
                connection.protocol,
                connection.family,
                formatEndpoint(
                    connection.local
                ),
                formatEndpoint(
                    connection.remote
                ),
                connection.hostname,
                connection.status,
            ]
                .filter(
                    value =>
                        value !== null
                        &&
                        value !== undefined
                )
                .join(" ")
                .toLowerCase();


            return searchable.includes(
                query
            );
        }
    );
}


function renderConnections() {

    const body =
        document.getElementById(
            "connection-body"
        );


    body.innerHTML = "";


    getFilteredConnections()
        .forEach(
            connection => {

                const row =
                    document.createElement(
                        "tr"
                    );


                row.innerHTML = `
                    <td>
                        <strong>
                            ${connection.process_name}
                        </strong>

                        <small>
                            PID ${connection.pid ?? "—"}
                        </small>
                    </td>

                    <td>
                        ${connection.protocol}
                        <small>
                            ${connection.family}
                        </small>
                    </td>

                    <td class="endpoint">
                        ${formatEndpoint(
                    connection.local
                )}
                    </td>

                    <td class="endpoint">
                        ${formatEndpoint(
                    connection.remote
                )}
                    </td>

                    <td>
                        ${connection.hostname
                    ?? "Resolving / unknown"
                    }
                    </td>

                    <td>
                        <span
                            class="
                                status-chip
                                status-${connection
                        .status
                        .toLowerCase()
                    }
                            "
                        >
                            ${connection.status}
                        </span>
                    </td>
                `;


                body.appendChild(row);
            }
        );
}


connectionSearch.addEventListener(
    "input",
    renderConnections
);

protocolFilter.addEventListener(
    "change",
    renderConnections
);

remoteOnly.addEventListener(
    "change",
    renderConnections
);


async function fetchNetwork() {

    try {

        const response =
            await fetch(
                "/api/network/"
            );


        if (!response.ok) {
            throw new Error(
                `HTTP ${response.status}`
            );
        }


        const data =
            await response.json();


        const network =
            data.network;


        document
            .getElementById(
                "network-download"
            )
            .textContent =
            formatRate(
                network
                    .download_bytes_per_second
            );


        document
            .getElementById(
                "network-upload"
            )
            .textContent =
            formatRate(
                network
                    .upload_bytes_per_second
            );


        document
            .getElementById(
                "network-established"
            )
            .textContent =
            network.summary.established;


        document
            .getElementById(
                "network-remote"
            )
            .textContent =
            network.summary
                .remote_connections;


        connections =
            network.connections;


        updateChart(
            data.history
        );


        renderInterfaces(
            network.interfaces
        );


        renderConnections();


        document
            .getElementById(
                "network-last-updated"
            )
            .textContent =
            `Updated ${new Date(
                data.timestamp
            )
                .toLocaleTimeString()
            }`;

    }

    catch (error) {

        console.error(
            "Unable to retrieve network data:",
            error
        );

    }

    finally {

        setTimeout(
            fetchNetwork,
            1000
        );
    }
}


fetchNetwork();