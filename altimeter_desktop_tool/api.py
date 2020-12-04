import asyncio
from altimeter_desktop_tool.port_scanner import scan_ips as async_scan_ips
from altimeter_desktop_tool.ssh_helpers import iter_all_successfull_ssh

def scan_ips_fast(min_ip, max_ip, port=22):
    return list(filter(None, asyncio.run(async_scan_ips(min_ip, max_ip, port))))

def iter_connect_raspberry_pi_in_ip_range(minIp, maxIp, username="pi", password="raspberry"):
    ips = scan_ips_fast(minIp, maxIp)
    last_cli = None
    for cli in iter_all_successfull_ssh(ips, username, password):
        if last_cli:
            last_cli.close()
        last_cli = cli
        yield cli

def connect_first_raspberry_pi_in_ip_range(minIp, maxIp, username="pi", password="raspberry"):
    return next(iter_connect_raspberry_pi_in_ip_range(minIp, maxIp, username, password))
if __name__ == "__main__":
    import time

    t0 = time.time()
    cli = connect_first_raspberry_pi_in_ip_range('192.168.1.0', '192.168.1.255')

    print("Got Cli %0.2fs" % (time.time() - t0))
