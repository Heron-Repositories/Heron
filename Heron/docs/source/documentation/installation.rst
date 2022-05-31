
Installation
============

The hardcore way (as of |today|)
--------------------------------

Heron was designed so that it doesn't require installation.
You can download the code from its github repository and just run it (check out the Startup paragraph on what running
Heron actually means).

The same goes for putting the Heron code on machines other than the one running the Heron GUI (in order to use Heron's
network functionality). All you have to do is copy the code from the repository to somewhere in your machines that your
main machine can have access to through SSH (see info on how Heron connects different machines in the :doc:`lan_use`)

Requirements
""""""""""""
In order for the 'just copy the code over' idea to work, you will need to have a python environment that can support
Heron's needs. The minimal environment for Heron to start its GUI and also use all its pre packaged Nodes is the following:

1. numpy
2. pandas
3. pyzmq > 20.x
4. paramiko
5. h5py
6. tornado
7. pynput
8. serial
9. dearpygui > 1.2
10. opencv >= 4.x

All of the above, except dearpygui and opencv, can be installed through conda (pynput and serial are in the conda-forge).
So once you set up conda (either miniconda or anaconda) you can do:

.. code-block:: python

       conda install package_name

or

.. code-block:: python

       conda install -c conda-forge package_name

for the packages that can be found the the conda-forge.

You can get dearpygui with a:

.. code-block:: python

       pip install dearpygui

It won't bother the rest of the conda installations. For OpenCV read on.


If the environment you are setting up is for a machine that will not call Heron's GUI then dearpygui is not required.
Also check which Nodes you will need to use in this machine and figure out their imports. The absolutely necessary
packages for Heron to run on a non GUI machine are numpy, pandas, pyzmq, paramiko and tornado.

OpenSSH
"""""""
If you are on Windows you will not necessarily have openssh up and running. Heron requires this to work properly
irrespective of whether you are going to use the LAN functionality of Heron or not. Here is what Microsoft
`has to say about this. <https://docs.microsoft.com/en-us/windows-server/administration/openssh/openssh_install_firstuse>`_

You will need both the client and the server. To check that everything has worked properly go to where openssh has generated
the .ssh folder (check out your user folder) and see if there is a folder in there called known_hosts. If that exists
then Heron will not complain.
Also after you have set the whole thing up test it out by sshing somewhere from your Windows machine and from somewhere
to your Windows machine (making sure both server and client are working).

Tornado
"""""""
After you have installed everything there is a possibility that pyzmq will issue a warning regarding tornado every time
you try to run Heron. If this is the case uninstall pyzmq and tornado and then install tornado first then pyzmq and
finally update pyzmq (conda update pyzmq).

OpenCV
""""""
If you install OpenCV from conda then everything will break. Again this is true at the time of this writing. Maybe, at
some point the OpenCV in conda will not generate an inconsistent environment. We wil see. Until this day nothing bad
happens if OpenCV is installed through pip. Do:

.. code-block:: python

       pip install opencv-python

or (but not both!)

.. code-block:: python

       pip install opencv-contrib-python

Heron will work with either version. It is up to you if you need the extra functionality of the contrib version.

The standard way
-----------------

Heron can also be installed as a pip package. Just do

.. code-block:: python

    pip install heron_of_alexandria

The pip install has as requirements everything mentioned above except openCV.


Node requirements
-----------------

The above requirements are for Heron and the Nodes that come bundled together in the Heron repository.
The `heron-repos <https://github.com/Heron-Repositories>`_ holds some more Nodes, and hopefully in the future there will be
many more of them. Each Node has its own imports and the environment that runs the worker script of a Node
needs to have all the required packages both for the basic Heron functionality and for the Nodes it is
running.

Environments
------------

It is not a bad idea to put Heron and its basic needs all in a single environment separate from everything else.
On the other hand as long as you keep your environment consistent Heron won't complain. The way Heron operates though
allows you to have Nodes that work only in different environments than Heron's and with requirements that would clash
with each other and still be used in the same pipeline (again see :doc:`lan_use`).







