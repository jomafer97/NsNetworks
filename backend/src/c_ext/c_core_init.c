#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <sys/wait.h>
#include <signal.h>
#include <errno.h>

int main(int argc, char *argv[]) {
    if (argc < 2) {
        fprintf(stderr, "Error: Faltan argumentos para c_core_init\n");
        return 1;
    }

    signal(SIGTERM, SIG_DFL);
    signal(SIGINT, SIG_IGN);

    pid_t child = fork();

    if (child < 0) {
        perror("fork en init");
        return 1;
    }

    if (child == 0) {
        setsid();
        execvp(argv[1], &argv[1]);
        perror("execvp payload");
        _exit(127);
    }

    int status;
    while (1) {
        pid_t pid = waitpid(-1, &status, 0);

        if (pid < 0) {
            if (errno == EINTR) {
                continue;
            }
            if (errno == ECHILD) {
                break;
            }
            perror("waitpid error critico en init");
            sleep(1);
        } else if (pid == child) {
            break;
        }
    }

    return 0;
}