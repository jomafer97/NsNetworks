import os, shutil, signal, abc, subprocess
import c_core
from network_namespace import NetworkNamespace
from iface import Iface


class Node(metaclass=abc.ABCMeta):
    """
    Clase Abstracta Base.
    Define lo que CUALQUIER cosa conectada a la red debe tener.
    """

    def __init__(self, name):
        self.name = name
        self.net_ns = NetworkNamespace(f"netns_{name}")
        self._iface_counter = 0

    @abc.abstractmethod
    def start(self):
        """Arranque del nodo"""
        pass

    @abc.abstractmethod
    def stop(self):
        """Detención del nodo"""
        pass

    def attach(self, iface: Iface):
        """
        Añade una interfaz al netns del nodo
        """
        self.net_ns.attach(iface)

    def get_next_iface_name(self) -> str:
        """
        Genera un nombre dinámico y seguro.
        Comprueba el inventario de red para evitar colisiones con interfaces hardcodeadas.
        """
        safe_name = self.name[:10]
        max_tries = 256
        tries = 0

        while tries < max_tries:
            candidate = f"{safe_name}-e{self._iface_counter}"

            self._iface_counter += 1

            if candidate not in self.net_ns.ifaces:
                return candidate

            tries += 1

        raise RuntimeError(
            f"[!] Error Crítico: El nodo '{self.name}' ha superado el límite "
            f"de {max_tries} intentos o hay un bucle infinito en la asignación."
        )


class IsolatedNode(Node):
    """
    Nodos aislados mediante namespaces, OverlayFS, Cgroups y Apparmor
    """

    BASE_PATH = "/var/lib/net_project"
    CGROUP_ROOT = "/sys/fs/cgroup/net_project"

    def __init__(
        self,
        name: str,
        lower_dir: str = f"{BASE_PATH}/alpine_base",
        apparmor_profile: str = "apparmor-default",
        limits: dict | None = None,
        command: str = "/bin/sleep 3600",
    ):
        super().__init__(name)
        self.apparmor_profile = apparmor_profile
        self.cgroup_path = f"{IsolatedNode.CGROUP_ROOT}/{name}"
        self.cgroup_limits = limits or {}
        self.command = command
        self.pid = None

        self.overlay = {
            "lower": lower_dir,
            "upper": f"{IsolatedNode.BASE_PATH}/nodes/{name}/upper",
            "work": f"{IsolatedNode.BASE_PATH}/nodes/{name}/work",
            "merged": f"{IsolatedNode.BASE_PATH}/nodes/{name}/merged",
        }

    def _setup_fs(self):
        """Prepara las carpetas para el OverlayFS"""
        os.makedirs(self.overlay["upper"], exist_ok=True)
        os.makedirs(self.overlay["work"], exist_ok=True)
        os.makedirs(self.overlay["merged"], exist_ok=True)

    def _apply_cgroups(self):
        """Aplica la jerarquía de Cgroups v2 y los límites"""
        os.makedirs(self.cgroup_path, exist_ok=True)

        with open(f"{IsolatedNode.CGROUP_ROOT}/cgroup.subtree_control", "w") as f:
            f.write("+memory +pids +cpu")

        with open(f"{self.cgroup_path}/cgroup.procs", "w") as f:
            f.write(str(self.pid))

        for key, value in self.cgroup_limits.items():
            path = f"{self.cgroup_path}/{key}"
            if os.path.exists(path):
                with open(path, "w") as f:
                    f.write(str(value))

    def start(self):
        """Inicia el entorno de la siguiente forma:
        - Crea los directorios de OverlayFS y Cgroups
        - Invoca al motor de C para que haga el unshare y pivot_root
        """
        self._setup_fs()

        self.pid = c_core.create_container(
            node_name=self.name,
            lower_dir=self.overlay["lower"],
            upper_dir=self.overlay["upper"],
            work_dir=self.overlay["work"],
            merged_dir=self.overlay["merged"],
            apparmor_profile=self.apparmor_profile,
            netns_name=self.net_ns.name,
            command=self.command,
        )

        if self.pid == -1:
            raise RuntimeError(f"Fallo crítico al levantar el nodo {self.name} en C")

        self._apply_cgroups()

    def exec_in_node(self, command: list[str]):
        """Ejecuta un comando dentro del contexto aislado del nodo"""
        if not self.pid:
            raise RuntimeError(f"El nodo {self.name} no está en ejecución.")

        prefix = ["nsenter", "-t", str(self.pid), "-a", "--"]

        result = subprocess.run(prefix + command, capture_output=True, text=True)

        stdout = result.stdout.strip()
        stderr = result.stderr.strip()

        if result.returncode != 0:
            print(f"[!] Error ejecutando '{' '.join(command)}' en {self.name}:")
            print(f"Salida de error: {stderr}")

        return stdout

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

        self.net_ns.cleanup()

        subprocess.run(
            ["umount", "-l", self.overlay["merged"]], stderr=subprocess.DEVNULL
        )

        node_dir = os.path.dirname(self.overlay["upper"])
        if os.path.exists(node_dir):
            shutil.rmtree(node_dir, ignore_errors=True)

        try:
            if os.path.exists(self.cgroup_path):
                os.rmdir(self.cgroup_path)
        except OSError as e:
            print(f"[*] Aviso: No se pudo eliminar el cgroup de {self.name}: {e}")

        print(f"[*] Nodo {self.name} destruido limpiamente.")
