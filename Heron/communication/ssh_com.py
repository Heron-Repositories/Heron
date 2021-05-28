
import paramiko
import json
import os
from pathlib import Path
import subprocess
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

    def setup_client(self):
        try:
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
            zmq.ssh.tunnel_connection(socket, socket_ip, "{}@{}".format(self.ssh_local_username, self.ssh_local_ip),
                                      password=self.ssh_local_password,
                                      paramiko=True)

    def connect_socket_to_remote_ssh_tunnel(self, socket, socket_ip):
        if self.remote_server_id != 'None':
            zmq.ssh.tunnel_connection(socket, socket_ip, "{}@{}".format(self.remote_server_info['username'],
                                                                                      self.remote_server_info['IP']),
                                      password=self.remote_server_info['password'],
                                      paramiko=True)

    def add_local_server_info_to_arguments(self, arguments_list):
        arguments_list.append(self.local_server_info['IP'])
        arguments_list.append(self.local_server_info['username'])
        arguments_list.append(self.local_server_info['password'])

        return arguments_list

    def start_process(self, arguments_list):

        if self.remote_server_id == 'None':
            return subprocess.Popen(arguments_list).pid
        else:
            print(arguments_list)
            self.client.connect(self.remote_server_info['IP'],
                                int(self.remote_server_info['Port']),
                                self.remote_server_info['username'],
                                self.remote_server_info['password'])
            stdin, stdout, stderr = self.client.exec_command(arguments_list)

            return 'Remote unknown pid'

