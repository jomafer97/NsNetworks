from pyroute2 import IPRoute
from interface import Interface


class Link:
    def __init__(self, iface_1: Interface, iface_2: Interface):
        """Crea el par veth físico en el host."""
        self.ifaces = (iface_1, iface_2)
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

    def attach(self, netns_1: str | None = None, netns_2: str | None = None):
        """Mueve los interfaces a sus respectivos namespaces (Capa 1/2)."""
        try:
            with IPRoute() as ipr:
                if netns_1:
                    self.ifaces[0].attach_netns(net_ns=netns_1, ipr=ipr)
                if netns_2:
                    self.ifaces[1].attach_netns(net_ns=netns_2, ipr=ipr)
        except Exception as e:
            print(f"Error distribuyendo Link: {e}")
            raise

    def delete(self):
        """Destruye el cable virtual."""
        try:
            self.ifaces[0].delete()
        except Exception as e:
            print(f"Aviso al borrar el enlace: {e}")
