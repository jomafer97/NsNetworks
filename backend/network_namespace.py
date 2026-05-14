from pyroute2 import NetNS, netns
from .iface import Iface


class NetworkNamespace:
    def __init__(self, name: str):
        self.name = name
        self.ipr = None
        self.ifaces: dict[str, Iface] = {}

        self.start()

    def start(self):
        """Crea el namespace y levanta la interfaz loopback (lo)."""
        if self.name in netns.listnetns():
            netns.remove(self.name)

        netns.create(self.name)
        self.ipr = NetNS(self.name)

        try:
            lo = Iface("lo")
            lo.net_ns = self
            lo.up()

        except Exception as e:
            self.cleanup()
            raise RuntimeError(f"Fallo configurando loopback en {self.name}: {e}")

    def attach(self, iface: Iface):
        """
        Registra una interfaz física/virtual en este namespace.
        Si la interfaz vive en otro namespace, la arrastra hacia el actual.
        """
        if iface.net_ns != self:
            iface.attach_netns(self)

        self.ifaces[iface.name] = iface

    def get_Iface(self, name: str) -> Iface:
        """Recupera una interfaz para configurarla."""
        if name not in self.ifaces:
            raise KeyError(
                f"La interfaz {name} no está registrada en el netns {self.name}"
            )
        return self.ifaces[name]

    def get_ifaces(self) -> dict:
        """
        Devuelve un diccionario con las interfaces
        """
        return self.ifaces

    def get_name(self):
        """
        Devuelve el nombre
        """
        return self.name

    def get_ipr(self):
        """
        Devuelve una referencia hacia él
        """
        return self.ipr

    def cleanup(self):
        """Elimina el namespace del sistema."""
        try:
            if self.ipr:
                self.ipr.close()

            netns.remove(self.name)
            print(f"Namespace {self.name} eliminado.")
        except Exception as e:
            print(f"Aviso: No se pudo eliminar el netns {self.name}: {e}")
