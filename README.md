# NsNetworks

NsNetworks es una herramienta que permite crear topologías de nodos arbitrarias haciendo uso de las herramientas de aislamiento del Kernel de Linux.

Su funcionamento se basa en el principio de virtualización del Sistema Operativo (SO) realizado por los Container Runtime como *containerd*, siendo cada nodo un contenedor creado a partir del procedimiento habitual de construcción de contenedores.

## Características Principales

* **Independencia con respecto a orquestadores de contenedores:** A diferencia de otras herramientas similares, NsNetworks incorpora toda la lógica necesaria para la creación de contenedores, no requiriendo del uso de *Container Runtimes* externos.

* **Aislamiento de nodos mediante las herramientas del Kernel de Linux:** Todos los procesos ejecutados dentro de los nodos de la topología presentan un nivel de aislamiento similar al de los contenedores OCI:

    - El sistema de archivos raíz del nodo se encuentra aislado gracias al uso del montaje *OverlayFS* y el clonado del *mnt namespace*.

    - El árbol de procesos, nombre del sistema, pila de red y los mecanismos de comunicación entre procesos se encuentran aislados gracias al uso de las *flags* correspondientes al crear el nuevo proceso mediante la función `clone()`.

    - Todos los procesos se encuentran registrados en el `cgroups.proc` del directorio del árbol de cgroups correspondiente, lo que permite establecer límities a los recursos que estos pueden consumir.

* **Capacidad de interconexión entre nodos:** Los nodos pueden ser conectados entre ellos mediante enlaces `veth` que conectan sus *Network Namespaces*.

* **Compatibilidad con múltiples *frontend*:** Aunque en este proyecto se adjunta un ejemplo de *frontend* implementado de forma específica para la aplicación, esta es compatible con cualquier *frontend* que realice las llamadas correctas a su API.

## Requisitos del Sistema

### Backend (Orquestador y Motor en C)

Debido a que se trata de un proyecto que interactúa de forma directa con el Kernel de Linux, el host en el que se ejecute el *backend* debe cumplir con los siguientes requisitos:

* **Sistema Operativo:** Debian 12 o superior.
* **Librerías del sistema:**
    - `build-essential` (incluye `gcc` para compilar el motor nativo en C)
    - `python3`
    - `python3-pip`
    - `ca-certificates`
* **Entorno de ejecución:** Python 3.10 o superior.
* **Permisos:** Privilegios de superusuario (`sudo`) para la manipulación de la pila de red, clonación de *namespaces* y gestión de los directorios de control de *Cgroups*.

### Frontend (Interfaz Gráfica)

Dado que la interfaz presenta una arquitectura desacoplada y se sirve de forma estática, sus requisitos se dividen entre el entorno que compila el código y el cliente final:

* **Entorno de compilación (Desarrollo):**
    - Node.js (versión 18 o superior recomendada).
    - Gestor de paquetes `pnpm`.
* **Alojamiento (Host):** Cualquier servidor web capaz de servir archivos estáticos (Nginx, Apache, o utilidades ligeras como `http.server` de Python).
* **Entorno de ejecución (Cliente):** Navegador web moderno con soporte estándar para JavaScript (Google Chrome, Mozilla Firefox, Microsoft Edge, etc.). No requiere la instalación de ningún software adicional en la máquina del usuario final.

## Ejecución del programa

A continuación, se describen los pasos a seguir para ejecutar la aplicación de forma sencilla.

### 1. Compilación del motor en C (Cython)

Antes de inicializar el orquestador, es estrictamente necesario compilar el código fuente en C para generar la librería dinámica (`.so`) que permitirá a Python ejecutar la rutina de aislamiento. Además, se deben instalar las dependencias del orquestador.

```bash
cd backend
pip install -r requirements.txt
python3 setup.py build_ext --inplace
```

### 2. Inicialización del servidor

La inicialización del servidor se puede realizar de forma sencilla a través del script `main.py` presente en la carpeta `backend`. La rutina realizada por este script es la siguiente:

1. **Comprobación de privilegios:** Verifica que la ejecución se realiza con permisos de superusuario (*root*), necesarios para interactuar con el Kernel.
2. **Verificación de dependencias:** Confirma que las herramientas clave del sistema host (`ip`, `nsenter`, `mount`, `umount`) están instaladas.
3. **Validación de subsistemas del Kernel:** Comprueba que el módulo `overlay` está cargado y que la jerarquía de *Cgroups v2* se encuentra montada correctamente.
4. **Verificación del sistema de archivos base:** Comprueba la existencia del *rootfs* de Alpine Linux en `/var/lib/net_project/alpine_base`. Si es la primera ejecución y no lo encuentra, invoca automáticamente al script `init.sh` para descargarlo, instalar sus dependencias (como FRRouting) y compilar el proceso *init* nativo en C.
5. **Despliegue de la API:** Tras validar el entorno de bajo nivel, lanza el servidor Uvicorn exponiendo la API REST de FastAPI en el puerto 8000.

Para arrancar el motor, basta con ejecutar (en el directorio *backend*):

```bash
sudo python3 main.py
```

### 3. Compilación de la interfaz gráfica (Frontend)

Aunque no es necesario que el *frontend* se ejecute en el mismo host que el *backend*, es importante que el valor de la clave `baseURL` presente en la llamada a la función `axios.create()` en el archivo `api.js` contenga la dirección en la que se encuentra escuchando la API del servidor.

```jsx
const ApiClient = axios.create({
    baseURL: 'http://192.168.2.100:8000/api/v1',
    timeout: 10000,
});
```

Una vez ajustada la dirección a la que se enviarán las peticiones HTTP, el código desarrollado en React/Vite debe compilarse para generar los archivos estáticos (HTML/JS/CSS) en la carpeta de distribución (`dist`).

```bash
cd frontend
pnpm install
pnpm build
cd ..
```

### 4. Ejecución de la aplicación web

Una vez realizado el build del frontend, los archivos resultantes pueden ser alojados en cualquier servidor web estándar (como Nginx o Apache) o en servicios de despliegue estático.

Por ejemplo, para un despliegue local rápido o entorno de pruebas, es posible utilizar el servidor HTTP integrado en Python para servir la interfaz gráfica directamente desde la carpeta generada:

```bash
cd frontend/dist
python3 -m http.server 3000
```

Tras ejecutar este comando, la interfaz estará accesible abriendo un navegador web en http://localhost:3000 (o la IP correspondiente de la máquina anfitriona). Desde ahí, el navegador del cliente se encargará de enrutar de forma transparente todas las órdenes operativas hacia la API del backend expuesta en el puerto 8000.