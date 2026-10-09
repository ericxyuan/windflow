"""Preserve the complete saved fan study and its user-facing work history."""

import argparse
import base64
import csv
from datetime import datetime, timezone
import hashlib
import importlib.metadata
import json
from pathlib import Path
import re
import shutil
import sys


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def message_text(payload):
    return "".join(block.get("text", "") for block in payload.get("content", [])
                   if isinstance(block, dict))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--session", type=Path, required=True)
    args = parser.parse_args()
    destination = Path(__file__).resolve().parents[1]
    workspace = destination.parent
    assert destination.name == "rotor_selection"
    assert destination.resolve().is_relative_to(workspace.resolve())

    calculation_relative = "docs/fan-shape-study-2026-10-09/calculations.json"
    calculations = json.loads((workspace / calculation_relative).read_text(encoding="utf-8"))
    head_report = json.loads((workspace / "cad/rev_c/head-validation.json").read_text(encoding="utf-8-sig"))

    relative_files = set(calculations["input_sha256"])
    relative_files.update({
        "docs/fan-shape-analysis-2026-10-09.md",
        "docs/rev-c-motor-power.md", "docs/rev-c-impeller.md",
        "docs/rev-c-airflow-and-mechanism.md", "docs/rev-c-firmware.md",
        "hardware/power-budget.md", "README.md", "cad/rev_c/rotor-validation.json",
        "tools/kicad-runtime.json", "tools/routing-dependencies.json",
    })
    relative_files.update(p.relative_to(workspace).as_posix()
                          for p in (workspace / "docs/fan-shape-study-2026-10-09").iterdir()
                          if p.is_file())
    relative_files.update(relative.replace("\\", "/")
                          for relative in head_report["input_sha256"]
                          if "rev_c" in relative or "impeller" in relative)

    for relative, expected in calculations["input_sha256"].items():
        assert digest(workspace / relative) == expected, f"Study input changed: {relative}"

    # Preserve the study's original directory relationships and exact bytes.
    copy_records = []
    for relative in sorted(relative_files):
        source = workspace / relative
        target_relative = "source-snapshots/workspace-README.md" if relative == "README.md" else relative
        target = destination / target_relative
        assert target.resolve().is_relative_to(destination.resolve())
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
        expected = digest(source)
        assert digest(target) == expected, f"Copy differs: {relative}"
        copy_records.append({"original_relative_path": relative,
                             "saved_relative_path": target_relative,
                             "bytes": target.stat().st_size,
                             "sha256": expected})
    write_json(destination / "source-snapshots/copy-record.json", copy_records)

    # Keep user messages, visible assistant messages, calls and returned results.
    # Internal reasoning, system/developer messages and internal metadata are not
    # user-facing work artifacts and are never exported.
    records = []
    active = False
    for line in args.session.read_text(encoding="utf-8").splitlines():
        record = json.loads(line)
        if record.get("type") != "response_item":
            continue
        payload = record.get("payload", {})
        item_type = payload.get("type")
        if item_type == "message" and payload.get("role") == "user":
            text = message_text(payload)
            if "Analyse different fan shapes with the target being the fastest airspeed" in text:
                active = True
            if active and "Save literally every bit of work you just did" in text:
                break
        if not active:
            continue
        if item_type == "message":
            if payload.get("role") not in {"user", "assistant"}:
                continue
            if payload.get("channel") in {"analysis", "summary"}:
                continue
            clean = {key: payload[key] for key in ("type", "role", "phase", "channel", "content")
                     if key in payload}
        elif item_type in {"function_call", "custom_tool_call"}:
            clean = {key: payload[key] for key in ("type", "name", "call_id", "arguments", "input", "status")
                     if key in payload}
        elif item_type in {"function_call_output", "custom_tool_call_output"}:
            clean = {key: payload[key] for key in ("type", "call_id", "output", "status")
                     if key in payload}
        else:
            continue
        records.append({"timestamp": record.get("timestamp"), "item": clean})
    assert records and any("I recommend a 150 mm" in message_text(record["item"])
                           for record in records if record["item"]["type"] == "message")

    history = destination / "history"
    history.mkdir(parents=True, exist_ok=True)
    (history / "study-log.jsonl").write_text("".join(json.dumps(record, ensure_ascii=False) + "\n"
                                                     for record in records), encoding="utf-8")
    conversation = ["# Original rotor-selection conversation", "",
                    "Saved verbatim user-facing text from the original study, including the layout approval.", ""]
    research = ["# Original research and tool record", "",
                "Exact retained calls and returned text from the study. Earlier truncated outputs remain marked as truncated.", ""]
    patch_count = 0
    image_count = 0
    final_response = None
    for index, record in enumerate(records, 1):
        item = record["item"]
        kind = item["type"]
        stamp = record["timestamp"]
        if kind == "message":
            text = message_text(item)
            conversation.extend([f"## {item['role'].title()} — {stamp}", "", text, ""])
            if item.get("role") == "assistant" and item.get("phase") == "final_answer":
                final_response = text
            elif item.get("role") == "assistant" and text.startswith("**I recommend a 150 mm"):
                final_response = text
        elif kind in {"custom_tool_call", "function_call"}:
            source = item.get("input", item.get("arguments", ""))
            if not isinstance(source, str):
                source = json.dumps(source, ensure_ascii=False, indent=2)
            research.extend([f"## Call {index}: {item.get('name', 'tool')} — {stamp}", "",
                             "````text", source, "````", ""])
            for match in re.finditer(r'tools\.apply_patch\(("(?:[^"\\]|\\.)*")\)', source):
                patch_count += 1
                patch = json.loads(match.group(1))
                patch_path = history / "patches" / f"{patch_count:02d}-study-edit.patch"
                patch_path.parent.mkdir(parents=True, exist_ok=True)
                patch_path.write_text(patch + "\n", encoding="utf-8")
                # Preserve directly readable first revisions as well as their
                # exact patches; later refined revisions are copied below.
                for addition in re.finditer(r"\*\*\* Add File: ([^\n]+)\n(.*?)(?=\n\*\*\* |$)", patch, re.S):
                    original_name = addition.group(1).replace("\\", "/").rsplit("/", 1)[-1]
                    lines = [line[1:] for line in addition.group(2).splitlines() if line.startswith("+")]
                    revision_path = history / "revisions" / f"{patch_count:02d}-initial-{original_name}"
                    revision_path.parent.mkdir(parents=True, exist_ok=True)
                    revision_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        else:
            output = item.get("output", [])
            blocks = output if isinstance(output, list) else [{"type": "text", "text": str(output)}]
            research.extend([f"## Result {index} — {stamp}", ""])
            for block in blocks:
                if not isinstance(block, dict):
                    research.extend([str(block), ""])
                    continue
                if "text" in block:
                    research.extend(["````text", block["text"], "````", ""])
                url = block.get("image_url", "")
                if isinstance(url, str) and url.startswith("data:"):
                    mime, encoded = url.split(",", 1)
                    extension = "png" if "image/png" in mime else "jpg"
                    image_count += 1
                    image_path = history / "viewed-images" / f"{image_count:02d}-viewed-image.{extension}"
                    image_path.parent.mkdir(parents=True, exist_ok=True)
                    image_path.write_bytes(base64.b64decode(encoded))
                    research.extend([f"![Image viewed during original study](viewed-images/{image_path.name})", ""])
    assert final_response is not None
    (history / "conversation.md").write_text("\n".join(conversation), encoding="utf-8")
    (history / "research-and-tool-results.md").write_text("\n".join(research), encoding="utf-8")
    (history / "original-final-response.md").write_text(final_response + "\n", encoding="utf-8")
    for relative in ["tools/analyse_fan_shapes.py", "docs/fan-shape-analysis-2026-10-09.md"]:
        target = history / "revisions" / f"03-final-{Path(relative).name}"
        shutil.copy2(destination / relative, target)

    links = calculations["sources"].copy()
    links["mixed_flow_example"] = "https://mag.ebmpapst.com/en/industries/electronics/diaforce-diagonal-fan-combines-axial-and-centrifugal-in-one-fan_14990/"
    write_json(destination / "references/source-links.json", links)
    (destination / "references/sources.md").write_text(
        "# Research sources\n\nSources consulted on 9 October 2026. The original returned research text, queries and retrieval results are retained in [the research record](../history/research-and-tool-results.md).\n\n" +
        "\n".join(f"- [{key.replace('_', ' ').title()}]({url})" for key, url in links.items()) + "\n", encoding="utf-8")

    runtime = {"python_version": sys.version, "python_executable_used": sys.executable,
               "packages": {name: importlib.metadata.version(name) for name in ("matplotlib", "numpy")}}
    write_json(destination / "verification/runtime.json", runtime)
    (destination / "tools/requirements.txt").write_text(
        "\n".join(f"{name}=={version}" for name, version in runtime["packages"].items()) + "\n", encoding="utf-8")

    report = destination / "docs/fan-shape-analysis-2026-10-09.md"
    report_links = re.findall(r"\]\(([^)]+)\)", report.read_text(encoding="utf-8"))
    local_links = [link for link in report_links if not link.startswith("https://")]
    missing = [link for link in local_links if not (report.parent / link).is_file()]
    assert not missing, f"Missing report links: {missing}"
    assert patch_count == 3, f"Expected three study edits, got {patch_count}"
    assert image_count == 3, f"Expected three images viewed during the study, got {image_count}"

    readme = f"""# Rotor selection — complete saved study

Study date: **9 October 2026**. This folder preserves the saved fan-selection work for Windflow, including the original user request and approval to rearrange the layout within a 200 mm total height.

Start with the [full fan shape, motor, airspeed, noise and boost analysis](docs/fan-shape-analysis-2026-10-09.md).

## Saved work

- **Report:** the full original analysis, copied byte for byte.
- **Diagrams:** both final figures in PNG and editable vector SVG form under [the study outputs](docs/fan-shape-study-2026-10-09/).
- **Calculations:** the complete [JSON record](docs/fan-shape-study-2026-10-09/calculations.json) and all three CSV tables.
- **Calculation source:** the exact [original study script](tools/analyse_fan_shapes.py), with a pinned [dependency list](tools/requirements.txt).
- **Source snapshots:** original motor/ESC specifications, rotor/head parameters, assembly/export reports, relevant CAD source and existing rotor STEP, control configuration and implementation, and consulted project documentation. Their original relative paths are preserved so the report and calculation remain self-contained.
- **Conversation:** [the original request, progress updates, layout approval and final response](history/conversation.md), plus the [final response separately](history/original-final-response.md).
- **Research history:** [all retained calls and returned text](history/research-and-tool-results.md), the structured [study log](history/study-log.jsonl), all **{patch_count} original edit patches**, readable initial and final source/report revisions, and **{image_count} viewed-image snapshots**, including the earlier chart version.
- **References:** [source links and retrieval context](references/sources.md).
- **Verification:** copy hashes, report-link checks, runtime details and a complete file manifest.

The recommended 150 mm five-blade swept/twisted axial stage and 195 mm product height are analytical design proposals. This archive contains no new CFD, physical fan/noise measurements or revised clearance-checked production CAD.

## Reproduction

Run `tools/analyse_fan_shapes.py` from this folder with Python and the dependencies in `tools/requirements.txt`. It uses the preserved source snapshots and writes the calculations, CSV tables and figures to `docs/fan-shape-study-2026-10-09`. The original run's environment is recorded in [runtime.json](verification/runtime.json).

Copies retain the original bytes and relative structure. The original workspace files remain available. The workspace README is preserved separately as [workspace-README.md](source-snapshots/workspace-README.md) to keep this folder's index clear.

The [copy record](source-snapshots/copy-record.json) maps every copied file to its original workspace path. [manifest.json](manifest.json) records file sizes and SHA-256 hashes; it excludes itself and the verification result to avoid circular hashes.
"""
    (destination / "README.md").write_text(readme, encoding="utf-8")

    excluded = {"manifest.json", "verification/archive-validation.json"}
    entries = [{"path": path.relative_to(destination).as_posix(), "bytes": path.stat().st_size,
                "sha256": digest(path)}
               for path in sorted(destination.rglob("*"))
               if path.is_file() and path.relative_to(destination).as_posix() not in excluded]
    manifest = {"saved_utc": datetime.now(timezone.utc).isoformat(), "study_date": "2026-10-09",
                "folder": str(destination), "files": entries,
                "total_manifested_bytes": sum(entry["bytes"] for entry in entries),
                "excluded_self_records": sorted(excluded)}
    write_json(destination / "manifest.json", manifest)
    for entry in entries:
        assert digest(destination / entry["path"]) == entry["sha256"]
    verification = {"result": "PASS", "copied_original_files": len(copy_records),
                    "copied_files_byte_identical": True, "manifested_files": len(entries),
                    "total_saved_files_including_manifest_and_validation": len(entries) + 2,
                    "all_manifest_hashes_verified": True, "report_local_links_checked": len(local_links),
                    "missing_report_links": missing, "original_study_records": len(records),
                    "original_patches_saved": patch_count, "viewed_images_saved": image_count,
                    "original_calculation_inputs_still_match": True,
                    "manifest_sha256": digest(destination / "manifest.json")}
    write_json(destination / "verification/archive-validation.json", verification)
    print(json.dumps({**verification, "saved_folder": str(destination),
                      "total_manifested_megabytes": manifest["total_manifested_bytes"] / 1e6}, indent=2))


if __name__ == "__main__":
    main()
