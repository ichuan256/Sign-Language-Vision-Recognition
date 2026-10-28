# RTL Lint Report — vision_preprocess_axi

## Scope

Vivado 2024.1 `synth_design -lint` checked the current `vision_preprocess_axi` RTL for `xc7z020clg400-1`. The canonical parsed rows are in [`messages.csv`](messages.csv); [`linter.rpt`](linter.rpt) is the raw report.

## Summary

| Severity | Count |
|---|---:|
| Error | 0 |
| Critical Warning | 0 |
| Warning | 7 |

| Rule | Count | Files |
|---|---:|---|
| ASSIGN-6 | 5 | `vision_preprocess_axi.v`, `vision_rgb565_affine.v` |
| QOR-1 | 1 | `vision_preprocess_axi.v` |
| ASSIGN-1 | 1 | `vision_rgb565_affine.v` |

No syntax, latch, mixed-clock-edge, or reset lint violation was reported.

## Findings

### ASSIGN-6 — `core_busy` is assigned but not read

**CSV row:** 1 · **File:** [vision_preprocess_axi.v:55](../../../../fpga/rtl/vision_preprocess/vision_preprocess_axi.v#L55)

```diff
-    wire core_busy, core_done; // `core_busy` is never read by the wrapper
+    wire core_done;            // Remove the dead local net after confirming the wrapper owns `busy`
```

The sampler output is connected at line 77, while the wrapper's public `busy` register is maintained by the AXI-Lite control block and includes the output-drain phase. The safe choices are to remove the unused connection or deliberately use `core_busy` in a consistency/status check. No RTL was changed.

### QOR-1 — precision loss in the byte-count adder

**CSV row:** 2 · **Source use:** [vision_preprocess_axi.v:148](../../../../fpga/rtl/vision_preprocess/vision_preprocess_axi.v#L148)

The declaration is at line 135 and the value is consumed at line 148:

```diff
-    wire [2:0] bytes_this_beat = {2'b00,m_axis_tkeep[0]}+{2'b00,m_axis_tkeep[1]}+{2'b00,m_axis_tkeep[2]}+{2'b00,m_axis_tkeep[3]}; // 4-bit intermediate is narrowed to 3 bits
+    wire [3:0] bytes_this_beat = {2'b00,m_axis_tkeep[0]}+{2'b00,m_axis_tkeep[1]}+{2'b00,m_axis_tkeep[2]}+{2'b00,m_axis_tkeep[3]}; // Preserve the legal 0..4 result
```

A 4-bit result is required to represent four valid bytes. This is a bookkeeping path; widening it does not change AXI output behavior. Re-run lint and synthesis after applying the candidate change.

### ASSIGN-1 — address expression wider than the consumed 32-bit AXI address

**CSV row:** 3 · **File:** [vision_rgb565_affine.v:64](../../../../fpga/rtl/vision_preprocess/vision_rgb565_affine.v#L64)

```verilog
wire [63:0] sample_addr_wide = {32'd0,src_base}
                      + ({32'd0,src_stride} * {52'd0,sample_y[11:0]})
                      + ({52'd0,sample_x[11:0]} << 1);
wire [31:0] sample_word_addr = {sample_addr_wide[31:2],2'b00};
```

The interface contract is explicitly 32-bit and the start-time frame-span check rejects a source buffer crossing `2^32`. Therefore, blindly widening the AXI address is not a valid automatic fix. Treat this as a design-contract review item: either make the upper-bit-zero proof explicit and waive the intentional projection, or redesign the memory interface for a wider address. No paste-ready RTL change is recommended without that decision.

### ASSIGN-6 — low bits of `rounded_r` are unused

**CSV row:** 6 · **File:** [vision_rgb565_affine.v:95](../../../../fpga/rtl/vision_preprocess/vision_rgb565_affine.v#L95)

```diff
-    wire [17:0] rounded_r = sum_r + 18'd512; // Only [17:10] is consumed at the output
+    wire [7:0] rounded_r = (sum_r + 18'd512) >> 10; // Keep only the emitted channel byte
```

The output expression must change with the declaration:

```diff
-                    : {rounded_b[17:10],rounded_g[17:10],rounded_r[17:10]};
+                    : {rounded_b,rounded_g,rounded_r};
```

This is bit-equivalent to the current rounding/truncation for the documented channel range. Apply the analogous change to `rounded_g` and `rounded_b` if you choose this cleanup.

### ASSIGN-6 — low bits of `rounded_g` are unused

**CSV row:** 5 · **File:** [vision_rgb565_affine.v:96](../../../../fpga/rtl/vision_preprocess/vision_rgb565_affine.v#L96)

```diff
-    wire [17:0] rounded_g = sum_g + 18'd512; // Only [17:10] is consumed at the output
+    wire [7:0] rounded_g = (sum_g + 18'd512) >> 10; // Keep only the emitted channel byte
```

Use the same output-concatenation change shown above. No RTL was changed during this check.

### ASSIGN-6 — low bits of `rounded_b` are unused

**CSV row:** 4 · **File:** [vision_rgb565_affine.v:97](../../../../fpga/rtl/vision_preprocess/vision_rgb565_affine.v#L97)

```diff
-    wire [17:0] rounded_b = sum_b + 18'd512; // Only [17:10] is consumed at the output
+    wire [7:0] rounded_b = (sum_b + 18'd512) >> 10; // Keep only the emitted channel byte
```

Use the same output-concatenation change shown above. No RTL was changed during this check.

### ASSIGN-6 — `sample_addr_wide[0]` is unused

**CSV row:** 7 · **File:** [vision_rgb565_affine.v:64](../../../../fpga/rtl/vision_preprocess/vision_rgb565_affine.v#L64)

```diff
-    wire [63:0] sample_addr_wide = ...; // Bit 0 is not read; bit 1 selects the RGB565 halfword
+    wire [63:0] sample_addr_wide = ...; // Keep the byte address and document/verify the even-byte invariant
```

Bit 0 should be zero because the pixel byte address is formed as `2 * sample_x`; it is not safe to remove the bit without preserving the halfword select at bit 1. This warning can be waived after the address-alignment invariant is checked, or handled with an explicit assertion/check in the integration contract.

## Priority

1. Review `sample_addr_wide`/`sample_word_addr` together: the width warning and unused-bit warning concern the same 32-bit address contract.
2. Widen `bytes_this_beat` to 4 bits; this is the lowest-risk warning and may remove the QoR warning.
3. Remove or consume `core_busy` only after confirming the wrapper's `busy` semantics.
4. Narrow the rounded channels only if the output bit-equivalence is covered by the sampler regression.

## Verification status

No RTL was modified. These are report-only candidate changes. The current RTL still produces 7 lint warnings.
