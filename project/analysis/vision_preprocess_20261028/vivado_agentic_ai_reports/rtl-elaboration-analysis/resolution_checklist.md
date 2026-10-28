# Resolution Checklist

## HAS RESOLUTION FILE
| ID | Severity | Short Name | Resolution File | Loaded? |
|---|---|---|---|---|
| 734 | ERROR | Invalid parameter | `resolution/8-734.md` | [x] |
| 3917 | WARNING | Constant-driven top port | `resolution/8-3917.md` | [x] |

## NO RESOLUTION FILE (use Vivado documentation or own analysis)
| ID | Severity | Description | Source |
|---|---|---|---|
| 7080 | WARNING | Parallel synthesis criteria is not met | own analysis; no matching resolution file |

The 8-734 occurrence came from the first lint invocation's unsupported `linterCsvFile` parameter in Vivado 2024.1. It is an invocation/environment issue, not an RTL source violation. The later lint invocation completed successfully.

The loaded guides describe generic parameter/port cases. Here 8-734 is a tool-version parameter rejection (not an RTL module-parameter override), and 8-3917 reports intentionally constant AXI fields (not dangling functional ports); the exact observed log and top-level interface take precedence over the generic text.
