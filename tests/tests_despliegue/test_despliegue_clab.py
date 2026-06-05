import subprocess
import time
import sys
import os


def generate_yaml(n):
    filename = f"anillo-{n}.yaml"
    with open(filename, "w") as f:
        f.write(f"name: test-anillo-{n}\n")
        f.write("topology:\n  nodes:\n")
        for i in range(1, n + 1):
            f.write(
                f"    r{i}:\n      kind: linux\n      image: frrouting/frr:latest\n"
            )

        f.write("\n  links:\n")
        f.write('    - endpoints: ["r1:eth1", "r2:eth1"]\n')
        for i in range(2, n):
            f.write(f'    - endpoints: ["r{i}:eth2", "r{i+1}:eth1"]\n')
        f.write(f'    - endpoints: ["r{n}:eth2", "r1:eth2"]\n')
    return filename


def measure_real_ram():
    """Mide Cgroups (Contenedor) + RSS (Containerd-Shim)."""
    print("[*] 3. Rastreando procesos en el Kernel para medir RAM real...")
    time.sleep(4)

    try:
        res = subprocess.run(
            [
                "sudo",
                "docker",
                "ps",
                "-q",
                "--no-trunc",
                "--filter",
                "name=clab-test-anillo",
            ],
            capture_output=True,
            text=True,
            check=True,
        )
        container_ids = res.stdout.strip().split("\n")

        total_cgroup_mb = 0.0
        total_shim_mb = 0.0
        count = 0

        for cid in container_ids:
            if not cid:
                continue

            cgroup_path = (
                f"/sys/fs/cgroup/system.slice/docker-{cid}.scope/memory.current"
            )
            alt_path = f"/sys/fs/cgroup/docker/{cid}/memory.current"
            path_to_read = cgroup_path if os.path.exists(cgroup_path) else alt_path

            try:
                with open(path_to_read, "r") as f:
                    cgroup_mb = int(f.read().strip()) / (1024 * 1024)
                    total_cgroup_mb += cgroup_mb
            except FileNotFoundError:
                continue

            try:
                pgrep_res = subprocess.run(
                    ["pgrep", "-f", f"containerd-shim.*{cid}"],
                    capture_output=True,
                    text=True,
                )
                pid = pgrep_res.stdout.strip().split("\n")[0]

                if pid:
                    ps_res = subprocess.run(
                        ["ps", "-o", "rss=", "-p", pid], capture_output=True, text=True
                    )
                    rss_kb = int(ps_res.stdout.strip())
                    total_shim_mb += rss_kb / 1024
            except Exception:
                pass

            count += 1

        if count > 0:
            avg_cgroup = total_cgroup_mb / count
            avg_shim = total_shim_mb / count
            avg_total = avg_cgroup + avg_shim

            print("\n" + "=" * 55)
            print("      RESULTADOS EMPÍRICOS DE RAM (CONTAINERLAB)     ")
            print("=" * 55)
            print(f"[+] Nodos analizados:          {count}")
            print(f"[+] RAM Media Contenedor:      {avg_cgroup:.2f} MB")
            print(f"[+] RAM Media Peaje (Shim):    {avg_shim:.2f} MB")
            print("-" * 55)
            print(f"[!] COSTE REAL POR NODO:       {avg_total:.2f} MB")
            print(f"[!] COSTE TOTAL ({count} nodos): {avg_total * count:.2f} MB")
            print("=" * 55 + "\n")

    except Exception as e:
        print(f"[!] Error midiendo la RAM: {e}")


def run_clab_suite(node_counts, workers=2):
    print("==================================================")
    print("  SUITE AUTOMATIZADA: BENCHMARK CONTAINERLAB (L3)")
    print("==================================================\n")

    results = {}

    for n in node_counts:
        print(f"\n[*] --- INICIANDO CICLO PARA {n} ROUTERS ---")
        yaml_file = generate_yaml(n)

        print("[*] 1. Preparando entorno Docker...")
        subprocess.run(
            ["sudo", "docker", "system", "prune", "-f"], stdout=subprocess.DEVNULL
        )

        print(f"[*] 2. Desplegando {n} nodos (max-workers={workers})...")
        start_time = time.perf_counter()

        try:
            subprocess.run(
                [
                    "sudo",
                    "clab",
                    "deploy",
                    "-t",
                    yaml_file,
                    "--max-workers",
                    str(workers),
                ],
                check=True,
            )
            deploy_time = time.perf_counter() - start_time
            results[n] = f"{deploy_time:.4f} s"
            print(f"\n    [+] Despliegue completado en {deploy_time:.4f} segundos")

            measure_real_ram()

        except subprocess.CalledProcessError:
            results[n] = "Fallo de Despliegue"
            print(f"\n    [!] ERROR: Containerlab falló en el despliegue.")

        print("[*] 4. Destruyendo topología...")
        subprocess.run(["sudo", "clab", "destroy", "-t", yaml_file, "--cleanup"])

        if os.path.exists(yaml_file):
            os.remove(yaml_file)

        print("[*] Pausa de seguridad antes del siguiente ciclo...")
        time.sleep(5)

    print("\n" + "=" * 50)
    print("                 RESUMEN FINAL DE TIEMPOS         ")
    print("=" * 50)
    for n, t in results.items():
        print(f"[*] {n} Routers: {t}")
    print("=" * 50 + "\n")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        counts = [int(x) for x in sys.argv[1:] if x.isdigit()]
    else:
        counts = [10, 20]

    run_clab_suite(counts, workers=7)
