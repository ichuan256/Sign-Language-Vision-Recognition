# Revision-control follow-up

The original audit in `../revision_control_audit.md` describes the pre-fix state and remains historical evidence. The reproducibility gaps identified there are addressed for the independent verification line:

- `project/board/vision_preprocess/README.md` now documents the clean-checkout PowerShell/Tcl sequence, dependencies, unique output directories, lint, XSim and OOC acceptance conditions.
- `vision_preprocess_prepare.tcl` and `vision_preprocess_ooc.tcl` use an explicit fixed source manifest for the three RTL files and accept caller-provided output/vector directories. They reject missing source files and do not treat a routed DCP as a timing pass.
- The final source/testbench/script hashes are recorded in [`source_sha256.txt`](source_sha256.txt). The final vector manifest is archived beside this summary; generated `.mem` fixtures and Vivado project directories remain temporary artifacts under `project/_tmp/` and are not the source of truth.
- Final evidence is isolated in this `after_fix_final/` directory; the original baseline evidence is not overwritten.

The original audit's untracked status described the pre-fix workspace. This follow-up packages the independent verification sources and final evidence for version control.
