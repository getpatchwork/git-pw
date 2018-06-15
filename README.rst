======
git-pw
======

.. NOTE: If editing this, be sure to update the line numbers in
     'doc/introduction'

.. image:: https://badge.fury.io/py/git-pw.svg
   :target: https://badge.fury.io/py/git-pw
   :alt: PyPi Status

.. image:: https://readthedocs.org/projects/git-pw/badge/?version=latest
   :target: http://git-pw.readthedocs.io/en/latest/?badge=latest
   :alt: Documentation Status

.. image:: https://travis-ci.org/getpatchwork/git-pw.svg?branch=master
   :target: https://travis-ci.org/getpatchwork/git-pw
   :alt: Build Status

*git-pw* is a tool for integrating Git with `Patchwork`__, the web-based patch
tracking system.

.. important::

   `git-pw` only supports Patchwork 2.0+ and REST API support must be enabled
   on the server end. You can check for support by browsing ``/about`` for your
   given instance. If this page returns a 404, you are using Patchwork < 2.0.

   The `pwclient`__ utility can be used to interact with older Patchwork
   instances or instances with the REST API disabled.

__ http://jk.ozlabs.org/projects/patchwork/
__ https://patchwork.ozlabs.org/help/pwclient/

Installation
------------

The easiest way to install *git-pw* and its dependencies is using ``pip``. To
do so, run:

.. code-block:: bash

   $ pip install git-pw

You can also install *git-pw* manually. First, install the required
dependencies.  On Fedora, run:

.. code-block:: bash

   $ sudo dnf install python-requests python-click python-pbr python-arrow \
     python-tabulate

On Ubuntu, run:

.. code-block:: bash

   $ sudo apt-get install python-requests python-click python-pbr python-arrow \
     python-tabulate

Once dependencies are installed, clone this repo and run ``setup.py``:

.. code-block:: bash

   $ git clone https://github.com/getpatchwork/git-pw
   $ cd git-pw
   $ pip install --user .  # or 'sudo python setup.py'

Getting Started
---------------

To begin, you'll need to configure Git settings appropriately. The following
settings are **required**:

``pw.server``
  The URL for the Patchwork instance's API. This should include the API
  version::

      https://patchwork.ozlabs.org/api/1.1

  You can discover the API version supported by your instance by comparing the
  server version, found at ``/about``, with the API versions provided in the
  `documentation`__.

  __ https://patchwork.readthedocs.io/en/stable-2.1/api/rest/#rest-api-versions

``pw.project``
  The project name or list-id. This will appear in the URL when using the web
  UI::

      https://patchwork.ozlabs.org/project/{project_name}/list/

You also require authentication - you can use either API tokens or a
username/password combination:

``pw.token``
  The API token for you Patchwork account.

``pw.username``
  The username for your Patchwork account.

``pw.password``
  The password for your Patchwork account.

You can set these settings using the ``git config`` command. This should be
done in the repo in which you intend to apply patches. For example, to
configure the Patchwork project, run:

.. code-block:: bash

   $ git config pw.server 'https://patchwork.ozlabs.org/api/1.1/'
   $ git config pw.project 'patchwork'

Development
-----------

If you're interested in contributing to *git-pw*, first clone the repo:

.. code-block:: bash

   $ git clone https://github.com/getpatchwork/git-pw
   $ cd git-pw

Create a *virtualenv*, then install the package in `editable`__ mode:

.. code-block:: bash

   $ virtualenv .venv
   $ source .venv/bin/activate
   $ pip install --editable .

__ https://pip.pypa.io/en/stable/reference/pip_install/#editable-installs

Documentation
-------------

Documentation is available on `Read the Docs`__

__ https://git-pw.readthedocs.org/
