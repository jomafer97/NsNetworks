from pyroute2 import NetNS, IPRoute


class Interface:
    def __init__(self, name: str, net_ns: str | None = None):
        self.name = name
        self.net_ns = net_ns
        self.addr = None
        self.mask = None
        self.idx = None
        self.state = "down"

    def _get_handle(self):
        """Devuelve el manejador correcto según dónde viva la interfaz."""
        if self.net_ns:
            return NetNS(self.net_ns)

        return IPRoute()

    def get_index(self, ipr: IPRoute | NetNS | None = None):
        """Obtiene y cachea el índice numérico de la interfaz en el kernel."""
        if not self.idx:
            close_ipr = False

            if ipr is None:
                ipr = self._get_handle()
                close_ipr = True

            try:
                lookup_result = ipr.link_lookup(ifname=self.name)

                if not lookup_result:
                    raise RuntimeError(
                        f"La interfaz '{self.name}' no existe en el sistema."
                    )

                self.idx = lookup_result[0]

            finally:
                if close_ipr and ipr is not None:
                    ipr.close()

        return self.idx

    def is_up(self, ipr: IPRoute | NetNS | None = None) -> bool:
        """
        Pregunta al kernel el estado administrativo real de la interfaz.
        Devuelve True si está UP, False si está DOWN.
        """
        close_ipr = False

        if ipr is None:
            ipr = self._get_handle()
            close_ipr = True

        try:
            current_idx = self.get_index(ipr=ipr)

            link_info = ipr.get_links(current_idx)

            if not link_info:
                raise RuntimeError(
                    f"No se pudo obtener info de la interfaz {self.name}"
                )

            msg = link_info[0]

            flags = msg["flags"]
            return bool(flags & 1)

        except Exception as e:
            print(f"Error consultando el estado de la interfaz '{self.name}': {e}")
            raise
        finally:
            if close_ipr:
                ipr.close()

    def up(self, ipr: IPRoute | NetNS | None = None):
        """
        Levanta la interfaz si el kernel indica que está apagada.
        """
        close_ipr = False

        if ipr is None:
            ipr = self._get_handle()
            close_ipr = True

        try:
            if not self.is_up(ipr=ipr):

                current_idx = self.get_index(ipr=ipr)
                ipr.link("set", index=current_idx, state="up")

                self.state = "up"
            else:
                self.state = "up"

        except Exception as e:
            print(f"Error al levantar la interfaz '{self.name}': {e}")
            raise
        finally:
            if close_ipr:
                ipr.close()

    def set_addr(self, addr: str, mask: int, ipr: IPRoute | NetNS | None = None):
        close_ipr = False

        if ipr is None:
            ipr = self._get_handle()
            close_ipr = True

        try:
            current_idx = self.get_index(ipr=ipr)
            ipr.addr("add", index=current_idx, address=addr, mask=mask)
            self.addr = addr
            self.mask = mask
        except Exception as e:
            print(f"Error al establecer IP en interfaz: {e}")
            raise
        finally:
            if close_ipr:
                ipr.close()

    def attach_netns(
        self, net_ns: str | None = None, ipr: IPRoute | NetNS | None = None
    ):
        """
        Asocia un netns a la interfaz
        """
        if net_ns:
            close_ipr = False

            if ipr is None:
                ipr = self._get_handle()
                close_ipr = True

            try:
                current_idx = self.get_index(ipr=ipr)
                ipr.link("set", index=current_idx, net_ns_fd=net_ns)

                self.net_ns = net_ns
                self.idx = None
                self.state = "down"
                self.addr = None
                self.mask = None
            except Exception as e:
                print(f"Error al mover la interfaz: {e}")
                raise
            finally:
                if close_ipr:
                    ipr.close()

    def delete(self, ipr: IPRoute | NetNS | None = None):
        """
        Elimina la interfaz del sistema.
        """
        close_ipr = False
        if ipr is None:
            ipr = self._get_handle()
            close_ipr = True

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
            if close_ipr:
                ipr.close()
