# Ejecución de los tests

En esta carpeta se encuentra la implementación de los tests presentados en el Trabajo de Fin de Grado correspondiente a esta aplicación. Estos realizan una comparativa entre la velocidad de despliegue, throughput y aislamiento de las tres herramientas comparadas en el proyecto.

Las dependencias necesarias para la ejecución de los tests son las siguientes:

- NsNetworks: para ejecutar los tests de NsNetworks únicamente es necesario que el backend se encuentre en ejecución.

- Mininet: la ejecución de los tests de Mininet requiere de la instalación de la herramienta e iperf3:

```bash
sudo apt update
sudo apt install -y mininet iperf3
```

- ContainerLab: además de su instalación, esta herramienta requiere de la instalación de Docker para su correcto funcionamiento. En el caso de Debian 12, esto se haría mediante los siguientes comandos:

```bash
sudo apt update
sudo apt install -y ca-certificates curl gnupg
sudo install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/debian/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
sudo chmod a+r /etc/apt/keyrings/docker.gpg
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/debian \
  $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
sudo bash -c "$(curl -sL https://get.containerlab.dev)"
sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
```

## Tests de velocidad de despliegue

Para realizarlos es necesario ejecutar el `.py` de la herramienta correspondiente, pasando como parámetro el número de routers que se quieren testear:

```bash
python3 test_despliegue_nsnetworks.py 10 20 50
```

En el caso del test de mininet, este debe de ser ejecutado como sudo:

```bash
sudo python3 test_despliegue_mininet.py 10 20 50
```

## Tests de throughput

Estos pueden ser ejecutados de forma directa para cada una de las herramientas:

```bash
python3 test_throughput_nsnetworks.py
```

En el caso del test de mininet, este debe de ser ejecutado como sudo:

```bash
sudo python3 test_throughput_mininet.py
```

## Test de aislamiento

Este incluye el test de todas las herramientas, por lo que requiere de la presencia de todas estas para su correcto funcionamiento. Puede ser ejecutado de forma directa:

```bash
sudo python3 test_aislamiento.py
```