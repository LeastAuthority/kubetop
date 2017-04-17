
import attr

from zope.interface import Attribute, Interface, implementer

from twisted.internet.task import LoopingCall, react
from twisted.internet.defer import gatherResults

from tubes.itube import IFount, IFrame
from tubes.tube import tube, receiver, series
from tubes.undefer import deferredToResult

from datetime import datetime, timedelta

from ._script import CONFIG, current_context
from ._topdata import make_source
from ._textrenderer import _render_pod_top

class ITimestamp(Interface):
    when = Attribute("datetime.datetime instance")



@implementer(IFount)
@attr.s
class _ClockSignal(object):
    outputType = ITimestamp

    reactor = attr.ib()
    interval = attr.ib()

    loop = attr.ib(default=None)
    drain = attr.ib(default=None)

    def flowTo(self, drain):
        self.drain = drain
        self.loop = LoopingCall(self._signal)
        self.loop.reactor = self.reactor
        d = self.loop.start(self.interval.total_seconds(), now=False)
        d.addBoth(self._died)
        return self.drain.flowingFrom(self)


    def stopFlow(self):
        self.loop.stop()
        self._stop(None)


    def _signal(self):
        self.drain.receive(datetime.utcfromtimestamp(self.reactor.seconds()))


    def _died(self, reason=None):
        self.loop = None
        self._stop(reason)


    def _stop(self, reason):
        drain = self.drain
        self.drain = None
        drain.flowStopped(reason)



def clock_signal(**kw):
    return _ClockSignal(**kw)



@receiver(inputType=object)
def printer(item):
    print(item)



@receiver(inputType=ITimestamp, outputType=IFrame, name="kubetop")
def kubetop((when, node_info, pod_info)):
    yield _render_pod_top(when, (node_info, pod_info))



@tube
@attr.s
class _Retriever(object):
    source = attr.ib()

    def started(self):
        pass

    def stopped(self, reason):
        pass

    def received(self, item):
        return gatherResults([
            self.source.nodes(),
            self.source.pods(),
        ])



def retrieve(source):
    return _Retriever(source)



def main(reactor):
    series(
        clock_signal(reactor=reactor, interval=timedelta(seconds=3)),
        retrieve(make_source(reactor, CONFIG, current_context(CONFIG))),
        deferredToResult(),
        kubetop,
        printer,
    )

    reactor.run()

react(main, [])
