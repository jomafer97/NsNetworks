from pyroute2 import NetNS, netns
from interface import Interface


class NetworkNamespace:
    def __init__(self, name: str):
        self.name = name
        self.ifaces: dict[str, Interface] = {}

        self._create_namespace()

    def _create_namespace(self):
        """Crea el namespace y levanta la interfaz loopback (lo)."""
        netns.create(self.name)

        try:
            with NetNS(self.name) as ns:
                lo = Interface("lo", net_ns=self.name)
                lo.up(ipr=ns)

                self.add_interface(lo)

        except Exception as e:
            self.cleanup()
            raise RuntimeError(f"Fallo configurando loopback en {self.name}: {e}")

    def add_interface(self, iface: Interface):
        """
        Registra una interfaz física/virtual (ej: veth) en este namespace.
        Nota: Se asume que la interfaz ya ha sido movida a este namespace en el kernel.
        """
        if iface.net_ns != self.name:
            raise ValueError(
                f"Error al añadir la interfaz {iface.name} al netns {self.name}"
            )

        self.ifaces[iface.name] = iface

    def get_interface(self, name: str) -> Interface:
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
