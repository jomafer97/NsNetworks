from .iface import Iface
from pyroute2 import netns


class NetworkNamespace:
    def __init__(self, name: str):
        self.name = name
        self.ifaces: dict[str, Iface] = {}
        self.start()

    def start(self):
        """Crea el namespace y levanta la interfaz loopback (lo)."""
        if self.name in netns.listnetns():
            netns.remove(self.name)

        netns.create(self.name)

        try:
            lo = Iface("lo")
            lo.netns_name = self.name
            lo.up()
        except Exception as e:
            self.cleanup()
            raise RuntimeError(f"Fallo configurando loopback en {self.name}: {e}")

    def attach(self, iface: Iface):
        if iface.netns_name != self.name:
            iface.attach_netns(self.name)
        self.ifaces[iface.name] = iface

    def remove_iface(self, iface_name: str):
        iface = self.ifaces.pop(iface_name, None)
        if iface:
            iface.delete()

    def get_Iface(self, name: str) -> Iface:
        if name not in self.ifaces:
            raise KeyError(f"La interfaz {name} no está en el netns {self.name}")
        return self.ifaces[name]

    def get_ifaces(self) -> dict[str, Iface]:
        return self.ifaces

    def get_name(self):
        return self.name

    def cleanup(self):
        try:
            netns.remove(self.name)
            print(f"Namespace {self.name} eliminado.")
        except Exception as e:
            print(f"Aviso: No se pudo eliminar el netns {self.name}: {e}")
