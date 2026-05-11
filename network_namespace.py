from pyroute2 import NetNS, netns
from iface import Iface


class NetworkNamespace:
    def __init__(self, name: str):
        self.name = name
        self.ifaces: dict[str, Iface] = {}

        self._create_namespace()

    def _create_namespace(self):
        """Crea el namespace y levanta la interfaz loopback (lo)."""
        netns.create(self.name)

        try:
            with NetNS(self.name) as ns:
                lo = Iface("lo", net_ns=self.name)
                lo.up(ipr=ns)

                self.add_Iface(lo)

        except Exception as e:
            self.cleanup()
            raise RuntimeError(f"Fallo configurando loopback en {self.name}: {e}")

    def add_Iface(self, iface: Iface):
        """
        Registra una interfaz física/virtual en este namespace.
        Si la interfaz vive en otro namespace, la arrastra hacia el actual.
        """
        if iface.net_ns != self.name:
            iface.attach_netns(self.name)

        self.ifaces[iface.name] = iface

    def get_Iface(self, name: str) -> Iface:
        """Recupera una interfaz para configurarla."""
        if name not in self.ifaces:
            raise KeyError(
                f"La interfaz {name} no está registrada en el netns {self.name}"
            )
        return self.ifaces[name]

    def cleanup(self):
        """Elimina el namespace del sistema."""
        try:
            netns.remove(self.name)
            print(f"Namespace {self.name} eliminado.")
        except Exception as e:
            print(f"Aviso: No se pudo eliminar el netns {self.name}: {e}")
