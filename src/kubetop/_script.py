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

from yaml import safe_load

from os.path import expanduser

from twisted.python.usage import Options
from twisted.python.filepath import FilePath

from ._twistmain import TwistMain
from ._runonce import run_once_service
from ._textrenderer import kubetop

CONFIG = FilePath(expanduser("~/.kube/config"))


def current_context(config_path):
    with config_path.open() as cfg:
        return safe_load(cfg)[u"current-context"]


class KubetopOptions(Options):
    optParameters = [
        ("context", None, current_context(CONFIG), "The kubectl context to use."),
    ]



def makeService(main, options):
    from twisted.internet import reactor

    # _topdata imports txkube and treq, both of which import
    # twisted.web.client, which imports the reactor, which installs a default.
    # That breaks TwistMain unless we delay it until makeService is called.
    from ._topdata import make_source

    import sys

    s = make_source(reactor, CONFIG, options["context"])
    return run_once_service(main, reactor, lambda: kubetop(s, sys.__stdout__))


main = TwistMain(KubetopOptions, makeService)
