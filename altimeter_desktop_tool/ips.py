import operator
import socket

import six


def ip2int(ip):
    octet1,octet2,octet3,octet4 = map(int,ip.split("."))
    return (octet1 << 24) | (octet2 << 16) | (octet3 << 8) | octet4
def int2octets(ipInt):
    return [ipInt >> 24,(ipInt >> 16)&0xFF,(ipInt >> 8)&0xFF,ipInt&0xFF]
def octets2ip(octets):
    return ".".join(map(lambda x:str(int(x)),octets))
def int2ip(ipInt):
    return ".".join(map(str,int2octets(ipInt)))
def count_ips(ip0,ip1):
    if isinstance(ip0,IP):
        return ip0 - ip1
    elif isinstance(ip1,IP):
        return ip2int(ip0) - ip1.int
    return ip2int(ip1) - ip2int(ip0)
def add_ips(ip0,num_ips,type="str"):
    result = ip2int(ip0)+num_ips
    if type=="int":
        return result
    result = int2octets(result)
    if type == "list":
        return result
    return ".".join(map(str,result))

def fast_port_check(ip,port,timeout=0.03):
    # print("CHECK: ",ip,port,timeout)
    s = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
    s.settimeout(timeout)
    try:
        s.connect((ip,port))
    except Exception as e:
        if ip == "192.168.1.139":
            pass # canary
            # traceback.print_exc()
            # print("FALSE!",repr(ip) )
        return False
    else:
        # print("TRUE:",ip,port)
        return True
    finally:
        try:
            s.close()
        except:
            pass
class IP:
    def __str__(self):
        return self.str
    def __repr__(self):
        return "<IP %s>"%self.str
    def __init__(self,ip):
        self.setIP(ip)
    def checkPort(self,port,timeout=0.03):
        return fast_port_check(self.str,port,timeout)
    def setIP(self,ip):
        if isinstance(ip,(bytes,list)) and len(ip) == 4:
            self.octets = list(map(int,ip))
            self.str = octets2ip(self.octets)
            self.int = ip2int(self.str)
        elif isinstance(ip,(bytes,six.string_types)):
            if hasattr(ip,"encode"):
                ip.encode("utf8")
            ip = ip.strip()
            self.str = ip
            self.int = ip2int(ip)
            self.octets = int2octets(self.int)
        elif isinstance(ip,six.integer_types):
            self.octets = int2octets(ip)
            self.str = int2ip(ip)
            self.int = ip
        else:
            raise TypeError(ip)
    def __cmp(self,fn,other):
        # print("CMP:",other)
        return getattr(operator,fn)(self.int,other.int)
        # return cmp(self.int,other.int)
    def __iadd__(self,other):
        if isinstance(other,int):
            self.setIP(self.int + other)
            return self
        elif isinstance(other,IP):
            self.setIP(self.int + other.int)
            return self
        raise ValueError("I dont know how to add that %r"%other,type(other))
    def __add__(self,other):
        if isinstance(other,int):
            new_ip = IP(self.int + other)
            return new_ip
        elif isinstance(other, IP):
            return IP(self.int + other.int)
        raise ValueError("I dont know how to add that!")
    def __isub__(self,other):
        if isinstance(other,int):
            self.setIP(self.int - other)
            return self
        elif isinstance(other,IP):
            self.setIP(self.int - other.int)
            return self
        raise ValueError("I dont know how to sub that")
    def __sub__(self,other):
        if isinstance(other,int):
            return IP(self.int - other)
        elif isinstance(other, IP):
            # print("IP:",self.str,self.int,"OTHER:",other.int,other.str)
            return IP(self.int - other.int)
        raise ValueError("I dont know how to sub that!")
    def __rshift__(self, other):
        return self.int >> other
    def __lshift__(self, other):
        return self.int << other
    def __and__(self, other):
        return self.int & other
    def __gt__(self, other):
        self.__cmp("gt",other)
    def __ge__(self, other):
        self.__cmp("ge",other)
    def __lt__(self, other):
        self.__cmp("lt",other)
    def __le__(self, other):
        self.__cmp("le",other)

def rangeType(s):
    parts = list(map(IP,s.split("-")))
    return parts


class IPRange:

    def __init__(self,ip):
        """
        :param ip:
        """
        ip = ip.strip("'\"")
        self.ips = list(map(IP,ip.split("-",1)))
        # print("IPS:",self.ips,ip)
        self.num_ips = (self.ips[1] - self.ips[0]).int
        self._curr = self.ips[0]
        # print("NUM IPS:",self.num_ips)
    def __next__(self):
        curr = self._curr
        if curr.int > self.ips[1].int:
            self._curr = None
            raise StopIteration()
        self._curr = curr + 1
        # print("N",self.curr)
        return curr
    def iter_strings(self):
        return map(str,self)

    def __iter__(self):
        self.curr = self.ips[0]
        return self
    def __str__(self):
        return "'%s - %s'"%tuple(self.ips)

def get_my_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        return (s.getsockname()[0])
    finally:
        s.close()
def get_mask(ip_addr):
    import os
    if os.name == "nt":
        os.popen("ipconfig")

def get_my_ip_range():
    return get_ip_range(get_my_ip())

def get_ip_range(base_ip):
    if base_ip.startswith("192.168"):
        base = base_ip.rsplit(".",1)[0]
        return "%s.%s"%(base,0),"%s.%s"%(base,255)
    elif base_ip.startswith("10.10"):
        base = base_ip.rsplit(".",2)[0]
        return base+".0.0",base+"255.255"
    raise Exception("ERRROR!@#!@#!@ :%s"%base_ip)

if __name__ == "__main__":
    import time
    L = list(IPRange('192.168.1.1-192.168.1.255').iter_strings())
    print(L)

        # break
