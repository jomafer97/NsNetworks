from .node import Node
from .link import Link
import json


class Topology:
    """
    Orquestador principal de la red.
    Contiene el inventario completo de nodos y enlaces, gestiona su ciclo de vida.
    """

    def __init__(self, name: str):
        self.name = name
        self.nodes: dict[str, Node] = {}
        self.links: list[Link] = []

    def add_node(self, node: Node) -> Node:
        """Registra un nodo en la topología."""
        if node.name in self.nodes:
            raise ValueError(
                f"[!] Error: El nodo '{node.name}' ya existe en esta topología."
            )

        self.nodes[node.name] = node
        print(f"[*] Nodo añadido a la topología: {node.name}")
        return node

    def add_link(self, node1_name: str, node2_name: str) -> Link:
        """
        Conecta dos nodos existentes en la topología.
        """
        n1 = self.nodes.get(node1_name)
        n2 = self.nodes.get(node2_name)

        if not n1 or not n2:
            raise KeyError(
                f"[!] Error: Ambos nodos deben existir en la topología para conectarlos. ({node1_name}, {node2_name})"
            )

        cable = Link.connect(n1, n2)
        self.links.append(cable)
        return cable

    def start_all(self):
        """Orquesta el arranque secuencial de toda la infraestructura."""
        print(f"\n[>>>] Iniciando topología: {self.name} [>>>]")

        for node in self.nodes.values():
            node.start()

        print(f"[>>>] Topología {self.name} operativa.\n")

    def stop_all(self):
        """Orquesta la destrucción limpia de la infraestructura."""
        print(f"\n[<<<] Destruyendo topología: {self.name} [<<<]")

        for link in self.links:
            link.delete()

        for node in self.nodes.values():
            node.stop()

        print(f"[<<<] Topología {self.name} eliminada por completo.\n")

    def export_to_json(self, filepath: str = "topology_state.json"):
        """
        Genera una radiografía completa de la red en formato JSON.
        """
        data = {
            "topology_name": self.name,
            "nodes": [node.to_dict() for node in self.nodes.values()],
            "links": [link.to_dict() for link in self.links],
        }

        with open(filepath, "w") as f:
            json.dump(data, f, indent=4)

        print(f"\n[*] Estado de la topología exportado correctamente a '{filepath}'")
        return data
