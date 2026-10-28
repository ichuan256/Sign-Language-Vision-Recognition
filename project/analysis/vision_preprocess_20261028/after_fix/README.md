# Intermediate verification records

This folder contains the lint and XSim iterations produced while resolving the wrapper byte-count width warning. The authoritative final results are in [`../after_fix_final/`](../after_fix_final/): its `linter_final2.rpt` has 0 Vivado lint messages, and its XSim transcripts were run after the final TKEEP popcount implementation.

`linter.rpt` and `linter_final.rpt` are intermediate reports and each retains one QOR-1 precision warning. `linter_final2.rpt` is the final report. Vivado reports 0 total messages and omits the Expanded violations table; the helper parser misread unrelated waiver-template text for this zero-row report, so `messages.csv` is intentionally empty based on Vivado's authoritative 0-message count.

`xsim/` is an earlier passing run before the final popcount rewrite. Use only `../after_fix_final/xsim/` when reviewing final-source simulation.
