from mininet.net import Mininet
from mininet.topo import LinearTopo
import time
import sys


def benchmark_mininet(n_nodos):
    print("==================================================")
    print(f"  BENCHMARK MININET: Despliegue de {n_nodos} Nodos L2")
    print("==================================================\n")

    print("[*] 1. Definiendo la topología (Solo estructura en memoria)...")
    topo = LinearTopo(k=n_nodos)

    print("[*] 2. ¡Orden de Aprovisionamiento! (Midiendo creación + arranque...)")

    start_time = time.perf_counter()

    net = Mininet(topo=topo, controller=None)

    net.start()

    end_time = time.perf_counter()
    deploy_time = end_time - start_time

    print("\n" + "=" * 50)
    print("                     RESULTADOS                  ")
    print("=" * 50)
    print(f"[+] Tiempo de Despliegue REAL (Mininet L2): {deploy_time:.4f} segundos")
    print("=" * 50 + "\n")

    print("[*] 3. Destruyendo el entorno para dejarlo limpio...")
    net.stop()


if __name__ == "__main__":
    num_nodos = 20
    if len(sys.argv) > 1 and sys.argv[1].isdigit():
        num_nodos = int(sys.argv[1])

    benchmark_mininet(num_nodos)
