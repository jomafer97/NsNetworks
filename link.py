from pyroute2 import IPRoute
from network_namespace import Interface
from node import Node


class Link:
    def __init__(self, iface_1: Interface, iface_2: Interface):
        """Crea el par veth físico en el host."""
        self.ifaces: tuple[Interface, Interface] = (iface_1, iface_2)

        try:
            with IPRoute() as ipr:
                ipr.link(
                    "add",
                    ifname=self.ifaces[0].name,
                    peer={"ifname": self.ifaces[1].name},
                    kind="veth",
                )
        except Exception as e:
            print(f"Error creando Link {iface_1.name}-{iface_2.name}: {e}")
            raise

    def attach(
        self,
        node_1: Node | None = None,
        node_2: Node | None = None,
    ):
        """Conecta dos nodos con el enlace"""
        try:
            if node_1:
                node_1.add_interface(self.ifaces[0])
            if node_2:
                node_2.add_interface(self.ifaces[1])
        except Exception as e:
            print(f"Error distribuyendo Link: {e}")
            raise

    def delete(self):
        """Destruye el cable virtual."""
        try:
            self.ifaces[0].delete()
        except Exception as e:
            print(f"Aviso al borrar el enlace: {e}")
