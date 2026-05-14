import ipaddress, os
from node import IsolatedNode
from pyroute2 import netns


class Router(IsolatedNode):
    """Router virtual con Pool de IPs precalculado"""

    _used_ids = set()
    _network = ipaddress.IPv4Network("10.255.0.0/24")
    _available_ids = [str(ip) for ip in reversed(list(_network.hosts()))]

    def __init__(
        self,
        name: str,
        router_id: str | None = None,
        lower_dir: str = f"{IsolatedNode.BASE_PATH}/alpine_base",
        limits: dict | None = None,
    ):
        cmd = (
            "chown -R frr:frr /etc/frr && "
            "/usr/lib/frr/zebra -d -f /etc/frr/frr.conf && "
            "/usr/lib/frr/ospfd -d -f /etc/frr/frr.conf && "
            "tail -f /dev/null"
        )

        super().__init__(
            name,
            lower_dir,
            limits,
            command=cmd,
        )

        if router_id:
            try:
                ipaddress.IPv4Address(router_id)
            except ipaddress.AddressValueError:
                raise ValueError(f"Error: '{router_id}' no es una IPv4 válida.")

            if router_id in Router._used_ids:
                raise ValueError(f"Error: El Router ID '{router_id}' ya está en uso.")

            if router_id in Router._available_ids:
                Router._available_ids.remove(router_id)

            self.router_id = router_id

        else:
            if not Router._available_ids:
                raise OverflowError("Se ha agotado el pool de Router IDs.")

            self.router_id = Router._available_ids.pop()

        Router._used_ids.add(self.router_id)

    def start(self):
        self._write_frr_config()

        super().start()

        self._enable_ip_forwarding()

    def _enable_ip_forwarding(self):
        """
        Habilita el IP Forwarding nativamente haciendo 'setns' desde Python
        para escribir directamente en el /proc/sys virtualizado del contenedor.
        """
        try:
            netns.pushns(self.net_ns.name)

            with open("/proc/sys/net/ipv4/ip_forward", "w") as f:
                f.write("1\n")

        except Exception as e:
            raise RuntimeError(
                f"Fallo nativo al habilitar IP Forwarding en {self.name}: {e}"
            )

        finally:
            try:
                netns.popns()
            except Exception:
                pass

    def _write_frr_config(self):
        """
        Genera los archivos de configuración de FRR y los inyecta en la capa
        de escritura (upper_dir) del contenedor antes de que arranque.
        """
        frr_etc_dir = os.path.join(self.overlay["upper"], "etc", "frr")
        os.makedirs(frr_etc_dir, exist_ok=True)

        frr_conf_path = os.path.join(frr_etc_dir, "frr.conf")

        with open("templates/frr.conf.template", "r") as template_file:
            frr_template = template_file.read()

        frr_config = frr_template.format(
            router_name=self.name, router_id=self.router_id
        )

        with open(frr_conf_path, "w") as f:
            f.write(frr_config)

    def stop(self):
        """Libera el Router ID y elimina el nodo"""
        if hasattr(self, "router_id") and self.router_id in Router._used_ids:
            Router._used_ids.remove(self.router_id)

            if self.router_id.startswith("10.255.0."):
                Router._available_ids.append(self.router_id)

        super().stop()
