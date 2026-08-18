
import socket
import psutil
# Again, these are cumulative counters, not speeds.
# psutil exposes sent/received bytes and packet counters,
# and can also report them per network interface later using pernic=True

def get_network_counters():
    counters = (
        psutil.net_io_counters()
    )

    return {
        "bytes_sent":
            counters.bytes_sent,

        "bytes_received":
            counters.bytes_recv,
    }


def get_interface_counters():
    """
    Return cumulative counters for every
    network interface.

    The sampler will turn these cumulative
    values into bytes/second rates.
    """

    counters = (
        psutil.net_io_counters(
            pernic=True
        )
    )


    return {
        name: {
            "bytes_sent":
                value.bytes_sent,

            "bytes_received":
                value.bytes_recv,
        }

        for name, value
        in counters.items()
    }


def get_network_interfaces():
    addresses = (
        psutil.net_if_addrs()
    )

    statistics = (
        psutil.net_if_stats()
    )


    interfaces = []


    for name in sorted(
        set(addresses)
        |
        set(statistics)
    ):

        stat = statistics.get(name)


        interface_addresses = []


        for address in addresses.get(
            name,
            []
        ):

            if (
                address.family
                == socket.AF_INET
            ):
                family = "IPv4"

            elif (
                address.family
                == socket.AF_INET6
            ):
                family = "IPv6"

            elif (
                address.family
                == psutil.AF_LINK
            ):
                family = "MAC"

            else:
                continue


            interface_addresses.append({
                "family":
                    family,

                "address":
                    address.address,

                "netmask":
                    address.netmask,

                "broadcast":
                    address.broadcast,
            })


        interfaces.append({
            "name":
                name,

            "is_up":
                stat.isup
                if stat
                else False,

            "speed_mbps":
                stat.speed
                if stat
                else 0,

            "mtu":
                stat.mtu
                if stat
                else None,

            "duplex":
                (
                    getattr(
                        stat.duplex,
                        "name",
                        str(stat.duplex),
                    )
                    if stat
                    else None
                ),

            "addresses":
                interface_addresses,
        })


    return interfaces


def _serialize_address(address):
    if not address:
        return None

    return {
        "ip":
            address.ip,

        "port":
            address.port,
    }


def get_network_connections(
    process_name_by_pid=None,
):
    """
    Return current IPv4 / IPv6 TCP and UDP
    sockets.

    process_name_by_pid lets us reuse the
    process snapshot already collected by
    SystemSampler.
    """

    if process_name_by_pid is None:
        process_name_by_pid = {}


    connections = []


    for connection in (
        psutil.net_connections(
            kind="inet"
        )
    ):

        if (
            connection.type
            == socket.SOCK_STREAM
        ):
            protocol = "TCP"

        elif (
            connection.type
            == socket.SOCK_DGRAM
        ):
            protocol = "UDP"

        else:
            protocol = "OTHER"


        if (
            connection.family
            == socket.AF_INET
        ):
            family = "IPv4"

        elif (
            connection.family
            == socket.AF_INET6
        ):
            family = "IPv6"

        else:
            family = "OTHER"


        status = getattr(
            connection.status,
            "value",
            str(connection.status),
        )


        pid = connection.pid


        connections.append({
            "pid":
                pid,

            "process_name":
                (
                    process_name_by_pid
                    .get(
                        pid,
                        "<unknown>",
                    )
                    if pid is not None
                    else "<system>"
                ),

            "protocol":
                protocol,

            "family":
                family,

            "local":
                _serialize_address(
                    connection.laddr
                ),

            "remote":
                _serialize_address(
                    connection.raddr
                ),

            "status":
                status,
        })


    return connections