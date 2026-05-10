from network_namespace import Link, NetworkNamespace

ns1 = NetworkNamespace("ns_cliente")
ns2 = NetworkNamespace("ns_servidor")

enlace = Link(("veth_cli", "veth_srv"))

enlace.attach_link(ns1.name, ns2.name)

enlace.set_ip("10.0.0.1", "10.0.0.2", mask=24)
enlace.up()

print("¡Red virtual aislada creada con éxito!")

# 5. Destrucción
enlace.cleanup()
ns1.cleanup()
ns2.cleanup()
