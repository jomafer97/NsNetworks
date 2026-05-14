from contextlib import asynccontextmanager
import threading
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from .topology import Topology
from .router import Router
from .switch import Switch

current_topology = None


def arrancar_red():
    """Lógica aislada en su propio hilo."""
    global current_topology
    print("\n[*] Precargando topología de prueba en hilo dedicado...")
    current_topology = Topology("API-Core")

    s1 = Switch("s1")
    r1 = Router("r1")
    r2 = Router("r2")

    current_topology.add_node(s1)
    current_topology.add_node(r1)
    current_topology.add_node(r2)

    current_topology.start_all()
    current_topology.add_link("r1", "s1")
    current_topology.add_link("r2", "s1")

    print("[*] Topología lista. Ya puedes abrir el frontend en tu navegador.\n")


# --- EL CONTROLADOR DE CICLO DE VIDA ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    # 1. STARTUP: Solo el proceso Worker ejecutará esto al arrancar
    hilo_red = threading.Thread(target=arrancar_red, daemon=True)
    hilo_red.start()

    yield  # El servidor web se queda aquí pausado sirviendo peticiones

    # 2. SHUTDOWN: Al pulsar CTRL+C, limpiamos la casa antes de salir
    if current_topology:
        print("\n[*] Apagando servidor, destruyendo topología...")
        current_topology.stop_all()


# Pasamos el lifespan a la instancia de FastAPI
app = FastAPI(title="SDN Topology API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", response_class=HTMLResponse)
def home():
    """
    Sirve el frontend directamente.
    Al entrar en localhost:8000 desde el navegador, se cargará la interfaz gráfica.
    """
    try:
        with open("frontend/index.html", "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return "<h1>Error: No se encuentra frontend/index.html</h1>"


@app.get("/api/topology")
def get_topology():
    if current_topology:
        return current_topology.export_to_json("temp_topo.json")
    return {"error": "No hay topología activa"}
