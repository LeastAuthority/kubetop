import attr

from zope.interface import implementer, implementedBy

from twisted.internet.defer import (
    CancelledError, inlineCallbacks, gatherResults, succeed,
)
from twisted.internet.task import deferLater

from datetime import datetime

from ._textrenderer import _render_pod_top

from tubes.itube import IFount, IDrain, IFrame
from tubes.tube import tube, receiver, series
from tubes.undefer import deferredToResult

ITimestamp = implementedBy(datetime)

@inlineCallbacks
def _iterate(reactor, intervals, f):
    """
    Run a function repeatedly.

    :param reactor: See ``run_many_service``.

    :return Deferred: A deferred which fires when ``f`` fails or when
        ``intervals`` is exhausted.
    """
    while True:
        before = reactor.seconds()
        yield f()
        after = reactor.seconds()
        try:
            interval = next(intervals)
        except StopIteration:
            break
        delay = max(0, interval - (after - before))
        yield deferLater(reactor, delay, lambda: None)



@implementer(IFount)
@attr.s
class _ClockSignal(object):
    outputType = ITimestamp

    _reactor = attr.ib()
    _intervals = attr.ib()
    _operation = attr.ib(default=None)

    drain = attr.ib(default=None)


    def flowTo(self, drain):
        self.drain = drain
        self.resumeFlow()
        return self.drain.flowingFrom(self)


    def stopFlow(self):
        self.pauseFlow()
        self._stop(None)


    def pauseFlow(self):
        self._operation.cancel()


    def resumeFlow(self):
        self._operation = _iterate(self._reactor, self._intervals, self._signal)
        self._operation.addErrback(self._died)


    def _signal(self, *a, **kw):
        self.drain.receive(datetime.utcfromtimestamp(self._reactor.seconds()))


    def _died(self, reason=None):
        self._operation = None
        if not reason.check(CancelledError):
            self._stop(reason)


    def _stop(self, reason):
        drain = self.drain
        self.drain = None
        drain.flowStopped(reason)



def clock_signal(**kw):
    return _ClockSignal(**kw)



@tube
@attr.s
class _Retriever(object):
    source = attr.ib()

    def received(self, timestamp):
        yield gatherResults([
            succeed(timestamp),
            self.source.nodes(),
            self.source.pods(),
        ])



def retrieve(source):
    return _Retriever(source)



@receiver(inputType=ITimestamp, outputType=IFrame, name="kubetop")
def kubetop((when, node_info, pod_info)):
    yield _render_pod_top(when, (node_info, pod_info))



@attr.s
@implementer(IDrain)
class _FileLike(object):
    inputType = IFrame
    fount = None

    _output = attr.ib()

    def flowingFrom(self, fount):
        self.fount = fount
        return None


    def receive(self, item):
        self._output.write(item)
        self._output.flush()
        return 0.0


    def flowStopped(self, reason):
        print("flowStopped", reason)
        self._output.close()



def printer(outfile):
    return _FileLike(output=outfile)



def kubetop_series(source, outfile):
    return series(
        retrieve(source),
        deferredToResult(),
        kubetop,
        printer(outfile),
    )
