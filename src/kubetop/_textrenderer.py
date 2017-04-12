# Copyright Least Authority Enterprises.
# See LICENSE for details.

"""
View implementation.

Theory of Operation
===================

#. Combine a data source with a text-emitting renderer function and a text
   output-capable target (e.g. a file descriptor).
"""

from __future__ import unicode_literals, division

from twisted.internet.defer import gatherResults

from datetime import datetime

from bitmath import Byte

COLUMNS = [
    (20, "POD"),
    (26, "(CONTAINER)"),
    (12, "%CPU"),
    (12, "MEM"),
    (10, "%MEM")
]


def kubetop(reactor, datasource, datasink):
    return gatherResults([
        datasource.nodes(), datasource.pods(),
    ]).addCallback(_render_kubetop, datasink, reactor)


def _render_kubetop(data, sink, reactor):
    sink.write(_render_pod_top(reactor, data))


def _render_row(*values):
    fields = []
    debt = 0
    for value, (width, label) in zip(values, COLUMNS):
        field = "{}".format(value).rjust(width - max(0, debt))
        debt = len(field) - width
        fields.append(field)
    return "".join(fields) + "\n"


def _clear():
    return "\x1b[2J\x1b[1;1H"


def _render_clockline(reactor):
    return "kubetop - {}\n".format(
        datetime.fromtimestamp(reactor.seconds()).strftime("%H:%M:%S")
    )


def _render_pod_top(reactor, (node_info, pod_info)):
    nodes = node_info["info"]["items"]
    node_usage = node_info["usage"]["items"]

    pods = pod_info["info"].items
    pod_usage = pod_info["usage"]["items"]

    return "".join((
        _clear(),
        _render_clockline(reactor),
        _render_nodes(nodes, node_usage, pods),
        _render_pod_phase_counts(pods),
        _render_header(nodes, pods),
        _render_pods(pod_usage),
    ))


def _render_pod_phase_counts(pods):
    phases = {}
    for pod in pods:
        phases[pod.status.phase] = phases.get(pod.status.phase, 0) + 1

    return (
        "Pods: "
        "{total:>8} total "
        "{running:>8} running "
        "{terminating:>8} terminating "
        "{pending:>8} pending\n"
    ).format(
        total=len(pods),
        running=phases.get("running", 0),
        terminating=phases.get("terminating", 0),
        pending=phases.get("pending", 0),
    )


def _render_header(nodes, pods):
    return _render_row(*(
        label
        for (width, label)
        in COLUMNS
    ))


def _render_nodes(nodes, node_usage, pods):
    usage_by_name = {
        usage["metadata"]["name"]: usage
        for usage
        in node_usage
    }
    def pods_for_node(node):
        return list(
            pod
            for pod
            in pods
            if pod.status is not None and pod.status.hostIP in (
                addr["address"] for addr in node["status"]["addresses"]
            )
        )

    return "".join(
        "Node {} {}\n".format(
            i,
            _render_node(
                node,
                usage_by_name[node["metadata"]["name"]],
                pods_for_node(node),
            ),
        )
        for i, node
        in enumerate(nodes)
    )


def _render_node(node, usage, pods):
    # From v1.NodeStatus model documentation:
    #
    #     Allocatable represents the resources of a node that are available
    #     for scheduling. Defaults to Capacity.
    allocatable = node["status"]["allocatable"]

    cpu_max = parse_cpu(allocatable["cpu"])
    cpu_used = parse_cpu(usage["usage"]["cpu"])

    mem_max = parse_memory(allocatable["memory"])
    mem_used = parse_memory(usage["usage"]["memory"])

    pod_count = len(pods)
    pod_max = int(allocatable["pods"])

    if any(
            condition["type"] == "Ready" and condition["status"] == "True"
            for condition
            in node["status"]["conditions"]
    ):
        condition = "Ready"
    else:
        condition = "NotReady"

    return (
        "CPU% {cpu:>6.2f} "
        "MEM% {mem:>5.2f} ({mem_used}/{mem_max})  "
        "POD% {pod:>5.2f} ({pod_count:3}/{pod_max:3}) "
        "{condition}"
    ).format(
        cpu=cpu_used / cpu_max * 100,
        mem=mem_used / mem_max * 100,
        mem_used=_render_memory(mem_used, "4.0"),
        mem_max=_render_memory(mem_max, "4.0"),
        pod=pod_count / pod_max * 100,
        pod_count=pod_count,
        pod_max=pod_max,
        condition=condition,
    )


def _render_pods(pods):
    pod_data = (
        (_render_pod(pod), _render_containers(pod["containers"]))
        for pod
        in sorted(pods, key=_pod_stats, reverse=True)
    )
    return "".join(
        rendered_pod + rendered_containers
        for (rendered_pod, rendered_containers)
        in pod_data
    )


def _pod_stats(pod):
    cpu = sum(
        map(
            parse_cpu, (
                container["usage"]["cpu"]
                for container
                in pod["containers"]
            ),
        ), 0,
    )
    mem = sum(
        map(
            parse_memory, (
                container["usage"]["memory"]
                for container
                in pod["containers"]
            ),
        ), Byte(0),
    )
    return (cpu, mem)


def _render_pod(pod):
    cpu, mem = _pod_stats(pod)
    return _render_row(
        pod["metadata"]["name"],
        "",
        cpu,
        _render_memory(mem),
        mem / Byte(1024),
    )


def _render_containers(containers):
    return "".join((
        _render_container(container)
        for container
        in sorted(containers, key=lambda c: -parse_cpu(c["usage"]["cpu"]))
    ))


def _render_container(container):
    return _render_row(
        "",
        "(" + container["name"] + ")",
        container["usage"]["cpu"],
        _render_memory(parse_memory(container["usage"]["memory"])),
        "",
    )


def _render_memory(amount, fmt="8.2"):
    amount = amount.best_prefix()
    return ("{:" + fmt + "f} {}").format(float(amount), amount.unit_singular)


def partition(seq, pred):
    return (
        filter(pred, seq),
        filter(lambda x: not pred(x), seq),
    )


def parse_cpu(s):
    return parse_k8s_resource(s, default_scale=1000)


def parse_memory(s):
    return Byte(parse_k8s_resource(s, default_scale=1))


def parse_k8s_resource(s, default_scale):
    amount, suffix = partition(s, unicode.isdigit)
    try:
        scale = suffix_scale(suffix)
    except KeyError:
        scale = default_scale
    return int(amount) * scale


def suffix_scale(suffix):
    return {
        "m": 1,
        "K": 2 ** 10,
        "Ki": 2 ** 10,
        "M": 2 ** 20,
        "Mi": 2 ** 20,
        "G": 2 ** 30,
        "Gi": 2 ** 30,
        "T": 2 ** 40,
        "Ti": 2 ** 40,
        "P": 2 ** 50,
        "Pi": 2 ** 50,
        "E": 2 ** 60,
        "Ei": 2 ** 60,
    }[suffix]
