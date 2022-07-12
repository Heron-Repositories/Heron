
In Node Visualisation
=====================

The API
________

Heron defines an API for simple visualisation that the Node developer can use to add data visualisation elements to a
Node without developing them from scratch.

This is the API that is also used by the Visualisation Node.

The in Node visualisation is based on the class VisualisationDPG in the gui/visualisation_dpg.py script.

To use the API one first needs to import the class and define a global variable with VisualisationDPG type:

.. code-block:: python

    from Heron.gui.visualisation_dpg import VisualisationDPG

    vis: VisualisationDPG

then, in the initialisation function the vis object needs to be instantiated:

.. code-block:: python

    visualisation_type = 'Value'
    buffer = 20
    vis = VisualisationDPG(_node_name=_worker_object.node_name, _node_index=_worker_object.node_index,
                           _visualisation_type=visualisation_type, _buffer=buffer)

by passing to it the visualisation type and the buffer integer. The visualisation_type variable is a string with possible
values:

* 'Image'
* 'Value'
* 'Single Pane Plot'
* 'Multi Pane Plot'

(see below what each produces). The buffer is the number of data points to visualise (where applicable).

In the worker function one needs to first check if the visualisation is visible or not (assuming a
Visualisation parameter has been defined in the com script) and then pass the data to be visualised to the vis object:

.. code-block:: python

    global vis

    vis.visualisation_on = parameters[0]

    vis.visualise(some_data_to_visualise)

The VisualisationDPG object will take care of creating and killing the required separate threads so that the visualising
element requested through the visualisation_type argument will show only when the vis.visualisation_on is true.

Finally, the VisualisationDPG object needs to properly close down some graphical elements before the process terminates
so in the end of life function one needs to add:

.. code-block:: python

    global vis
    vis.end_of_life()

The visualisation elements
___________________________

