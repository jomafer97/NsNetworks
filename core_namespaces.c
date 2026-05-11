#define _GNU_SOURCE
#include <sched.h>
#include <stdio.h>
#include <stdlib.h>
#include <sys/mount.h>
#include <sys/wait.h>
#include <sys/syscall.h>
#include <unistd.h>
#include <string.h>
#include <fcntl.h>
#include <sys/stat.h>
#include <sys/types.h>

// El tamaño de la pila que necesita clone() para el proceso hijo
#define STACK_SIZE (1024 * 1024)

// Estructura para pasarle los parámetros desde Python al hijo en C
struct node_config {
    char *node_name;
    char *lower_dir; // Rutas concatenadas con :
    char *upper_dir;
    char *work_dir;
    char *merged_dir;
    char *apparmor_profile;
    char *netns_name;
};

// -----------------------------------------------------------------
// ESTA ES LA FUNCIÓN QUE SE EJECUTA DENTRO DEL CONTENEDOR (PID 1)
// -----------------------------------------------------------------
int container_entry(void *arg) {
    struct node_config *config = arg;

    printf("[C-Core] Inicializando contenedor %s (PID interno: %d)\n", config->node_name, getpid());

    char netns_path[256];
    snprintf(netns_path, sizeof(netns_path), "/var/run/netns/%s", config->netns_name);

    /*
    Obtención del file descriptor del netns como readonly, que se cerrará en exec
    */
    int netns_fd = open(netns_path, O_RDONLY | O_CLOEXEC);
    if (netns_fd < 0) {
        perror("Error abriendo el netns");
        return -1;
    }

    /*
    Se establece el nuevo netns a partir del descriptor
    */
    if (setns(netns_fd, CLONE_NEWNET) != 0) {
        perror("Fallo en setns para red");
        close(netns_fd);
        return -1;
    }

    close(netns_fd);

    /*
    Para evitar la propagación de montajes hacia el host. Esto hace que todo montaje
    que se realice en este mnt namespace no afecte al exterior
    */
    if (mount(NULL, "/", NULL, MS_REC | MS_PRIVATE, NULL) != 0) {
        perror("Fallo en mount MS_PRIVATE");
        return -1;
    }

    /*
    Establecimiento de los parámetros del overlayfs
    */
    char options[4096];

    int ret = snprintf(options, sizeof(options),
                       "lowerdir=%s,upperdir=%s,workdir=%s",
                       config->lower_dir, config->upper_dir, config->work_dir);

    if (ret < 0 || (size_t)ret >= sizeof(options)) {
        fprintf(stderr, "[C-Core] Error: las rutas del OverlayFS son demasiado largas.\n");
        return -1;
    }

    /*
    Montaje del overlayfs
    */
    if (mount("overlay", config->merged_dir, "overlay", 0, options) != 0) {
        perror("Fallo al montar OverlayFS");
        return -1;
    }

    /*
    Antes de realizar un pivot root, la raíz se convierte en un nuevo punto de montaje
    */
    if (mount(config->merged_dir, config->merged_dir, "bind", MS_BIND | MS_REC, NULL) != 0) {
        perror("Fallo en bind mount del merged_dir");
        return -1;
    }

    chdir(config->merged_dir);

    /*
    Creación de carpeta temporal para el antiguo root
    */
    mkdir("oldroot", 0777);

    /*
    Realización de pivot root
    */
    if (syscall(SYS_pivot_root, ".", "oldroot") != 0) {
        perror("Fallo en pivot_root");
        return -1;
    }

    /*
    Entrada a la nueva raíz
    */
    chdir("/");

    /*
    Montar el fs de tipo "proc" en /proc
    */
    if (mount("proc", "/proc", "proc", MS_NOEXEC | MS_NOSUID | MS_NODEV, NULL) != 0) {
        perror("Fallo al montar /proc");
        return -1;
    }

    /*
    Desmontaje y eliminación de la antigua raíz
    */
    umount2("/oldroot", MNT_DETACH);
    rmdir("/oldroot");

    // 5. Aplicar AppArmor
    // Escribimos el perfil en /proc/self/attr/exec para que se aplique
    // justo en el momento de hacer el execve.
    int aa_fd = open("/proc/self/attr/exec", O_WRONLY);
    if (aa_fd >= 0) {
        dprintf(aa_fd, "exec %s", config->apparmor_profile);
        close(aa_fd);
    } else {
        printf("[C-Core] Advertencia: No se pudo aplicar AppArmor.\n");
    }

    // 6. Mutación final: Ejecutar el proceso (FRR o bash)
    // Al usar execve, este proceso reemplaza la imagen de memoria,
    // pero mantiene el PID 1 dentro del namespace.

    // char *exec_args[] = {"/usr/lib/frr/frrinit.sh", "start", NULL}; // O tu script de entrada
    // char *exec_env[]  = {"PATH=/bin:/usr/bin:/sbin:/usr/sbin", "TERM=xterm", NULL};

    char *exec_args[] = {"/bin/sleep", "3600", NULL};
    char *exec_env[]  = {"PATH=/bin:/usr/bin", NULL};

    if (execve(exec_args[0], exec_args, exec_env) == -1) {
        perror("Fallo en execve");
        return -1;
    }

    return 0;
}

// -----------------------------------------------------------------
// ESTA ES LA FUNCIÓN QUE LLAMARÁS DESDE PYTHON (VÍA CYTHON)
// -----------------------------------------------------------------
int start_node(char *node_name, char *lower_dir, char *upper_dir, char *work_dir, char *merged_dir, char *apparmor_profile, char *netns_name) {
    char *stack = malloc(STACK_SIZE);
    if (!stack) return -1;

    struct node_config config = {
        .node_name = node_name,
        .lower_dir = lower_dir,
        .upper_dir = upper_dir,
        .work_dir = work_dir,
        .merged_dir = merged_dir,
        .apparmor_profile = apparmor_profile,
        .netns_name = netns_name
    };

    int clone_flags = CLONE_NEWPID | CLONE_NEWNS | CLONE_NEWUTS | CLONE_NEWIPC | SIGCHLD;

    /* Los parámetros son:
        1. Función que ejecutará el nuevo proceso al nacer
        2. Pila de memoria invertida, se le pasa el inicio (stack apunta al inicio) más el tamaño del stack
        3. Flags de clonado
        4. Argumentos de la función
    */
    pid_t child_pid = clone(container_entry, stack + STACK_SIZE, clone_flags, &config);

    if (child_pid == -1) {
        perror("Fallo en clone");
        free(stack);
        return -1;
    }

    // Importante: Aquí (en el host) es donde meteríamos el child_pid
    // en el archivo cgroup.procs de este nodo antes de continuar.

    return child_pid; // Devolvemos el PID real del host a Python
}