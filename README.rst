======
git-pw
======

.. image:: https://badge.fury.io/py/git-pw.svg
   :target: https://badge.fury.io/py/git-pw
   :alt: PyPi Status

.. image:: https://readthedocs.org/projects/git-pw/badge/?version=latest
   :target: http://git-pw.readthedocs.io/en/latest/?badge=latest
   :alt: Documentation Status

git-pw is a tool for integrating Git with `Patchwork`__, the web-based patch
tracking system.

__ http://jk.ozlabs.org/projects/patchwork/

Installation
------------

To install ``git-pw``, use ``pip``:

.. code-block:: bash

   $ pip install git-pw

Getting Started
---------------

To begin, you'll need to configure Git settings appropriately. The following
settings are **required**:

pw.server

  The URL for the Patchwork instance. This will typically look like. For
  example::

      https://patchwork.ozlabs.org/

pw.project

  The project name or list-id. This will appear in the URL when using the web
  UI::

      https:://patchwork.ozlabs.org/project/{project_name}/list/

The following settings are **optional**:

pw.states

  A comma-separated list of slugified patch states. This defaults to the
  default Patchwork states::

      new,under-review,accepted,rejected,rfc,not-applicable,changes-requested,
      awaiting-upstream,superseded,deferred

pw.api_server

   The URL for the Patchwork REST API root endpoint. This defaults to::


       {server}/api/v1/

   where ``{{server}}`` is the value of ``pw.server``. If defined, this should
   be an absolute URL. For example::

       https://api.example.com/v1/

You can set these settings using the ``git config`` command. This should be
done in the repo in which you intend to apply patches. For example, to
configure the Patchwork project, run:

.. code-block:: bash

   $ git config pw.server 'https://patchwork.ozlabs.org/api/v1/'
   $ git config pw.project 'patchwork'

Development
-----------

If you're interested in contributing to git-pw, first clone the repo:

.. code-block:: bash

   $ git clone https://github.com/stephenfin/git-pw
   $ cd git-pw

Create a virtualenv, then install the package in `editable`__ mode::

.. code-block:: bash

   $ virtualenv .venv
   $ source .venv/bin/activate
   $ pip install --editable .

__ https://pip.pypa.io/en/stable/reference/pip_install/#editable-installs

Documentation
-------------

Documentation is available on `Read the Docs`__

__ https://git-pw.readthedocs.org/
