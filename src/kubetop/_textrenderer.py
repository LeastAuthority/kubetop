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

from struct import pack, unpack
from termios import TIOCGWINSZ
from fcntl import ioctl

from twisted.internet.defer import gatherResults
from twisted.python.compat import unicode

from datetime import datetime

from bitmath import Byte

import attr
from attr import validators

COLUMNS = [
    (20, "POD"),
    (26, "(CONTAINER)"),
    (12, "%CPU"),
    (12, "MEM"),
    (7, "%MEM")
]


def kubetop(reactor, datasource, datasink):
    return gatherResults([
        datasource.nodes(), datasource.pods(),
    ]).addCallback(_render_kubetop, datasink, reactor)



@attr.s
class Size(object):
    rows = attr.ib()
    columns = attr.ib()
    xpixels = attr.ib()
    ypixels = attr.ib()



def terminal_size(terminal_fd):
    s = pack('HHHH', 0, 0, 0, 0)
    t = ioctl(terminal_fd, TIOCGWINSZ, s)
    return Size(*unpack('HHHH', t))



@attr.s
class Terminal(object):
    fd = attr.ib()

    def size(self):
        return terminal_size(self.fd)



@attr.s
class Sink(object):
    terminal = attr.ib()
    outfile = attr.ib()


    @classmethod
    def from_file(cls, outfile):
        return cls(Terminal(outfile.fileno()), outfile)


    def write(self, text):
        size = self.terminal.size()
        num_lines = size.rows
        truncated = "\n".join(text.splitlines()[:num_lines])
        self.outfile.write(truncated)
        self.outfile.flush()



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


def _render_pod_top(reactor, data):
    (node_info, pod_info) = data
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
        _render_pods(pods, pod_usage, nodes),
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
            if _pod_on_node(pod, node)
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
        "MEM% {mem} ({mem_used}/{mem_max})  "
        "POD% {pod:>5.2f} ({pod_count:3}/{pod_max:3}) "
        "{condition}"
    ).format(
        cpu=cpu_used / cpu_max * 100,
        mem=mem_max.render_percentage(mem_used),
        mem_used=mem_used.render("4.0"),
        mem_max=mem_max.render("4.0"),
        pod=pod_count / pod_max * 100,
        pod_count=pod_count,
        pod_max=pod_max,
        condition=condition,
    )



def _pod_on_node(pod, node):
    return pod.status is not None and pod.status.hostIP in (
        addr["address"] for addr in node["status"]["addresses"]
    )



class _UnknownMemory(object):
    def render(self):
        return "???"


    def render_percentage(self, portion):
        return ""



@attr.s(frozen=True)
class _Memory(object):
    amount = attr.ib(validator=validators.instance_of(Byte))

    def render(self, fmt):
        amount = self.amount.best_prefix()
        return ("{:" + fmt + "f} {}").format(float(amount), amount.unit_singular)


    def render_percentage(self, portion):
        return "{:>5.2f}".format(portion.amount / self.amount * 100)



@attr.s(frozen=True)
class _CPU(object):
    # in millicpus
    amount = attr.ib(validator=validators.instance_of(int))

    def render_percentage(self, portion):
        return "{:>5.1f}".format(portion.amount / self.amount * 100)


def _node_allocable_memory(pod, nodes):
    for node in nodes:
        if _pod_on_node(pod, node):
            return parse_memory(node["status"]["allocatable"]["memory"])
    return _UnknownMemory()


def _render_pods(pods, pod_usage, nodes):
    pod_by_name = {
        pod.metadata.name: pod
        for pod
        in pods
    }
    pod_data = (
        (
            _render_pod(
                usage,
                _node_allocable_memory(
                    pod_by_name[usage["metadata"]["name"]],
                    nodes,
                ),
            ),
            _render_containers(usage["containers"]),
        )
        for usage
        in sorted(pod_usage, key=_pod_stats, reverse=True)
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
            lambda s: parse_memory(s).amount, (
                container["usage"]["memory"]
                for container
                in pod["containers"]
            ),
        ), Byte(0),
    )
    return (_CPU(cpu), _Memory(mem))


def _render_limited_width(s, w):
    if w < 3:
        raise ValueError("Minimum rendering width is 3")
    if len(s) <= w:
        return s
    return (
        s[:int(round(w / 2 - 1))] +
        "\N{HORIZONTAL ELLIPSIS}" +
        s[-int(w / 2):]
    )


def _render_pod(pod, node_allocable_memory):
    cpu, mem = _pod_stats(pod)
    mem_percent = node_allocable_memory.render_percentage(mem)
    return _render_row(
        # Limit rendered name to combined width of the pod and container
        # columns.
        _render_limited_width(pod["metadata"]["name"], 46),
        "",
        _CPU(1000).render_percentage(cpu),
        mem.render("8.2"),
        mem_percent,
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
        _render_limited_width("(" + container["name"] + ")", 46),
        _CPU(1000).render_percentage(_CPU(parse_cpu(container["usage"]["cpu"]))),
        parse_memory(container["usage"]["memory"]).render("8.2"),
        "",
    )


def partition(seq, pred):
    return (
        u"".join(x for x in seq if pred(x)),
        u"".join(x for x in seq if not pred(x)),
    )


def parse_cpu(s):
    return parse_k8s_resource(s, default_scale=1000)


def parse_memory(s):
    return _Memory(Byte(parse_k8s_resource(s, default_scale=1)))


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
