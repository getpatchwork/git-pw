git-pw
======

git-pw is a tool for integrating Git with `Patchwork`_, the web-based patch
tracking system.

Installation
------------

To install ``git-pw``, use ``pip``:

.. code-block:: bash

    $ pip install git-pw

Getting Started
---------------

To begin, you'll need to configure git settings appropriately. The following
settings are required:

pw.server
  The path to the XMLRPC endpoint. This will typically look like
  'http://HOSTNAME/xmlrpc'. For example:
  'https://patchwork.ozlabs.org/xmlrpc/'
pw.projectid
  The project ID

You can set these settings as seen below. This should be done in the repo in
which you intend to apply patches:

.. code-block:: bash

    $ git config pw.server = https://patchwork.ozlabs.org/xmlrpc/
    $ git config pw.projectid = 16

Documentation
-------------

Documentation is available on `Read the Docs`_.

.. _`Patchwork`: http://jk.ozlabs.org/projects/patchwork/
.. _`Read the Docs`: https://git-pw.readthedocs.org/
