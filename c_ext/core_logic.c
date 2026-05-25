#define _GNU_SOURCE

#include <sched.h>
#include <stdio.h>
#include <stdlib.h>
#include <sys/prctl.h>
#include <signal.h>
#include <sys/mount.h>
#include <sys/wait.h>
#include <sys/syscall.h>
#include <unistd.h>
#include <string.h>
#include <fcntl.h>
#include <sys/stat.h>
#include <sys/types.h>
#include <sys/sysmacros.h>
#include <stdint.h>
#include <errno.h>

#define STACK_SIZE (1024 * 1024)

struct node_config {
    char node_name[64];

    char lower_dir[512];
    char upper_dir[512];
    char work_dir[512];
    char merged_dir[512];

    char netns_name[128];

    char command[1024];

    char cgroup_path[512];

    /*
     * FD de sincronización para evitar race conditions
     */
    int sync_fd;
};

/*
 * ============================================================
 * FUNCIONES AUXILIARES
 * ============================================================
 */

static int write_file(const char *path, const char *value) {
    int fd = open(path, O_WRONLY);

    if (fd < 0) {
        return -1;
    }

    ssize_t ret = write(fd, value, strlen(value));

    close(fd);

    return (ret < 0) ? -1 : 0;
}

static int add_pid_to_cgroup(const char *cgroup_path, pid_t pid) {
    char procs_file[1024];

    snprintf(procs_file,
             sizeof(procs_file),
             "%s/cgroup.procs",
             cgroup_path);

    char pid_str[32];

    snprintf(pid_str, sizeof(pid_str), "%d", pid);

    return write_file(procs_file, pid_str);
}

/*
 * ============================================================
 * PROCESO CONTENEDOR
 * ============================================================
 */

int container_entry(void *arg) {
    struct node_config *config = (struct node_config *)arg;

    char dummy;

    if (read(config->sync_fd, &dummy, 1) != 1) {
        perror("read sync pipe");
        return -1;
    }

    close(config->sync_fd);

    prctl(PR_SET_NAME, "c_core_init\0", 0, 0, 0);

    printf("[C-Core] Inicializando contenedor %s (PID interno: %d)\n",
           config->node_name,
           getpid());

    /*
     * --------------------------------------------------------
     * UTS namespace
     * --------------------------------------------------------
     */

    if (sethostname(config->node_name,
                    strlen(config->node_name)) != 0) {
        perror("sethostname");
        return -1;
    }

    /*
     * --------------------------------------------------------
     * NET namespace
     * --------------------------------------------------------
     */

    char netns_path[256];

    snprintf(netns_path,
             sizeof(netns_path),
             "/var/run/netns/%s",
             config->netns_name);

    int netns_fd = open(netns_path, O_RDONLY | O_CLOEXEC);

    if (netns_fd < 0) {
        perror("open netns");
        return -1;
    }

    if (setns(netns_fd, CLONE_NEWNET) != 0) {
        perror("setns");
        close(netns_fd);
        return -1;
    }

    close(netns_fd);

    /*
     * --------------------------------------------------------
     * Mount namespace
     * --------------------------------------------------------
     */

    if (mount(NULL,
              "/",
              NULL,
              MS_REC | MS_PRIVATE,
              NULL) != 0) {
        perror("mount MS_PRIVATE");
        return -1;
    }

    /*
     * --------------------------------------------------------
     * OverlayFS
     * --------------------------------------------------------
     */

    char options[4096];

    int ret = snprintf(options,
                       sizeof(options),
                       "lowerdir=%s,upperdir=%s,workdir=%s",
                       config->lower_dir,
                       config->upper_dir,
                       config->work_dir);

    if (ret < 0 || (size_t)ret >= sizeof(options)) {
        fprintf(stderr, "Overlay options demasiado largas\n");
        return -1;
    }

    if (mount("overlay",
              config->merged_dir,
              "overlay",
              0,
              options) != 0) {
        perror("mount overlay");
        return -1;
    }

    /*
     * merged_dir debe ser un mountpoint para pivot_root
     */

    if (mount(config->merged_dir,
              config->merged_dir,
              NULL,
              MS_BIND | MS_REC,
              NULL) != 0) {
        perror("bind mount merged_dir");
        return -1;
    }

    if (chdir(config->merged_dir) != 0) {
        perror("chdir merged_dir");
        return -1;
    }

    mkdir("oldroot", 0777);

    /*
     * --------------------------------------------------------
     * pivot_root
     * --------------------------------------------------------
     */

    if (syscall(SYS_pivot_root, ".", "oldroot") != 0) {
        perror("pivot_root");
        return -1;
    }

    if (chdir("/") != 0) {
        perror("chdir /");
        return -1;
    }

    /*
     * --------------------------------------------------------
     * /proc
     * --------------------------------------------------------
     */

    mkdir("/proc", 0555);

    if (mount("proc",
              "/proc",
              "proc",
              MS_NOEXEC | MS_NOSUID | MS_NODEV,
              NULL) != 0) {
        perror("mount /proc");
        return -1;
    }

    /*
     * --------------------------------------------------------
     * /sys
     * --------------------------------------------------------
     */

    mkdir("/sys", 0555);

    if (mount("sysfs",
              "/sys",
              "sysfs",
              MS_RDONLY | MS_NOEXEC |
              MS_NOSUID | MS_NODEV,
              NULL) != 0) {
        perror("mount /sys");
    }

    /*
     * --------------------------------------------------------
     * /dev
     * --------------------------------------------------------
     */

    mkdir("/dev", 0755);

    if (mount("tmpfs",
              "/dev",
              "tmpfs",
              MS_NOSUID | MS_STRICTATIME,
              "mode=755") != 0) {
        perror("mount /dev");
    }

    mknod("/dev/null",    S_IFCHR | 0666, makedev(1, 3));
    mknod("/dev/zero",    S_IFCHR | 0666, makedev(1, 5));
    mknod("/dev/random",  S_IFCHR | 0666, makedev(1, 8));
    mknod("/dev/urandom", S_IFCHR | 0666, makedev(1, 9));

    /*
     * --------------------------------------------------------
     * Limpiar oldroot
     * --------------------------------------------------------
     */

    if (umount2("/oldroot", MNT_DETACH) != 0) {
        perror("umount oldroot");
    }

    rmdir("/oldroot");

    /*
     * --------------------------------------------------------
     * Ejecutar proceso final
     * --------------------------------------------------------
     */

        /*
    * ============================================================
    * INIT SIMPLE (PID 1)
    * ============================================================
    */

    signal(SIGCHLD, SIG_DFL);

    pid_t child = fork();

    if (child < 0) {
        perror("fork");
        return -1;
    }

    /*
    * ------------------------------------------------------------
    * HIJO
    * ------------------------------------------------------------
    */

    if (child == 0) {

        /*
        * Crear nueva sesión
        */
        setsid();

        char *exec_args[] = {
            "/bin/sh",
            "-c",
            config->command,
            NULL
        };

        char *exec_env[] = {
            "PATH=/bin:/usr/bin:/sbin:/usr/sbin",
            NULL
        };

        execve(exec_args[0], exec_args, exec_env);

        perror("execve");

        _exit(127);
    }

    /*
    * ------------------------------------------------------------
    * PADRE = PID 1
    * ------------------------------------------------------------
    */

    int status;

    while (1) {
        pid_t pid = waitpid(-1, &status, 0);

        if (pid < 0) {
            if (errno == EINTR) {
                continue;
            }

            if (errno == ECHILD) {
                sleep(1);
                continue;
            }

            perror("waitpid error critico");
            sleep(1);
            continue;
        }

    }

    return 0;
}

/*
 * ============================================================
 * API PRINCIPAL
 * ============================================================
 */

int start_node(char *node_name,
               char *lower_dir,
               char *upper_dir,
               char *work_dir,
               char *merged_dir,
               char *netns_name,
               char *command,
               char *cgroup_path) {

    printf("[C-Core PADRE] Creando contenedor -> %s\n",
           node_name);

    fflush(stdout);

    /*
     * --------------------------------------------------------
     * Crear stack
     * --------------------------------------------------------
     */

    char *stack = malloc(STACK_SIZE);

    if (!stack) {
        perror("malloc");
        return -1;
    }

    /*
     * --------------------------------------------------------
     * Pipe de sincronización
     * --------------------------------------------------------
     */

    int sync_pipe[2];

    if (pipe(sync_pipe) != 0) {
        perror("pipe");
        free(stack);
        return -1;
    }

    /*
     * --------------------------------------------------------
     * Config en la stack
     * --------------------------------------------------------
     */
    struct node_config *config =
        calloc(1, sizeof(struct node_config));

    if (!config) {
        perror("malloc config");
        free(stack);
        return -1;
    }

    memset(config, 0, sizeof(struct node_config));

    strncpy(config->node_name,
            node_name,
            sizeof(config->node_name) - 1);

    strncpy(config->lower_dir,
            lower_dir,
            sizeof(config->lower_dir) - 1);

    strncpy(config->upper_dir,
            upper_dir,
            sizeof(config->upper_dir) - 1);

    strncpy(config->work_dir,
            work_dir,
            sizeof(config->work_dir) - 1);

    strncpy(config->merged_dir,
            merged_dir,
            sizeof(config->merged_dir) - 1);

    strncpy(config->netns_name,
            netns_name,
            sizeof(config->netns_name) - 1);

    strncpy(config->command,
            command,
            sizeof(config->command) - 1);

    strncpy(config->cgroup_path,
            cgroup_path,
            sizeof(config->cgroup_path) - 1);

    /*
     * El hijo leerá desde aquí
     */

    config->sync_fd = sync_pipe[0];

    /*
     * --------------------------------------------------------
     * clone()
     * --------------------------------------------------------
     */

    int clone_flags =
        CLONE_NEWPID |
        CLONE_NEWNS  |
        CLONE_NEWUTS |
        CLONE_NEWIPC |
        SIGCHLD;

    pid_t child_pid =
        clone(container_entry,
              stack + STACK_SIZE,
              clone_flags,
              config);

    if (child_pid == -1) {
        perror("clone");

        close(sync_pipe[0]);
        close(sync_pipe[1]);

        free(stack);

        return -1;
    }

    printf("[C-Core PADRE] El PID del hijo en el host es %d\n", child_pid);
    fflush(stdout);
    /*
     * El padre no necesita leer
     */

    close(sync_pipe[0]);

    /*
     * --------------------------------------------------------
     * Añadir proceso al cgroup
     * --------------------------------------------------------
     */

    if (add_pid_to_cgroup(cgroup_path,
                          child_pid) != 0) {

        perror("add_pid_to_cgroup");

        kill(child_pid, SIGKILL);

        close(sync_pipe[1]);

        waitpid(child_pid, NULL, 0);

        free(stack);

        return -1;
    }

    /*
     * --------------------------------------------------------
     * Liberar al hijo
     * --------------------------------------------------------
     */

    if (write(sync_pipe[1], "x", 1) != 1) {
        perror("sync write");
    }

    close(sync_pipe[1]);

    return child_pid;
}