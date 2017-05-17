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

   kubetop - 13:02:57
   Node 0 CPU%   9.80 MEM% 57.97 (   2 GiB/   4 GiB)  POD%  7.27 (  8/110) Ready
   Node 1 CPU%  21.20 MEM% 59.36 (   2 GiB/   4 GiB)  POD%  3.64 (  4/110) Ready
   Node 2 CPU%  99.90 MEM% 58.11 (   2 GiB/   4 GiB)  POD%  7.27 (  8/110) Ready
   Pods:       20 total        0 running        0 terminating        0 pending
                    POD               (CONTAINER)        %CPU         MEM   %MEM
   s4-infrastructure-3073578190-2k2vw                    75.5  782.05 MiB  20.76
                         (subscription-converger)        72.7  459.11 MiB
                                    (grid-router)         2.7   98.07 MiB
                                            (web)         0.1   67.61 MiB
                           (subscription-manager)         0.0   91.62 MiB
                          (foolscap-log-gatherer)         0.0   21.98 MiB
                                          (flapp)         0.0   21.46 MiB
                                 (wormhole-relay)         0.0   22.19 MiB

Installing
----------

Pip / Pipsi
~~~~~~~~~~~

To install the latest version of kubetop using `pip`_ or `pipsi`_::

  $ pipsi install kubetop

Docker
~~~~~~

A Docker image containing a kubetop installation is also available.
You can run it like this::

  $ docker run -it --rm --volume ~/.kube/:/root/.kube/:ro exarkun/kubetop

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
The fourth segment of a kubetop version is a bugfix release counter.
It is present if a new release is made that diffs from a previous release only by including one or more bug fixes.
For each bug fix release, the fourth segment is incremented.

License
-------

txkube is open source software released under the MIT License.
See the LICENSE file for more details.


.. _Kubernetes: https://kubernetes.io/
.. _CalVer: http://calver.org/
.. _pip: https://pip.pypa.io/en/stable/
.. _pipsi: https://pypi.python.org/pypi/pipsi
