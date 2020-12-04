import asyncio
import time


from altimeter_desktop_tool.ips import fast_port_check, IPRange




async def async_check_port(ip,port,timeout=0.03):
    result = await asyncio.get_running_loop().run_in_executor(None,fast_port_check,ip,port,timeout)
    if result:
        return ip

async def check_ips_for_port(ips,port,timeout=0.03):
    tasks = []
    for ip in ips:
        # print("CHECK IP??:",ip)
        task = asyncio.create_task(async_check_port(str(ip), port,timeout))
        tasks.append(task)
    results = await asyncio.gather(*tasks)
    return results


async def scan_ips(min_ip,max_ip,port=22,timeout=0.03):
    ips = IPRange('%s-%s'%(min_ip,max_ip))
    results = await check_ips_for_port(ips,port,timeout)
    return results

async def main(min_ip,max_ip):
    return await scan_ips(min_ip,max_ip)

if __name__ == '__main__':
    t1 = time.time()
    r = asyncio.run(main('192.168.1.1','192.168.1.255'))
    print("----- %0.3fs -- " %(time.time()-t1))
    # print("R:",r)
