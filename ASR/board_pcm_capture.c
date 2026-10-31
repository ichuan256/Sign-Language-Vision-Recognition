/* Continuous PS-side capture using the installed PYNQ codec register protocol.
 * Configure ADAU1761 before starting. This does not program the FPGA.
 */
#define _GNU_SOURCE
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <fcntl.h>
#include <unistd.h>
#include <sys/mman.h>
#include <time.h>
#include <sched.h>
#include <sys/resource.h>

int main(int argc, char **argv) {
    if (argc != 2 && argc != 3) return 2;
    /* AV mode gives the sampler its own core; legacy two-argument use stays valid. */
    if (argc == 3) {
        char *end = NULL;
        long cpu = strtol(argv[2], &end, 10);
        if (!end || end == argv[2] || *end || cpu < 0 || cpu >= CPU_SETSIZE) return 7;
        cpu_set_t affinity;
        CPU_ZERO(&affinity);
        CPU_SET((int)cpu, &affinity);
        if (sched_setaffinity(0, sizeof(affinity), &affinity) < 0) {
            perror("audio CPU affinity"); return 7;
        }
        if (setpriority(PRIO_PROCESS, 0, -12) < 0) {
            perror("audio scheduling priority"); return 8;
        }
        fprintf(stderr, "PCM sampler cpu=%ld nice=-12 (normal scheduler)\n", cpu);
    }
    int fd = open(argv[1], O_RDWR);
    if (fd < 0) { perror("open uio"); return 3; }
    volatile uint32_t *regs = mmap(NULL, 65536, PROT_READ | PROT_WRITE, MAP_SHARED, fd, 0);
    if (regs == MAP_FAILED) { perror("mmap"); return 4; }
    int16_t block[4800];
    for (;;) {
        for (int i = 0; i < 4800; ++i) {
            struct timespec start = {0, 0}, now;
            int timer_started = 0;
            unsigned polls = 0;
            while (regs[4] == 0) {
                if ((++polls & 65535) == 0) {
                    clock_gettime(CLOCK_MONOTONIC, &now);
                    if (!timer_started) {
                        start = now;
                        timer_started = 1;
                    } else if (now.tv_sec - start.tv_sec > 2) {
                        fprintf(stderr, "audio sample clock timeout\n"); return 5;
                    }
                }
            }
            regs[4] = 1;
            uint32_t left = regs[0];
            (void)regs[1];
            block[i] = (int16_t)(((int32_t)(left << 8)) >> 16);
        }
        size_t sent = 0;
        while (sent < sizeof(block)) {
            ssize_t count = write(STDOUT_FILENO, (char *)block + sent, sizeof(block) - sent);
            if (count <= 0) return 6;
            sent += (size_t)count;
        }
    }
}
