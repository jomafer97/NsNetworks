import os, shutil, signal, abc, subprocess
import c_core
from .network_namespace import NetworkNamespace
from .iface import Iface


class Node(metaclass=abc.ABCMeta):
    """
    Clase Abstracta Base.
    Define lo que CUALQUIER cosa conectada a la red debe tener.
    """

    def __init__(self, name):
        self.name = name
        self.net_ns: NetworkNamespace = NetworkNamespace(f"netns_{name}")
        self._iface_counter = 0

    def get_name(self):
        return self.name

    @abc.abstractmethod
    def start(self):
        """Arranque del nodo"""
        pass

    @abc.abstractmethod
    def delete(self):
        """Detención del nodo"""
        pass

    def attach(self, iface: Iface):
        """
        Añade una interfaz al netns del nodo
        """
        self.net_ns.attach(iface)

    def get_ifaces(self):
        """
        Devuelve el diccionario de interfaces
        """
        return self.net_ns.get_ifaces()

    def remove_iface(self, iface_name: str):
        """
        Elimina una interfaz del nodo
        """
        self.net_ns.remove_iface(iface_name)

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

    def to_dict(self) -> dict:
        serialized_interfaces = []

        for iface_obj in self.get_ifaces().values():
            ip_cidr = f"{iface_obj.addr}/{iface_obj.mask}" if iface_obj.addr else None

            serialized_interfaces.append(
                {"name": iface_obj.name, "ip": ip_cidr, "state": iface_obj.state}
            )

        return {
            "name": self.name,
            "type": self.__class__.__name__,
            "interfaces": serialized_interfaces,
        }


class IsolatedNode(Node):
    """
    Nodos aislados mediante namespaces, OverlayFS y Cgroups
    """

    BASE_PATH = "/var/lib/net_project"
    CGROUP_ROOT = "/sys/fs/cgroup/net_project"

    def __init__(
        self,
        name: str,
        lower_dir: str = f"{BASE_PATH}/alpine_base",
        limits: dict | None = None,
        command: str = "/bin/sleep 3600",
    ):
        super().__init__(name)
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

    def set_cgroups(self, new_limits: dict):
        """
        Actualiza los cgroups en tiempo de ejecución.
        Si un límite previo no está en el nuevo diccionario, se resetea a su valor por defecto (ilimitado).
        """
        keys_to_reset = set(self.cgroup_limits.keys()) - set(new_limits.keys())
        self.cgroup_limits = new_limits
        self._apply_cgroups(keys_to_reset)

    def _apply_cgroups(self, keys_to_reset: set | None = None):
        """Aplica la jerarquía de Cgroups v2 y los límites"""
        os.makedirs(self.cgroup_path, exist_ok=True)

        with open(f"{IsolatedNode.CGROUP_ROOT}/cgroup.subtree_control", "w") as f:
            f.write("+memory +pids +cpu")

        for key, value in self.cgroup_limits.items():
            path = f"{self.cgroup_path}/{key}"
            if os.path.exists(path):
                with open(path, "w") as f:
                    f.write(str(value))

        if keys_to_reset:
            for key in keys_to_reset:
                path = f"{self.cgroup_path}/{key}"
                if os.path.exists(path):
                    with open(path, "w") as f:
                        f.write("max")

    def start(self):
        """Inicia el entorno de la siguiente forma:
        - Crea los directorios de OverlayFS y Cgroups
        - Invoca al motor de C para que haga el unshare y pivot_root
        """
        self._setup_fs()

        self._apply_cgroups()

        self.pid = c_core.create_container(
            node_name=self.name,
            lower_dir=self.overlay["lower"],
            upper_dir=self.overlay["upper"],
            work_dir=self.overlay["work"],
            merged_dir=self.overlay["merged"],
            netns_name=self.net_ns.name,
            command=self.command,
            cgroup_path=self.cgroup_path,
        )

        if self.pid == -1:
            raise RuntimeError(f"Fallo crítico al levantar el nodo {self.name} en C")

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

    def delete(self):
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

    def get_cgroups_for_frontend(self) -> dict:
        """
        Parsea el diccionario interno de cgroups a formato legible por React.
        Usa validación estricta para evitar caídas de la API.
        """
        res: dict[str, int | None] = {"cpu": None, "ram": None}

        mem_max = self.cgroup_limits.get("memory.max")

        if mem_max is not None:
            mem_str = str(mem_max).strip()
            if mem_str.isdigit():
                res["ram"] = int(mem_str) // 1048576

        cpu_max = self.cgroup_limits.get("cpu.max")

        if cpu_max is not None:
            cpu_str = str(cpu_max).strip()
            parts = cpu_str.split()

            if len(parts) == 2 and parts[0].isdigit() and parts[1].isdigit():
                quota = int(parts[0])
                period = int(parts[1])

                if period > 0:
                    res["cpu"] = int((quota / period) * 100)
        return res

    def to_dict(self) -> dict:
        data = super().to_dict()

        data["status"] = "UP" if self.pid else "DOWN"
        data["pid"] = self.pid
        data["cgroups"] = self.get_cgroups_for_frontend()
        return data
