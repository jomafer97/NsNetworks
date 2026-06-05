import time
import json
from mininet.net import Mininet
from mininet.node import Node
from mininet.log import setLogLevel
from mininet.clean import cleanup

class LinuxRouter(Node):
    def config(self, **params):
        super(LinuxRouter, self).config(**params)
        self.cmd('sysctl net.ipv4.ip_forward=1')

    def terminate(self):
        self.cmd('sysctl net.ipv4.ip_forward=0')
        super(LinuxRouter, self).terminate()

def test_n_routers_mininet(n):
    print(f"\n" + "-"*60)
    print(f"[*] Evaluando topología lineal con {n} Router(s) (Mininet)...")
    print("-" * 60)

    cleanup()
    net = Mininet(controller=None)

    routers = [net.addHost(f'r{i}', cls=LinuxRouter, ip='0.0.0.0') for i in range(1, n + 1)]
    h1 = net.addHost('host1', ip='10.100.1.10/24', defaultRoute='via 10.100.1.1')
    h2 = net.addHost('host2', ip='10.100.2.10/24', defaultRoute='via 10.100.2.1')

    net.addLink(h1, routers[0], intfName1='host1-eth1', intfName2='r1-eth1')
    for i in range(n - 1):
        net.addLink(routers[i], routers[i+1], intfName1=f'r{i+1}-eth2', intfName2=f'r{i+2}-eth1')
    net.addLink(routers[-1], h2, intfName1=f'r{n}-eth2', intfName2='host2-eth1')

    net.start()

    routers[0].cmd('ip addr add 10.100.1.1/24 dev r1-eth1')
    routers[-1].cmd(f'ip addr add 10.100.2.1/24 dev r{n}-eth2')

    for i in range(n - 1):
        routers[i].cmd(f'ip addr add 10.1.{i+1}.1/24 dev r{i+1}-eth2')
        routers[i+1].cmd(f'ip addr add 10.1.{i+1}.2/24 dev r{i+2}-eth1')

    for i in range(1, n):
        routers[i-1].cmd(f'ip route add 10.100.2.0/24 via 10.1.{i}.2')
    for i in range(n, 1, -1):
        routers[i-1].cmd(f'ip route add 10.100.1.0/24 via 10.1.{i-1}.1')

    h2.cmd("ping -c 1 -W 1 10.100.1.10")
    h1.cmd("iperf3 -s -D")
    time.sleep(1)

    resultado = h2.cmd("iperf3 -c 10.100.1.10 -t 5 --json")

    try:
        datos = json.loads(resultado)
        gbps = datos['end']['sum_received']['bits_per_second'] / 1e9
        print(f"      [+] Rendimiento sostenido: {gbps:.2f} Gbps")
        net.stop()
        return gbps
    except Exception as e:
        print(f"      [!] Error ejecutando iperf3: {e}")
        net.stop()
        return 0.0

def run_scaling_suite_mininet():
    print("="*60)
    print("  SUITE DE ESCALABILIDAD L3: MININET")
    print("="*60)
    setLogLevel('error')

    resultados = {}
    for routers in range(1, 11):
        try:
            resultados[routers] = test_n_routers_mininet(routers)
        except Exception as e:
            print(f"      [!] Error en iteración {routers}: {e}")
            resultados[routers] = 0.0

    print("\n" + "="*60)
    print("                 RESULTADOS FINALES (CSV)")
    print("="*60)
    print("Saltos_L3, Throughput_Gbps")
    for saltos, bw in resultados.items():
        print(f"{saltos}, {bw:.2f}")
    print("="*60)

if __name__ == "__main__":
    run_scaling_suite_mininet()