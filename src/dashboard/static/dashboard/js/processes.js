const processCount =
    document.getElementById("process-count");

const processSearch =
    document.getElementById("process-search");

const processTableBody =
    document.getElementById("process-table-body");

const processTree =
    document.getElementById("process-tree");

const lastUpdated =
    document.getElementById("process-last-updated");

const tableView =
    document.getElementById("table-view");

const treeView =
    document.getElementById("tree-view");

const tableViewButton =
    document.getElementById("table-view-button");

const treeViewButton =
    document.getElementById("tree-view-button");


let processes = [];

let sortKey = "cpu_percent";

let sortDirection = "desc";

const expandedPids = new Set();

function bytesToMB(bytes) {
    return bytes / (1024 ** 2);
}


function formatMemory(bytes) {

    const mb =
        bytesToMB(bytes);

    if (mb >= 1024) {

        return `${(
            mb / 1024
        ).toFixed(2)} GB`;
    }

    return `${mb.toFixed(1)} MB`;
}

function getFilteredProcesses() {

    const query =
        processSearch.value
            .trim()
            .toLowerCase();


    if (!query) {
        return [...processes];
    }


    return processes.filter((process) => {

        const name =
            process.name.toLowerCase();

        const pid =
            String(process.pid);

        const ppid =
            String(process.ppid);


        return (
            name.includes(query)
            ||
            pid.includes(query)
            ||
            ppid.includes(query)
        );
    });
}

function sortProcesses(items) {

    return items.sort((a, b) => {

        let aValue = a[sortKey];
        let bValue = b[sortKey];


        if (
            typeof aValue === "string"
            &&
            typeof bValue === "string"
        ) {

            aValue =
                aValue.toLowerCase();

            bValue =
                bValue.toLowerCase();
        }


        if (aValue < bValue) {

            return (
                sortDirection === "asc"
                    ? -1
                    : 1
            );
        }


        if (aValue > bValue) {

            return (
                sortDirection === "asc"
                    ? 1
                    : -1
            );
        }


        return 0;
    });
}

document
    .querySelectorAll(
        ".process-list-table th[data-sort]"
    )
    .forEach((header) => {

        header.addEventListener(
            "click",
            () => {

                const newSortKey =
                    header.dataset.sort;


                if (sortKey === newSortKey) {

                    sortDirection =
                        (
                            sortDirection === "asc"
                                ? "desc"
                                : "asc"
                        );
                }

                else {

                    sortKey =
                        newSortKey;

                    sortDirection =
                        (
                            newSortKey === "name"
                                ? "asc"
                                : "desc"
                        );
                }


                render();
            }
        );
    });

function createTableCell(
    value,
    className = ""
) {

    const cell =
        document.createElement("td");

    cell.textContent =
        value;

    if (className) {

        cell.className =
            className;
    }

    return cell;
}


function renderTable(items) {

    processTableBody.innerHTML = "";


    items.forEach((process) => {

        const row =
            document.createElement("tr");


        row.appendChild(
            createTableCell(
                process.name,
                "process-table-name"
            )
        );


        row.appendChild(
            createTableCell(
                process.pid,
                "process-table-pid"
            )
        );


        row.appendChild(
            createTableCell(
                process.ppid,
                "process-table-pid"
            )
        );


        row.appendChild(
            createTableCell(
                `${process.cpu_percent.toFixed(2)}%`,
                "process-table-number"
            )
        );


        row.appendChild(
            createTableCell(
                formatMemory(
                    process.memory_bytes
                ),
                "process-table-number"
            )
        );


        processTableBody.appendChild(
            row
        );
    });
}

function buildProcessTree(items) {

    const nodes =
        new Map();


    items.forEach((process) => {

        nodes.set(
            process.pid,
            {
                ...process,
                children: [],
            }
        );
    });


    const roots = [];


    nodes.forEach((node) => {

        const parent =
            nodes.get(node.ppid);


        if (
            parent
            &&
            node.ppid !== node.pid
        ) {

            parent.children.push(
                node
            );
        }

        else {

            roots.push(
                node
            );
        }
    });


    return roots;
}

function createTreeNode(
    node,
    isRoot = false,
    visited = new Set()
) {

    if (visited.has(node.pid)) {

        const cycle =
            document.createElement("div");

        cycle.textContent =
            `[cycle detected: PID ${node.pid}]`;

        return cycle;
    }


    const newVisited =
        new Set(visited);

    newVisited.add(
        node.pid
    );


    const details =
        document.createElement("details");


    details.classList.add(
        "tree-node"
    );


    if (isRoot) {

        details.classList.add(
            "tree-node-root"
        );
    }


    if (
        expandedPids.has(node.pid)
    ) {

        details.open = true;
    }


    const summary =
        document.createElement("summary");


    const toggle =
        document.createElement("span");

    toggle.className =
        "tree-toggle";

    toggle.textContent =
        node.children.length
            ? "▶"
            : "•";


    const name =
        document.createElement("span");

    name.className =
        "tree-process-name";

    name.textContent =
        node.name;


    const info =
        document.createElement("span");

    info.className =
        "tree-process-info";

    info.textContent =
        `PID ${node.pid} · PPID ${node.ppid}`;


    const resources =
        document.createElement("span");

    resources.className =
        "tree-process-resource";

    resources.textContent =
        `${node.cpu_percent.toFixed(2)}% · `
        +
        formatMemory(
            node.memory_bytes
        );


    summary.append(
        toggle,
        name,
        info,
        resources
    );


    details.appendChild(
        summary
    );


    if (node.children.length) {

        const children =
            document.createElement("div");

        children.className =
            "tree-children";


        node.children
            .sort(
                (a, b) =>
                    a.name.localeCompare(
                        b.name
                    )
            )
            .forEach((child) => {

                children.appendChild(
                    createTreeNode(
                        child,
                        false,
                        newVisited
                    )
                );
            });


        details.appendChild(
            children
        );
    }


    details.addEventListener(
        "toggle",
        () => {

            if (details.open) {

                expandedPids.add(
                    node.pid
                );
            }

            else {

                expandedPids.delete(
                    node.pid
                );
            }
        }
    );


    return details;
}

function renderTree(items) {

    processTree.innerHTML = "";


    const roots =
        buildProcessTree(items);


    roots
        .sort(
            (a, b) =>
                a.name.localeCompare(
                    b.name
                )
        )
        .forEach((root) => {

            processTree.appendChild(
                createTreeNode(
                    root,
                    true
                )
            );
        });
}

function render() {

    const filtered =
        getFilteredProcesses();


    const sorted =
        sortProcesses(filtered);


    renderTable(
        sorted
    );


    renderTree(
        filtered
    );
}

processSearch.addEventListener(
    "input",
    () => {
        render();
    }
);

tableViewButton.addEventListener(
    "click",
    () => {

        tableView.classList.remove(
            "hidden"
        );

        treeView.classList.add(
            "hidden"
        );


        tableViewButton.classList.add(
            "active"
        );

        treeViewButton.classList.remove(
            "active"
        );
    }
);


treeViewButton.addEventListener(
    "click",
    () => {

        treeView.classList.remove(
            "hidden"
        );

        tableView.classList.add(
            "hidden"
        );


        treeViewButton.classList.add(
            "active"
        );

        tableViewButton.classList.remove(
            "active"
        );
    }
);

async function fetchProcesses() {

    try {

        const response =
            await fetch(
                "/api/processes/"
            );


        if (!response.ok) {

            throw new Error(
                `HTTP ${response.status}`
            );
        }


        const data =
            await response.json();


        processes =
            data.processes;


        processCount.textContent =
            data.count;


        render();


        const updated =
            new Date(
                data.timestamp
            );


        lastUpdated.textContent =
            `Updated `
            +
            updated.toLocaleTimeString();

    }

    catch (error) {

        console.error(
            "Failed to retrieve processes:",
            error
        );


        lastUpdated.textContent =
            "Unable to retrieve process data";
    }

    finally {

        setTimeout(
            fetchProcesses,
            1000
        );
    }
}


fetchProcesses();