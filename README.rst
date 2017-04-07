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

   kubetop - 11:36:03       1m0s window
   Pods:     123 total      7 Running     3 Terminating     1 Pending
   %Node0:   CPU 35%        MEM 20% (12/48GiB)
   %Node1:   CPU 30%        MEM 25% (25/100GiB)
   %Node2:   CPU 25%        MEM 50% (15/30GiB)

   POD     (CONTAINER)                          %CPU      MEM     %MEM
   infrastructure-216976705-nkn7r                 13   123MiB       11
                 (web)                             6    80MiB        7
		 (db)                              7    43MiB        4
   billing-230948372-nnmxwui                       3   123MiB       11
                 (api)                             1    80MiB        7
		 (db)                              2    43MiB        4

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

License
-------

txkube is open source software released under the MIT License.
See the LICENSE file for more details.


.. _Kubernetes: https://kubernetes.io/
