import requests
import time
import sys
import os

# La IP de tu máquina virtual donde corre Uvicorn
BASE_URL = "http://192.168.2.100:8000/api/v1"


def check_api():
    """Verifica que el orquestador esté corriendo antes de la prueba."""
    try:
        requests.get(f"{BASE_URL}/network", timeout=2)
    except requests.exceptions.ConnectionError:
        print("[!] ERROR: No puedo conectar con la API.")
        print("[!] Asegúrate de haber ejecutado 'sudo python3 main.py' primero.")
        sys.exit(1)


def init_ring_topology(nRouters):
    for i in range(1, nRouters + 1):
        res = requests.post(
            f"{BASE_URL}/nodes", json={"name": f"r{i}", "type": "router"}
        )
        if res.status_code != 201:
            print(f"[!] Fallo al definir r{i}: {res.text}")

    for i in range(1, nRouters):
        requests.post(
            f"{BASE_URL}/links", json={"source": f"r{i}", "target": f"r{i+1}"}
        )
    requests.post(f"{BASE_URL}/links", json={"source": f"r{nRouters}", "target": "r1"})


def speed_test(nRouters):
    print("==================================================")
    print("  TEST 1: VELOCIDAD DE DESPLIEGUE ")
    print("==================================================\n")

    print("[*] 1. Limpiando el entorno...")
    requests.delete(f"{BASE_URL}/network")
    time.sleep(1)

    total_start = time.perf_counter()

    print(f"[*] 2. Generando topología de {nRouters} routers...")
    init_ring_topology(nRouters=nRouters)

    print("[*] 3. Inicializando nodos (Aprovisionamiento al Kernel)...")
    kernel_start = time.perf_counter()

    response = requests.post(f"{BASE_URL}/network/start")

    end_time = time.perf_counter()

    if response.status_code == 200:
        kernel_time = end_time - kernel_start
        total_time = end_time - total_start

        print("\n" + "=" * 50)
        print("                 RESULTADOS DE CPU               ")
        print("=" * 50)
        print(f"[+] Tiempo de Inicialización: {kernel_time:.4f} segundos")
        print(f"[+] Tiempo Total:    {total_time:.4f} segundos")
        print("=" * 50 + "\n")

        data = requests.get(f"{BASE_URL}/network").json()
        up_nodes = sum(1 for n in data["nodes"] if n.get("status") == "UP")
        print(f"[*] Verificación: {up_nodes}/{nRouters} nodos reportan estado UP.")

        return up_nodes == nRouters
    else:
        print(f"\n[!] Error crítico en el despliegue: {response.text}")
        return False


def ram_test(nRouters):
    print("\n==================================================")
    print("  TEST 2: HUELLA DE MEMORIA (RAM) ")
    print("==================================================\n")

    print("[*] 1. Dando 3 segundos para que los procesos FRR se estabilicen...")
    time.sleep(3)

    total_ram_mb = 0
    successful_reads = 0

    print("[*] 2. Consultando el consumo base desde Cgroups v2...")

    for i in range(1, nRouters + 1):
        cgroup_path = f"/sys/fs/cgroup/net_project/r{i}/memory.current"

        try:
            with open(cgroup_path, "r") as f:
                bytes_used = int(f.read().strip())
                mb_used = bytes_used / (1024 * 1024)
                total_ram_mb += mb_used
                successful_reads += 1

                if i <= 3 or i == nRouters:
                    print(f"    - Router r{i}: {mb_used:.2f} MB")
                elif i == 4:
                    print("    - ... (truncado) ...")

        except FileNotFoundError:
            print(f"[!] No se encontró el Cgroup para r{i}. ¿Está apagado?")
        except Exception as e:
            print(f"[!] Error leyendo la RAM de r{i}: {e}")

    if successful_reads > 0:
        avg_ram_mb = total_ram_mb / successful_reads
        print("\n" + "=" * 50)
        print("                 RESULTADOS DE RAM               ")
        print("=" * 50)
        print(f"[+] Consumo Medio por Router: {avg_ram_mb:.2f} MB")
        print(f"[+] Consumo Total ({successful_reads} routers): {total_ram_mb:.2f} MB")
        print("=" * 50 + "\n")


if __name__ == "__main__":
    check_api()

    if len(sys.argv) > 1 and sys.argv[1].isdigit():
        num_routers = int(sys.argv[1])
    else:
        print("Uso: python3 benchmark.py <numero_de_routers>")
        sys.exit(0)

    success = speed_test(num_routers)

    if success:
        ram_test(num_routers)

    print("[*] Limpiando infraestructura y desmontando Cgroups...")
    requests.delete(f"{BASE_URL}/network")
    print("[+] Test finalizado con éxito.")
