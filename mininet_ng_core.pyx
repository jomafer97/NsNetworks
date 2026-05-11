# 1. Importamos la declaración de C indicando dónde está el header
cdef extern from "core_namespaces.h":
    int start_node(char *node_name, char *lower_dir, char *upper_dir, char *work_dir, char *merged_dir, char *apparmor_profile, char *netns_name)

# 2. Creamos la función que Python llamará
def create_container(node_name: str, lower_dir: str, upper_dir: str, work_dir: str, merged_dir: str, apparmor_profile: str, netns_name: str) -> int:
    """
    Wrapper para instanciar el contenedor desde C.
    Convierte los strings de Python a bytes para que C los interprete como char*.
    """
    print(f"[Cython Debug] Preparando nodo: {node_name} | Netns: {netns_name}")
    # Conversión estricta a bytes (UTF-8)
    cdef bytes b_node_name = node_name.encode('utf-8')
    cdef bytes b_lower_dir = lower_dir.encode('utf-8')
    cdef bytes b_upper_dir = upper_dir.encode('utf-8')
    cdef bytes b_work_dir = work_dir.encode('utf-8')
    cdef bytes b_merged_dir = merged_dir.encode('utf-8')
    cdef bytes b_apparmor = apparmor_profile.encode('utf-8')
    cdef bytes b_netns = netns_name.encode('utf-8')

    # Llamada nativa a la función en C
    cdef int child_pid = start_node(
        b_node_name,
        b_lower_dir,
        b_upper_dir,
        b_work_dir,
        b_merged_dir,
        b_apparmor,
        b_netns
    )

    return child_pid