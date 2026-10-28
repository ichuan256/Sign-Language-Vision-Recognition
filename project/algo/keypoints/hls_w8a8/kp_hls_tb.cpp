/* kp_hls_tb.cpp — C-sim / co-sim testbench for the bounded W8/A8 kernels.
 * Loads the raw vectors produced by fixed_student_reference.py --vectors-c
 * and checks the HLS top outputs bit-exactly against {layer}_out.bin.
 * Build with -DVECTORS_DIR=\"<dir>\" (absolute path, forward slashes).
 */
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <cstdint>

extern "C" void kp_hls_dw3(const uint8_t *, const int8_t *, const int64_t *,
                           const int32_t *, int, uint8_t *);
extern "C" void kp_hls_pw3(const uint8_t *, const int8_t *, const int64_t *,
                           const int32_t *, int, uint8_t *);
extern "C" void kp_hls_stem(const uint8_t *, const int8_t *, const int64_t *,
                            const int32_t *, int, uint8_t *);
extern "C" void kp_hls_pw3_v2(const uint8_t *, const int8_t *, const int32_t *,
                              const int32_t *, int, uint8_t *);
extern "C" void kp_hls_pw3_v3(const uint8_t *, const int8_t *, const int32_t *,
                              const int32_t *, int, uint8_t *);

/* Build with -DVECTORS_DIR=<dir> (unquoted path; stringized below). */
#ifndef VECTORS_DIR
#define VECTORS_DIR .
#endif
#define KP_STR_(x) #x
#define KP_STR(x) KP_STR_(x)

static void *load(const char *name, const char *suffix, size_t bytes)
{
    char path[1024];
    void *buf = malloc(bytes ? bytes : 1);
    snprintf(path, sizeof path, "%s/%s_%s.bin", KP_STR(VECTORS_DIR), name, suffix);
    FILE *fp = fopen(path, "rb");
    if (!fp) { perror(path); exit(2); }
    if (fread(buf, 1, bytes, fp) != bytes) { fprintf(stderr, "short %s\n", path); exit(2); }
    fclose(fp);
    return buf;
}

static int check(const char *name, const uint8_t *got, const uint8_t *ref, size_t n)
{
    for (size_t e = 0; e < n; e++)
        if (got[e] != ref[e]) {
            fprintf(stderr, "HLS MISMATCH %s[%zu] got=%d want=%d\n",
                    name, e, got[e], ref[e]);
            return 1;
        }
    printf("HLS_LAYER %s values=%zu OK\n", name, n);
    return 0;
}

int main()
{
    const int F = 30;   /* all layers in the v3 manifest */
    int bad = 0;

    {
        uint8_t *in = (uint8_t *)load("dw_3", "in", 2 * 12 * 12 * 48);
        int8_t *w = (int8_t *)load("dw_3", "w", 3 * 3 * 48);
        int64_t *bias = (int64_t *)load("dw_3", "bias", 48 * sizeof(int64_t));
        int32_t *M = (int32_t *)load("dw_3", "M", 48 * sizeof(int32_t));
        uint8_t *ref = (uint8_t *)load("dw_3", "out", 2 * 6 * 6 * 48);
        uint8_t *got = (uint8_t *)calloc(2 * 6 * 6 * 48, 1);
        kp_hls_dw3(in, w, bias, M, F, got);
        bad += check("dw_3", got, ref, 2 * 6 * 6 * 48);
        free(in); free(w); free(bias); free(M); free(ref); free(got);
    }
    {
        uint8_t *in = (uint8_t *)load("pw_3", "in", 2 * 6 * 6 * 48);
        int8_t *w = (int8_t *)load("pw_3", "w", 48 * 64);
        int64_t *bias = (int64_t *)load("pw_3", "bias", 64 * sizeof(int64_t));
        int32_t *M = (int32_t *)load("pw_3", "M", 64 * sizeof(int32_t));
        uint8_t *ref = (uint8_t *)load("pw_3", "out", 2 * 6 * 6 * 64);
        uint8_t *got = (uint8_t *)calloc(2 * 6 * 6 * 64, 1);
        kp_hls_pw3(in, w, bias, M, F, got);
        bad += check("pw_3", got, ref, 2 * 6 * 6 * 64);
        free(in); free(w); free(bias); free(M); free(ref); free(got);
    }
    {
        uint8_t *in = (uint8_t *)load("stem", "in", 2 * 96 * 96 * 3);
        int8_t *w = (int8_t *)load("stem", "w", 3 * 3 * 3 * 16);
        int64_t *bias = (int64_t *)load("stem", "bias", 16 * sizeof(int64_t));
        int32_t *M = (int32_t *)load("stem", "M", 16 * sizeof(int32_t));
        uint8_t *ref = (uint8_t *)load("stem", "out", 2 * 48 * 48 * 16);
        uint8_t *got = (uint8_t *)calloc(2 * 48 * 48 * 16, 1);
        kp_hls_stem(in, w, bias, M, F, got);
        bad += check("stem", got, ref, 2 * 48 * 48 * 16);
        free(in); free(w); free(bias); free(M); free(ref); free(got);
    }

    /* dataflow v2: pw_3, batch=1 (sample 0 only), int32 shared accumulator.
     * bias_q (int64 in the vectors) must fit int32 per the <=24-bit bound. */
    {
        uint8_t *in2 = (uint8_t *)load("pw_3", "in", 2 * 6 * 6 * 48);
        int8_t *w2 = (int8_t *)load("pw_3", "w", 48 * 64);
        int64_t *bias64 = (int64_t *)load("pw_3", "bias", 64 * sizeof(int64_t));
        int32_t *M2 = (int32_t *)load("pw_3", "M", 64 * sizeof(int32_t));
        uint8_t *ref2 = (uint8_t *)load("pw_3", "out", 2 * 6 * 6 * 64);
        int32_t bias32[64];
        for (int i = 0; i < 64; i++) {
            if (bias64[i] > 2147483647LL || bias64[i] < -2147483648LL) {
                fprintf(stderr, "bias_q overflow at %d: %lld\n", i, (long long)bias64[i]);
                return 2;
            }
            bias32[i] = (int32_t)bias64[i];
        }
        uint8_t *got2 = (uint8_t *)calloc(6 * 6 * 64, 1);
        kp_hls_pw3_v2(in2, w2, bias32, M2, F, got2);
        bad += check("pw_3_v2", got2, ref2, 6 * 6 * 64);
        free(in2); free(w2); free(bias64); free(M2); free(ref2); free(got2);
    }

    /* dataflow v3: transposed weights (COUT,CIN), BRAM-resident tile.
     * Weight transpose is host-side (layout contract), values unchanged. */
    {
        uint8_t *in3 = (uint8_t *)load("pw_3", "in", 2 * 6 * 6 * 48);
        int8_t *w2 = (int8_t *)load("pw_3", "w", 48 * 64);
        int64_t *bias64b = (int64_t *)load("pw_3", "bias", 64 * sizeof(int64_t));
        int32_t *M3 = (int32_t *)load("pw_3", "M", 64 * sizeof(int32_t));
        uint8_t *ref3 = (uint8_t *)load("pw_3", "out", 2 * 6 * 6 * 64);
        int8_t wt[64 * 48];
        for (int ci = 0; ci < 48; ci++)
            for (int co = 0; co < 64; co++)
                wt[co * 48 + ci] = w2[ci * 64 + co];
        int32_t bias32b[64];
        for (int i = 0; i < 64; i++) bias32b[i] = (int32_t)bias64b[i];
        uint8_t *got3 = (uint8_t *)calloc(6 * 6 * 64, 1);
        kp_hls_pw3_v3(in3, wt, bias32b, M3, F, got3);
        bad += check("pw_3_v3", got3, ref3, 6 * 6 * 64);
        free(in3); free(w2); free(bias64b); free(M3); free(ref3); free(got3);
    }

    if (bad) {
        fprintf(stderr, "{\"hls_csim\": \"FAIL\", \"layers_bad\": %d}\n", bad);
        return 1;
    }
    printf("{\"hls_csim\": \"PASS\", \"layers\": 3}\n");
    return 0;
}
