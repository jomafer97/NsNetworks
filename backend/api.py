from contextlib import asynccontextmanager
import threading
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from .topology import Topology
from .router import Router
from .switch import Switch

current_topology = None


def start_net():
    """Inicia la topología"""
    global current_topology
    current_topology = Topology("API-Core")


# --- EL CONTROLADOR DE CICLO DE VIDA ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    net_thread = threading.Thread(target=start_net, daemon=True)
    net_thread.start()

    yield

    if current_topology:
        print("\n[*] Apagando servidor, destruyendo topología...")
        current_topology.delete_all()


app = FastAPI(title="Topology API", version="1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class NodeCreate(BaseModel):
    name: str
    type: str


class LinkCreate(BaseModel):
    source: str
    target: str


class IPAssignment(BaseModel):
    addr: str
    mask: int


@app.get("/api/v1/network", tags=["Network"])
def get_network_state():
    """Devuelve el estado completo del grafo (Nodos y Enlaces)."""
    if not current_topology:
        raise HTTPException(status_code=503, detail="El motor no está inicializado")
    return current_topology.export_to_json("topology.json")


@app.post("/api/v1/nodes", status_code=status.HTTP_201_CREATED, tags=["Nodes"])
def create_node(node: NodeCreate):
    """Instancia un nuevo nodo en el kernel y lo conecta al switch principal."""
    if not current_topology:
        raise HTTPException(status_code=503, detail="El motor no está inicializado")

    if node.name in current_topology.nodes:
        raise HTTPException(
            status_code=400, detail=f"El nodo '{node.name}' ya existe en la red."
        )

    try:
        if node.type.lower() == "router":
            new_node = Router(node.name)
        elif node.type.lower() == "switch":
            new_node = Switch(node.name)
        else:
            raise HTTPException(
                status_code=400,
                detail="Tipo de nodo no soportado. Usa 'router' o 'switch'.",
            )

        current_topology.add_node(new_node)

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Fallo interno del motor: {str(e)}"
        )


@app.post(
    "/api/v1/nodes/{node_name}/start", status_code=status.HTTP_200_OK, tags=["Nodes"]
)
def start_node(node_name: str):
    global current_topology
    if not current_topology:
        raise HTTPException(
            status_code=404, detail="La red no se encuentra inicializada"
        )
    if node_name not in current_topology.nodes:
        raise HTTPException(status_code=404, detail=f"El nodo '{node_name}' no existe.")

    try:
        current_topology.start_node(node_name)
        return {"message": f"Nodo {node_name} arrancado."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete(
    "/api/v1/nodes/{node_name}", status_code=status.HTTP_204_NO_CONTENT, tags=["Nodes"]
)
def delete_node(node_name: str):
    global current_topology
    if not current_topology:
        raise HTTPException(
            status_code=404, detail="La red no se encuentra inicializada"
        )
    if node_name not in current_topology.nodes:
        raise HTTPException(status_code=404, detail=f"El nodo '{node_name}' no existe.")

    try:
        current_topology.delete_node(node_name)
        return
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/links", status_code=status.HTTP_201_CREATED, tags=["Links"])
def create_link(link: LinkCreate):
    """Conecta dos nodos existentes mediante un cable veth."""
    global current_topology
    if not current_topology:
        raise HTTPException(
            status_code=404, detail="La red no se encuentra inicializada"
        )
    if link.source not in current_topology.nodes:
        raise HTTPException(
            status_code=404, detail=f"El nodo '{link.source}' no existe."
        )
    if link.target not in current_topology.nodes:
        raise HTTPException(
            status_code=404, detail=f"El nodo '{link.target}' no existe."
        )

    try:
        current_topology.add_link(node1_name=link.source, node2_name=link.target)
        return {"message": "Enlace creado exitosamente"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete(
    "/api/v1/links/{link_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["Links"]
)
def delete_link(link_id: str):
    """Destruye un cable virtual a partir de su ID único."""
    global current_topology
    if not current_topology:
        raise HTTPException(status_code=503, detail="La red no está inicializada")

    try:
        current_topology.delete_link(link_id)
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Fallo del kernel al borrar enlace: {str(e)}"
        )


@app.post(
    "/api/v1/nodes/{node_name}/interfaces/{iface_name}/ip",
    status_code=status.HTTP_200_OK,
    tags=["Interfaces"],
)
def set_addr(node_name: str, iface_name: str, data: IPAssignment):
    global current_topology
    if not current_topology:
        raise HTTPException(
            status_code=404, detail="La red no se encuentra inicializada"
        )
    node = current_topology.nodes.get(node_name)
    if not node:
        raise HTTPException(status_code=404, detail=f"El nodo '{node_name}' no existe.")

    iface = node.get_ifaces().get(iface_name)
    if not iface:
        raise HTTPException(
            status_code=404,
            detail=f"El nodo '{node_name}' no tiene la interfaz {iface_name}.",
        )

    try:
        iface.set_addr(addr=data.addr, mask=data.mask)
        return {"message": "IP asignada con éxito"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
