==============
RPM spec files
==============

Spec files for building an RPM for ``git-pw``. These should follow the Fedora
Python Packaging Guidelines, found `here`__.

These are published on `copr`__. You can build the RPM yourself using the
following commands:

.. code-block:: bash

   $ copr build $USER/$PROJECT rpm/git-pw.spec

where ``$USER/$PROJECT`` refers to a project you've created on copr. If you
haven't created one already, you can do like so:

.. code-block:: bash

    $ copr create $PROJECT

.. note::

    The source code is pulled from PyPI, thus, local builds will only reflect
    changes to the spec file - not the source itself. If you wish to also
    reflect these changes, you need to update the value of ``Source0`` in the
    spec file.

More information can be found in the `copr docs`__.

.. __: https://docs.fedoraproject.org/en-US/packaging-guidelines/Python/
.. __: https://copr.fedorainfracloud.org/coprs/stephenfin/git-pw/
.. __: https://docs.pagure.org/copr.copr/user_documentation.html
