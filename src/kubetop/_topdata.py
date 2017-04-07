# Copyright Least Authority Enterprises.
# See LICENSE for details.

"""
Retrieve resource usage data by Kubernetes Objects.

Theory of Operation
===================

#. Combine Kubernetes API server location with a resource collection object.
#. Collect resource usage information via the Heapster service on the
   Kubernetes API server.
"""

from __future__ import unicode_literals

import attr
import attr.validators

from treq import json_content
from treq.client import HTTPClient

from txkube import IKubernetes, network_kubernetes_from_context


def source(reactor, config_path, context_name):
    """
    Get a source of Kubernetes resource usage data.
    """
    kubernetes = network_kubernetes_from_context(reactor, context_name, config_path)
    return _Source(kubernetes=kubernetes)


@attr.s(frozen=True)
class _Source(object):
    kubernetes = attr.ib(validator=attr.validators.provides(IKubernetes))


    def pods(self):
        return self._pods_usage_from_client(self._client(), self.kubernetes.base_url)


    def _client(self):
        k8s_client = self.kubernetes.client()
        agent = k8s_client.agent
        return HTTPClient(agent=agent)


    def _pods_usage_from_client(self, client, base_url):
        d = client.get(base_url.asText() + self.pod_location())
        d.addCallback(json_content)
        return d


    def pod_location(self):
        return (
            u"/api/v1/namespaces/kube-system/services/http:heapster:"
            u"/proxy/apis/metrics/v1alpha1/namespaces/{namespace}/pods?"
            u"labelSelector="
        ).format(namespace=u"default")
