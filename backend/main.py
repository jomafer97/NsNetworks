import sys
import shutil
import subprocess
import uvicorn
import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent

INIT_SCRIPT_PATH = PROJECT_ROOT / "scripts" / "init.sh"
BASE_PATH = "/var/lib/net_project"
ALPINE_BASE = f"{BASE_PATH}/alpine_base"
CGROUP_ROOT = "/sys/fs/cgroup"


def check_root_privileges():
    """Verifica que el orquestador se ejecuta con permisos de superusuario."""
    if os.geteuid() != 0:
        print(
            "[!] ERROR CRÍTICO: El orquestador interactúa directamente con el kernel."
        )
        print("[!] Debes ejecutar este script como root (ej. sudo python3 main.py).")
        sys.exit(1)


def check_system_dependencies():
    """Verifica que los binarios necesarios del sistema operativo están instalados."""
    required_tools = ["ip", "nsenter", "mount", "umount"]
    missing = []

    for tool in required_tools:
        if not shutil.which(tool):
            missing.append(tool)

    if missing:
        print(
            f"[!] ERROR CRÍTICO: Faltan dependencias en el sistema host: {', '.join(missing)}"
        )
        print("[!] Instálalas antes de arrancar el orquestador (ej. iproute2, frr).")
        sys.exit(1)


def setup_kernel_environment():
    """Carga módulos del kernel y verifica subsistemas (Cgroups v2)."""
    try:
        subprocess.run(["modprobe", "overlay"], check=True, stderr=subprocess.DEVNULL)
    except subprocess.CalledProcessError:
        print("[!] ERROR CRÍTICO: El módulo del kernel 'overlay' no está disponible.")
        sys.exit(1)

    if not os.path.exists(f"{CGROUP_ROOT}/cgroup.controllers"):
        print("[!] ERROR CRÍTICO: Cgroups v2 no está montado en el host.")
        print("[!] Tu sistema parece usar Cgroups v1 o no lo tiene habilitado.")
        sys.exit(1)


def verify_filesystem_structure():
    """Verifica que la imagen base exista. Si no existe, lanza el instalador."""

    os.makedirs(f"{CGROUP_ROOT}/net_project", exist_ok=True)

    if not Path(ALPINE_BASE).exists():
        print(f"\n[*] El rootfs base no existe en '{ALPINE_BASE}'.")
        print(
            "[*] Parece ser la primera ejecución. Lanzando el instalador (init.sh)..."
        )

        if not INIT_SCRIPT_PATH.exists():
            print(f"[!] ERROR CRÍTICO: No se encuentra '{INIT_SCRIPT_PATH}'.")
            sys.exit(1)

        try:
            subprocess.run(["chmod", "+x", INIT_SCRIPT_PATH], check=True)
            subprocess.run(["bash", INIT_SCRIPT_PATH], cwd=PROJECT_ROOT, check=True)

        except subprocess.CalledProcessError:
            print(
                f"[!] ERROR CRÍTICO: El script de instalación falló. Abortando arranque."
            )
            sys.exit(1)

        print("[+] Entorno base construido correctamente.\n")
    else:
        print("[+] Sistema de archivos Alpine detectado. Omitiendo instalación.")


def main():
    print("=====================================================")
    print("      Iniciando SDN Controller (Motor de Bajo Nivel) ")
    print("=====================================================\n")

    print("[*] 1/4 Comprobando privilegios del sistema...")
    check_root_privileges()

    print("[*] 2/4 Verificando dependencias instaladas...")
    check_system_dependencies()

    print("[*] 3/4 Validando subsistemas del Kernel (OverlayFS, Cgroups v2)...")
    setup_kernel_environment()

    print("[*] 4/4 Verificando sistema de archivos base...")
    verify_filesystem_structure()

    print("\n[+] Entorno verificado con éxito. Arrancando API de FastAPI...\n")

    sys.path.insert(0, str(PROJECT_ROOT))
    uvicorn.run(
        "backend.api:app", host="0.0.0.0", port=8000, log_level="info", reload=False
    )


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n[*] Apagado forzado del orquestador.")
        sys.exit(0)
