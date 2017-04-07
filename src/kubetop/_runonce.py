# Copyright Least Authority Enterprises.
# See LICENSE for details.

"""
Glue a one-shot function to Twisted's application system.
"""

from twisted.python.log import err
from twisted.application.service import Service
from twisted.internet.defer import maybeDeferred


class _RunOnceService(Service):
    def startService(self):
        Service.startService(self)
        self.reactor.callWhenRunning(self._run_and_stop)


    def _run_and_stop(self):
        d = maybeDeferred(self.f)
        d.addErrback(self._failed)
        d.addCallback(lambda ignored: self.reactor.stop())


    def _failed(self, reason):
        err(reason)
        self.main.set_exit_reason(reason)


def run_once_service(main, reactor, f):
    s = _RunOnceService()
    s.main = main
    s.reactor = reactor
    s.f = f
    return s
