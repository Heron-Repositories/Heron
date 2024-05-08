

Adding Repositories as new Nodes
=================================

Adding an existing repository
-----------------------------

Heron can add repositories that have the correct folder structure (see below) as symbolic links into its own folder
structure and thus allow Heron's GUI to see code in these repositories as Nodes. This is the principal way of adding
new Nodes to Heron's GUI.

The first step in that process is to create or download a repository designed to be a Heron Node or group of Nodes.
Once such a repository is in place on the hard disk somewhere (do not put it in Heron's folder structure) then
do Menu Bar -> Nodes -> Add new Operations Folder (as Symbolic Link from Existing Repo). Point Heron to the
top folder of the repository and it will add the correct parts of it in Heron's Operations folder as symbolic links.

.. note::
    In Windows, in order for an app to make symbolic links it needs to have Administrator rights, so to do the above in
    Windows, Heron must have been started with a Run as administrator (Linux does not require anything like this).
    If the above is not the case then Heron will give a warning reminding the user to give it elevated privileges.
    Another error will be generated if the directory Heron is pointed to does not contain a valid Heron Nodes folder
    structure.

Downloading a repository from inside Heron
-------------------------------------------
Heron allows you to clone a repository from an online source and then add the newly created repository to the Operations
folder. To do this click Menu Bar -> Nodes -> Download Operations from the Heron-Repositories page. You will then
be asked to fill in the URL of the repo and after that you will be asked to select a folder into which the repo will
be cloned (with the same base folder name as the name of the online repo). Once these two steps are done Heron will
automatically clone the repo in the target folder and then add the new local repo in the Operations folder as a symbolic
link. Again, in Windows you have to be running Heron as an Administrator (Heron will let you know if you are not).

Creating a valid Heron Nodes repository from scratch
----------------------------------------------------
The only requirement for a valid Heron Node repository is its correct folder structure. This is as follows

| Base_repository_folder
|  Sources / Transforms / Sinks
|    Subcategory
|     __top__
|       ignore.gitignore
|     Name_of_Node
|       com_script.py
|       worker_script.py


Here is an example with 4 Nodes in it, a Source called *Weird Camera* (under Vision), a Transform called
*Super Motor Controller* (under Motion) and two Sinks called *Saving CSVs* (under Saving) and
*Some Other Sink Node* (under General).

| My_awesome_Nodes_repo
|   README.md
|   Sources
|      Vision
|         __top__
|            ignore.gitignore
|         Weird_Camera
|            weird_camera_com.py
|            weird_camera_worker.com
|   Transforms
|      Motion
|         __top__
|            ignore.gitignore
|         Super_Motor_Controller
|            Maybe_Another_Folder
|               another_script.py
|            super_motor_controller_com.py
|            super_motro_controller_worker.py
|   Sinks
|      Saving
|         __top__
|            ignore.gitignore
|         Saving_CSVs
|            some_other_script.py
|            saving_csvs_com.py
|            saving_csvs_worker.py
|      General
|         __top__
|            ignore.gitignore
|         Some_Other_Sink_Node
|            some_other_sink_node_com.py
|            some_other_sink_node_worker.py

The actual name of the Node as seen on Heron's GUI is set in the xxx_com.py script. It is good practice to give the
folder holding the Node (i.e. the Python scripts) the same name but with underscores instead of spaces. Heron doesn't
mind if the name of the folder is different but it does mind spaces so pretend it is 1980 and make folder names
without spaces.

The folder __top__ needs to exist if the Subcategory you are making under the Sources/Transforms/Sinks folder doesn't
already exist in your Heron folder structure. Otherwise it can be skipped. In general it is a good idea to just include
it. The ignore.gitignore file is an empty file that gets added to the git repository so that the __top__ folder
is also added to the repository.

The file / folder structure inside the Node folder can be anything as long as the xxx_com.py and xxx_worker.py scripts
are also present.

The `Heron repos <https://github.com/Heron-Repositories>`_  organisation on GitHub has plenty of examples of Node
repositories.





