# Frozen fan-mount negative-control baseline

These seven files are byte-for-byte copies of the checked Rev B mount inputs at repository commit `ee3ddc9cbf206eec5d336ee8c083fa07e3193e1a`, preserved before the corrected mount was adopted into the main model. Their SHA-256 values appear under `input_sha256` in the repair study's `../validation.json`.

| Archived file | Original location |
| --- | --- |
| `head-left-integral-outlet.step` | `cad/rev_b/head-left-integral-outlet.step` |
| `head-right-integral-outlet.step` | `cad/rev_b/head-right-integral-outlet.step` |
| `bellmouth-rear-inlet.step` | `cad/rev_b/bellmouth-rear-inlet.step` |
| `tpu-fan-pad-m3.step` | `cad/rev_b/tpu-fan-pad-m3.step` |
| `parameters.json` | `cad/parameters.json` |
| `build_head.py` | `cad/build_head.py` |
| `check_assembly.py` | `cad/check_assembly.py` |

The old pad and bell plate deliberately retain the defects detected by the independent repair study. Do not select them as current production print files. The archived Python scripts are provenance references; their relative dependency paths were defined for the original `cad/` directory. Run `cad/fan_mount_study.py` from the repository to reproduce the independent study rather than executing these copies in place.

The Noctua manufacturer fan STEP remains a reproducibly downloaded dependency in `cad/vendor/`, with its exact input hash recorded by the study and its download source in `hardware/sources.json`.
