# Copyright Least Authority Enterprises.
# See LICENSE for details.

"""
The command-line interface.

Theory of Operation
===================

#. Convert command line arguments to structured configuration, supplying defaults where necessary.
#. Construct the top-level kubetop service from the configuration.
#. Run the Twisted reactor.
"""

# Get the one that twisted.logger has not monkeyed with.
from sys import __stdout__ as outfile
from itertools import repeat
from os.path import expanduser

from yaml import safe_load

import attr

from twisted.python.usage import Options
from twisted.python.filepath import FilePath
from twisted.internet.defer import Deferred

from ._runonce import run_once_service
from ._twistmain import TwistMain
from ._textrenderer import Sink
from ._tubes import clock_signal, kubetop_series


CONFIG = FilePath(expanduser("~/.kube/config"))


def current_context(config_path):
    with config_path.open() as cfg:
        return safe_load(cfg)[u"current-context"]


class KubetopOptions(Options):
    optParameters = [
        ("context", None, current_context(CONFIG), "The kubectl context to use."),
        ("interval", None, 3.0, "The number of seconds between iterations.", float),
        ("iterations", None, None, "The number of iterations to perform.", int),
    ]



def fixed_intervals(interval, iterations):
    if iterations is None:
        return repeat(interval)
    return repeat(interval, iterations)



@attr.s
class _CloseNotifyingFile(object):
    _file = attr.ib()
    _notify = attr.ib()


    def write(self, data):
        return self._file.write(data)


    def fileno(self):
        return self._file.fileno()


    def close(self):
        try:
            return self._file.close()
        finally:
            self._notify()



def makeService(main, options):
    from twisted.internet import reactor

    # _topdata imports txkube and treq, both of which import
    # twisted.web.client, which imports the reactor, which installs a default.
    # That breaks TwistMain unless we delay it until makeService is called.
    from ._topdata import make_source

    def run_kubetop():
        done = Deferred()
        fount = clock_signal(
            reactor=reactor,
            intervals=fixed_intervals(options["interval"], options["iterations"]),
        )
        series = kubetop_series(
            make_source(reactor, CONFIG, options["context"]),
            _CloseNotifyingFile(Sink.from_file(outfile), lambda: done.callback(None)),
        )
        fount.flowTo(series)
        return done

    return run_once_service(main, reactor, run_kubetop)


main = TwistMain(KubetopOptions, makeService)
