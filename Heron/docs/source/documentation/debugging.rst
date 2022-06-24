

Debugging
==========

Things go wrong, so read on.

Usage and limitations of the python debugging tools
_________________________________________
By far the most common way to debug the construction of a Node (i.e. the creation of the xxx_worker.py script) is to use
the Python standard debugging tools. That is the Python debugger and the print method. Both those will work just fine
as long as the Node's worker process runs on the same machine that Heron's GUI is also running. The print method will
print to the Heron's command line window while a debugger will stop the xxx_worker.py script in exactly the same way as
if it was called by Python (which it is just through the com process).


The logging system
___________________

But if the worker process is running on a different machine then neither the debugger will see it nor any print
statements will be pass their output to the main machine and Heron's command line window. In order to solve this (and to
also keep a general eye on Heron's overall performance) Heron has implemented two levels of Python's logging.

The com process verbosity and log
________________________________
