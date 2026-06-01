import sys


def generar_yaml(n):
    nombre_archivo = f"anillo-{n}.yaml"

    with open(nombre_archivo, "w") as f:
        f.write(f"name: test-anillo-{n}\n")
        f.write("topology:\n")
        f.write("  nodes:\n")

        # Generar los N nodos
        for i in range(1, n + 1):
            f.write(f"    r{i}:\n")
            f.write("      kind: linux\n")
            f.write("      image: frrouting/frr:latest\n")

        f.write("\n  links:\n")

        # Generar los N enlaces en anillo
        f.write('    - endpoints: ["r1:eth1", "r2:eth1"]\n')
        for i in range(2, n):
            f.write(f'    - endpoints: ["r{i}:eth2", "r{i+1}:eth1"]\n')

        # Cerrar el anillo del último al primero
        f.write(f'    - endpoints: ["r{n}:eth2", "r1:eth2"]\n')

    print(f"[+] Archivo {nombre_archivo} generado con éxito ({n} routers).")


if __name__ == "__main__":
    generar_yaml(20)
    generar_yaml(50)
