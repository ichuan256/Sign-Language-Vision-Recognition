# Revision-control audit — vision_preprocess

## Result

The independent preprocessing RTL/TB/scripts/oracle/evidence set is present and reproducible in the working tree, but it is not yet included in Git. The scoped files are currently untracked; the temporary Vivado project under `project/_tmp/` is ignored and contains machine-specific absolute paths.

## Rebuild path

- `project/fpga/scripts/vision_preprocess_prepare.tcl` creates a fresh `xc7z020clg400-1` project and registers the three RTL files and three testbenches.
- `project/fpga/scripts/vision_preprocess_sim.tcl` runs the three bounded XSim tests.
- `project/fpga/scripts/vision_preprocess_ooc.tcl` creates an in-memory OOC project, runs synthesis/opt/place/route, and writes reports/checkpoint evidence.
- `project/scripts/vision_preprocess/generate_vectors.py` generates the deterministic 16-case vector set.

## Gaps

1. The current prepare script refuses to reuse an existing XPR and defaults to a fixed `_tmp/vision_preprocess_20261028` directory; a clean-checkout README command should generate vectors and choose a new output directory.
2. The OOC script writes `routed.dcp` and reports before returning an error on negative setup slack. Its result is therefore a failed timing gate with useful evidence, not a passing build.
3. The XPR is a temporary verification artifact and should not be treated as the revision-controlled source of truth.

No source files were modified by this audit.
