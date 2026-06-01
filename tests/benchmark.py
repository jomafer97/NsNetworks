import requests
import time
import sys

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


def benchmark_engine(nRouters):
    print("==================================================")
    print("  BENCHMARK: VELOCIDAD DE DESPLIEGUE ")
    print("==================================================\n")

    print("[*] 1. Limpiando el entorno (estado puro)...")
    requests.delete(f"{BASE_URL}/network")
    time.sleep(1)

    total_start = time.perf_counter()

    print(f"[*] 2. Definiendo la topología ({nRouters} routers)...")
    for i in range(1, nRouters + 1):
        res = requests.post(
            f"{BASE_URL}/nodes", json={"name": f"r{i}", "type": "router"}
        )
        if res.status_code != 201:
            print(f"[!] Fallo al definir r{i}: {res.text}")

    print(f"[*] 3. Cableando el anillo de red ({nRouters} enlaces)...")
    for i in range(1, nRouters):
        requests.post(
            f"{BASE_URL}/links", json={"source": f"r{i}", "target": f"r{i+1}"}
        )
    requests.post(f"{BASE_URL}/links", json={"source": f"r{nRouters}", "target": "r1"})

    print("[*] 4. ¡Orden de Aprovisionamiento al Kernel! (Midiendo...)")

    kernel_start = time.perf_counter()

    response = requests.post(f"{BASE_URL}/network/start")

    kernel_end = time.perf_counter()
    total_end = time.perf_counter()

    if response.status_code == 200:
        kernel_time = kernel_end - kernel_start
        total_time = total_end - total_start

        print("\n" + "=" * 50)
        print("                     RESULTADOS                  ")
        print("=" * 50)
        print(f"[+] Tiempo de Motor (solo Kernel): {kernel_time:.4f} segundos")
        print(f"[+] Tiempo Total (incluye API):    {total_time:.4f} segundos")
        print("=" * 50 + "\n")

        data = requests.get(f"{BASE_URL}/network").json()
        up_nodes = sum(1 for n in data["nodes"] if n.get("status") == "UP")
        print(f"[*] Verificación: {up_nodes}/{nRouters} nodos reportan estado UP.")
    else:
        print(f"\n[!] Error crítico en el despliegue: {response.text}")


if __name__ == "__main__":
    check_api()

    num_routers = 10

    if len(sys.argv) > 1 and sys.argv[1].isdigit():
        num_routers = int(sys.argv[1])

    benchmark_engine(nRouters=num_routers)
