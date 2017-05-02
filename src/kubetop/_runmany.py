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


from ._runonce import run_once_service

def run_many_service(main, reactor, f, intervals):
    """
    Create a service to run a function repeatedly.

    :param TwistMain main: The main entrypoint object.

    :param reactor: The IReactorTime & IReactorCore provider to use for
        delaying subsequent iterations.

    :param intervals: An iterable of numbers giving the delay between
        subsequent invocations of the function.

    :param f: A zero-argument callable to repeatedly call.

    :return IService: A service which will run the function until the interval
        iterator is exhausted.
    """
    def run_many():
        return _iterate(reactor, intervals, f)

    return run_once_service(main, reactor, run_many)
