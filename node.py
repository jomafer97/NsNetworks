import os, sys, subprocess
import mininet_ng_core
from network_namespace import NetworkNamespace


class Node:
    BASE_PATH = "/var/lib/net_project"
    CGROUP_PATH = "/sys/fs/cgroup/net_project"

    def __init__(self, name, **kwargs):
        self.name = name
        self.netns = NetworkNamespace(f"netns_{name}")

        self.overlay_dirs = {
            "lower": kwargs.get("lower_dir", f"{Node.BASE_PATH}/alpine_base"),
            "upper": f"{Node.BASE_PATH}/nodes/{name}/upper",
            "work": f"{Node.BASE_PATH}/nodes/{name}/work",
            "merged": f"{Node.BASE_PATH}/nodes/{name}/merged",
        }

        self.apparmor_profile = kwargs.get("apparmor", "apparmor-default")

        self.cgroup_path = f"{Node.CGROUP_PATH}/{name}"
        self.cgroup_limits = kwargs.get("limits", {})

        self.pid = None

    def start(self):
        """Inicia el entorno de la siguiente forma:
        - Crea los directorios de OverlayFS y Cgroups
        - Invoca al motor de C para que haga el unshare y pivot_root
        """
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

    def stop(self):
        """Elimina el nodo:
        - mata el proceso
        - Desmonta el OverlayFs y limpia directorios temporales
        - Elimina directorio de Cgroups
        """
