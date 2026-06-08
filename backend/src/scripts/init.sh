#!/bin/bash

# Salir inmediatamente si un comando falla
set -e

# 1. Comprobación de privilegios
if [ "$EUID" -ne 0 ]; then
  echo "[!] Por favor, ejecuta este script como root (sudo ./init.sh)"
  exit 1
fi

# 2. Rutas
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
BACKEND_ROOT="$( cd "$SCRIPT_DIR/../.." && pwd )"

NET_PROJECT_DATA="/var/lib/net_project"
BASE_DIR="$NET_PROJECT_DATA/alpine_base"
ALPINE_TAR="alpine-minirootfs-3.19.1-x86_64.tar.gz"

TEMPLATES_DIR="$BACKEND_ROOT/templates"
C_INIT_PATH="$SCRIPT_DIR/../c_ext/c_core_init.c"

echo "[*] Iniciando la construcción del entorno Alpine..."
mkdir -p $NET_PROJECT_DATA

# 3. Descargar y extraer Alpine Linux
if [ ! -d "$BASE_DIR" ]; then
    echo "[*] Descargando Alpine Linux (Mini RootFS) en el disco nativo..."
    mkdir -p $BASE_DIR
    wget -q "https://dl-cdn.alpinelinux.org/alpine/v3.19/releases/x86_64/$ALPINE_TAR" -O /tmp/$ALPINE_TAR
    tar -xf /tmp/$ALPINE_TAR -C $BASE_DIR
    rm /tmp/$ALPINE_TAR
else
    echo "[*] El directorio $BASE_DIR ya existe. Omitiendo descarga."
fi

# 4. Instalar dependencias DENTRO de Alpine
echo "[*] Instalando FRRouting e iproute2 en la imagen base..."

# Copiamos temporalmente la configuración de DNS del host para que el chroot tenga internet
cp /etc/resolv.conf $BASE_DIR/etc/

# Entramos en la habitación de Alpine e instalamos los paquetes
chroot $BASE_DIR /bin/sh -c "
  apk update
  apk add frr iproute2 frr-pythontools python3 iperf3
"

# 4.5 Compilar e inyectar el Init del motor C
echo "[*] Compilando el proceso Init del contenedor..."

if [ ! -f "$C_INIT_PATH" ]; then
    echo "[!] ERROR: No se encuentra $C_INIT_PATH."
    exit 1
fi

gcc -static -O2 "$C_INIT_PATH" -o init-c-core

echo "[*] Instalando el Init en el sistema de archivos del contenedor..."
cp init-c-core $BASE_DIR/sbin/init-c-core
chmod +x $BASE_DIR/sbin/init-c-core

rm init-c-core

# 5. Generar las plantillas en tu carpeta de proyecto
echo "[*] Generando plantillas de configuración OSPF..."
mkdir -p $TEMPLATES_DIR

cat << 'EOF' > $TEMPLATES_DIR/frr.conf.template
frr version 8.1
frr defaults traditional
hostname {router_name}
log syslog informational
no ipv6 forwarding
!
router ospf
 ospf router-id {router_id}
 redistribute connected
 network 0.0.0.0/0 area 0.0.0.0
!
line vty
!
EOF

echo "[*] ¡Entorno inicializado con éxito!"
echo "    -> Sistema base (Alpine): $BASE_DIR"
echo "    -> Plantillas (Python): $TEMPLATES_DIR"