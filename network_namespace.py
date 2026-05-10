from pyroute2 import NetNS, IPRoute, netns
import os


class NetworkNamespace:
    def __init__(self, name: str):
        self.name = name
        self._create_namespace()

    def _create_namespace(self):
        """Crea el namespace y levanta la interfaz loopback (lo)."""
        netns.create(self.name)

        try:
            with NetNS(self.name) as ns:
                lo_idx = ns.link_lookup(ifname="lo")[0]
                ns.link("set", index=lo_idx, state="up")
        except Exception as e:
            self.cleanup()
            raise RuntimeError(f"Fallo configurando loopback en {self.name}: {e}")

    def cleanup(self):
        """Elimina el namespace del sistema."""
        try:
            netns.remove(self.name)
            print(f"Namespace {self.name} eliminado.")
        except Exception as e:
            print(f"Aviso: No se pudo eliminar el netns {self.name}: {e}")


class Link:
    def __init__(self, ifaces: tuple):
        """
        Crea un par veth: ifaces[0] <-> ifaces[1]
        """
        self.ifaces = ifaces
        self.ipr = IPRoute()
        self.attached_netns = None
        self.IP = None
        try:
            self.ipr.link(
                "add",
                ifname=self.ifaces[0],
                peer={"ifname": self.ifaces[1]},
                kind="veth",
            )

            idx0 = self.ipr.link_lookup(ifname=self.ifaces[0])
            idx1 = self.ipr.link_lookup(ifname=self.ifaces[1])

            if not idx0 or not idx1:
                raise RuntimeError(
                    "Fallo al obtener índices de las interfaces creadas."
                )

            self.iface_idx = (idx0[0], idx1[0])

        except Exception as e:
            if hasattr(self, "ipr"):
                self.ipr.close()
            raise ConnectionError(f"Error inicializando Link: {e}")

    def _get_handle(self, idx):
        """
        Devuelve el manejador (NetNS o IPRoute) adecuado para la interfaz.
        self.ifaces[idx]
        """
        if self.attached_netns and self.attached_netns[idx]:
            return NetNS(self.attached_netns[idx])
        else:
            if getattr(self.ipr, "closed", True):
                self.ipr = IPRoute()
            return self.ipr

    def attach_link(self, netns_1, netns_2):
        """
        Mueve una de las interfaces del par veth a un namespace específico.
        """
        if getattr(self.ipr, "closed", True):
            self.ipr = IPRoute()

        try:
            self.attached_netns = (netns_1, netns_2)

            if netns_1:
                self.ipr.link("set", index=self.iface_idx[0], net_ns_fd=netns_1)
            if netns_2:
                self.ipr.link("set", index=self.iface_idx[1], net_ns_fd=netns_2)
        except Exception as e:
            print(f"Error al mover la interfaz: {e}")
            raise
        finally:
            self.ipr.close()

    def set_ip(self, ip_1: str, ip_2: str, mask: int = 24):
        """Configura las IPs de los enlaces de forma segura."""
        self.IP = (ip_1, ip_2)

        try:
            if ip_1:
                handler = self._get_handle(0)
                handler.addr("add", index=self.iface_idx[0], address=ip_1, mask=mask)
                if isinstance(handler, NetNS):
                    handler.close()

            if ip_2:
                handler = self._get_handle(1)
                handler.addr("add", index=self.iface_idx[1], address=ip_2, mask=mask)
                if isinstance(handler, NetNS):
                    handler.close()

        except Exception as e:
            print(f"Error configurando IPs: {e}")
            raise

    def up(self):
        """Levanta las interfaces usando 'link' (L2)."""
        try:
            handler = self._get_handle(0)
            handler.link("set", index=self.iface_idx[0], state="up")
            if isinstance(handler, NetNS):
                handler.close()

            handler = self._get_handle(1)
            handler.link("set", index=self.iface_idx[1], state="up")
            if isinstance(handler, NetNS):
                handler.close()

        except Exception as e:
            print(f"Error levantando interfaces: {e}")
            raise

    def cleanup(self):
        """Elimina el enlace asegurando el cierre de sockets de Netlink."""
        try:
            if self.attached_netns:
                for ns_name in self.attached_netns:
                    if os.path.exists(f"/var/run/netns/{ns_name}"):
                        try:
                            with NetNS(ns_name) as ns:
                                ns.link("delete", index=self.iface_idx[0])
                            return
                        except Exception:
                            continue

            if getattr(self.ipr, "closed", True):
                self.ipr = IPRoute()

            self.ipr.link("delete", index=self.iface_idx[0])

        except Exception as e:
            print(f"Cleanup: No se pudo eliminar el enlace: {e}")
        finally:
            if hasattr(self, "ipr"):
                self.ipr.close()
