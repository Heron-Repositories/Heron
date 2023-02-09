
import logging
import signal
import platform
import paramiko
import os
import subprocess
import threading
import zmq.ssh
from Heron import general_utils as gu


class SSHCom:
    def __init__(self, worker_exec=None, local_server_id=None, remote_server_id=None,
                 ssh_local_ip=None, ssh_local_username=None, ssh_local_password=None):
        if worker_exec is not None:
            self.local_server_id = local_server_id
            self.remote_server_id = remote_server_id
            self.worker_exec = worker_exec
            self.local_server_info = self.get_ssh_server_info(self.local_server_id)
            self.remote_server_info = self.get_ssh_server_info(self.remote_server_id)
        if ssh_local_ip is not None:
            self.ssh_local_ip = ssh_local_ip
            self.ssh_local_username = ssh_local_username
            self.ssh_local_password = ssh_local_password
        self.client = None
        self.setup_client()
        self.stdout = None
        self.stderr = None
        self.tunnelling_processes_pids = []

    def setup_client(self):
        try:
            pass
            self.client = paramiko.SSHClient()
            self.client.load_host_keys(os.path.expanduser('~/.ssh/known_hosts'))
            self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        except Exception as e:
            print('Starting paramiko client failed with error {}'.format(e))

    @staticmethod
    def get_ssh_server_info(id):
        """
        Reads the ssh_info.json file and returns the dictionary that has the info for the ssh server with the given id
        :param id: A string of an int that represents the unique id of the ssh_info.json server entry
        :return: The dict that carries the info of the specified server (IP, port, username and password)
        """
        ssh_info = gu.get_ssh_info_file()

        result = {}
        if id != 'None':
            result = ssh_info[id]
        else:
            result['IP'] = result['Port'] = result['username'] = result['password'] = 'None'

        return result

    def connect_socket_to_local(self, socket, socket_ip, socket_port, skip_ssh=False):
        """
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
        locally. This was used for the case of sockets that do proof of life (and connect to the local proof of life
        forwarder). It is not used any more. The ability though to create a local socket without ssh piping even with
        a local ssh server running is left in this function
        :return: Nothing
        """

        if self.ssh_local_ip == 'None':
            socket.connect("{}:{}".format(socket_ip, socket_port))
        else:
            logging.debug('== Connecting back to local (computer running editor) with port : {}'.format(socket_port))
            try:
                if self.ssh_local_password == 'None' or skip_ssh:
                    logging.debug('=== Using normal sockets (not SSH) connecting to tcp://{}:{}'
                                  .format(self.ssh_local_ip, socket_port))
                    socket.connect(r"tcp://{}:{}".format(self.ssh_local_ip, socket_port))
                else:
                    logging.debug('=== Using SSH connecting to {} -> {}:{}'.
                                  format(self.ssh_local_ip, socket_ip, socket_port))
                    tunneling_process = zmq.ssh.tunnel_connection(socket, '{}:{}'.format(socket_ip, socket_port),
                                                                  "{}@{}".format(self.ssh_local_username,
                                                                                 self.ssh_local_ip),
                                                                  password=self.ssh_local_password,
                                                                  paramiko=True)
                    logging.debug('PID of generated tunneling process = {}'.format(tunneling_process.pid))
                    self.tunnelling_processes_pids.append(tunneling_process.pid)
            except Exception as e:
                logging.debug("=== Failed to connect with error: {}".format(e))
            finally:
                logging.debug('=== Connected')

    def connect_socket_to_remote(self, socket, socket_ip):
        if self.remote_server_id != 'None':
            logging.debug('ssh remote with ip:port : {}'.format(socket_ip))
            tunnelling_pid = zmq.ssh.tunnel_connection(socket, socket_ip, "{}@{}".
                                                       format(self.remote_server_info['username'],
                                                              self.remote_server_info['IP']),
                                                       password=self.remote_server_info['password'],
                                                       paramiko=True)
            logging.debug(tunnelling_pid)
            self.tunnelling_processes_pids.append(tunnelling_pid.pid)

    def add_local_server_info_to_arguments(self, arguments_list):
        arguments_list.append(self.local_server_info['IP'])
        arguments_list.append(self.local_server_info['username'])
        arguments_list.append(self.local_server_info['password'])

        return arguments_list

    def list_to_string(self, list):
        result = ''
        for arg in list:
            result += '{} '.format(arg)
        return result[:-1]

    def remote_stderr_thread(self):
        for line in self.stderr:
            print('// REMOTE COMPUTER {} ERROR: {}'.format(self.remote_server_info['IP'], line))

    def remote_stdout_thread(self):
        for line in self.stdout:
            print('// REMOTE COMPUTER {} SAYS: {}'.format(self.remote_server_info['IP'], line))

    def start_process(self, arguments_list):
        if self.remote_server_id == 'None':
            if len(arguments_list[0].split(' ')) > 1:
                new_arguments_list = arguments_list[0].split(' ')
                for i in range(1, len(arguments_list)):
                    new_arguments_list.append(arguments_list[i])
            else:
                new_arguments_list = arguments_list

            kwargs = {'start_new_session': True} if os.name == 'posix' else \
                {'creationflags': subprocess.CREATE_NEW_PROCESS_GROUP}
            return subprocess.Popen(new_arguments_list, **kwargs).pid
        else:
            self.client.connect(self.remote_server_info['IP'],
                                int(self.remote_server_info['Port']),
                                self.remote_server_info['username'],
                                self.remote_server_info['password'])
            stdin, self.stdout, self.stderr = self.client.exec_command(self.list_to_string(arguments_list))
            stderr_thread = threading.Thread(target=self.remote_stderr_thread, daemon=True)
            stdout_thread = threading.Thread(target=self.remote_stdout_thread, daemon=True)

            stderr_thread.start()
            stdout_thread.start()

            return 'Remote unknown pid'

    def kill_tunneling_processes(self):
        logging.debug('KILLING THE PROCESSES {}'.format(self.tunnelling_processes_pids))
        if platform.system() == 'Windows':
            signal_to_send = signal.SIGBREAK
        elif platform.system() == 'Linux':
            signal_to_send = signal.SIGTERM
        for pid in self.tunnelling_processes_pids:
            os.kill(pid, signal_to_send)
        pid = os.getpid()
        os.kill(pid, signal_to_send)

