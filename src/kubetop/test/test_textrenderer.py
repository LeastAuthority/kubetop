# Copyright Least Authority Enterprises.
# See LICENSE for details.

"""
Tests for ``_textrenderer``.
"""

from __future__ import unicode_literals

from twisted.trial.unittest import TestCase

from bitmath import Byte

from .._textrenderer import (
    _render_memory, _render_container, _render_containers, _render_pods,
)


class RenderMemoryTests(TestCase):
    def test_bytes(self):
        self.assertEqual(
            "  123.00 Byte",
            _render_memory(Byte(123)),
        )


    def test_kibibytes(self):
        self.assertEqual(
            "   12.50 KiB",
            _render_memory(Byte(1024 * 12 + 512)),
        )


    def test_mebibytes(self):
        self.assertEqual(
            "  123.25 MiB",
            _render_memory(Byte(2 ** 20 * 123 + 2 ** 20 / 4)),
        )


    def test_gibibytes(self):
        self.assertEqual(
            "    1.05 GiB",
            _render_memory(Byte(2 ** 30 + 2 ** 30 / 20)),
        )


    def test_tebibytes(self):
        self.assertEqual(
            "  100.00 TiB",
            _render_memory(Byte(2 ** 40 * 100)),
        )


    def test_pebibytes(self):
        self.assertEqual(
            "  100.00 PiB",
            _render_memory(Byte(2 ** 50 * 100)),
        )


    def test_exbibytes(self):
        self.assertEqual(
            "  100.00 EiB",
            _render_memory(Byte(2 ** 60 * 100)),
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
            "        100m"
            "  200.00 MiB"
            "          "
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
        pods = [
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
            in _render_pods(pods).splitlines()
            if not line.strip().startswith("(")
        )
        self.assertEqual(
            ["bar", "foo"],
            list(line.split()[0].strip() for line in lines),
        )
