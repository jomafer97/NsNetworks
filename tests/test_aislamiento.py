import subprocess
import time
import os
import requests
from mininet.net import Mininet
from mininet.topo import SingleSwitchTopo
from mininet.log import setLogLevel


def generate_clab_yaml():
    yaml_content = """name: test-aislamiento
topology:
  nodes:
    r1:
      kind: linux
      image: frrouting/frr:latest
"""
    filename = "aislamiento.yaml"
    with open(filename, "w") as f:
        f.write(yaml_content)
    return filename


def run_isolation_suite():
    comandos_auditoria = {
        "Procesos (PID)": "ps -e | sed '1d' | wc -l",
        "Filesystem (Mount)": "df -T / | awk 'NR==2 {print $2}'",
        "Seccomp Filter": "grep '^Seccomp:' /proc/self/status | awk '{print $2}'",
        "Privilegios (CapEff)": "grep '^CapEff:' /proc/self/status | awk '{print $2}'",
        "AppArmor Profile": "cat /proc/self/attr/current 2>/dev/null || cat /proc/self/attr/apparmor/current 2>/dev/null || echo 'unconfined'",
    }

    resultados = {"Mininet": {}, "Containerlab": {}, "Motor Propio": {}}

    print("\n" + "=" * 60)
    print("   INICIANDO SUITE DE AUDITORÍA DE SEGURIDAD Y AISLAMIENTO")
    print("=" * 60)

    # --- 1. MININET ---
    print("\n[*] 1. Auditando Mininet (L2)...")
    setLogLevel("error")
    net = Mininet(topo=SingleSwitchTopo(1), controller=None)
    net.start()
    h1 = net.get("h1")

    for prueba, cmd in comandos_auditoria.items():
        print(f"    [>] Ejecutando en Mininet: {cmd}")
        resultados["Mininet"][prueba] = h1.cmd(cmd).strip()

    net.stop()
    print("    [+] Mininet auditado.")

    # --- 2. CONTAINERLAB ---
    print("\n[*] 2. Auditando Containerlab (Docker)...")
    clab_yaml = generate_clab_yaml()

    print("    [>] Desplegando topología con clab deploy...")
    subprocess.run(["sudo", "clab", "deploy", "-t", clab_yaml])
    time.sleep(3)

    container_name = "clab-test-aislamiento-r1"

    for prueba, cmd in comandos_auditoria.items():
        print(f"    [>] Ejecutando en Docker (clab): {cmd}")
        res = subprocess.run(
            ["sudo", "docker", "exec", container_name, "sh", "-c", cmd],
            capture_output=True,
            text=True,
        )
        resultados["Containerlab"][prueba] = res.stdout.strip()

    print("    [>] Destruyendo topología con clab destroy...")
    subprocess.run(["sudo", "clab", "destroy", "-t", clab_yaml, "--cleanup"])

    if os.path.exists(clab_yaml):
        os.remove(clab_yaml)
    print("    [+] Containerlab auditado.")

    # --- 3. MOTOR PROPIO ---
    print("\n[*] 3. Auditando Motor Propio vía API...")
    BASE_URL = "http://127.0.0.1:8000/api/v1"

    print("    [>] Preparando red y arrancando nodo r1 vía REST...")
    requests.delete(f"{BASE_URL}/network")
    requests.post(f"{BASE_URL}/network/start")
    requests.post(f"{BASE_URL}/nodes", json={"name": "r1", "type": "router"})
    requests.post(f"{BASE_URL}/nodes/r1/start")

    for prueba, cmd in comandos_auditoria.items():
        print(f"    [>] Ejecutando en Motor Propio (API exec): {cmd}")
        res = requests.post(
            f"{BASE_URL}/nodes/r1/exec", json={"command": ["sh", "-c", cmd]}
        )

        if res.status_code == 200:
            resultados["Motor Propio"][prueba] = res.json().get("output", "").strip()
        else:
            resultados["Motor Propio"][prueba] = "Error API"

    print("    [>] Destruyendo red vía REST...")
    requests.delete(f"{BASE_URL}/network")
    print("    [+] Motor Propio auditado.")

    return resultados


def print_results(resultados):
    print("\n" + "=" * 80)
    print(
        f"{'Métrica Auditada':<22} | {'Mininet':<16} | {'Containerlab':<16} | {'Motor Propio':<16}"
    )
    print("-" * 80)

    for prueba in [
        "Procesos (PID)",
        "Filesystem (Mount)",
        "Seccomp Filter",
        "Privilegios (CapEff)",
        "AppArmor Profile",
    ]:
        m_res = resultados["Mininet"].get(prueba, "N/A")
        c_res = resultados["Containerlab"].get(prueba, "N/A")
        p_res = resultados["Motor Propio"].get(prueba, "N/A")
        print(f"{prueba:<22} | {m_res:<16} | {c_res:<16} | {p_res:<16}")
    print("=" * 80 + "\n")


if __name__ == "__main__":
    res = run_isolation_suite()
    print_results(res)
