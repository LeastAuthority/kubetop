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
