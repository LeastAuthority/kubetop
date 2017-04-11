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
        # Services can get started before the reactor has started.  This
        # complicates things.  Get rid of all that complexity but not running
        # any interesting application code until the reactor has actually
        # started.
        self.reactor.callWhenRunning(self._run_and_stop)


    def _run_and_stop(self):
        d = maybeDeferred(self.f)
        d.addErrback(self._failed)
        d.addCallback(lambda ignored: self.main.exit())


    def _failed(self, reason):
        err(reason)
        self.main.exit(reason)


def run_once_service(main, reactor, f):
    """
    Create a service to run a function once.

    :param TwistMain main: The main entrypoint object.

    :param IReactorCore reactor: Only call ``f`` after this reactor has
        started up.

    :param f: A zero-argument callable to repeatedly call.

    :return IService: A service which will run the function and then exit
        ``main`` loop.
    """
    s = _RunOnceService()
    s.main = main
    s.reactor = reactor
    s.f = f
    return s
