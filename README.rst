kubetop
=======

.. image:: http://img.shields.io/pypi/v/kubetop.svg
   :target: https://pypi.python.org/pypi/kubetop
   :alt: PyPI Package

.. image:: https://travis-ci.org/LeastAuthority/kubetop.svg
   :target: https://travis-ci.org/LeastAuthority/kubetop
   :alt: CI status

.. image:: https://codecov.io/github/LeastAuthority/kubetop/coverage.svg
   :target: https://codecov.io/github/LeastAuthority/kubetop
   :alt: Coverage

What is this?
-------------

kubetop is a top(1)-like tool for `Kubernetes`_.

Usage Sample
------------

.. code-block:: sh

   $ kubetop

Output Sample
-------------

.. code-block::

   kubetop - 13:04:31
   Node 0 CPU%  10.20 MEM% 55.63 (   2 GiB/   4 GiB)  POD%  7.27 (  8/110) Ready
   Node 1 CPU%   6.70 MEM% 26.84 (1011 MiB/   4 GiB)  POD%  7.27 (  8/110) Ready
   Node 2 CPU%  11.90 MEM% 36.53 (   1 GiB/   4 GiB)  POD%  0.91 (  1/110) Ready
   Pods:     123 total      7 Running     3 Terminating     1 Pending
                    POD               (CONTAINER)        %CPU         MEM   %MEM
   s4-infrastructure-216976705-nkn7r                        1  127.43 MiB   3.10
                                            (web)          1m   45.88 MiB
                                          (flapp)           0   35.28 MiB
                                 (wormhole-relay)           0   24.80 MiB
                          (foolscap-log-gatherer)           0   21.47 MiB
   image-building-3987116516-g6s93                          0   13.34 MiB   0.31
                                 (image-building)           0   13.34 MiB

Installing
----------

To install the latest version of kubetop using pip::

  $ pip install kubetop

Testing
-------

kubetop uses pyunit-style tests.
After installing the development dependencies, you can run the test suite with trial::

  $ pip install kubetop[dev]
  $ trial kubetop

Version
-------

kubetop uses the `CalVer`_ versioning convention.
The first three segments of a kubetop version tell you the year (two digit), month, and day that version was released.


License
-------

txkube is open source software released under the MIT License.
See the LICENSE file for more details.


.. _Kubernetes: https://kubernetes.io/
.. _CalVer: http://calver.org/
