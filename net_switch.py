from pyroute2 import NetNS, netns
from node import Node


class NetSwitch(Node):
    def __init__(self, name: str, **kwargs):
        """
        Crea un switch virtual (Linux Bridge) dentro de su propio namespace aislado.
        """
        super().__init__(name, kwargs=kwargs)

        with NetNS(self.netns_name) as ns:
            try:
                ns.link("add", ifname=self.name, kind="bridge")

                # Obtenemos su índice DENTRO de este namespace
                self.idx = ns.link_lookup(ifname=self.name)[0]

                # Lo encendemos
                ns.link("set", index=self.idx, state="up")

                # Opcional pero recomendado: Levantar también la loopback del switch
                lo_idx = ns.link_lookup(ifname="lo")[0]
                ns.link("set", index=lo_idx, state="up")
            except Exception as e:
                raise RuntimeError(f"Fallo creando el switch aislado {self.name}: {e}")

    def attach_port(self, host_iface):
        """
        Mueve un cable (veth) desde el host hacia el namespace del switch y lo enchufa.
        """
        # 1. Teletransportamos la interfaz desde el host al namespace del switch
        # (Asumiendo que tu clase Interface tiene el método attach_netns que pulimos antes)
        host_iface.attach_netns(net_ns=self.netns_name)

        # 2. Entramos al namespace del switch para hacer las conexiones locales
        with NetNS(self.netns_name) as ns:
            try:
                # Obtenemos el nuevo índice de la interfaz (los índices cambian al cambiar de netns)
                iface_idx = host_iface.get_index(ipr=ns)

                # Lo conectamos al bridge (master)
                ns.link("set", index=iface_idx, master=self.idx)

                # Y lo encendemos
                ns.link("set", index=iface_idx, state="up")
            except Exception as e:
                raise RuntimeError(
                    f"Fallo conectando {host_iface.name} al switch {self.name}: {e}"
                )
