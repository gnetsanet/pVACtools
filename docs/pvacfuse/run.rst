.. image:: ../images/pVACfuse_logo_trans-bg_sm_v4b.png
    :align: right
    :alt: pVACfuse logo

.. _pvacfuse_run:

Usage
====================================

.. warning::
   Using a local IEDB installation is strongly recommended for larger datasets
   or when the making predictions for many alleles, epitope lengths, or
   prediction algorithms. More information on how to install IEDB locally can
   be found on the :ref:`Installation <iedb_install>` page.

.. program-output:: pvacfuse run -h

.. .. argparse::
        :module: tools.pvacfuse.run
        :func: define_parser
        :prog: pvacfuse run
