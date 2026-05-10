import os, sys, subprocess
import mininet_ng_core
from pyroute2 import NetNS, IPRoute

PROJECT_NAME = "mininet_ng"


class Node:
    def __init__(self, name, **kwargs):
        # Name
        self.name = name

        # Network Namespace
        self.netns_name = f"netns_{name}"
        self.netns = None

        # Mount Namespace (OverlayFS)
        base_path = f"/var/lib/{PROJECT_NAME}"
        self.overlay_dirs = {
            "lower": kwargs.get("lower_dir", f"{base_path}/alpine_base"),
            "upper": f"{base_path}/nodes/{name}/upper",
            "work": f"{base_path}/nodes/{name}/work",
            "merged": f"{base_path}/nodes/{name}/merged",
        }

        # AppArmor Profile
        self.apparmor_profile = kwargs.get("apparmor", "apparmor-default")

        # Cgroups v2
        self.cgroup_path = f"/sys/fs/cgroup/{PROJECT_NAME}/{name}"
        self.cgroup_limits = kwargs.get("limits", {})

        # Status Control
        self.pid = None

    def start(self):
        """Inicia el entorno de la siguiente forma:
        - Crea los directorios de OverlayFS y Cgroups
        - Invoca al motor de C para que haga el unshare y pivot_root
        """
        self.pid = mininet_ng_core.create_container(
            node_name=self.name,
            merged_dir=self.overlay_dirs["merged"],
            lower_dir=self.overlay_dirs["lower"],
            upper_dir=self.overlay_dirs["upper"],
            work_dir=self.overlay_dirs["work"],
            apparmor_profile=self.apparmor_profile,
            netns_name=self.netns_name,
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
