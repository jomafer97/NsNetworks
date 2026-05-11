from pyroute2 import IPRoute
from network_namespace import Iface
from node import Node


class Link:
    """
    Clase que representa un cable virtual entre dos interfaces
    """

    def __init__(self, name_1: str, name_2: str):
        """Crea el par veth físico en el host."""
        self.ifaces: tuple[Iface, Iface] = (Iface(name_1), Iface(name_2))

        try:
            with IPRoute() as ipr:
                ipr.link(
                    "add",
                    ifname=self.ifaces[0].name,
                    peer={"ifname": self.ifaces[1].name},
                    kind="veth",
                )
        except Exception as e:
            print(f"Error creando Link {name_1}-{name_2}: {e}")
            raise

    def attach(
        self,
        node_1: Node | None = None,
        node_2: Node | None = None,
    ):
        """Conecta dos nodos con el enlace"""
        try:
            if node_1:
                node_1.attach(self.ifaces[0])
            if node_2:
                node_2.attach(self.ifaces[1])
        except Exception as e:
            print(f"Error distribuyendo Link: {e}")
            raise

    def delete(self):
        """Destruye el cable virtual."""
        try:
            self.ifaces[0].delete()
        except Exception as e:
            print(f"Aviso al borrar el enlace: {e}")
