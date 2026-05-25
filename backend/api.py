from contextlib import asynccontextmanager
import threading, asyncio, signal, os
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from .topology import Topology
from .node import IsolatedNode
from .router import Router
from .switch import Switch

current_topology = None

active_node_pids = set()


async def zombie_reaper_task():
    """
    Tarea en segundo plano que recolecta los procesos huérfanos (zombis).
    Gracias a que el contenedor en C emite SIGCHLD, waitpid estándar es suficiente.
    """
    while True:
        for pid in list(active_node_pids):
            try:
                zombie_pid, status = os.waitpid(pid, os.WNOHANG)

                if zombie_pid == pid:
                    print(
                        f"[*] Nodo (PID {pid}) enterrado limpiamente (Status: {status})"
                    )
                    active_node_pids.remove(pid)

            except ChildProcessError:
                active_node_pids.remove(pid)
            except ProcessLookupError:
                active_node_pids.remove(pid)
            except Exception as e:
                print(f"[!] Error inesperado revisando PID {pid}: {e}")

        await asyncio.sleep(2)


def start_net():
    """Inicia la topología"""
    global current_topology
    current_topology = Topology("API-Core")


@asynccontextmanager
async def lifespan(app: FastAPI):
    reaper = asyncio.create_task(zombie_reaper_task())

    net_thread = threading.Thread(target=start_net, daemon=True)
    net_thread.start()

    yield

    reaper.cancel()

    try:
        await reaper
    except asyncio.CancelledError:
        pass

    if current_topology:
        print("\n[*] Apagando servidor, destruyendo topología...")
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(None, current_topology.delete_all)


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


class CgroupAssignment(BaseModel):
    cpu: int | None = None
    ram: int | None = None


class IPAssignment(BaseModel):
    addr: str
    mask: int


class ConfigUpdate(BaseModel):
    config: str


@app.get("/api/v1/network", tags=["Network"])
def get_network_state():
    """Devuelve el estado completo del grafo (Nodos y Enlaces)."""
    if not current_topology:
        raise HTTPException(status_code=503, detail="El motor no está inicializado")
    return current_topology.export_to_json("topology.json")


@app.delete("/api/v1/network", tags=["Network"])
def delete_all():
    """Elimina la topología actual"""
    global current_topology
    if not current_topology:
        raise HTTPException(status_code=503, detail="La red no está inicializada")

    try:
        current_topology.delete_all()
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error del servidor al eliminar la topología: {str(e)}",
        )


@app.post("/api/v1/network/start", status_code=status.HTTP_200_OK, tags=["Network"])
def start_all():
    """Inicializa todos los routers"""
    global current_topology
    if not current_topology:
        raise HTTPException(status_code=503, detail="El motor no está inicializado")

    try:
        pids = current_topology.start_all()
        if pids:
            active_node_pids.update(pids)
        return {"message": f"Todos los routers inicializados exitosamente."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/nodes", status_code=status.HTTP_201_CREATED, tags=["Nodes"])
def create_node(node: NodeCreate):
    """Instancia un nuevo nodo en el kernel y lo conecta al switch principal."""
    global current_topology
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
        pid = current_topology.start_node(node_name)
        if pid:
            active_node_pids.add(pid)
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
    node = current_topology.get_node(node_name)
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


@app.post(
    "/api/v1/nodes/{node_name}/cgroups",
    status_code=status.HTTP_200_OK,
    tags=["Nodes"],
)
def set_cgroups(node_name: str, data: CgroupAssignment):
    global current_topology
    if not current_topology:
        raise HTTPException(
            status_code=404, detail="La red no se encuentra inicializada"
        )

    node = current_topology.get_node(node_name)

    if not node:
        raise HTTPException(status_code=404, detail=f"El nodo '{node_name}' no existe.")

    if not isinstance(node, IsolatedNode):
        raise HTTPException(
            status_code=404,
            detail=f"No se puede asignar cgroups al nodo '{node_name}'.",
        )

    limits = {}

    if data.ram:
        bytes_ram = int(data.ram) * 1024 * 1024
        limits["memory.max"] = str(bytes_ram)

    if data.cpu:
        quota = int((data.cpu / 100.0) * 100000)
        limits["cpu.max"] = f"{quota} 100000"

    try:
        node.set_cgroups(limits)
        return {"message": "Cgroups configurados con éxito"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/nodes/{node_name}/ospf/neighbors", tags=["OSPF"])
def get_ospf_neighbors(node_name: str):
    """Devuelve la tabla de vecinos OSPF del nodo."""
    global current_topology
    if not current_topology:
        raise HTTPException(status_code=503, detail="Motor no inicializado")

    node = current_topology.get_node(node_name)

    if not isinstance(node, Router):
        raise HTTPException(status_code=404, detail=f"Router {node_name} no encontrado")

    return node.get_ospf_neighbors()


@app.get("/api/v1/nodes/{node_name}/ospf/interfaces", tags=["OSPF"])
def get_ospf_interfaces(node_name: str):
    """Devuelve la tabla de interfaces OSPF del nodo."""
    global current_topology
    if not current_topology:
        raise HTTPException(status_code=503, detail="Motor no inicializado")

    node = current_topology.get_node(node_name)

    if not isinstance(node, Router):
        raise HTTPException(status_code=404, detail=f"Router {node_name} no encontrado")

    return node.get_ospf_interfaces()


@app.get("/api/v1/nodes/{node_name}/routing_table", tags=["OSPF"])
def get_routing_table(node_name: str):
    """Devuelve la tabla de enrutamiento del nodo."""
    global current_topology
    if not current_topology:
        raise HTTPException(status_code=503, detail="Motor no inicializado")

    node = current_topology.get_node(node_name)

    if not isinstance(node, Router):
        raise HTTPException(status_code=404, detail=f"Router {node_name} no encontrado")

    return node.get_routing_table()


@app.get("/api/v1/nodes/{node_name}/ospf/border-routers", tags=["OSPF"])
def get_ospf_border_routers(node_name: str):
    """Devuelve la tabla de routers de borde OSPF del nodo."""
    global current_topology
    if not current_topology:
        raise HTTPException(status_code=503, detail="Motor no inicializado")

    node = current_topology.get_node(node_name)

    if not isinstance(node, Router):
        raise HTTPException(status_code=404, detail=f"Router {node_name} no encontrado")

    return node.get_ospf_border_routers()


@app.get("/api/v1/nodes/{node_name}/config", tags=["Config"])
def get_running_config(node_name: str):
    """Devuelve el archivo running-config del router en texto plano."""
    global current_topology
    if not current_topology:
        raise HTTPException(status_code=503, detail="Motor no inicializado")

    node = current_topology.get_node(node_name)

    if not isinstance(node, Router):
        raise HTTPException(status_code=404, detail=f"Router {node_name} no encontrado")

    config_text = node.get_running_config()
    return {"config": config_text}


@app.post("/api/v1/nodes/{node_name}/config", tags=["Config"])
def set_running_config(node_name: str, data: ConfigUpdate):
    """Sobrescribe el archivo running-config del router y recarga el demonio."""
    global current_topology
    if not current_topology:
        raise HTTPException(status_code=503, detail="Motor no inicializado")

    node = current_topology.get_node(node_name)

    if not isinstance(node, Router):
        raise HTTPException(status_code=404, detail=f"Router {node_name} no encontrado")

    try:
        output = node.set_running_config(data.config)
        return {"message": f"Configuración establecida con éxito: {output}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
