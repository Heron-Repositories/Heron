
Installation & Startup
======================

Installation
------------

The standard way
^^^^^^^^^^^^^^^^^

Heron can be installed as a pip package. Just do:

.. code-block:: python

       python -m pip install heron-42ad

(or whatever python command you use in your system - python3, py, etc.) in any python environment you want.
This will install all the required libraries and Heron itself and give you a fully
working system.

At some point we also plan to release a conda package, but currently this is lower on the priority list.

The hardcore way (as of |today|)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

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
8. pyserial
9. dearpygui > 1.2
10. opencv >= 4.x
11. psutil

All of the above, except dearpygui and opencv, can be installed through conda (pynput and pyserial are in the conda-forge).
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


OS Compatibility
^^^^^^^^^^^^^^^^^
Heron runs on all systems that its libraries can run on. That means Windows, MacOS, Linux and ARM based systems.
It has been tested on Windows (10 and 11), MacOS, Linux (Ubuntu 20.04.6, x64) and Raspberry Pi 4 (Debian GNU/Linux 12
(bookworm), aarch64).

Specific OS issues are:

Windows - OpenSSH
""""""""""""""""""
If you are on Windows you will not necessarily have openssh up and running. Heron requires this to work properly
irrespective of whether you are going to use the LAN functionality of Heron or not. Here is what Microsoft
`has to say about this. <https://docs.microsoft.com/en-us/windows-server/administration/openssh/openssh_install_firstuse>`_

You will need both the client and the server. To check that everything has worked properly go to where openssh has generated
the .ssh folder (check out your user folder) and see if there is a folder in there called known_hosts. If that exists
then Heron will not complain.
Also after you have set the whole thing up test it out by sshing somewhere from your Windows machine and from somewhere
to your Windows machine (making sure both server and client are working).

Linux (both x86 and ARM)
""""""""""""""""""""""""
If you install Heron using pip on a machine running Linux (either a PC or a Raspberry Pi) you will need to give executable
privileges to the python scripts in Heron. Go into the top Heron directory and do::
    $ sudo chmod -R 700 ./Heron

The 700 will give you (the user) the minimum required privileges. Other, more permissive privilege combinations are also
fine.

Raspberry Pi
"""""""""""""
Installing on Raspberry pi (again at the time of writing this - March 2024) is a little bit trickier. All Heron required
libraries except DearPyGui will install with a simple pip. DearPyGui needs to be compiled. Follow the instructions
`here <https://github.com/hoffstadt/DearPyGui/issues/1741>`_. Things are still a little experimental (at least until
DearPyGui 2.0) so your mileage may vary.

Once DearPyGui is up and running then Heron can be installed either through a pip command or by installing the individual
requirements and then downloading Heron from its github page.

Once up and running, Heron might complain that it cannot find the /$HOME/.ssh/known_hosts file. If this is the case
then you will need to make an empty known_hosts in the directory Heron is looking for it. This will not bother your
standard ssh installation. If you are planning on using the Heron GUI running on Raspberry Pi to run graphs that connect
to Nodes on other machines then you need to setup your ssh so that the known_hosts file resides in /$HOME/.ssh.



Node requirements
^^^^^^^^^^^^^^^^^

The above requirements are for Heron and the Nodes that come bundled together in the Heron repository.
The `heron-repos <https://github.com/Heron-Repositories>`_ holds more Nodes, and in the future there will be
many more of them. Each Node has its own imports and the environment that runs the worker script of some Nodes
needs to have all the required packages both for the basic Heron functionality and for the Nodes it is
running.

Environments
^^^^^^^^^^^^^

It is not a bad idea to put Heron and its basic needs all in a single environment separate from everything else.
On the other hand as long as you keep your environment consistent Heron won't complain. The way Heron operates though
allows you to have Nodes that work only in different environments than Heron's and with requirements that would clash
with each other and still be used in the same pipeline (again see :doc:`lan_use`).

Startup
-------

After pip install
^^^^^^^^^^^^^^^^^^
If you install Heron through pip then you will get a Heron command to start the GUI. On a command line terminal with
the correct environment activated just issue the command

.. code-block:: bash

    Heron

and the GUI will start.

After manual install
^^^^^^^^^^^^^^^^^^^^^

Heron's GUI is just a Python script so the way to run it is by calling in a command line the following code

.. code-block:: bash

    python directory_path_to_Heron/Heron/gui/editor.py

If you have used an environment you need to first activate that. If you are on Windows and you do not want to deal
with command lines all the time then make a batch file (e.g. Heron.bat) and put in it whatever you would write on your
command line. So if for example you have set up a conda environment called base then put in the batch file this:

.. code-block:: bash

    CALL conda activate base
    python directory_path_to_Heron\Heron\gui\editor.py

If you are on Linux the assumption is you do not need this manual to set up a bash file.
















