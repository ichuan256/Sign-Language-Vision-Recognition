/* kp_vector_check.c — C-sim layer-by-layer parity check against the Python
 * W8/A8 golden reference (fixed_student_reference.py).
 *
 * Reads a raw-vector directory produced by the Python script's --vectors-c:
 *   vectors_manifest.txt lines:
 *     name kind stride F k N H W C oN oH oW oC
 *   __stem_input__ line marks the raw network input (u8) for reference only.
 * Per layer: {name}_in.bin(u8) {name}_w.bin(i8) {name}_bias.bin(i64)
 *            {name}_M.bin(i32) {name}_acc.bin(i64) {name}_out.bin
 *            (u8; i16 for dense)
 *
 * For every layer the testbench recomputes, in plain C with the same TF
 * 'same' padding semantics as the golden reference:
 *   1) int64 accumulators (MAC + bias), compared BIT-EXACT against _acc.bin;
 *   2) requant via kp_w8a8_contract.h (rne_shift(acc*M,F) then saturation),
 *      compared bit-exact against _out.bin.
 * Any mismatch prints details and exits non-zero.
 *
 * Build (MSVC, see project/_tmp/run_kp_vector_check.bat for an example):
 *   cl /TC /Iproject/algo/keypoints kp_vector_check.c
 */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
#include "kp_w8a8_contract.h"

typedef struct {
    char name[64];
    char kind[16];
    int stride, F, k;
    int N, H, W, C;         /* input  NHWC */
    int oN, oH, oW, oC;     /* output NHWC */
} layer_t;

static void *load(const char *dir, const char *name, const char *suffix,
                  size_t bytes)
{
    char path[512];
    void *buf = malloc(bytes ? bytes : 1);
    FILE *fp;
    if (!buf) { fprintf(stderr, "oom\n"); exit(2); }
    snprintf(path, sizeof path, "%s/%s_%s.bin", dir, name, suffix);
    fp = fopen(path, "rb");
    if (!fp) { perror(path); exit(2); }
    if (fread(buf, 1, bytes, fp) != bytes) {
        fprintf(stderr, "short read %s\n", path); exit(2);
    }
    fclose(fp);
    return buf;
}

static void same_pad(int h, int k, int s, int *before, int *after)
{
    int out = (h + s - 1) / s;
    int t = (out - 1) * s + k - h;
    if (t < 0) t = 0;
    *before = t / 2;
    *after = t - t / 2;
}

int main(int argc, char **argv)
{
    char manifest[512], line[512];
    FILE *fp;
    int n_layers = 0, total_values = 0, failures = 0;

    if (argc < 2) { fprintf(stderr, "usage: %s <vectors_dir>\n", argv[0]); return 2; }
    snprintf(manifest, sizeof manifest, "%s/vectors_manifest.txt", argv[1]);
    fp = fopen(manifest, "r");
    if (!fp) { perror(manifest); return 2; }

    while (fgets(line, sizeof line, fp)) {
        layer_t L;
        int pt, pb, pl, pr, i, j, n, ci, co, u, v;
        int is_dw, is_head;
        size_t in_elems, out_elems, acc_elems;
        uint8_t *xin;
        int8_t *w;
        int64_t *bias, *acc_ref, *acc;
        int32_t *M;
        size_t padded_elems, acc_i;
        int64_t *xp;
        if (line[0] == '\n' || line[0] == '\0') continue;
        if (sscanf(line, "%63s %15s %d %d %d %d %d %d %d %d %d %d %d",
                   L.name, L.kind, &L.stride, &L.F, &L.k,
                   &L.N, &L.H, &L.W, &L.C, &L.oN, &L.oH, &L.oW, &L.oC) != 13) {
            fprintf(stderr, "bad manifest line: %s\n", line);
            return 2;
        }
        if (!strcmp(L.name, "__stem_input__")) continue;   /* reference only */
        is_dw = !strcmp(L.kind, "depthwise");
        is_head = !strcmp(L.kind, "dense");

        in_elems = (size_t)L.N * L.H * L.W * L.C;
        out_elems = (size_t)L.oN * L.oH * L.oW * L.oC;
        acc_elems = out_elems;
        xin = load(argv[1], L.name, "in", in_elems);
        w = load(argv[1], L.name, "w", (size_t)L.k * L.k *
                 (is_dw ? L.C : L.C) * (is_dw ? 1 : L.oC));
        bias = load(argv[1], L.name, "bias", (size_t)L.oC * sizeof(int64_t));
        M = load(argv[1], L.name, "M", (size_t)L.oC * sizeof(int32_t));
        acc_ref = load(argv[1], L.name, "acc", acc_elems * sizeof(int64_t));

        /* pad input to int64 workspace */
        same_pad(L.H, L.k, L.stride, &pt, &pb);
        same_pad(L.W, L.k, L.stride, &pl, &pr);
        padded_elems = (size_t)L.N * (L.H + pt + pb) * (L.W + pl + pr) * L.C;
        xp = calloc(padded_elems, sizeof(int64_t));
        acc = malloc(acc_elems * sizeof(int64_t));
        if (!xp || !acc) { fprintf(stderr, "oom\n"); return 2; }
        for (n = 0; n < L.N; n++)
            for (i = 0; i < L.H; i++)
                for (j = 0; j < L.W; j++)
                    for (ci = 0; ci < L.C; ci++)
                        xp[(((size_t)n * (L.H + pt + pb) + i + pt) *
                            (L.W + pl + pr) + j + pl) * L.C + ci] =
                            xin[(((size_t)n * L.H + i) * L.W + j) * L.C + ci];

        acc_i = 0;
        for (n = 0; n < L.oN; n++)
            for (i = 0; i < L.oH; i++)
                for (j = 0; j < L.oW; j++)
                    for (co = 0; co < L.oC; co++, acc_i++) {
                        int64_t a = bias[co];
                        if (is_dw) {
                            for (u = 0; u < L.k; u++)
                                for (v = 0; v < L.k; v++) {
                                    int ii = i * L.stride + u;
                                    int jj = j * L.stride + v;
                                    int8_t wv = w[(u * L.k + v) * L.C + co];
                                    a += xp[(((size_t)n * (L.H + pt + pb) + ii) *
                                             (L.W + pl + pr) + jj) * L.C + co] * wv;
                                }
                        } else {
                            for (u = 0; u < L.k; u++)
                                for (v = 0; v < L.k; v++) {
                                    int ii = i * L.stride + u;
                                    int jj = j * L.stride + v;
                                    for (ci = 0; ci < L.C; ci++) {
                                        int8_t wv = w[(((size_t)u * L.k + v) * L.C + ci) *
                                                      L.oC + co];
                                        a += xp[(((size_t)n * (L.H + pt + pb) + ii) *
                                                 (L.W + pl + pr) + jj) * L.C + ci] * wv;
                                    }
                                }
                        }
                        acc[acc_i] = a;
                    }

        /* 1) accumulator bit-exactness */
        {
            size_t e;
            for (e = 0; e < acc_elems; e++)
                if (acc[e] != acc_ref[e]) {
                    if (failures < 5)
                        fprintf(stderr, "ACC MISMATCH %s[%zu] got=%lld want=%lld\n",
                                L.name, e, (long long)acc[e], (long long)acc_ref[e]);
                    failures++;
                    break;   /* one report per layer is enough */
                }
        }

        /* 2) requant bit-exactness */
        {
            size_t e;
            int sat = 0;
            if (is_head) {
                int16_t *out_ref = load(argv[1], L.name, "out",
                                        out_elems * sizeof(int16_t));
                for (e = 0; e < out_elems; e++) {
                    int32_t got = kp_requant_i16(acc[e], M[e % L.oC], L.F, &sat);
                    if (got != out_ref[e]) {
                        if (failures < 5)
                            fprintf(stderr, "OUT MISMATCH %s[%zu] got=%d want=%d\n",
                                    L.name, e, got, out_ref[e]);
                        failures++;
                        break;
                    }
                }
                free(out_ref);
            } else {
                uint8_t *out_ref = load(argv[1], L.name, "out", out_elems);
                for (e = 0; e < out_elems; e++) {
                    int32_t got = kp_requant_u8(acc[e], M[e % L.oC], L.F, &sat);
                    if (got != (int32_t)out_ref[e]) {
                        if (failures < 5)
                            fprintf(stderr, "OUT MISMATCH %s[%zu] got=%d want=%d\n",
                                    L.name, e, got, (int)out_ref[e]);
                        failures++;
                        break;
                    }
                }
                free(out_ref);
            }
        }

        total_values += (int)(acc_elems + out_elems);
        n_layers++;
        printf("LAYER %-44s acc+out values=%zu OK\n", L.name,
               acc_elems + out_elems);
        free(xin); free(w); free(bias); free(M); free(acc_ref); free(xp); free(acc);
    }
    fclose(fp);
    if (failures) {
        fprintf(stderr, "{\"vector_check\": \"FAIL\", \"layers\": %d}\n", n_layers);
        return 1;
    }
    printf("{\"vector_check\": \"PASS\", \"layers\": %d, \"values\": %d}\n",
           n_layers, total_values);
    return 0;
}
