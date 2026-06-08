import subprocess
from .iface import Iface
from .node import Node


class Switch(Node):
    """
    Representa un Switch de Capa 2.
    """

    def __init__(self, name: str):
        super().__init__(name)
        self.bridge = None
        self.start()

    def start(self):
        """
        Inicializa el Bridge interno mediante comandos nativos del kernel
        para evitar bloqueos de hilos (deadlocks) en FastAPI.
        """
        if self.bridge:
            return

        bridge_name = "br0"
        self.bridge = Iface(bridge_name)
        ns_name = self.net_ns.get_name()

        subprocess.run(
            [
                "ip",
                "netns",
                "exec",
                ns_name,
                "ip",
                "link",
                "add",
                "name",
                bridge_name,
                "type",
                "bridge",
                "stp_state",
                "0",
            ],
            check=True,
        )

        self.bridge.netns_name = ns_name
        self.bridge.up()

    def attach(self, iface: Iface):
        """
        Sobrescribe el método de Node para que, además de mudar
        la interfaz al namespace, la conecte automáticamente al Bridge.
        """
        super().attach(iface)

        if self.bridge:
            ns_name = self.net_ns.get_name()

            subprocess.run(
                [
                    "ip",
                    "netns",
                    "exec",
                    ns_name,
                    "ip",
                    "link",
                    "set",
                    iface.name,
                    "master",
                    self.bridge.name,
                ],
                check=True,
            )

            subprocess.run(
                ["ip", "netns", "exec", ns_name, "ip", "link", "set", iface.name, "up"],
                check=True,
            )
        else:
            print(
                f"[*] Aviso: Interfaz {iface.name} añadida, pero el bridge en {self.name} aún no está levantado."
            )

    def delete(self):
        print(f"[*] Destruyendo Switch {self.name}...")
        self.net_ns.cleanup()

    def to_dict(self) -> dict:
        data = super().to_dict()
        data["status"] = "UP" if self.bridge else "DOWN"
        return data
