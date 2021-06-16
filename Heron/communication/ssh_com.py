
import logging
import paramiko
import json
import os
import time
from pathlib import Path
import subprocess
import threading
import zmq.ssh

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
        ssh_info_file = os.path.join(Path(os.path.dirname(os.path.realpath(__file__))), 'ssh_info.json')
        with open(ssh_info_file) as f:
            ssh_info = json.load(f)

        result = {}
        if id != 'None':
            result = ssh_info[id]
        else:
            result['IP'] = result['Port'] = result['username'] = result['password'] = 'None'

        return result

    def connect_socket_to_local_ssh_tunnel(self, socket, socket_ip):
        if self.ssh_local_ip != 'None':
            logging.debug('ssh local with port : {}'.format(socket_ip))
            try:
                tunnelling_pids = zmq.ssh.tunnel_connection(socket, socket_ip, "{}@{}".format(self.ssh_local_username, self.ssh_local_ip),
                                          password=self.ssh_local_password,
                                          paramiko=True)
                logging.debug(tunnelling_pids)
                for pid in tunnelling_pids:
                    self.tunnelling_processes_pids.append(pid)
                logging.debug('connected')
            except Exception as e:
                logging.debug(e)

    def connect_socket_to_remote_ssh_tunnel(self, socket, socket_ip):
        if self.remote_server_id != 'None':
            logging.debug('ssh remote : ')
            tunnelling_pids = zmq.ssh.tunnel_connection(socket, socket_ip, "{}@{}".format(self.remote_server_info['username'],
                                                                        self.remote_server_info['IP']),
                                      password=self.remote_server_info['password'],
                                      paramiko=True)
            logging.debug(tunnelling_pids)
            for pid in tunnelling_pids:
                self.tunnelling_processes_pids.append(pid)

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
            print(line)

    def remote_stdout_thread(self):
        for line in self.stdout:
            print(line)

    def start_process(self, arguments_list):

        if self.remote_server_id == 'None':
            return subprocess.Popen(arguments_list, creationflags=subprocess.CREATE_NEW_PROCESS_GROUP).pid
        else:
            logging.debug(arguments_list)
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
        print(self.tunnelling_processes_pids)
        for _, pid in self.tunnelling_processes_pids:
            os.kill(pid)

