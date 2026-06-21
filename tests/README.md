# Ejecución de los tests

En esta carpeta se encuentra la implementación de los tests presentados en el Trabajo de Fin de Grado correspondiente a esta aplicación. Estos realizan una comparativa entre la velocidad de despliegue, throughput y aislamiento de las tres herramientas comparadas en el proyecto.

Las dependencias necesarias para la ejecución de los tests son las siguientes:

- NsNetworks: para ejecutar los tests de NsNetworks únicamente es necesario que el backend se encuentre en ejecución.

- Mininet: la ejecución de los tests de Mininet requiere de su previa instalación:

```bash
sudo apt update
sudo apt install -y mininet
```

- ContainerLab: además de su instalación, esta herramienta requiere de la instalación de Docker para su correcto funcionamiento:

```bash
sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
sudo bash -c "$(curl -sL https://get.containerlab.dev)"
```

## Tests de velocidad de despliegue

Para realizarlos es necesario ejecutar el `.py` de la herramienta correspondiente, pasando como parámetro el número de routers que se quieren testear:

```bash
python3 test_despliegue_nsnetworks.py 10 20 50
```

## Tests de throughput

Estos pueden ser ejecutados de forma directa para cada una de las herramientas:

```bash
python3 test_throughput_nsnetworks.py
```

## Test de aislamiento

Este incluye el test de todas las herramientas, por lo que requiere de la presencia de todas estas para su correcto funcionamiento. Puede ser ejecutado de forma directa:

```bash
python3 test_aislamiento.py
```