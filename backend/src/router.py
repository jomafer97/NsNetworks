import ipaddress, os, json
from .node import IsolatedNode
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
        cmd = """
chown -R frr:frr /etc/frr || exit 1
sed -i 's/ospfd=no/ospfd=yes/g' /etc/frr/daemons
/usr/lib/frr/frrinit.sh start
tail -f /dev/null
"""

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

    def delete(self):
        """Libera el Router ID y elimina el nodo"""
        if hasattr(self, "router_id") and self.router_id in Router._used_ids:
            Router._used_ids.remove(self.router_id)

            if self.router_id.startswith("10.255.0."):
                Router._available_ids.append(self.router_id)

        super().delete()

    def get_ospf_neighbors(self) -> dict:
        """
        Obtiene los vecinos OSPF del router en formato JSON.
        """
        try:
            neighbors = self.exec_in_node(["vtysh", "-c", "show ip ospf neighbor json"])
            return json.loads(neighbors) if neighbors else {}
        except Exception as e:
            print(f"Error obteniendo vecinos OSPF en {self.name}: {e}")
            return {}

    def get_ospf_interfaces(self) -> dict:
        """
        Obtiene las interfaces configuradas con OSPF en formato JSON
        """
        try:
            interfaces = self.exec_in_node(
                ["vtysh", "-c", "show ip ospf interface json"]
            )
            return json.loads(interfaces) if interfaces else {}
        except Exception as e:
            print(f"Error obteniendo interfaces OSPF en {self.name}: {e}")
            return {}

    def get_routing_table(self) -> dict:
        """
        Obtiene la tabla de rutas IP general.
        """
        try:
            routing_table = self.exec_in_node(["vtysh", "-c", "show ip route json"])
            return json.loads(routing_table) if routing_table else {}
        except Exception as e:
            print(f"Error obteniendo tabla de rutas en {self.name}: {e}")
            return {}

    def get_ospf_border_routers(self):
        """Obtiene los Border Routers (ASBR/ABR) de OSPF."""
        try:
            border_routers = self.exec_in_node(
                ["vtysh", "-c", "show ip ospf border-routers json"]
            )
            return json.loads(border_routers) if border_routers else {}
        except Exception as e:
            print(f"Error obteniendo border-routers en {self.name}: {e}")
            return {}

    def get_running_config(self) -> str:
        """Obtiene la configuración actual del router limpia de cabeceras."""
        try:
            conf = self.exec_in_node(["vtysh", "-c", "show running-config"])
            if not conf:
                return "! Configuración vacía o router apagado"

            marker = "Current configuration:"
            if marker in conf:
                conf = conf.split(marker, 1)[1].lstrip()
            elif "frr version" in conf:
                conf = conf[conf.find("frr version") :]

            return conf
        except Exception as e:
            print(f"Error obteniendo running-config en {self.name}: {e}")
            return f"! Error obteniendo configuración: {e}"

    def set_running_config(self, config_text: str):
        """
        Inyecta la configuración y recarga los demonios en caliente
        calculando el diff, sin tirar las adyacencias OSPF.
        """
        if not self.pid:
            raise RuntimeError(
                f"El nodo {self.name} debe estar encendido para reconfigurarlo."
            )

        if not config_text.endswith("\n"):
            config_text += "\n"

        temp_conf = "/tmp/new_frr.conf"

        self.exec_in_node(["sh", "-c", f"cat > {temp_conf}"], input_text=config_text)
        self.exec_in_node(["chown", "frr:frr", temp_conf])
        self.exec_in_node(["sed", "-i", "s/ospfd=no/ospfd=yes/g", "/etc/frr/daemons"])

        reload_cmd = ["/usr/lib/frr/frr-reload.py", "--reload", temp_conf]

        try:
            output = self.exec_in_node(reload_cmd)

        except RuntimeError as e:
            self.exec_in_node(["rm", "-f", temp_conf])

            return {
                "status": "error",
                "message": f"Error de sintaxis en FRR. Cambios revertidos.\nDetalles: {str(e)}",
            }

        self.exec_in_node(["mv", temp_conf, "/etc/frr/frr.conf"])

        return {
            "status": "success",
            "message": "Configuración aplicada correctamente sin cortes en OSPF.",
        }
