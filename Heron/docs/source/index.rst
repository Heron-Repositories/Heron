.. This is used to create the local doc (outside of readthedocs) and runs the
  autoapi.
  It will be called with the command 'sphinx-build -b html . ../build' inside the
  Heron/Heron/docs/source directory. This will also build the source/autoapi/Heron/index
  that can then be used by the readthedocs (docs\index.rst) to put the automatically
  created API on the readthedocs page

Heron's documentation!
=================================

.. toctree::
    :maxdepth: 2
    :caption: About

    about/about_heron.rst


.. toctree::
    :maxdepth: 2
    :caption: Documentation

    documentation/installation.rst
    documentation/the_editor.rst
    documentation/lan_use.rst
    documentation/node_types.rst
    documentation/adding_repos.rst
    documentation/writing_new_nodes.rst
    documentation/visualisation.rst
    documentation/saving_state.rst
    documentation/synchronisation.rst
    documentation/debugging.rst

.. toctree::
   :maxdepth: 2
   :caption: API Reference

   autoapi/Heron/index.rst

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
