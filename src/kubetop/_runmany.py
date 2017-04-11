# Copyright Least Authority Enterprises.
# See LICENSE for details.

"""
Integration between the per-frame kubetop rendering and the Twisted
startup/shutdown interfaces.

Theory of Operation
===================

#. Glue kubetop rendering object together with a time-based trigger (for periodic re-rendering).
#. Wrap the trigger up in an ``IService`` which can be started and stopped.
#. Deliver rendering success/failure to the main object for reporting and exit.
"""

from twisted.python.failure import Failure
from twisted.internet.defer import inlineCallbacks
from twisted.internet.task import deferLater
from twisted.application.service import Service


@inlineCallbacks
def _iterate(main, reactor, intervals, f):
    while True:
        before = reactor.seconds()
        try:
            yield f()
        except:
            main.exit(Failure())
            break
        after = reactor.seconds()
        try:
            interval = next(intervals)
        except StopIteration:
            main.exit()
            break
        delay = max(0, interval - (after - before))
        yield deferLater(reactor, delay, lambda: None)



class _RunManyService(Service):
    def startService(self):
        Service.startService(self)
        # Services can get started before the reactor has started.  This
        # complicates things.  Get rid of all that complexity but not running
        # any interesting application code until the reactor has actually
        # started.
        self.reactor.callWhenRunning(self._run_until_error)


    def _run_until_error(self):
        _iterate(self.main, self.reactor, self.intervals, self.f)



def run_many_service(main, reactor, f, intervals):
    s = _RunManyService()
    s.main = main
    s.reactor = reactor
    s.f = f
    s.intervals = intervals
    return s
