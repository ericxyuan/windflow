# Rotor selection — complete saved study

Study date: **9 October 2026**. This folder preserves the saved fan-selection work for Windflow, including the original user request and approval to rearrange the layout within a 200 mm total height.

Start with the [full fan shape, motor, airspeed, noise and boost analysis](docs/fan-shape-analysis-2026-10-09.md).

## Saved work

- **Report:** the full original analysis, copied byte for byte.
- **Diagrams:** both final figures in PNG and editable vector SVG form under [the study outputs](docs/fan-shape-study-2026-10-09/).
- **Calculations:** the complete [JSON record](docs/fan-shape-study-2026-10-09/calculations.json) and all three CSV tables.
- **Calculation source:** the exact [original study script](tools/analyse_fan_shapes.py), with a pinned [dependency list](tools/requirements.txt).
- **Source snapshots:** original motor/ESC specifications, rotor/head parameters, assembly/export reports, relevant CAD source and existing rotor STEP, control configuration and implementation, and consulted project documentation. Their original relative paths are preserved so the report and calculation remain self-contained.
- **Conversation:** [the original request, progress updates, layout approval and final response](history/conversation.md), plus the [final response separately](history/original-final-response.md).
- **Research history:** [all retained calls and returned text](history/research-and-tool-results.md), the structured [study log](history/study-log.jsonl), all **3 original edit patches**, readable initial and final source/report revisions, and **3 viewed-image snapshots**, including the earlier chart version.
- **References:** [source links and retrieval context](references/sources.md).
- **Verification:** copy hashes, report-link checks, runtime details and a complete file manifest.

The recommended 150 mm five-blade swept/twisted axial stage and 195 mm product height are analytical design proposals. This archive contains no new CFD, physical fan/noise measurements or revised clearance-checked production CAD.

## Reproduction

Run `tools/analyse_fan_shapes.py` from this folder with Python and the dependencies in `tools/requirements.txt`. It uses the preserved source snapshots and writes the calculations, CSV tables and figures to `docs/fan-shape-study-2026-10-09`. The original run's environment is recorded in [runtime.json](verification/runtime.json).

Copies retain the original bytes and relative structure. The original workspace files remain available. The workspace README is preserved separately as [workspace-README.md](source-snapshots/workspace-README.md) to keep this folder's index clear.

The [copy record](source-snapshots/copy-record.json) maps every copied file to its original workspace path. [manifest.json](manifest.json) records file sizes and SHA-256 hashes; it excludes itself and the verification result to avoid circular hashes.
