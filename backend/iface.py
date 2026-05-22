import subprocess
from pyroute2 import IPRoute


class Iface:
    """Ofrece una capa de abstracción sobre las interfaces del kernel"""

    def __init__(self, name: str):
        self.name = name
        self.net_ns = None
        self.addr = None
        self.mask = None
        self.idx = None
        self.state = "down"

    def _get_handle(self):
        """Devuelve una referencia a IPRoute"""
        return IPRoute(), True

    def get_index(self, ipr=None):
        """Obtiene y cachea el índice numérico de la interfaz en el host."""
        if self.net_ns:
            return None

        if not self.idx:
            close_ipr = False
            if ipr is None:
                ipr, close_ipr = self._get_handle()
            try:
                res = ipr.link_lookup(ifname=self.name)
                if res:
                    self.idx = res[0]
            finally:
                if close_ipr and ipr:
                    ipr.close()
        return self.idx

    def is_up(self, ipr=None) -> bool:
        """Devuelve True si está UP, False si está DOWN."""
        if self.net_ns:
            res = subprocess.run(
                [
                    "ip",
                    "netns",
                    "exec",
                    self.net_ns.get_name(),
                    "ip",
                    "link",
                    "show",
                    self.name,
                ],
                capture_output=True,
                text=True,
            )
            return ",UP" in res.stdout or "state UP" in res.stdout

        close_ipr = False
        if ipr is None:
            ipr, close_ipr = self._get_handle()
        try:
            current_idx = self.get_index(ipr=ipr)
            if not current_idx:
                return False
            info = ipr.get_links(current_idx)
            return bool(info[0]["flags"] & 1) if info else False
        finally:
            if close_ipr and ipr:
                ipr.close()

    def up(self, ipr=None):
        """Levanta la interfaz."""
        if self.net_ns:
            subprocess.run(
                [
                    "ip",
                    "netns",
                    "exec",
                    self.net_ns.get_name(),
                    "ip",
                    "link",
                    "set",
                    self.name,
                    "up",
                ],
                check=True,
            )
            self.state = "up"
            return

        close_ipr = False
        if ipr is None:
            ipr, close_ipr = self._get_handle()
        try:
            current_idx = self.get_index(ipr=ipr)
            ipr.link("set", index=current_idx, state="up")
            self.state = "up"
        finally:
            if close_ipr and ipr:
                ipr.close()

    def set_addr(self, addr: str, mask: int, ipr=None):
        if self.addr:
            self.delete_addr(ipr=ipr)

        if self.net_ns:
            subprocess.run(
                [
                    "ip",
                    "netns",
                    "exec",
                    self.net_ns.get_name(),
                    "ip",
                    "addr",
                    "add",
                    f"{addr}/{mask}",
                    "dev",
                    self.name,
                ],
                check=True,
            )
            self.addr = addr
            self.mask = mask
            return

        close_ipr = False
        if ipr is None:
            ipr, close_ipr = self._get_handle()
        try:
            current_idx = self.get_index(ipr=ipr)
            ipr.addr("add", index=current_idx, address=addr, mask=mask)
            self.addr = addr
            self.mask = mask
        finally:
            if close_ipr and ipr:
                ipr.close()

    def delete_addr(self, ipr=None):
        if not self.addr or not self.mask:
            return

        if self.net_ns:
            subprocess.run(
                [
                    "ip",
                    "netns",
                    "exec",
                    self.net_ns.get_name(),
                    "ip",
                    "addr",
                    "del",
                    f"{self.addr}/{self.mask}",
                    "dev",
                    self.name,
                ],
                check=False,
            )
            self.addr = None
            self.mask = None
            return

        close_ipr = False
        if ipr is None:
            ipr, close_ipr = self._get_handle()
        try:
            current_idx = self.get_index(ipr=ipr)
            ipr.addr("delete", index=current_idx, address=self.addr, mask=self.mask)
            self.addr = None
            self.mask = None
        finally:
            if close_ipr and ipr:
                ipr.close()

    def attach_netns(self, target_net_ns):
        """
        Asocia un netns a la interfaz
        """
        if target_net_ns == self.net_ns:
            return

        ipr, close_ipr = self._get_handle()

        try:
            current_idx = self.get_index(ipr=ipr)
            ipr.link("set", index=current_idx, net_ns_fd=target_net_ns.get_name())
            self.net_ns = target_net_ns
            self.idx = None
            self.state = "down"
            self.addr = None
            self.mask = None
        finally:
            if close_ipr and ipr:
                ipr.close()

    def delete(self, ipr=None):
        if self.net_ns:
            subprocess.run(
                [
                    "ip",
                    "netns",
                    "exec",
                    self.net_ns.get_name(),
                    "ip",
                    "link",
                    "del",
                    self.name,
                ],
                check=False,
            )
            self.idx = None
            self.state = "down"
            self.net_ns = None
            self.addr = None
            return

        close_ipr = False
        if ipr is None:
            ipr, close_ipr = self._get_handle()
        try:
            current_idx = self.get_index(ipr=ipr)
            if current_idx:
                ipr.link("del", index=current_idx)
            self.idx = None
            self.state = "down"
            self.net_ns = None
            self.addr = None
        finally:
            if close_ipr and ipr:
                ipr.close()
