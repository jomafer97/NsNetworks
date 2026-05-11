import os, shutil, signal
import mininet_ng_core
from network_namespace import NetworkNamespace, Interface


class Node:
    BASE_PATH = "/var/lib/net_project"
    CGROUP_PATH = "/sys/fs/cgroup/net_project"

    def __init__(
        self,
        name: str,
        lower_dir: str = f"{BASE_PATH}/alpine_base",
        apparmor_profile: str = "apparmor-default",
        limits: dict | None = None,
    ):
        self.name = name
        self.netns = NetworkNamespace(f"netns_{name}")

        self.overlay_dirs = {
            "lower": lower_dir,
            "upper": f"{Node.BASE_PATH}/nodes/{name}/upper",
            "work": f"{Node.BASE_PATH}/nodes/{name}/work",
            "merged": f"{Node.BASE_PATH}/nodes/{name}/merged",
        }

        self.apparmor_profile = apparmor_profile
        self.cgroup_path = f"{Node.CGROUP_PATH}/{name}"
        self.cgroup_limits = limits or {}

        self.pid = None

    def start(self):
        """Inicia el entorno de la siguiente forma:
        - Crea los directorios de OverlayFS y Cgroups
        - Invoca al motor de C para que haga el unshare y pivot_root
        """
        os.makedirs(self.overlay_dirs["upper"], exist_ok=True)
        os.makedirs(self.overlay_dirs["work"], exist_ok=True)
        os.makedirs(self.overlay_dirs["merged"], exist_ok=True)

        self.pid = mininet_ng_core.create_container(
            node_name=self.name,
            lower_dir=self.overlay_dirs["lower"],
            upper_dir=self.overlay_dirs["upper"],
            work_dir=self.overlay_dirs["work"],
            merged_dir=self.overlay_dirs["merged"],
            apparmor_profile=self.apparmor_profile,
            netns_name=self.netns.name,
        )

        if self.pid == -1:
            raise RuntimeError(f"Fallo crítico al levantar el nodo {self.name} en C")

        print(f"[*] Nodo {self.name} levantado de forma aislada. PID: {self.pid}")

    def add_interface(self, iface: Interface):
        """
        Añade una interfaz al netns del nodo
        """
        self.netns.add_interface(iface)

    def stop(self):
        """Elimina el nodo:
        - mata el proceso
        - Desmonta el OverlayFs y limpia directorios temporales
        - Elimina directorio de Cgroups
        """
        print(f"[*] Deteniendo nodo {self.name}...")

        if self.pid:
            try:
                os.kill(self.pid, signal.SIGKILL)
                os.waitpid(self.pid, 0)
            except (ProcessLookupError, ChildProcessError):
                pass

        self.netns.cleanup()

        shutil.rmtree(self.overlay_dirs["upper"], ignore_errors=True)
        shutil.rmtree(self.overlay_dirs["work"], ignore_errors=True)
        shutil.rmtree(self.overlay_dirs["merged"], ignore_errors=True)

        try:
            if os.path.exists(self.cgroup_path):
                os.rmdir(self.cgroup_path)
        except OSError as e:
            print(f"[*] Aviso: No se pudo eliminar el cgroup de {self.name}: {e}")

        print(f"[*] Nodo {self.name} destruido limpiamente.")
