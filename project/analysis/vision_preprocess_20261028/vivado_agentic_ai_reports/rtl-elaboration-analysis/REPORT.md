# RTL Elaboration Analysis Report — vision_preprocess_axi

## Summary

This report covers the non-INFO diagnostics parsed from the saved Vivado session log. The session contains one failed setup attempt followed by successful lint, synthesis, and XSim commands.

| Severity | Count | Actionable | Advisory |
|---|---:|---:|---:|
| Error | 1 | 0 | 1 |
| Critical Warning | 0 | 0 | 0 |
| Warning | 23 | 0 | 23 |

The single error is `[Synth 8-734] Invalid parameter 'linterCsvFile'`, caused by using a CSV-only linter parameter that Vivado 2024.1 does not support. After removing that parameter, the same lint command completed with 0 errors and 7 lint warnings. The 22 `[Synth 8-3917]` warnings are constant-driven AXI read-control fields; the design intentionally implements one-beat reads. `[Synth 8-7080]` says the small design did not meet Vivado's parallel-synthesis heuristic and is not a functional failure. The three sections below account for 24 non-INFO CSV rows: 1 + 22 + 1.

## Message distribution

| ID | Severity | Count | Interpretation |
|---|---|---:|---|
| 734 | ERROR | 1 | Invalid linter parameter in the first invocation |
| 3917 | WARNING | 22 | Fixed AXI single-beat control fields |
| 7080 | WARNING | 1 | Parallel synthesis heuristic not met |

## Fixes and advisories

### [Synth 8-734] Invalid parameter `linterCsvFile`

**CSV S.No:** 4

**File:** Vivado session command; no RTL location was reported.

**Message:** `ERROR: [Synth 8-734] Invalid parameter 'linterCsvFile'`

**Root cause:** Vivado 2024.1 does not accept the CSV-format parameter used by the first lint attempt. The follow-up invocation removed it and produced a valid `linter.rpt`.

**Problematic command:**

```diff
- set_param synth.elaboration.rodinMoreOptions "rt::set_parameter linterCsvFile true"  // unsupported in Vivado 2024.1
+ set_param synth.elaboration.rodinMoreOptions {}  // use the 2024.1 .rpt output and parse it externally
```

**Corrected command:**

```tcl
set_param synth.elaboration.rodinMoreOptions {}
```

> You can copy the command above into the Vivado Tcl console before rerunning lint.

**Rationale:** This is a tool/version invocation issue, not a design elaboration error. The valid lint report is [`../rtl-lint/linter.rpt`](../rtl-lint/linter.rpt).

### [Synth 8-3917] Constant-driven AXI read-control fields

**Occurrences:** 22 (CSV S.No. 22–43)

| S.No. | Port bit/field | Source |
|---:|---|---|
| 22 | `m_axi_read_arid[0]` | [vision_preprocess_axi.v:67](../../../../fpga/rtl/vision_preprocess/vision_preprocess_axi.v#L67) |
| 23–30 | `m_axi_read_arlen[7:0]` | [vision_preprocess_axi.v:68](../../../../fpga/rtl/vision_preprocess/vision_preprocess_axi.v#L68) |
| 31–33 | `m_axi_read_arsize[2:0]` | [vision_preprocess_axi.v:69](../../../../fpga/rtl/vision_preprocess/vision_preprocess_axi.v#L69) |
| 34–35 | `m_axi_read_arburst[1:0]` | [vision_preprocess_axi.v:70](../../../../fpga/rtl/vision_preprocess/vision_preprocess_axi.v#L70) |
| 36 | `m_axi_read_arlock` | [vision_preprocess_axi.v:71](../../../../fpga/rtl/vision_preprocess/vision_preprocess_axi.v#L71) |
| 37–40 | `m_axi_read_arcache[3:0]` | [vision_preprocess_axi.v:72](../../../../fpga/rtl/vision_preprocess/vision_preprocess_axi.v#L72) |
| 41–43 | `m_axi_read_arprot[2:0]` | [vision_preprocess_axi.v:73](../../../../fpga/rtl/vision_preprocess/vision_preprocess_axi.v#L73) |

**Message:** `design vision_preprocess_axi has port <field> driven by constant <value>`

**Root cause:** The adapter intentionally issues a single 32-bit, incrementing, non-locked read. Fixed ID, length, size, burst, cache, and protection fields are therefore constants.

**Actual RTL:**

```diff
-    assign m_axi_read_arid=1'b0;       // fixed single-outstanding request ID
-    assign m_axi_read_arlen=8'd0;      // one beat
-    assign m_axi_read_arsize=3'b010;   // 32-bit beat
-    assign m_axi_read_arburst=2'b01;   // incrementing burst type
-    assign m_axi_read_arlock=1'b0;
-    assign m_axi_read_arcache=4'b0011;
-    assign m_axi_read_arprot=3'b000;
+    // Keep these constants: they encode the one-beat AXI read contract.  // no functional change
```

**Recommendation:** retain the constants and document/waive this warning for the adapter. Removing the ports would break the AXI master interface. Revisit only if the design changes to variable-length or cacheable bursts.

**Corrected code:**

```verilog
assign m_axi_read_arid=1'b0;
assign m_axi_read_arlen=8'd0;
assign m_axi_read_arsize=3'b010;
assign m_axi_read_arburst=2'b01;
assign m_axi_read_arlock=1'b0;
assign m_axi_read_arcache=4'b0011;
assign m_axi_read_arprot=3'b000;
```

> The block above can be copied into `vision_preprocess_axi.v` at lines 67–73; it preserves the current one-beat AXI contract.

### [Synth 8-7080] Parallel synthesis criteria is not met

**CSV S.No:** 21

**File:** no RTL location; this is a synthesis heuristic message.

**Message:** `WARNING: [Synth 8-7080] Parallel synthesis criteria is not met`

**Root cause:** The module is small and did not meet Vivado's threshold for parallel synthesis. The successful synthesis log reports 0 errors and 0 critical warnings; this warning does not indicate incorrect RTL.

**Recommended action:** no RTL change. Keep the project thread count at the constrained value used for reproducibility, or remove the constraint only if build time matters more than deterministic resource use.

```diff
- set_param general.maxThreads 2  // current reproducible setting
+ # no RTL change; this is an informational synthesis heuristic
```

> No RTL paste is required for this message; the source design is unaffected.

## Verification evidence

- Parsed lint: [`../rtl-lint/messages.csv`](../rtl-lint/messages.csv), 7 warnings, 0 errors.
- Full synthesis/elaboration: 0 errors, 0 critical warnings, 23 warnings; synthesis completed and produced a netlist.
- Behavioral XSim: all three testbenches passed with explicit `TEST_PASS` markers.
- Existing OOC implementation evidence: 3,568 fully routed nets and 0 routing errors; setup timing is not met (WNS −10.558 ns, 330 failing endpoints, TNS −2492.229 ns at the 10 ns constraint).

## Conclusions

The current PL preprocessing RTL is syntactically/elaborationally buildable and functionally passes the available self-checking simulation suite. It is not timing-ready at the documented 100 MHz OOC constraint. The address-width lint warning and the 18-cycle sampler critical path should be resolved or explicitly accepted before integrating this module into a clocked PL data path.


