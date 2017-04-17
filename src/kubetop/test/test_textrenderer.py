# Copyright Least Authority Enterprises.
# See LICENSE for details.

"""
Tests for ``_textrenderer``.
"""

from __future__ import unicode_literals

from io import StringIO as TextIO

from hypothesis import given
from hypothesis.strategies import integers, text

from twisted.trial.unittest import TestCase

from bitmath import Byte

import attr

from .._textrenderer import (
    _render_container, _render_containers, _render_pods,
    _render_pod, _render_nodes,
    _render_limited_width,
    _Memory,
    Size, Sink,
)

from txkube import v1


class RenderLimitedWidthTests(TestCase):
    @given(integers(min_value=3), text())
    def test_width(self, limit, long_text):
        rendered = _render_limited_width(long_text, limit)
        self.assertEqual(min(limit, len(long_text)), len(rendered))


    @given(integers(max_value=2), text())
    def test_too_narrow(self, limit, long_text):
        with self.assertRaises(ValueError):
            _render_limited_width(long_text, limit)


class RenderMemoryTests(TestCase):
    def test_bytes(self):
        self.assertEqual(
            "  123.00 Byte",
            _Memory(Byte(123)).render("8.2"),
        )


    def test_kibibytes(self):
        self.assertEqual(
            "   12.50 KiB",
            _Memory(Byte(1024 * 12 + 512)).render("8.2"),
        )


    def test_mebibytes(self):
        self.assertEqual(
            "  123.25 MiB",
            _Memory(Byte(2 ** 20 * 123 + 2 ** 20 / 4)).render("8.2"),
        )


    def test_gibibytes(self):
        self.assertEqual(
            "    1.05 GiB",
            _Memory(Byte(2 ** 30 + 2 ** 30 / 20)).render("8.2"),
        )


    def test_tebibytes(self):
        self.assertEqual(
            "  100.00 TiB",
            _Memory(Byte(2 ** 40 * 100)).render("8.2"),
        )


    def test_pebibytes(self):
        self.assertEqual(
            "  100.00 PiB",
            _Memory(Byte(2 ** 50 * 100)).render("8.2"),
        )


    def test_exbibytes(self):
        self.assertEqual(
            "  100.00 EiB",
            _Memory(Byte(2 ** 60 * 100)).render("8.2"),
        )



class ContainersTests(TestCase):
    def test_render_one(self):
        container = {
            "name": "foo",
            "usage": {
                "cpu": "100m",
                "memory": "200Mi",
            },
        }
        self.assertEqual(
            "                    "
            "                     (foo)"
            "        10.0"
            "  200.00 MiB"
            "       "
            "\n",
            _render_container(container),
        )


    def test_render_several(self):
        containers = [
            {
                "name": "foo",
                "usage": {
                    "cpu": "100m",
                    "memory": "200Mi",
                },
            },
            {
                "name": "bar",
                "usage": {
                    "cpu": "200m",
                    "memory": "100Mi",
                },
            },
        ]
        lines = _render_containers(containers).splitlines()
        self.assertEqual(
            ["(bar)", "(foo)"],
            list(line.split()[0].strip() for line in lines),
        )



class PodTests(TestCase):
    def test_render_several(self):
        name = "alpha"

        nodes = [
            v1.Node(
                metadata=v1.ObjectMeta(
                    name=name,
                ),
                status=v1.NodeStatus(
                    allocatable={
                        "memory": "100MiB",
                    },
                ),
            ),
        ]

        pods = [
            v1.Pod(
                metadata=v1.ObjectMeta(
                    name="foo",
                ),
            ),
            v1.Pod(
                metadata=v1.ObjectMeta(
                    name="bar",
                ),
            ),
        ]

        pod_usage = [
            {
                "metadata": {
                    "name": "foo",
                    "namespace": "default",
                    "creationTimestamp": "2017-04-07T15:21:22Z"
                },
                "timestamp": "2017-04-07T15:21:00Z",
                "window": "1m0s",
                "containers": [
                    {
                        "name": "foo-a",
                        "usage": {
                            "cpu": "100m",
                            "memory": "50Ki"
                        }
                    },
                    {
                        "name": "foo-b",
                        "usage": {
                            "cpu": "200m",
                            "memory": "150Ki"
                        }
                    }
                ]
            },
            {
                "metadata": {
                    "name": "bar",
                    "namespace": "default",
                    "creationTimestamp": "2017-04-07T15:21:22Z"
                },
                "timestamp": "2017-04-07T15:21:00Z",
                "window": "1m0s",
                "containers": [
                    {
                        "name": "bar-a",
                        "usage": {
                            "cpu": "100m",
                            "memory": "50Ki"
                        }
                    },
                    {
                        "name": "bar-b",
                        "usage": {
                            "cpu": "500m",
                            "memory": "10Ki"
                        }
                    }
                ]
            },
        ]
        lines = list(
            line
            for line
            in _render_pods(pods, pod_usage, nodes).splitlines()
            if not line.strip().startswith("(")
        )
        self.assertEqual(
            ["bar", "foo"],
            list(line.split()[0].strip() for line in lines),
        )

    def test_render_pod(self):
        pod_usage = {
            "metadata": {
                "name": "foo",
                "namespace": "default",
                "creationTimestamp": "2017-04-07T15:21:22Z"
            },
            "timestamp": "2017-04-07T15:21:00Z",
            "window": "1m0s",
            "containers": [
                {
                    "name": "foo-a",
                    "usage": {
                        "cpu": "100m",
                        "memory": "128Ki"
                    }
                },
            ]
        }
        fields = _render_pod(pod_usage, _Memory(Byte(1024 * 1024))).split()
        self.assertEqual(
            [u'foo', u'10.0', u'128.00', u'KiB', u'12.50'],
            fields,
        )


class NodeTests(TestCase):
    def test_render_several(self):
        node = {
            "kind":"Node",
            "apiVersion":"v1",
            "metadata":{
                "name":"ip-172-20-86-0.ec2.internal",
                "selfLink":"/api/v1/nodesip-172-20-86-0.ec2.internal",
                "uid":"e35442ce-0e45-11e7-acfa-1272db66581c",
                "resourceVersion":"17592039",
                "creationTimestamp":"2017-03-21T14:51:38Z",
                "labels":{
                    "beta.kubernetes.io/arch":"amd64",
                    "beta.kubernetes.io/instance-type":"m3.medium",
                    "beta.kubernetes.io/os":"linux",
                    "failure-domain.beta.kubernetes.io/region":"us-east-1",
                    "failure-domain.beta.kubernetes.io/zone":"us-east-1b",
                    "kubernetes.io/hostname":"ip-172-20-86-0.ec2.internal",
                },
                "annotations":{
                    "volumes.kubernetes.io/controller-managed-attach-detach":"true",
                },
            },
            "spec":{
                "podCIDR":"100.96.1.0/24",
                "externalID":"i-0dd2f62f32659dcb2",
                "providerID":"aws:///us-east-1b/i-0dd2f62f32659dcb2",
            },
            "status":{
                "capacity":{
                    "alpha.kubernetes.io/nvidia-gpu":"0",
                    "cpu":"1",
                    "memory":"3857324Ki",
                    "pods":"110",
                },
                "allocatable":{
                    "alpha.kubernetes.io/nvidia-gpu":"0",
                    "cpu":"1",
                    "memory":"200Ki",
                    "pods":"110",
                },
                "conditions":[
                    {
                        "type":"OutOfDisk",
                        "status":"False",
                        "lastHeartbeatTime":"2017-04-07T22:56:28Z",
                        "lastTransitionTime":"2017-03-21T14:51:38Z",
                        "reason":"KubeletHasSufficientDisk",
                        "message":"kubelet has sufficient disk space available",
                    },
                    {
                        "type":"MemoryPressure",
                        "status":"False",
                        "lastHeartbeatTime":"2017-04-07T22:56:28Z",
                        "lastTransitionTime":"2017-03-21T14:51:38Z",
                        "reason":"KubeletHasSufficientMemory",
                        "message":"kubelet has sufficient memory available",
                    },
                    {
                        "type":"DiskPressure",
                        "status":"False",
                        "lastHeartbeatTime":"2017-04-07T22:56:28Z",
                        "lastTransitionTime":"2017-03-21T14:51:38Z",
                        "reason":"KubeletHasNoDiskPressure",
                        "message":"kubelet has no disk pressure",
                    },
                    {
                        "type":"Ready",
                        "status":"True",
                        "lastHeartbeatTime":"2017-04-07T22:56:28Z",
                        "lastTransitionTime":"2017-03-21T14:52:08Z",
                        "reason":"KubeletReady",
                        "message":"kubelet is posting ready status",
                    },
                    {
                        "type":"NetworkUnavailable",
                        "status":"False",
                        "lastHeartbeatTime":"2017-03-21T14:51:43Z",
                        "lastTransitionTime":"2017-03-21T14:51:43Z",
                        "reason":"RouteCreated",
                        "message":"RouteController created a route",
                    },
                ],
                "addresses":[
                    {"type":"InternalIP","address":"172.20.86.0"},
                    {"type":"LegacyHostIP","address":"172.20.86.0"},
                    {"type":"ExternalIP","address":"54.82.248.124"},
                    {"type":"Hostname","address":"ip-172-20-86-0.ec2.internal"},
                ],
                "daemonEndpoints":{
                    "kubeletEndpoint":{"Port":10250},
                },
                "nodeInfo":{
                    "machineID":"1af1476dd91d40c0952ff71f54297123",
                    "systemUUID":"EC28F27B-6B13-F91A-79BF-DFC0EA0B0BBD",
                    "bootID":"a4d005b1-3117-4989-8a56-37d831d66d9d",
                    "kernelVersion":"4.4.26-k8s",
                    "osImage":"Debian GNU/Linux 8 (jessie)",
                    "containerRuntimeVersion":"docker://1.12.3",
                    "kubeletVersion":"v1.5.2",
                    "kubeProxyVersion":"v1.5.2",
                    "operatingSystem":"linux",
                    "architecture":"amd64",
                },
                "images":[
                    {
                        "names":[
                            "example.invalid/foo@sha256:1685a4543dc70cb29e5a9df4b47a09ed7d6e54c00fb50296afff65683c67e0ff",
                            "example.invalid/foo:1941d38",
                        ],
                        "sizeBytes":752076313,
                    },
                ],
                "volumesInUse":[
                    "kubernetes.io/aws-ebs/vol-01b01d11a6b17e2de",
                    "kubernetes.io/aws-ebs/aws://us-east-1b/vol-0b977509f3c44d901",
                    "kubernetes.io/aws-ebs/aws://us-east-1b/vol-091a8106ddd94357b",
                    "kubernetes.io/aws-ebs/vol-0e80ac26be3edd63f",
                ],
                "volumesAttached":[
                    {"name":"kubernetes.io/aws-ebs/vol-01b01d11a6b17e2de","devicePath":"/dev/xvdbc"},
                    {"name":"kubernetes.io/aws-ebs/aws://us-east-1b/vol-091a8106ddd94357b","devicePath":"/dev/xvdba"},
                    {"name":"kubernetes.io/aws-ebs/vol-0e80ac26be3edd63f","devicePath":"/dev/xvdbb"},
                    {"name":"kubernetes.io/aws-ebs/aws://us-east-1b/vol-0b977509f3c44d901","devicePath":"/dev/xvdbd"},
                ],
            },
        }

        usage = {
            "metadata": {
                "name": "ip-172-20-86-0.ec2.internal",
                "creationTimestamp": "2017-04-11T14:41:47Z"
            },
            "timestamp": "2017-04-11T14:41:00Z",
            "window": "1m0s",
            "usage": {
                "cpu": "68m",
                "memory": "100Ki"
            }
        }

        pods = [
            v1.Pod(
                status=v1.PodStatus(
                    hostIP=node["status"]["addresses"][0]["address"],
                ),
            ),
        ]

        self.assertEqual(
            "Node 0 "
            "CPU%   6.80 "
            "MEM% 50.00 ( 100 KiB/ 200 KiB)  "
            "POD%  0.91 (  1/110) "
            "Ready\n",
            _render_nodes([node], [usage], pods),
        )



@attr.s
class StubTerminal(object):
    _size = attr.ib()

    def size(self):
        return self._size



class SinkTests(TestCase):
    def test_maximum_rows(self):
        """
        Any single string passed to ``Sink.write`` gets limited to the number of
        rows available on the sink.
        """
        size = Size(rows=3, columns=80, xpixels=3, ypixels=7)
        outfile = TextIO()
        sink = Sink(
            terminal=StubTerminal(size=size), outfile=outfile,
        )
        lines = list(
            "Hello {}\n".format(n)
            for n
            in range(size.rows + 1)
        )
        sink.write("".join(lines))
        self.assertEqual(
            lines[:size.rows],
            list(
                line + "\n" for line in outfile.getvalue().splitlines()
            ),
        )
