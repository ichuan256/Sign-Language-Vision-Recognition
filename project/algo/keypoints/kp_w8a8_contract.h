/* kp_w8a8_contract.h — W8/A8 requant contract reference (isolated candidate).
 *
 * 2026-10-28: the legacy kp_layer/kp_gemm_tile interface (bias + shift only)
 * does NOT cover the v2/v3 requant contract (per-channel multiplier M,
 * round-half-to-even, then saturation). This header is the standalone
 * candidate for the new contract; it is a plain-C reference for C-simulation
 * parity against project/scripts/keypoints/fixed_student_reference.py,
 * not yet an HLS kernel and not connected to kp_layer.
 *
 * Contract (must match the Python golden reference bit-for-bit):
 *   y = sat(rne_shift(acc * M, F))        -- RNE AFTER product, sat AFTER RNE
 *   activation layers:      sat to [0, 255]
 *   coordinate head (int16): sat to [-32768, 32767]
 *   rne_shift: arithmetic round-half-to-even of a signed two's-complement
 *   value divided by 2^F (symmetric: rne(-x) == -rne(x)).
 *
 * Accumulator scope: the int32 claim proven so far covers MAC+bias only, for
 * the frozen W8/A8 weights with full 255-code inputs. The product acc*M is
 * kept in int64 here; its required width is a separate proof obligation
 * (see product_bits / measured_product_bits in the Python report).
 */
#ifndef KP_W8A8_CONTRACT_H
#define KP_W8A8_CONTRACT_H

#include <stdint.h>
#include <stddef.h>

static inline int64_t kp_rne_shift(int64_t q, int f)
{
    /* Round half to even of q / 2^f, exact integer arithmetic. */
    int neg = q < 0;
    uint64_t a = neg ? (uint64_t)(-q) : (uint64_t)q;
    uint64_t base = a >> f;
    uint64_t rem = a & ((((uint64_t)1) << f) - 1);
    uint64_t half = ((uint64_t)1) << (f - 1);
    int up = (rem > half) || (rem == half && (base & 1));
    int64_t r = (int64_t)(base + (up ? 1 : 0));
    return neg ? -r : r;
}

static inline int32_t kp_requant_u8(int64_t acc, int32_t M, int f, int *saturated)
{
    /* acc * M in int64 (width proven separately), RNE, then clamp to u8. */
    int64_t q = kp_rne_shift(acc * (int64_t)M, f);
    int64_t c = q < 0 ? 0 : (q > 255 ? 255 : q);
    *saturated |= (c != q);
    return (int32_t)c;
}

static inline int32_t kp_requant_i16(int64_t acc, int32_t M, int f, int *saturated)
{
    /* Coordinate-head export: y16 = sat(rne_shift(acc*M, f), -32768, 32767). */
    int64_t q = kp_rne_shift(acc * (int64_t)M, f);
    int64_t c = q < -32768 ? -32768 : (q > 32767 ? 32767 : q);
    *saturated |= (c != q);
    return (int32_t)c;
}

#endif /* KP_W8A8_CONTRACT_H */

#ifdef KP_W8A8_SELF_TEST
/* Standalone boundary parity test: compile with -DKP_W8A8_SELF_TEST and run.
 * Mirrors --self-test of the Python golden reference. */
#include <stdio.h>
#include <stdlib.h>

static void check(int cond, const char *what)
{
    if (!cond) { fprintf(stderr, "FAIL: %s\n", what); exit(1); }
}

int main(void)
{
    /* RNE edges, F=4 */
    check(kp_rne_shift(24, 4) == 2,  "1.5 -> 2 (even)");
    check(kp_rne_shift(40, 4) == 2,  "2.5 -> 2 (even)");
    check(kp_rne_shift(8, 4) == 0,   "0.5 -> 0 (even)");
    check(kp_rne_shift(-24, 4) == -2, "-1.5 -> -2");
    check(kp_rne_shift(-40, 4) == -2, "-2.5 -> -2");
    check(kp_rne_shift(17, 4) == 1,  "1.0625 -> 1");
    /* saturation AFTER rounding, both polarities */
    {
        int sat = 0;
        check(kp_requant_u8(8, 3, 4, &sat) == 2 && !sat, "u8 chain 1.5");
        check(kp_requant_u8(-8, 3, 4, &sat) == 0, "u8 clamps negative to 0");
        check(kp_requant_u8((300 << 4) / 3 * 3, 3, 4, &sat) == 255 && sat,
              "u8 saturates after RNE");
    }
    {
        int sat = 0;
        check(kp_requant_i16(8, 3, 4, &sat) == 2 && !sat, "i16 chain 1.5");
        check(kp_requant_i16(-8, 3, 4, &sat) == -2, "i16 -1.5");
        check(kp_requant_i16(((int64_t)2000000 << 4), 1, 4, &sat) == 32767 && sat,
              "i16 saturates high");
        check(kp_requant_i16(-(((int64_t)2000000 << 4)), 1, 4, &sat) == -32768 && sat,
              "i16 saturates low");
    }
    /* f=1 and f=30 spot checks against exact values */
    check(kp_rne_shift(1, 1) == 0, "0.5 -> 0 (even), f=1");
    check(kp_rne_shift(3, 1) == 2, "1.5 -> 2 (even), f=1");
    check(kp_rne_shift((int64_t)5 << 30, 30) == 5, "exact integer passthrough");
    puts("{\"self_test\": \"PASS\"}");
    return 0;
}
#endif
