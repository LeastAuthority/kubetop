# Copyright Least Authority Enterprises.
# See LICENSE for details.

"""
View implementation.

Theory of Operation
===================

#. Combine a data source with a text-emitting renderer function and a text
   output-capable target (e.g. a file descriptor).
"""

from __future__ import unicode_literals

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
    return datasource.pods().addCallback(_render_kubetop, datasink, reactor)


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
    return "".join((
        _clear(),
        _render_clockline(reactor),
        _render_header(data),
        _render_pods(data["items"]),
    ))


def _render_header(data):
    return _render_row(*(
        label
        for (width, label)
        in COLUMNS
    ))


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


def _render_memory(amount):
    amount = amount.best_prefix()
    return "{:8.2f} {}".format(float(amount), amount.unit_singular)


def partition(seq, pred):
    return (
        filter(pred, seq),
        filter(lambda x: not pred(x), seq),
    )


def parse_cpu(s):
    return parse_k8s_resource(s)


def parse_memory(s):
    return Byte(parse_k8s_resource(s))


def parse_k8s_resource(s):
    amount, suffix = partition(s, unicode.isdigit)
    scale = suffix_scale(suffix)
    return int(amount) * scale


def suffix_scale(suffix):
    return {
        "": 1,
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
