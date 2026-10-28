/* kp_hls_kernels.cpp — bounded HLS kernels for the W8/A8 contract, first
 * feasibility round: dw_3, pw_3 and stem (front-end large feature map),
 * sized to the real layer dimensions from the v3 vectors manifest.
 *
 * Numeric contract (must match kp_w8a8_contract.h / Python golden reference):
 *   acc = MAC(int8 w, uint8 x) + bias(int64), int64
 *   y   = sat(rne_shift(acc * M, F))          -- RNE after product, sat after
 *   conv layers clamp to [0,255]; TF/Keras 'same' padding semantics.
 *
 * This is a feasibility experiment (bounded synthesis numbers only); it is
 * NOT the final streaming architecture and NOT yet integrated with
 * kp_layer. Vitis HLS 2024.1 (F:/APP/Xilinx/Vitis_HLS/2024.1).
 */
#include <cstdint>
#include <cstring>

#include <ap_int.h>

static inline int kp_hls_rne_shift(int64_t q, int f)
{
#pragma HLS INLINE
    int neg = q < 0;
    uint64_t a = neg ? (uint64_t)(-q) : (uint64_t)q;
    uint64_t base = a >> f;
    uint64_t rem = a & ((((uint64_t)1) << f) - 1);
    uint64_t half = ((uint64_t)1) << (f - 1);
    int up = (rem > half) || (rem == half && (base & 1));
    int64_t r = (int64_t)(base + (up ? 1 : 0));
    return (int)(neg ? -r : r);
}

static constexpr int kp_hls_same_pad_before(int h, int k, int s)
{
    int out = (h + s - 1) / s;
    int t = (out - 1) * s + k - h;
    if (t < 0) t = 0;
    return t / 2;
}

/* Depthwise conv k=3, TF same padding, int64 acc, u8 output via M/F requant. */
template <int N, int H, int W, int C, int S>
void kp_hls_dw_core(const uint8_t *in, const int8_t *w, const int64_t *bias,
                    const int32_t *M, int F, uint8_t *out)
{
    constexpr int K = 3;
    constexpr int OH = (H + S - 1) / S;
    constexpr int OW = (W + S - 1) / S;
    constexpr int PT = kp_hls_same_pad_before(H, K, S);
    constexpr int PL = kp_hls_same_pad_before(W, K, S);
    constexpr int PH = H + PT + (PT + 1);   /* total pad <= K-1 <= 2 for our sizes */
    constexpr int PW_ = W + PL + (PL + 1);
    uint8_t xp[N][PH][PW_][C];
#pragma HLS ARRAY_PARTITION variable = xp dim = 3 complete
    memset(xp, 0, sizeof xp);           /* padding taps must read as zero */

    for (int n = 0; n < N; n++)
        for (int i = 0; i < H; i++)
            for (int j = 0; j < W; j++)
                for (int c = 0; c < C; c++)
                    xp[n][i + PT][j + PL][c] = in[(((n * H) + i) * W + j) * C + c];

    for (int n = 0; n < N; n++)
        for (int i = 0; i < OH; i++)
            for (int j = 0; j < OW; j++)
                for (int c = 0; c < C; c++) {
#pragma HLS PIPELINE II = 1
                    int64_t acc = bias[c];
                    for (int u = 0; u < K; u++)
                        for (int v = 0; v < K; v++)
                            acc += (int64_t)xp[n][i * S + u][j * S + v][c] *
                                   (int64_t)w[(u * K + v) * C + c];
                    int q = kp_hls_rne_shift(acc * M[c], F);
                    out[(((n * OH) + i) * OW + j) * C + c] =
                        (uint8_t)(q < 0 ? 0 : (q > 255 ? 255 : q));
                }
}

/* Pointwise (1x1) conv, u8 output via M/F requant. */
template <int N, int H, int W, int CIN, int COUT>
void kp_hls_pw_core(const uint8_t *in, const int8_t *w, const int64_t *bias,
                    const int32_t *M, int F, uint8_t *out)
{
    for (int n = 0; n < N; n++)
        for (int i = 0; i < H; i++)
            for (int j = 0; j < W; j++)
                for (int co = 0; co < COUT; co++) {
#pragma HLS PIPELINE II = 1
                    int64_t acc = bias[co];
                    for (int ci = 0; ci < CIN; ci++)
                        acc += (int64_t)in[(((n * H) + i) * W + j) * CIN + ci] *
                               (int64_t)w[ci * COUT + co];
                    int q = kp_hls_rne_shift(acc * M[co], F);
                    out[(((n * H) + i) * W + j) * COUT + co] =
                        (uint8_t)(q < 0 ? 0 : (q > 255 ? 255 : q));
                }
}

/* Standard conv k=3 (stem), TF same padding, u8 output via M/F requant. */
template <int N, int H, int W, int CIN, int S, int COUT>
void kp_hls_conv_core(const uint8_t *in, const int8_t *w, const int64_t *bias,
                      const int32_t *M, int F, uint8_t *out)
{
    constexpr int K = 3;
    constexpr int OH = (H + S - 1) / S;
    constexpr int OW = (W + S - 1) / S;
    constexpr int PT = kp_hls_same_pad_before(H, K, S);
    constexpr int PL = kp_hls_same_pad_before(W, K, S);
    constexpr int PH = H + PT + (PT + 1);
    constexpr int PW_ = W + PL + (PL + 1);
    uint8_t xp[N][PH][PW_][CIN];
#pragma HLS ARRAY_PARTITION variable = xp dim = 3 complete
    memset(xp, 0, sizeof xp);           /* padding taps must read as zero */

    for (int n = 0; n < N; n++)
        for (int i = 0; i < H; i++)
            for (int j = 0; j < W; j++)
                for (int c = 0; c < CIN; c++)
                    xp[n][i + PT][j + PL][c] = in[(((n * H) + i) * W + j) * CIN + c];

    for (int n = 0; n < N; n++)
        for (int i = 0; i < OH; i++)
            for (int j = 0; j < OW; j++)
                for (int co = 0; co < COUT; co++) {
#pragma HLS PIPELINE II = 1
                    int64_t acc = bias[co];
                    for (int u = 0; u < K; u++)
                        for (int v = 0; v < K; v++)
                            for (int ci = 0; ci < CIN; ci++)
                                acc += (int64_t)xp[n][i * S + u][j * S + v][ci] *
                                       (int64_t)w[((u * K + v) * CIN + ci) * COUT + co];
                    int q = kp_hls_rne_shift(acc * M[co], F);
                    out[(((n * OH) + i) * OW + j) * COUT + co] =
                        (uint8_t)(q < 0 ? 0 : (q > 255 ? 255 : q));
                }
}

/* Fixed-config tops matching the v3 vectors manifest. */
extern "C" void kp_hls_dw3(const uint8_t *in, const int8_t *w, const int64_t *bias,
                           const int32_t *M, int F, uint8_t *out)
{
#pragma HLS INTERFACE m_axi port = in bundle = gmem depth = 2 * 12 * 12 * 48
#pragma HLS INTERFACE m_axi port = w bundle = gmem depth = 3 * 3 * 48
#pragma HLS INTERFACE m_axi port = bias bundle = gmem depth = 48
#pragma HLS INTERFACE m_axi port = M bundle = gmem depth = 48
#pragma HLS INTERFACE m_axi port = out bundle = gmem depth = 2 * 6 * 6 * 48
#pragma HLS INTERFACE s_axilite port = F bundle = ctrl
#pragma HLS INTERFACE s_axilite port = return bundle = ctrl
    kp_hls_dw_core<2, 12, 12, 48, 2>(in, w, bias, M, F, out);
}

extern "C" void kp_hls_pw3(const uint8_t *in, const int8_t *w, const int64_t *bias,
                           const int32_t *M, int F, uint8_t *out)
{
#pragma HLS INTERFACE m_axi port = in bundle = gmem depth = 2 * 6 * 6 * 48
#pragma HLS INTERFACE m_axi port = w bundle = gmem depth = 48 * 64
#pragma HLS INTERFACE m_axi port = bias bundle = gmem depth = 64
#pragma HLS INTERFACE m_axi port = M bundle = gmem depth = 64
#pragma HLS INTERFACE m_axi port = out bundle = gmem depth = 2 * 6 * 6 * 64
#pragma HLS INTERFACE s_axilite port = F bundle = ctrl
#pragma HLS INTERFACE s_axilite port = return bundle = ctrl
    kp_hls_pw_core<2, 6, 6, 48, 64>(in, w, bias, M, F, out);
}

extern "C" void kp_hls_stem(const uint8_t *in, const int8_t *w, const int64_t *bias,
                            const int32_t *M, int F, uint8_t *out)
{
#pragma HLS INTERFACE m_axi port = in bundle = gmem depth = 2 * 96 * 96 * 3
#pragma HLS INTERFACE m_axi port = w bundle = gmem depth = 3 * 3 * 3 * 16
#pragma HLS INTERFACE m_axi port = bias bundle = gmem depth = 16
#pragma HLS INTERFACE m_axi port = M bundle = gmem depth = 16
#pragma HLS INTERFACE m_axi port = out bundle = gmem depth = 2 * 48 * 48 * 16
#pragma HLS INTERFACE s_axilite port = F bundle = ctrl
#pragma HLS INTERFACE s_axilite port = return bundle = ctrl
    kp_hls_conv_core<2, 96, 96, 3, 2, 16>(in, w, bias, M, F, out);
}

/* ---------------------------------------------------------------------------
 * Dataflow v2: pointwise layer, batch=1, partial-unrolled int8 MAC array.
 *
 * Accumulator: int32. Per-layer conservative MAC+bias bound is <=24 bits for
 * the frozen W8/A8 weights (see kp_integer_student96_w8a8_20261028_v3
 * report.json), so int32 accumulation is bit-identical to the int64 golden
 * reference. The requant product acc*M keeps int64 (one op per output).
 * CIN unrolled by P DSP lanes; COUT loop pipelined II=1.
 * ------------------------------------------------------------------------- */
template <int H, int W, int CIN, int COUT, int P>
void kp_hls_pw_core_v2(const uint8_t *in, const int8_t *w, const int32_t *bias,
                       const int32_t *M, int F, uint8_t *out)
{
    /* Pipeline applies to the CIN-chunk loop: P lanes per cycle, CIN/P
     * cycles per output. v2a-c put II=1 on the COUT loop, which forced HLS
     * to duplicate the MAC array (35 DSP, 21K LUT, constraints unmet). */
    for (int n = 0; n < H * W; n++) {
        for (int co = 0; co < COUT; co++) {
            int32_t acc = bias[co];
            for (int ci = 0; ci < CIN; ci += P) {
#pragma HLS PIPELINE II = 1
                for (int p = 0; p < P; p++) {
#pragma HLS UNROLL
                    /* 8x8 -> 16 via ap_int: C integer promotion would
                     * silently rebuild a 32x32 multiplier. */
                    ap_int<16> xa = (ap_int<16>)in[n * CIN + ci + p];
                    ap_int<16> xw = (ap_int<16>)w[(ci + p) * COUT + co];
                    acc += (int32_t)(xa * xw);
                }
            }
            int64_t prod = (int64_t)acc * M[co];
            int q = kp_hls_rne_shift(prod, F);
            out[n * COUT + co] = (uint8_t)(q < 0 ? 0 : (q > 255 ? 255 : q));
        }
    }
}

extern "C" void kp_hls_pw3_v2(const uint8_t *in, const int8_t *w, const int32_t *bias,
                              const int32_t *M, int F, uint8_t *out)
{
#pragma HLS INTERFACE m_axi port = in bundle = gmem depth = 6 * 6 * 48
#pragma HLS INTERFACE m_axi port = w bundle = gmem depth = 48 * 64
#pragma HLS INTERFACE m_axi port = bias bundle = gmem depth = 64
#pragma HLS INTERFACE m_axi port = M bundle = gmem depth = 64
#pragma HLS INTERFACE m_axi port = out bundle = gmem depth = 6 * 6 * 64
#pragma HLS INTERFACE s_axilite port = F bundle = ctrl
#pragma HLS INTERFACE s_axilite port = return bundle = ctrl
    kp_hls_pw_core_v2<6, 6, 48, 64, 16>(in, w, bias, M, F, out);
}

/* ---------------------------------------------------------------------------
 * Dataflow v3: weights transposed to (COUT,CIN); input tile and weights
 * burst-loaded into BRAM once, then the chunk loop pipelines at II=1 from
 * partitioned local arrays (v2d's II=32 was single-port m_axi serialization).
 * ------------------------------------------------------------------------- */
template <int H, int W, int CIN, int COUT, int P>
void kp_hls_pw_core_v3(const uint8_t *in, const int8_t *wt, const int32_t *bias,
                       const int32_t *M, int F, uint8_t *out)
{
    uint8_t lin[H * W * CIN];
    int8_t lwt[COUT * CIN];
#pragma HLS ARRAY_PARTITION variable = lin cyclic factor = P dim = 1
#pragma HLS ARRAY_PARTITION variable = lwt cyclic factor = P dim = 1
    memcpy(lin, in, sizeof lin);
    memcpy(lwt, wt, sizeof lwt);

    for (int n = 0; n < H * W; n++) {
        for (int co = 0; co < COUT; co++) {
            int32_t acc = bias[co];
            for (int ci = 0; ci < CIN; ci += P) {
#pragma HLS PIPELINE II = 1
                for (int p = 0; p < P; p++) {
#pragma HLS UNROLL
                    ap_int<16> xa = (ap_int<16>)lin[n * CIN + ci + p];
                    ap_int<16> xw = (ap_int<16>)lwt[co * CIN + ci + p];
                    acc += (int32_t)(xa * xw);
                }
            }
            int64_t prod = (int64_t)acc * M[co];
            int q = kp_hls_rne_shift(prod, F);
            out[n * COUT + co] = (uint8_t)(q < 0 ? 0 : (q > 255 ? 255 : q));
        }
    }
}

extern "C" void kp_hls_pw3_v3(const uint8_t *in, const int8_t *wt, const int32_t *bias,
                              const int32_t *M, int F, uint8_t *out)
{
#pragma HLS INTERFACE m_axi port = in bundle = gmem depth = 6 * 6 * 48
#pragma HLS INTERFACE m_axi port = wt bundle = gmem depth = 64 * 48
#pragma HLS INTERFACE m_axi port = bias bundle = gmem depth = 64
#pragma HLS INTERFACE m_axi port = M bundle = gmem depth = 64
#pragma HLS INTERFACE m_axi port = out bundle = gmem depth = 6 * 6 * 64
#pragma HLS INTERFACE s_axilite port = F bundle = ctrl
#pragma HLS INTERFACE s_axilite port = return bundle = ctrl
    kp_hls_pw_core_v3<6, 6, 48, 64, 16>(in, wt, bias, M, F, out);
}
