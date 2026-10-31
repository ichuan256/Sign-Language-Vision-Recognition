/* Continuous PS-side capture using the installed PYNQ codec register protocol.
 * Configure ADAU1761 before starting. This does not program the FPGA.
 */
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <fcntl.h>
#include <unistd.h>
#include <sys/mman.h>
#include <time.h>

int main(int argc, char **argv) {
    if (argc != 2) return 2;
    int fd = open(argv[1], O_RDWR);
    if (fd < 0) { perror("open uio"); return 3; }
    volatile uint32_t *regs = mmap(NULL, 65536, PROT_READ | PROT_WRITE, MAP_SHARED, fd, 0);
    if (regs == MAP_FAILED) { perror("mmap"); return 4; }
    int16_t block[4800];
    for (;;) {
        for (int i = 0; i < 4800; ++i) {
            struct timespec start, now;
            clock_gettime(CLOCK_MONOTONIC, &start);
            unsigned polls = 0;
            while (regs[4] == 0) {
                if ((++polls & 65535) == 0) {
                    clock_gettime(CLOCK_MONOTONIC, &now);
                    if (now.tv_sec - start.tv_sec > 2) {
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
