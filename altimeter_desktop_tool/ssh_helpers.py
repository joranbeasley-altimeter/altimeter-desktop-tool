import hashlib
import os
from contextlib import contextmanager

import paramiko
from paramiko import SFTPClient


class MySshClient(paramiko.SSHClient):
    def __init__(self,*args,**kwargs):
        paramiko.SSHClient.__init__(self)
        self.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        self.args = args
        self.kwargs = kwargs
        self.hostname = None
        if args or kwargs:
            self.connect(*args,**kwargs)
    def download_file(self,remote_src,local_dst):
        sftpCli = self.open_sftp()
        assert isinstance(sftpCli,SFTPClient)
        sftpCli.get(remote_src,local_dst)
    def getpeername(self):
        return self.get_transport().sock.getpeername()
    def reconnect(self):
        self.connect(*self.connect_args,**self.connect_kwargs)
    def connect(self,*args,**kwargs):
        self.connect_args = args
        self.connect_kwargs = kwargs
        # print("C:",args,kwargs)
        paramiko.SSHClient.connect(self,*args,**kwargs)

    @contextmanager
    def killable_sudo_command(self,cmd):
        nonce = hashlib.md5(os.urandom(32)).hexdigest()
        cmd = cmd.rstrip(";") + "; echo JOB %s"%nonce
        # print("CMD:",cmd)
        stdin,stdout,stderr = self.sudo_exec(cmd)
        # print(stderr.read())
        # token = stdout.readline()
        yield
        self.sudo_pkill(nonce)
    def kill_token(self,token):
        return self.sudo_pkill(token)
    def sudo_exec(self,cmd):
        cmd.replace('"', "\\\"")
        cmd = "sudo bash -c \"%s\"" % cmd
        stdin, stdout, stderr = self.exec_command(cmd)
        return stdin,stdout,stderr
    @contextmanager
    def lighted_context(self):
        self.turn_on_light()
        yield
        self.turn_off_light()
    def turn_on_light(self):
        self.sudo_exec("while [ 1 ]; do echo 1 > /sys/class/leds/led0/brightness; done;")
    def turn_off_light(self):
        self.sudo_pkill("leds/led")
    def sudo_kill(self,pid,code=9):
        self.exec_command("sudo kill -%s %s"%(code,pid))
    def sudo_pkill(self,search,code=9):
        self.exec_command("sudo pkill -%s -f %s"%(code,search))
    def check_output(self,cmd):
        stdin,stdout,stderr = self.exec_command(cmd)
        return [stdout.read(),stderr.read()]
    def iter_stdout(self,cmd):
        # session = self.get_transport().open_session()
        stdin,stdout,stderr = self.exec_command(cmd)
        # status = session.recv_exit_status()
        for line in iter(stdout.readline,''):
            yield line
        # callback(stdout.read())


    def check_stdout(self,cmd):
        stdin, stdout, stderr = self.exec_command(cmd)
        return stdout.read()

def connect_ssh(username, password, ip, port):
    try:
        client = MySshClient(ip, port, username, password, timeout=2.0)
    except:
        return None
    return client


def iter_all_successfull_ssh(ips, user, password, port=22,silent=True):
    for ip in ips:
        if not silent:
            print("TEST: %s:*******@%s" % (user, ip))
        client = connect_ssh(user, password, ip, port)
        if client:
            yield client


def find_first_successfull_ssh(ips, user, password, port=22):
    return next(iter_all_successfull_ssh(ips, user, password, port))



def paramiko_check_output(cli,cmd):
    stdin,stdout,stderr = cli.exec_command("ls -la /home/pi/python_altimeter_pkg2")
    return stdout[1].read()

def pexpect(cli,cmd,expecting,response):
    """
    respond to commands

    :param cli:
    :param cmd:
    :param expecting:
    :param response:
    :return:
    """
    pass
