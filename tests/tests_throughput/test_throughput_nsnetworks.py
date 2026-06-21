import time
import requests
import json

BASE_URL = "http://127.0.0.1:8000/api/v1"

def ejecutar_comando_api(nodo, comando):
    """Inyecta comandos vía API."""
    res = requests.post(f"{BASE_URL}/nodes/{nodo}/exec", json={"command": comando})
    if res.status_code != 200:
        raise RuntimeError(f"Fallo al ejecutar en {nodo}: {res.text}")
    return res.json().get("output", "")

def asignar_ip(nodo, iface, ip, mascara):
    """Usa el endpoint de la API para asignar una IP manual."""
    res = requests.post(
        f"{BASE_URL}/nodes/{nodo}/interfaces/{iface}/ip",
        json={"addr": ip, "mask": mascara}
    )
    if res.status_code != 200:
        raise RuntimeError(f"Fallo al asignar IP a {nodo}: {res.text}")

def test_n_routers_solucion(n):
    print(f"\n" + "-"*60)
    print(f"[*] Evaluando topología lineal con {n} Router(s) (Motor Propio)...")
    print("-" * 60)

    requests.delete(f"{BASE_URL}/network")
    time.sleep(1)

    for i in range(1, n + 1):
        requests.post(f"{BASE_URL}/nodes", json={"name": f"r{i}", "type": "router"})
    requests.post(f"{BASE_URL}/nodes", json={"name": "host1", "type": "router"})
    requests.post(f"{BASE_URL}/nodes", json={"name": "host2", "type": "router"})

    requests.post(f"{BASE_URL}/links", json={"source": "host1", "target": "r1"})
    for i in range(1, n):
        requests.post(f"{BASE_URL}/links", json={"source": f"r{i}", "target": f"r{i+1}"})
    requests.post(f"{BASE_URL}/links", json={"source": f"r{n}", "target": "host2"})

    # 3. Arranque
    requests.post(f"{BASE_URL}/network/start")

    res = requests.get(f"{BASE_URL}/network")
    for link in res.json().get("links", []):
        s, t = link["source"], link["target"]
        si, ti = link["source_iface"], link["target_iface"]

        if (s == "host1" and t == "r1") or (t == "host1" and s == "r1"):
            asignar_ip("host1", si if s == "host1" else ti, "10.100.1.10", 24)
            asignar_ip("r1", ti if s == "host1" else si, "10.100.1.1", 24)
        elif (s == f"r{n}" and t == "host2") or (t == f"r{n}" and s == "host2"):
            asignar_ip(f"r{n}", si if s == f"r{n}" else ti, "10.100.2.1", 24)
            asignar_ip("host2", ti if s == f"r{n}" else si, "10.100.2.10", 24)
        elif s.startswith("r") and t.startswith("r"):
            idx = int(s[1:]) if int(s[1:]) < int(t[1:]) else int(t[1:])
            asignar_ip(f"r{idx}", si if s == f"r{idx}" else ti, f"10.1.{idx}.1", 24)
            asignar_ip(f"r{idx+1}", ti if s == f"r{idx}" else si, f"10.1.{idx}.2", 24)

    ejecutar_comando_api("host1", ["ip", "route", "replace", "default", "via", "10.100.1.1"])
    ejecutar_comando_api("host2", ["ip", "route", "replace", "default", "via", "10.100.2.1"])

    for i in range(1, n):
        ejecutar_comando_api(f"r{i}", ["ip", "route", "add", "10.100.2.0/24", "via", f"10.1.{i}.2"])
    for i in range(n, 1, -1):
        ejecutar_comando_api(f"r{i}", ["ip", "route", "add", "10.100.1.0/24", "via", f"10.1.{i-1}.1"])

    ejecutar_comando_api("host2", ["ping", "-c", "1", "-W", "1", "10.100.1.10"])
    ejecutar_comando_api("host1", ["sh", "-c", "pkill iperf3 || true"])
    ejecutar_comando_api("host1", ["iperf3", "-s", "-D"])
    time.sleep(1)

    res_iperf = ejecutar_comando_api("host2", ["sh", "-c", "iperf3 -c 10.100.1.10 -t 5 --json || true"])

    try:
        datos = json.loads(res_iperf)
        gbps = datos['end']['sum_received']['bits_per_second'] / 1e9
        print(f"      [+] Rendimiento sostenido: {gbps:.2f} Gbps")
        return gbps
    except Exception as e:
        print(f"      [!] Error procesando iperf3: {e}")
        return 0.0

def run_scaling_suite_solucion():
    print("="*60)
    print("  SUITE DE ESCALABILIDAD L3: MOTOR PROPIO (API)")
    print("="*60)

    resultados = {}
    for routers in range(1, 11):
        try:
            resultados[routers] = test_n_routers_solucion(routers)
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

    requests.delete(f"{BASE_URL}/network")

if __name__ == "__main__":
    run_scaling_suite_solucion()