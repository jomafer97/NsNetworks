from .iface import Iface
from .node import Node


class Switch(Node):
    """
    Representa un Switch de Capa 2 utilizando un Linux Bridge.
    Hereda de Node para integrarse en la topología, pero es más ligero
    que un IsolatedNode.
    """

    def __init__(self, name: str):
        super().__init__(name)
        self.bridge = None
        self.start()

    def start(self):
        """
        Inicializa el Bridge interno.
        """
        if self.bridge:
            return

        bridge_name = "br0"
        self.bridge = Iface(bridge_name)

        ns = self.net_ns.get_ipr()

        if ns:
            ns.link("add", ifname=bridge_name, kind="bridge")
            ns.link("set", index=self.bridge.get_index(ipr=ns), br_stp_state=0)
            self.bridge.net_ns = self.net_ns
            self.bridge.up(ns)

    def attach(self, iface: Iface):
        """
        Sobrescribe el método de Node para que, además de mudar
        la interfaz al namespace, la conecte automáticamente al Bridge.
        """
        super().attach(iface)

        if self.bridge:
            ns = self.net_ns.get_ipr()
            if ns:
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

    def delete(self):
        print(f"[*] Destruyendo Switch {self.name}...")
        self.net_ns.cleanup()
