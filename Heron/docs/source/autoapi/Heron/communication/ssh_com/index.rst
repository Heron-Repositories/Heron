:py:mod:`Heron.communication.ssh_com`
=====================================

.. py:module:: Heron.communication.ssh_com


Module Contents
---------------

Classes
~~~~~~~

.. autoapisummary::

   Heron.communication.ssh_com.SSHCom




.. py:class:: SSHCom(worker_exec=None, local_server_id=None, remote_server_id=None, ssh_local_ip=None, ssh_local_username=None, ssh_local_password=None)

   .. py:method:: setup_client(self)


   .. py:method:: get_ssh_server_info(id)
      :staticmethod:

      Reads the ssh_info.json file and returns the dictionary that has the info for the ssh server with the given id
      :param id: A string of an int that represents the unique id of the ssh_info.json server entry
      :return: The dict that carries the info of the specified server (IP, port, username and password)


   .. py:method:: connect_socket_to_local(self, socket, socket_ip, socket_port, skip_ssh=False)

      Connects a socket to an IP and a port at the computer that is running the editor (local). It has three possible
      behaviours:

      1) If the node hasn't been set up as a remote node (i.e. has not been given the ip addresses for an SSH remote
      and an SSH local server) then the worker function runs locally and the socket is connected to the local ip
      (probably 127.0.0.1) and the correct port for the job.

      2) If the node is a remote running node (i.e. has ip addresses for the SSH remote and SSH local servers) then
      it has two possible behaviours:

      2a) If there is no local SSH running (denoted by the password of the local SSH server being None) then
      the socket is connected ("normally") to the ip address of the local computer (i.e. the ip address of the
      local SSH server given on the node's extra info) and the corresponding port for the job.

      2b) If there is a local SSH server actually running (there is a password associated with it in the SSH
      info page of the editor) then the socket is connected through an ssh tunnel

      :param socket: The socket to connect
      :param socket_ip: The localhost ip address used by Heron (probably 127.0.0.1)
      :param socket_port: The port to connect to
      :param skip_ssh: If true then the connection doesn't use an ssh tunnel even if there is an SSH server running
      locally. This is used for the case of sockets that do proof of life (and connect to the local proof of life
      forwarder).
      :return: Nothing


   .. py:method:: connect_socket_to_remote(self, socket, socket_ip)


   .. py:method:: add_local_server_info_to_arguments(self, arguments_list)


   .. py:method:: list_to_string(self, list)


   .. py:method:: remote_stderr_thread(self)


   .. py:method:: remote_stdout_thread(self)


   .. py:method:: start_process(self, arguments_list)


   .. py:method:: kill_tunneling_processes(self)



