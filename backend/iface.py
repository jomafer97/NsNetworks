from pyroute2 import IPRoute


class Iface:
    """
    Ofrece una capa de abstracción sobre las interfaces del kernel
    """

    def __init__(self, name: str):
        self.name = name
        self.net_ns = None
        self.addr = None
        self.mask = None
        self.idx = None
        self.state = "down"

    def _get_handle(self):
        """
        Devuelve una tupla: (handler, should_close).
        Si usa el puntero del netns, prohibimos el cierre (False).
        Si crea uno efímero en el host, obligamos a cerrarlo (True).
        """
        if self.net_ns and hasattr(self.net_ns, "get_ipr"):
            return self.net_ns.get_ipr(), False

        return IPRoute(), True

    def get_index(self, ipr=None):
        """Obtiene y cachea el índice numérico de la interfaz en el kernel."""
        if not self.idx:
            close_ipr = False
            if ipr is None:
                ipr, close_ipr = self._get_handle()

            try:
                lookup_result = ipr.link_lookup(ifname=self.name)
                if not lookup_result:
                    raise RuntimeError(f"La interfaz '{self.name}' no existe.")
                self.idx = lookup_result[0]
            finally:
                if close_ipr and ipr:
                    ipr.close()

        return self.idx

    def is_up(self, ipr=None) -> bool:
        """Devuelve True si está UP, False si está DOWN."""
        close_ipr = False
        if ipr is None:
            ipr, close_ipr = self._get_handle()

        try:
            current_idx = self.get_index(ipr=ipr)
            link_info = ipr.get_links(current_idx)

            if not link_info:
                raise RuntimeError(
                    f"No se pudo obtener info de la interfaz {self.name}"
                )

            flags = link_info[0]["flags"]
            return bool(flags & 1)

        except Exception as e:
            print(f"Error consultando el estado de la interfaz '{self.name}': {e}")
            raise
        finally:
            if close_ipr and ipr:
                ipr.close()

    def up(self, ipr=None):
        """Levanta la interfaz si el kernel indica que está apagada."""
        close_ipr = False
        if ipr is None:
            ipr, close_ipr = self._get_handle()

        try:
            if not self.is_up(ipr=ipr):
                current_idx = self.get_index(ipr=ipr)
                ipr.link("set", index=current_idx, state="up")
            self.state = "up"
        except Exception as e:
            print(f"Error al levantar la interfaz '{self.name}': {e}")
            raise
        finally:
            if close_ipr and ipr:
                ipr.close()

    def set_addr(self, addr: str, mask: int, ipr=None):
        close_ipr = False
        if ipr is None:
            ipr, close_ipr = self._get_handle()

        if self.addr:
            self.delete_addr(ipr=ipr)

        try:
            current_idx = self.get_index(ipr=ipr)
            ipr.addr("add", index=current_idx, address=addr, mask=mask)
            self.addr = addr
            self.mask = mask
        except Exception as e:
            print(f"Error al establecer IP en interfaz: {e}")
            raise
        finally:
            if close_ipr and ipr:
                ipr.close()

    def delete_addr(self, ipr=None):
        """
        Elimina la IP actual de la interfaz tanto en el kernel de Linux
        como en la memoria interna de Python.
        """
        if not self.addr or not self.mask:
            return

        close_ipr = False
        if ipr is None:
            ipr, close_ipr = self._get_handle()

        try:
            current_idx = self.get_index(ipr=ipr)
            ipr.addr("delete", index=current_idx, address=self.addr, mask=self.mask)
            self.addr = None
            self.mask = None
        except Exception as e:
            print(f"Error al eliminar IP en interfaz {self.name}: {e}")
            raise
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
            if ipr:
                current_idx = self.get_index(ipr=ipr)
                ipr.link("set", index=current_idx, net_ns_fd=target_net_ns.get_name())
                self.net_ns = target_net_ns
                self.idx = None
                self.state = "down"
                self.addr = None
                self.mask = None
        except Exception as e:
            print(f"Error al mover la interfaz: {e}")
            raise
        finally:
            if close_ipr and ipr:
                ipr.close()

    def delete(self, ipr=None):
        """Elimina la interfaz del sistema."""
        close_ipr = False
        if ipr is None:
            ipr, close_ipr = self._get_handle()

        try:
            current_idx = self.get_index(ipr=ipr)
            ipr.link("del", index=current_idx)

            self.idx = None
            self.state = "down"
            self.net_ns = None
            self.addr = None
        except Exception as e:
            print(f"Error al eliminar la interfaz: {e}")
        finally:
            if close_ipr and ipr:
                ipr.close()
