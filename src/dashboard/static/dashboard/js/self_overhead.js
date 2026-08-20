const selfOverheadBody =
    document.getElementById(
        "self-overhead-body"
    );

const selfOverheadToggle =
    document.getElementById(
        "self-overhead-toggle"
    );


function formatBytesPerSecond(bytes) {

    if (bytes >= 1024 ** 2) {

        return `${(
            bytes / (1024 ** 2)
        ).toFixed(2)} MB/s`;
    }


    if (bytes >= 1024) {

        return `${(
            bytes / 1024
        ).toFixed(1)} KB/s`;
    }


    return `${bytes.toFixed(0)} B/s`;
}


function formatMemory(bytes) {

    const mb =
        bytes / (1024 ** 2);


    if (mb >= 1024) {

        return `${(
            mb / 1024
        ).toFixed(2)} GB`;
    }


    return `${mb.toFixed(1)} MB`;
}


function updateSelfOverhead(
    data
) {

    const overhead =
        data.overhead;


    document
        .getElementById(
            "self-cpu"
        )
        .textContent =
        `${overhead.cpu_percent
            .toFixed(2)}%`;


    document
        .getElementById(
            "self-memory"
        )
        .textContent =
        formatMemory(
            overhead.memory_bytes
        );


    document
        .getElementById(
            "self-read"
        )
        .textContent =
        formatBytesPerSecond(
            overhead
                .read_bytes_per_second
        );


    document
        .getElementById(
            "self-write"
        )
        .textContent =
        formatBytesPerSecond(
            overhead
                .write_bytes_per_second
        );


    document
        .getElementById(
            "self-sample-time"
        )
        .textContent =
        `${overhead
            .sample_duration_ms
            .toFixed(1)} ms`;


    document
        .getElementById(
            "self-threads"
        )
        .textContent =
        overhead.thread_count ?? "—";


    document
        .getElementById(
            "self-handles"
        )
        .textContent =
        overhead.handle_count ?? "—";


    document
        .getElementById(
            "self-sockets"
        )
        .textContent =
        overhead
            .network_socket_count
        ?? "—";


    document
        .getElementById(
            "self-overhead-pid"
        )
        .textContent =
        `PID ${overhead.pid}`;


    document
        .getElementById(
            "self-overhead-updated"
        )
        .textContent =
        new Date(
            data.timestamp
        )
            .toLocaleTimeString();
}


async function fetchSelfOverhead() {

    try {

        const response =
            await fetch(
                "/api/self/"
            );


        if (!response.ok) {

            throw new Error(
                `HTTP ${response.status}`
            );
        }


        const data =
            await response.json();


        updateSelfOverhead(
            data
        );

    }

    catch (error) {

        console.error(
            "Unable to retrieve Sys Monitor overhead:",
            error
        );
    }

    finally {

        /*
         * Two seconds is enough for this widget.
         *
         * It deliberately polls more slowly than
         * the main monitoring UI so monitoring
         * the monitor does not create excessive
         * extra requests.
         */
        setTimeout(
            fetchSelfOverhead,
            2000
        );
    }
}


selfOverheadToggle
    .addEventListener(
        "click",
        () => {

            const collapsed =
                selfOverheadBody
                    .classList
                    .toggle(
                        "collapsed"
                    );


            selfOverheadToggle
                .textContent =
                collapsed
                    ? "+"
                    : "−";
        }
    );


fetchSelfOverhead();