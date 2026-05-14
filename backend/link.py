from .iface import Iface
from .node import Node
from pyroute2 import IPRoute


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

    def __iter__(self):
        """
        Permite iterar directamente sobre el objeto Link para obtener sus interfaces.
        """
        return iter(self.ifaces)

    @classmethod
    def connect(cls, node_1, node_2):
        """
        Conecta dos nodos automáticamente.
        Pide a cada nodo su siguiente nombre disponible, instancia el cable
        y realiza el attach delegando en los namespaces correspondientes.
        """
        name_1 = node_1.get_next_iface_name()
        name_2 = node_2.get_next_iface_name()

        cable = cls(name_1, name_2)

        cable.attach(node_1, node_2)

        for iface in cable:
            iface.up()

        print(
            f"[*] Enlace dinámico creado: {node_1.name}({name_1}) <---> {node_2.name}({name_2})"
        )
        return cable

    def to_dict(self):
        """Devuelve la representación del enlace."""
        return {
            "source": self.ifaces[0].name.split("-")[0],
            "target": self.ifaces[1].name.split("-")[0],
            "source_iface": self.ifaces[0].name,
            "target_iface": self.ifaces[1].name,
        }
