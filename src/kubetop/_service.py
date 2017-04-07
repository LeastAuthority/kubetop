# Copyright Least Authority Enterprises.
# See LICENSE for details.

"""
Integration between the per-frame kubetop rendering and the Twisted
startup/shutdown interfaces.

Theory of Operation
===================

#. Convert operational configuration to a kubetop rendering object.
#. Glue kubetop rendering object together with a time-based trigger (for periodic re-rendering).
#. Wrap the trigger up in an ``IService`` which can be started and stopped.
"""
