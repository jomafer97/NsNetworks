from mininet.net import Mininet
from mininet.topo import LinearTopo
import time
import sys


def run_mininet_suite(node_counts):
    print("==================================================")
    print("  SUITE AUTOMATIZADA: BENCHMARK MININET (L2)")
    print("==================================================\n")

    results = {}

    for n in node_counts:
        print(f"[*] Iniciando prueba con {n} nodos...")
        topo = LinearTopo(k=n)

        start_time = time.perf_counter()

        net = Mininet(topo=topo, controller=None)
        net.start()

        deploy_time = time.perf_counter() - start_time
        results[n] = deploy_time
        print(f"    [+] Tiempo registrado: {deploy_time:.4f} segundos")

        net.stop()
        time.sleep(1)

    print("\n" + "=" * 50)
    print("                 RESUMEN DE TIEMPOS               ")
    print("=" * 50)
    for n, t in results.items():
        print(f"[*] {n} Nodos: {t:.4f} segundos")
    print("=" * 50 + "\n")


if __name__ == "__main__":
    # Uso: python3 tests.py 10 20 50
    if len(sys.argv) > 1:
        counts = [int(x) for x in sys.argv[1:] if x.isdigit()]
    else:
        counts = [10, 20, 50]

    run_mininet_suite(counts)
