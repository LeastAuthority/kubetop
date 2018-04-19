# Copyright Least Authority Enterprises.
# See LICENSE for details.

"""
Adapter from IServiceMaker-like interface to setuptools console-entrypoint
interface.

Premise
=======

Given:

* twist is the focus of efforts to make a good client-oriented command-line
  driver for Twisted-based applications.
* kubetop is a client-y, command-line, Twisted-based application.
* Accounting for custom scripts in setup.py with setuptools is a lot harder
  than just using the ``console_script`` feature.

Therefore:

* Implement application code to the twist interface.
* Build a single utility for adapting that interface to the ``console_script``
  interface.

Theory of Operation
===================

#. Applications provide ``Options`` and ``makeService``, the main pieces of
  ``IServiceMaker``.
#. We provide an object which can be called as a ``console_script``
   entrypoint.

#. That object hooks ``Options`` and ``makeService`` up to the internals of
   ``twist`` (which are *totally* private, sigh).
"""

from sys import stdout, argv
from os.path import expanduser

import attr

from twisted.application.twist import _options
from twisted.application.twist._twist import Twist

@attr.s(frozen=True)
class MainService(object):
    tapname = "kubetop"
    description = "kubetop"
    options = attr.ib()
    makeService = attr.ib()


@attr.s
class TwistMain(object):
    options = attr.ib()
    make_service = attr.ib()

    exit_status = 0
    exit_message = None

    def exit(self, reason=None):
        if reason is not None:
            self.exit_status = 1
            self.exit_message = reason.getTraceback()
        from twisted.internet import reactor
        reactor.stop()


    def __call__(self):
        _options.getPlugins = lambda iface: [
            MainService(self.options, self._make_service),
        ]

        t = Twist()

        log_flag = u"--log-file"
        log_file = u"~/.kubetop.log"
        app_name = u"kubetop"
        if str is bytes:
            # sys.argv must be bytes Python 2
            log_flag = log_flag.encode("ascii")
            log_file = log_file.encode("ascii")
            app_name = app_name.encode("ascii")

        t.main([
            argv[0],
            log_flag, expanduser(log_file),
            app_name,
        ] + argv[1:])

        if self.exit_message:
            stdout.write(self.exit_message)
        raise SystemExit(self.exit_status)


    def _make_service(self, options):
        return self.make_service(self, options)
