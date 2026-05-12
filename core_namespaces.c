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
#include <sys/sysmacros.h>

// El tamaño de la pila que necesita clone() para el proceso hijo
#define STACK_SIZE (1024 * 1024)

// Estructura para pasarle los parámetros desde Python al hijo en C
struct node_config {
    char node_name[64];
    char lower_dir[512];
    char upper_dir[512];
    char work_dir[512];
    char merged_dir[512];
    char apparmor_profile[128];
    char netns_name[128];
    char command[1024];
};

// -----------------------------------------------------------------
// ESTA ES LA FUNCIÓN QUE SE EJECUTA DENTRO DEL CONTENEDOR (PID 1)
// -----------------------------------------------------------------
int container_entry(void *arg) {
    struct node_config *config = (struct node_config *)arg;

    printf("[C-Core] Inicializando contenedor %s (PID interno: %d)\n", config->node_name, getpid());

    char netns_path[256];
    snprintf(netns_path, sizeof(netns_path), "/var/run/netns/%s", config->netns_name);

    /*
    Se aprovecha el nuevo UTS para establecer un nombre nuevo al contenedor
    */
    if (sethostname(config->node_name, strlen(config->node_name)) != 0) {
        perror("Fallo en sethostname");
    }

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
    Montaje de /sys como read only
    */
    if (mount("sysfs", "/sys", "sysfs", MS_RDONLY | MS_NOEXEC | MS_NOSUID | MS_NODEV, NULL) != 0) {
        perror("Fallo al montar /sys");
    }

    /*
    Montaje de /dev limpio
    */
    if (mount("tmpfs", "/dev", "tmpfs", MS_NOSUID | MS_STRICTATIME, "mode=755") != 0) {
        perror("Fallo al montar /dev tmpfs");
    }

    mknod("/dev/null", S_IFCHR | 0666, makedev(1, 3));
    mknod("/dev/zero", S_IFCHR | 0666, makedev(1, 5));
    mknod("/dev/random", S_IFCHR | 0666, makedev(1, 8));
    mknod("/dev/urandom", S_IFCHR | 0666, makedev(1, 9));

    /* Esto habilitaría terminales

    mkdir("/dev/pts", 0755);
    if (mount("devpts", "/dev/pts", "devpts", 0, "newinstance,ptmxmode=0666") == 0) {
        symlink("/dev/pts/ptmx", "/dev/ptmx");
    }

    */

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

    char *exec_args[4];

    exec_args[0] = "/bin/sh";
    exec_args[1] = "-c";
    exec_args[2] = config->command;
    exec_args[3] = NULL;

    char *exec_env[]  = {"PATH=/bin:/usr/bin:/sbin:/usr/sbin", NULL};

    if (execve(exec_args[0], exec_args, exec_env) == -1) {
        perror("Fallo en execve");
        return -1;
    }

    return 0;
}

// -----------------------------------------------------------------
// ESTA ES LA FUNCIÓN QUE LLAMARÁS DESDE PYTHON (VÍA CYTHON)
// -----------------------------------------------------------------
int start_node(char *node_name, char *lower_dir, char *upper_dir, char *work_dir, char *merged_dir, char *apparmor_profile, char *netns_name, char* command) {
    // Sonda de seguridad
    printf("[C-Core PADRE] Inyectando en Pila -> Node: %s | Netns: %s\n", node_name, netns_name);
    fflush(stdout);

    char *stack = malloc(STACK_SIZE);
    if (!stack) return -1;

    // 1. Calculamos el tope de la pila (la pila crece hacia abajo)
    uintptr_t stack_top = (uintptr_t)(stack + STACK_SIZE);

    // 2. Restamos el tamaño exacto de nuestra estructura para hacerle hueco
    stack_top -= sizeof(struct node_config);

    // 3. Alineamos la memoria a 16 bytes (Obligatorio en x86_64 para evitar SegFaults)
    stack_top &= ~0xF;

    // 4. Instanciamos la estructura DENTRO de la memoria de la pila del hijo
    struct node_config *config = (struct node_config *)stack_top;

    // 5. Copiamos los bytes en crudo
    memset(config, 0, sizeof(struct node_config));
    strncpy(config->node_name, node_name, sizeof(config->node_name) - 1);
    strncpy(config->lower_dir, lower_dir, sizeof(config->lower_dir) - 1);
    strncpy(config->upper_dir, upper_dir, sizeof(config->upper_dir) - 1);
    strncpy(config->work_dir, work_dir, sizeof(config->work_dir) - 1);
    strncpy(config->merged_dir, merged_dir, sizeof(config->merged_dir) - 1);
    strncpy(config->apparmor_profile, apparmor_profile, sizeof(config->apparmor_profile) - 1);
    strncpy(config->netns_name, netns_name, sizeof(config->netns_name) - 1);
    strncpy(config->command, command, sizeof(config->command) - 1);

    int clone_flags = CLONE_NEWPID | CLONE_NEWNS | CLONE_NEWUTS | CLONE_NEWIPC | SIGCHLD;

    // Usamos el inicio de la estructura como puntero de la pila y le pasamos la misma dirección como argumento
    pid_t child_pid = clone(container_entry, (void *)config, clone_flags, config);

    if (child_pid == -1) {
        perror("Fallo en clone");
        free(stack);
        return -1;
    }

    // Nota técnica: Intencionadamente no hacemos free(stack) en el padre inmediatamente.
    // Asumimos un coste de 1MB por nodo para garantizar que el kernel no descarte
    // la página física de RAM antes de que el hijo termine de arrancar.

    return child_pid;
}