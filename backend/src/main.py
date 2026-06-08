import sys
import shutil
import subprocess
import uvicorn
import os
from pathlib import Path

SRC_DIR = Path(__file__).resolve().parent
BACKEND_DIR = SRC_DIR.parent

INIT_SCRIPT_PATH = SRC_DIR / "scripts" / "init.sh"
BASE_PATH = "/var/lib/net_project"
ALPINE_BASE = f"{BASE_PATH}/alpine_base"
CGROUP_ROOT = "/sys/fs/cgroup"


def check_root_privileges():
    if os.geteuid() != 0:
        print("[!] ERROR CRÍTICO: Debes ejecutar este script como root.")
        sys.exit(1)


def check_system_dependencies():
    required_tools = ["ip", "nsenter", "mount", "umount"]
    missing = [tool for tool in required_tools if not shutil.which(tool)]

    if missing:
        print(
            f"[!] ERROR CRÍTICO: Faltan dependencias: {', '.join(missing)}"
        )
        sys.exit(1)


def setup_kernel_environment():
    try:
        subprocess.run(
            ["modprobe", "overlay"],
            check=True,
            stderr=subprocess.DEVNULL,
        )
    except subprocess.CalledProcessError:
        print("[!] ERROR CRÍTICO: El módulo overlay no está disponible.")
        sys.exit(1)

    if not os.path.exists(f"{CGROUP_ROOT}/cgroup.controllers"):
        print("[!] ERROR CRÍTICO: Cgroups v2 no está montado.")
        sys.exit(1)


def verify_filesystem_structure():
    os.makedirs(f"{CGROUP_ROOT}/net_project", exist_ok=True)

    if not Path(ALPINE_BASE).exists():
        print(f"\n[*] El rootfs base no existe en '{ALPINE_BASE}'.")
        print("[*] Lanzando instalador...")

        if not INIT_SCRIPT_PATH.exists():
            print(f"[!] ERROR CRÍTICO: No existe '{INIT_SCRIPT_PATH}'.")
            sys.exit(1)

        try:
            subprocess.run(["chmod", "+x", str(INIT_SCRIPT_PATH)], check=True)
            subprocess.run(
                ["bash", str(INIT_SCRIPT_PATH)],
                cwd=BACKEND_DIR,
                check=True,
            )

        except subprocess.CalledProcessError:
            print("[!] ERROR CRÍTICO: init.sh falló.")
            sys.exit(1)

        print("[+] Entorno base construido correctamente.\n")
    else:
        print("[+] Sistema de archivos Alpine detectado.")


def main():
    print("=====================================================")
    print("      Iniciando SDN Controller")
    print("=====================================================\n")

    print("[*] 1/4 Comprobando privilegios...")
    check_root_privileges()

    print("[*] 2/4 Verificando dependencias...")
    check_system_dependencies()

    print("[*] 3/4 Validando Kernel...")
    setup_kernel_environment()

    print("[*] 4/4 Verificando filesystem...")
    verify_filesystem_structure()

    print("\n[+] Entorno verificado con éxito. Arrancando API...\n")

    sys.path.insert(0, str(BACKEND_DIR))

    uvicorn.run(
        "src.api:app",
        host="0.0.0.0",
        port=8000,
        log_level="info",
        reload=False,
    )


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n[*] Apagado forzado.")
        sys.exit(0)