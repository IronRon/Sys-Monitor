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

const graphView =
    document.getElementById("graph-view");

const tableViewButton =
    document.getElementById("table-view-button");

const treeViewButton =
    document.getElementById("tree-view-button");

const graphViewButton =
    document.getElementById("graph-view-button");

const graphContainer =
    document.getElementById("process-graph");

const graphStats =
    document.getElementById("graph-stats");

const graphZoomLabel =
    document.getElementById("graph-zoom-label");

const graphZoomOutButton =
    document.getElementById("graph-zoom-out");

const graphZoomInButton =
    document.getElementById("graph-zoom-in");

const graphFitButton =
    document.getElementById("graph-fit");

const graphRelayoutButton =
    document.getElementById("graph-relayout");

const graphNodeDetails =
    document.getElementById("graph-node-details");

const graphDetailsClose =
    document.getElementById("graph-details-close");

const graphDetailsName =
    document.getElementById("graph-details-name");

const graphDetailsPid =
    document.getElementById("graph-details-pid");

const graphDetailsPpid =
    document.getElementById("graph-details-ppid");

const graphDetailsCpu =
    document.getElementById("graph-details-cpu");

const graphDetailsMemory =
    document.getElementById("graph-details-memory");

const graphDetailsChildren =
    document.getElementById("graph-details-children");


let processes = [];
let sortKey = "cpu_percent";
let sortDirection = "desc";
let currentView = "table";

const expandedPids = new Set();

let processGraph = null;
let graphTopologySignature = null;
let graphLayoutDirty = false;
let selectedGraphPid = null;


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


function truncateText(value, maxLength = 24) {

    if (value.length <= maxLength) {
        return value;
    }

    return `${value.slice(0, maxLength - 1)}…`;
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


/* -------------------------------------------------------------------------- */
/* Cytoscape graph view                                                        */
/* -------------------------------------------------------------------------- */

function getCpuGraphClass(percent) {

    if (percent < 10) {
        return "cpu-idle";
    }

    if (percent < 30) {
        return "cpu-active";
    }

    if (percent < 60) {
        return "cpu-busy";
    }

    if (percent < 85) {
        return "cpu-hot";
    }

    return "cpu-critical";
}


function getGraphTopologySignature(items) {

    return [...items]
        .sort((a, b) => a.pid - b.pid)
        .map(
            (process) =>
                `${process.pid}:${process.ppid}`
        )
        .join("|");
}


function getGraphSizing(items) {

    const maxMemory =
        Math.max(
            1,
            ...items.map(
                (process) => process.memory_bytes
            )
        );


    return new Map(
        items.map((process) => {

            const ratio =
                Math.sqrt(
                    Math.max(
                        0,
                        process.memory_bytes
                    ) / maxMemory
                );

            return [
                process.pid,
                {
                    width: 164 + (ratio * 54),
                    height: 76 + (ratio * 22),
                },
            ];
        })
    );
}


function buildGraphElements(items) {

    const processByPid =
        new Map(
            items.map(
                (process) => [
                    process.pid,
                    process,
                ]
            )
        );

    const sizing =
        getGraphSizing(items);

    const nodes = [];
    const edges = [];


    items.forEach((process) => {

        const parentExists =
            processByPid.has(process.ppid)
            &&
            process.ppid !== process.pid;

        const size =
            sizing.get(process.pid);

        const nodeClasses = [
            getCpuGraphClass(
                process.cpu_percent
            ),
        ];

        if (!parentExists) {
            nodeClasses.push("graph-root");
        }


        nodes.push({
            group: "nodes",
            data: {
                id: `pid-${process.pid}`,
                pid: process.pid,
                ppid: process.ppid,
                parentNodeId:
                    parentExists
                        ? `pid-${process.ppid}`
                        : "",
                name: process.name,
                cpu: process.cpu_percent,
                memory: process.memory_bytes,
                cardWidth: size.width,
                cardHeight: size.height,
                label:
                    `${truncateText(process.name)}\n`
                    + `PID ${process.pid} • PPID ${process.ppid}\n`
                    + `CPU ${process.cpu_percent.toFixed(2)}% • ${formatMemory(process.memory_bytes)}`,
            },
            classes: nodeClasses.join(" "),
        });


        if (parentExists) {

            edges.push({
                group: "edges",
                data: {
                    id:
                        `edge-${process.ppid}-${process.pid}`,
                    source:
                        `pid-${process.ppid}`,
                    target:
                        `pid-${process.pid}`,
                },
            });
        }
    });


    return {
        nodes,
        edges,
    };
}


function getGraphStyle() {

    return [
        {
            selector: "node",
            style: {
                "shape": "round-rectangle",
                "width": "data(cardWidth)",
                "height": "data(cardHeight)",
                "background-color": "#17233a",
                "background-opacity": 0.96,
                "border-width": 1.5,
                "border-color": "#44536e",
                "label": "data(label)",
                "color": "#eef4ff",
                "font-family": "Segoe UI, Arial, sans-serif",
                "font-size": 10.5,
                "font-weight": 500,
                "text-wrap": "wrap",
                "text-max-width": 190,
                "text-valign": "center",
                "text-halign": "center",
                "text-justification": "center",
                "line-height": 1.45,
                "overlay-opacity": 0,
                "transition-property":
                    "background-color, border-color, opacity, width, height",
                "transition-duration": "220ms",
                "min-zoomed-font-size": 6,
            },
        },
        {
            selector: "node.cpu-idle",
            style: {
                "background-color": "#13253f",
                "border-color": "#315f94",
            },
        },
        {
            selector: "node.cpu-active",
            style: {
                "background-color": "#13343a",
                "border-color": "#2c8b8c",
            },
        },
        {
            selector: "node.cpu-busy",
            style: {
                "background-color": "#38401d",
                "border-color": "#93a742",
            },
        },
        {
            selector: "node.cpu-hot",
            style: {
                "background-color": "#49321c",
                "border-color": "#db8b39",
            },
        },
        {
            selector: "node.cpu-critical",
            style: {
                "background-color": "#4d2024",
                "border-color": "#ef5b64",
                "border-width": 2,
            },
        },
        {
            selector: "node.graph-root",
            style: {
                "border-width": 2.5,
                "border-style": "double",
            },
        },
        {
            selector: "edge",
            style: {
                "width": 1.35,
                "line-color": "#35445f",
                "target-arrow-color": "#536783",
                "target-arrow-shape": "triangle",
                "arrow-scale": 0.75,
                "curve-style": "taxi",
                "taxi-direction": "downward",
                "taxi-turn": 24,
                "taxi-turn-min-distance": 12,
                "opacity": 0.78,
                "overlay-opacity": 0,
            },
        },
        {
            selector: ".search-dim",
            style: {
                "opacity": 0.11,
            },
        },
        {
            selector: "edge.search-dim",
            style: {
                "opacity": 0.055,
            },
        },
        {
            selector: "node.search-match",
            style: {
                "border-color": "#8eb1ff",
                "border-width": 3,
                "opacity": 1,
            },
        },
        {
            selector: "edge.search-match",
            style: {
                "line-color": "#6489d7",
                "target-arrow-color": "#6489d7",
                "opacity": 0.85,
            },
        },
        {
            selector: "node:selected",
            style: {
                "border-color": "#ffffff",
                "border-width": 3,
                "opacity": 1,
            },
        },
    ];
}


function getGraphLayoutOptions() {

    return {
        name: "dagre",
        rankDir: "TB",
        ranker: "network-simplex",
        nodeSep: 42,
        edgeSep: 18,
        rankSep: 105,
        spacingFactor: 1.08,
        nodeDimensionsIncludeLabels: true,
        fit: true,
        padding: 70,
        animate: false,
    };
}


function setGraphLayoutDirty(isDirty) {

    graphLayoutDirty =
        isDirty;

    graphRelayoutButton.classList.toggle(
        "needs-layout",
        isDirty
    );

    graphRelayoutButton.title =
        isDirty
            ? "Processes changed. Relayout the graph when convenient."
            : "Recalculate the graph layout";
}


function updateGraphStats(items) {

    const processByPid =
        new Set(
            items.map(
                (process) => process.pid
            )
        );

    let links = 0;
    let roots = 0;

    items.forEach((process) => {

        if (
            processByPid.has(process.ppid)
            &&
            process.ppid !== process.pid
        ) {
            links += 1;
        }

        else {
            roots += 1;
        }
    });


    graphStats.textContent =
        `${items.length} nodes / ${links} links / ${roots} roots`;
}


function updateGraphZoomLabel() {

    if (!processGraph) {
        graphZoomLabel.textContent = "100%";
        return;
    }

    graphZoomLabel.textContent =
        `${Math.round(processGraph.zoom() * 100)}%`;
}


function applyGraphSearch() {

    if (!processGraph) {
        return;
    }


    const query =
        processSearch.value
            .trim()
            .toLowerCase();

    const nodes =
        processGraph.nodes();

    const edges =
        processGraph.edges();


    nodes.removeClass(
        "search-dim search-match"
    );

    edges.removeClass(
        "search-dim search-match"
    );


    if (!query) {
        return;
    }


    const matches =
        nodes.filter((node) => {

            const name =
                String(node.data("name"))
                    .toLowerCase();

            const pid =
                String(node.data("pid"));

            const ppid =
                String(node.data("ppid"));

            return (
                name.includes(query)
                ||
                pid.includes(query)
                ||
                ppid.includes(query)
            );
        });


    nodes
        .difference(matches)
        .addClass("search-dim");

    matches.addClass(
        "search-match"
    );


    edges.forEach((edge) => {

        const sourceMatches =
            edge.source().hasClass(
                "search-match"
            );

        const targetMatches =
            edge.target().hasClass(
                "search-match"
            );

        edge.addClass(
            sourceMatches || targetMatches
                ? "search-match"
                : "search-dim"
        );
    });
}


function showGraphNodeDetails(pid) {

    const process =
        processes.find(
            (item) => item.pid === pid
        );

    if (!process) {
        hideGraphNodeDetails();
        return;
    }


    selectedGraphPid =
        pid;

    const childCount =
        processes.filter(
            (item) =>
                item.ppid === pid
                &&
                item.pid !== pid
        ).length;


    graphDetailsName.textContent =
        process.name;

    graphDetailsPid.textContent =
        process.pid;

    graphDetailsPpid.textContent =
        process.ppid;

    graphDetailsCpu.textContent =
        `${process.cpu_percent.toFixed(2)}%`;

    graphDetailsMemory.textContent =
        formatMemory(
            process.memory_bytes
        );

    graphDetailsChildren.textContent =
        childCount;


    graphNodeDetails.classList.remove(
        "hidden"
    );
}


function hideGraphNodeDetails() {

    selectedGraphPid =
        null;

    graphNodeDetails.classList.add(
        "hidden"
    );

    if (processGraph) {
        processGraph.$(":selected").unselect();
    }
}


function ensureProcessGraph() {

    if (processGraph) {

        processGraph.resize();
        updateGraphZoomLabel();
        applyGraphSearch();

        return;
    }


    if (
        typeof window.cytoscape !== "function"
    ) {

        graphContainer.textContent =
            "Cytoscape.js could not be loaded.";

        return;
    }


    const elements =
        buildGraphElements(processes);


    processGraph =
        cytoscape({
            container: graphContainer,
            elements: [
                ...elements.nodes,
                ...elements.edges,
            ],
            style: getGraphStyle(),
            layout: getGraphLayoutOptions(),
            minZoom: 0.08,
            maxZoom: 2.6,
            wheelSensitivity: 0.18,
            boxSelectionEnabled: false,
            autoungrabify: true,
            selectionType: "single",
        });


    graphTopologySignature =
        getGraphTopologySignature(
            processes
        );

    setGraphLayoutDirty(false);
    updateGraphStats(processes);
    updateGraphZoomLabel();


    processGraph.on(
        "zoom",
        updateGraphZoomLabel
    );


    processGraph.on(
        "tap",
        "node",
        (event) => {

            const pid =
                Number(
                    event.target.data("pid")
                );

            showGraphNodeDetails(
                pid
            );
        }
    );


    processGraph.on(
        "tap",
        (event) => {

            if (event.target === processGraph) {
                hideGraphNodeDetails();
            }
        }
    );


    applyGraphSearch();
}


function getNewNodePosition(nodeData) {

    if (!processGraph) {
        return { x: 0, y: 0 };
    }


    if (nodeData.parentNodeId) {

        const parent =
            processGraph.getElementById(
                nodeData.parentNodeId
            );

        if (parent.length) {

            const parentPosition =
                parent.position();

            const jitter =
                ((nodeData.pid % 7) - 3) * 32;

            return {
                x: parentPosition.x + jitter,
                y: parentPosition.y + 150,
            };
        }
    }


    const extent =
        processGraph.extent();

    return {
        x: (extent.x1 + extent.x2) / 2,
        y: (extent.y1 + extent.y2) / 2,
    };
}


function syncProcessGraph(items) {

    if (!processGraph) {
        return;
    }


    const newSignature =
        getGraphTopologySignature(items);

    const topologyChanged =
        graphTopologySignature !== null
        &&
        newSignature !== graphTopologySignature;

    const elements =
        buildGraphElements(items);

    const nextNodes =
        new Map(
            elements.nodes.map(
                (node) => [
                    node.data.id,
                    node,
                ]
            )
        );

    const nextEdges =
        new Map(
            elements.edges.map(
                (edge) => [
                    edge.data.id,
                    edge,
                ]
            )
        );


    processGraph.batch(() => {

        processGraph.nodes().forEach((node) => {

            if (!nextNodes.has(node.id())) {
                node.remove();
            }
        });


        processGraph.edges().forEach((edge) => {

            if (!nextEdges.has(edge.id())) {
                edge.remove();
            }
        });


        nextNodes.forEach((nextNode, id) => {

            let node =
                processGraph.getElementById(id);

            if (!node.length) {

                node = processGraph.add({
                    ...nextNode,
                    position:
                        getNewNodePosition(
                            nextNode.data
                        ),
                });
            }

            else {

                node.data(
                    nextNode.data
                );

                node.removeClass(
                    "cpu-idle cpu-active cpu-busy cpu-hot cpu-critical graph-root"
                );

                node.addClass(
                    nextNode.classes
                );
            }
        });


        nextEdges.forEach((nextEdge, id) => {

            if (
                !processGraph
                    .getElementById(id)
                    .length
            ) {

                processGraph.add(
                    nextEdge
                );
            }
        });
    });


    graphTopologySignature =
        newSignature;

    updateGraphStats(items);


    if (topologyChanged) {

        // Do not automatically rerun Dagre every second. That would make the
        // graph jump while the user is panning around it. New processes are
        // placed near their parent and the Relayout button is marked instead.
        setGraphLayoutDirty(true);
    }


    if (
        selectedGraphPid !== null
    ) {

        const selectedStillExists =
            items.some(
                (process) =>
                    process.pid === selectedGraphPid
            );

        if (selectedStillExists) {
            showGraphNodeDetails(
                selectedGraphPid
            );
        }

        else {
            hideGraphNodeDetails();
        }
    }


    applyGraphSearch();
}


function runGraphLayout() {

    if (!processGraph) {
        return;
    }


    processGraph.layout(
        getGraphLayoutOptions()
    ).run();

    setGraphLayoutDirty(false);

    window.setTimeout(
        updateGraphZoomLabel,
        0
    );
}


function changeGraphZoom(multiplier) {

    if (!processGraph) {
        return;
    }


    const currentZoom =
        processGraph.zoom();

    const newZoom =
        Math.max(
            processGraph.minZoom(),
            Math.min(
                processGraph.maxZoom(),
                currentZoom * multiplier
            )
        );

    const container =
        processGraph.container();


    processGraph.zoom({
        level: newZoom,
        renderedPosition: {
            x: container.clientWidth / 2,
            y: container.clientHeight / 2,
        },
    });
}


graphZoomOutButton.addEventListener(
    "click",
    () => {
        ensureProcessGraph();
        changeGraphZoom(0.82);
    }
);


graphZoomInButton.addEventListener(
    "click",
    () => {
        ensureProcessGraph();
        changeGraphZoom(1.22);
    }
);


graphFitButton.addEventListener(
    "click",
    () => {

        ensureProcessGraph();

        if (processGraph) {
            processGraph.fit(
                processGraph.elements(),
                70
            );
        }
    }
);


graphRelayoutButton.addEventListener(
    "click",
    () => {
        ensureProcessGraph();
        runGraphLayout();
    }
);


graphDetailsClose.addEventListener(
    "click",
    hideGraphNodeDetails
);


/* -------------------------------------------------------------------------- */
/* Shared rendering + view switching                                           */
/* -------------------------------------------------------------------------- */

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


    applyGraphSearch();
}


processSearch.addEventListener(
    "input",
    () => {
        render();
    }
);


function setView(viewName) {

    currentView =
        viewName;


    tableView.classList.toggle(
        "hidden",
        viewName !== "table"
    );

    treeView.classList.toggle(
        "hidden",
        viewName !== "tree"
    );

    graphView.classList.toggle(
        "hidden",
        viewName !== "graph"
    );


    tableViewButton.classList.toggle(
        "active",
        viewName === "table"
    );

    treeViewButton.classList.toggle(
        "active",
        viewName === "tree"
    );

    graphViewButton.classList.toggle(
        "active",
        viewName === "graph"
    );


    if (viewName === "graph") {

        // Cytoscape should be initialised only after its container is visible,
        // otherwise the hidden element has no useful size for fitting/layout.
        window.requestAnimationFrame(
            () => {

                ensureProcessGraph();

                if (processGraph) {
                    processGraph.resize();
                }
            }
        );
    }
}


tableViewButton.addEventListener(
    "click",
    () => {
        setView("table");
    }
);


treeViewButton.addEventListener(
    "click",
    () => {
        setView("tree");
    }
);


graphViewButton.addEventListener(
    "click",
    () => {
        setView("graph");
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


        syncProcessGraph(
            processes
        );

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
