import subprocess
import time
import json
import os

def generar_yaml_lineal(n_routers):
    yaml_content = f"name: test-scaling\ntopology:\n  nodes:\n"

    for i in range(1, n_routers + 1):
        yaml_content += f"    r{i}:\n      kind: linux\n      image: frrouting/frr:latest\n"

    yaml_content += "    host1:\n      kind: linux\n      image: sflow/clab-iperf3\n"
    yaml_content += "    host2:\n      kind: linux\n      image: sflow/clab-iperf3\n"

    yaml_content += "\n  links:\n"
    yaml_content += f"    - endpoints: [\"host1:eth1\", \"r1:eth1\"]\n"

    for i in range(1, n_routers):
        yaml_content += f"    - endpoints: [\"r{i}:eth2\", \"r{i+1}:eth1\"]\n"

    yaml_content += f"    - endpoints: [\"r{n_routers}:eth2\", \"host2:eth1\"]\n"

    with open("clab-scaling.yaml", "w") as f:
        f.write(yaml_content)

def ejecutar(nodo, comando, ignorar_codigo=False):
    print(f"      [cmd] {nodo}: {comando}")
    nombre = f"clab-test-scaling-{nodo}"
    res = subprocess.run(["sudo", "docker", "exec", nombre, "sh", "-c", comando], capture_output=True, text=True)

    if res.returncode != 0 and not ignorar_codigo:
        raise RuntimeError(f"Fallo en {nodo} ({comando}):\nSTDERR: {res.stderr.strip()}\nSTDOUT: {res.stdout.strip()}")
    return res.stdout.strip()

def test_n_routers(n):
    print(f"\n" + "-"*60)
    print(f"[*] Evaluando topología lineal con {n} Router(s)...")
    print("-"*60)

    generar_yaml_lineal(n)
    print("    [>] Desplegando Containerlab...")
    subprocess.run(["sudo", "clab", "deploy", "-t", "clab-scaling.yaml"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(2)

    try:
        print("    [>] Configurando IPAM Lógico...")
        ejecutar("r1", "ip addr add 10.100.1.1/24 dev eth1")
        ejecutar("host1", "ip addr add 10.100.1.10/24 dev eth1")

        ejecutar(f"r{n}", "ip addr add 10.100.2.1/24 dev eth2")
        ejecutar("host2", "ip addr add 10.100.2.10/24 dev eth1")

        for i in range(1, n):
            ejecutar(f"r{i}", f"ip addr add 10.1.{i}.1/24 dev eth2")
            ejecutar(f"r{i+1}", f"ip addr add 10.1.{i}.2/24 dev eth1")

        print("    [>] Inyectando rutas estáticas...")
        ejecutar("host1", "ip route replace default via 10.100.1.1")
        ejecutar("host2", "ip route replace default via 10.100.2.1")

        for i in range(1, n):
            ejecutar(f"r{i}", f"ip route add 10.100.2.0/24 via 10.1.{i}.2")
        for i in range(n, 1, -1):
            ejecutar(f"r{i}", f"ip route add 10.100.1.0/24 via 10.1.{i-1}.1")

        print("    [>] Comprobando conectividad (Ping Preventivo)...")
        ejecutar("host2", "ping -c 1 -W 2 10.100.1.10")
        print("      [+] Ping exitoso, las rutas funcionan.")

        print("    [>] Lanzando cliente iperf3 desde host2 (5 segundos)...")
        resultado = ejecutar("host2", "iperf3 -c 10.100.1.10 -t 5 --json", ignorar_codigo=True)

        try:
            datos = json.loads(resultado)
            if "error" in datos:
                raise RuntimeError(f"Error de iperf3: {datos['error']}")
            gbps = datos['end']['sum_received']['bits_per_second'] / 1e9
            print(f"      [+] Rendimiento sostenido: {gbps:.2f} Gbps")
            return gbps
        except json.JSONDecodeError:
            raise RuntimeError(f"JSON inválido devuelto por iperf3. Salida bruta: {resultado}")

    finally:
        print("    [>] Limpiando topología...")
        subprocess.run(["sudo", "clab", "destroy", "-t", "clab-scaling.yaml", "--cleanup"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        if os.path.exists("clab-scaling.yaml"): os.remove("clab-scaling.yaml")

def run_scaling_suite():
    print("="*60)
    print("  SUITE DE ESCALABILIDAD L3: DEGRADACIÓN MULTISALTO (DOCKER)")
    print("="*60)

    if os.path.exists("clab-scaling.yaml"):
        subprocess.run(["sudo", "clab", "destroy", "-t", "clab-scaling.yaml", "--cleanup"], capture_output=True)
    subprocess.run(["sudo", "docker", "rm", "-f", "clab-test-scaling-host1", "clab-test-scaling-host2"], capture_output=True)
    for i in range(1, 15):
        subprocess.run(["sudo", "docker", "rm", "-f", f"clab-test-scaling-r{i}"], capture_output=True)

    resultados = {}

    # BARRIDO DEL 1 AL 10
    for routers in range(1, 11):
        try:
            throughput = test_n_routers(routers)
            resultados[routers] = throughput
        except Exception as e:
            print(f"\n    [!] Error crítico en iteración {routers}: {e}")
            resultados[routers] = 0.0
            break

    print("\n" + "="*60)
    print("                 RESULTADOS FINALES (CSV)")
    print("="*60)
    print("Saltos_L3, Throughput_Gbps")
    for saltos, bw in resultados.items():
        print(f"{saltos}, {bw:.2f}")
    print("="*60)

if __name__ == "__main__":
    run_scaling_suite()