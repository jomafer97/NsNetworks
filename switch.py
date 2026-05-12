from node import Node, Iface
from pyroute2 import NetNS


class Switch(Node):
    """
    Representa un Switch de Capa 2 utilizando un Linux Bridge.
    Hereda de Node para integrarse en la topología, pero es más ligero
    que un IsolatedNode.
    """

    def __init__(self, name: str):
        super().__init__(name)
        self.bridge = None

    def start(self):
        """
        Inicializa el Bridge interno.
        """
        bridge_name = "br0"
        self.bridge = Iface(bridge_name, net_ns=self.net_ns.name)

        with NetNS(self.net_ns.name) as ns:
            ns.link("add", ifname=bridge_name, kind="bridge")
            self.bridge.up(ns)
            ns.link("set", index=self.bridge.get_index(ipr=ns), br_stp_state=0)

        self.net_ns.attach(self.bridge)

    def attach(self, iface: Iface):
        """
        Sobrescribe el método de Node para que, además de mudar
        la interfaz al namespace, la conecte automáticamente al Bridge.
        """
        super().attach(iface)

        if self.bridge:
            with NetNS(self.net_ns.name) as ns:
                ns.link(
                    "set",
                    index=iface.get_index(ipr=ns),
                    master=self.bridge.get_index(ipr=ns),
                    state="up",
                )
        else:
            print(
                f"[*] Aviso: Interfaz {iface.name} añadida, pero el bridge en {self.name} aún no está levantado."
            )

    def stop(self):
        print(f"[*] Destruyendo Switch {self.name}...")
        self.net_ns.cleanup()
