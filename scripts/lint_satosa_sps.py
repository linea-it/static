#!/usr/bin/env python3
"""Lint SATOSA SP aggregate metadata XML files.

Validates well-formed XML and basic SP structure, optionally diffs entityIDs
between a base tree and the working tree for PR summaries.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from pathlib import Path


RNP_TEMPLATE_PATH = "docs/rnp-cafe-notify-template.md"
MARKER = "<!-- satosa-sps-lint -->"


def local_name(tag: str) -> str:
    if tag.startswith("{"):
        return tag.rsplit("}", 1)[-1]
    return tag


def find_children(parent: ET.Element, name: str) -> list[ET.Element]:
    return [child for child in parent if local_name(child.tag) == name]


def find_descendants(parent: ET.Element, name: str) -> list[ET.Element]:
    return [el for el in parent.iter() if local_name(el.tag) == name]


def entity_fingerprint(entity: ET.Element) -> str:
    """Stable hash of ACS locations + certificates for change detection."""
    parts: list[str] = []
    for acs in find_descendants(entity, "AssertionConsumerService"):
        binding = acs.get("Binding", "")
        location = acs.get("Location", "")
        parts.append(f"acs|{binding}|{location}")
    for cert in find_descendants(entity, "X509Certificate"):
        text = "".join((cert.text or "").split())
        parts.append(f"cert|{text}")
    raw = "\n".join(sorted(parts)).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


@dataclass
class SpInfo:
    entity_id: str
    fingerprint: str
    has_sp_sso: bool
    acs_count: int
    cert_count: int


@dataclass
class FileReport:
    path: Path
    errors: list[str] = field(default_factory=list)
    sps: dict[str, SpInfo] = field(default_factory=dict)

    @property
    ok(self) -> bool:
        return not self.errors


def parse_sps_file(path: Path) -> FileReport:
    report = FileReport(path=path)
    try:
        tree = ET.parse(path)
    except ET.ParseError as exc:
        report.errors.append(f"XML not well-formed: {exc}")
        return report

    root = tree.getroot()
    if local_name(root.tag) != "EntitiesDescriptor":
        report.errors.append(
            f"Root element must be EntitiesDescriptor, found {local_name(root.tag)}"
        )
        return report

    seen: dict[str, int] = {}
    for entity in find_children(root, "EntityDescriptor"):
        entity_id = (entity.get("entityID") or "").strip()
        if not entity_id:
            report.errors.append("EntityDescriptor missing entityID")
            continue

        seen[entity_id] = seen.get(entity_id, 0) + 1
        sp_sso = find_children(entity, "SPSSODescriptor")
        acs = find_descendants(entity, "AssertionConsumerService")
        certs = find_descendants(entity, "X509Certificate")

        info = SpInfo(
            entity_id=entity_id,
            fingerprint=entity_fingerprint(entity),
            has_sp_sso=bool(sp_sso),
            acs_count=len(acs),
            cert_count=len(certs),
        )
        report.sps[entity_id] = info

        if not info.has_sp_sso:
            report.errors.append(f"{entity_id}: missing SPSSODescriptor")
        if info.acs_count < 1:
            report.errors.append(f"{entity_id}: missing AssertionConsumerService")
        if info.cert_count < 1:
            report.errors.append(f"{entity_id}: missing X509Certificate")

    for entity_id, count in sorted(seen.items()):
        if count > 1:
            report.errors.append(f"duplicate entityID ({count}x): {entity_id}")

    return report


def discover_sps_files(metadata_dir: Path) -> list[Path]:
    return sorted(metadata_dir.glob("satosa-*-sps-*.xml"))


def is_prod_sps(path: Path) -> bool:
    return path.name.startswith("satosa-prod-sps-")


@dataclass
class DiffResult:
    added: list[str] = field(default_factory=list)
    removed: list[str] = field(default_factory=list)
    changed: list[str] = field(default_factory=list)
    rnp_notify: list[str] = field(default_factory=list)


def diff_sps(base: FileReport | None, head: FileReport) -> DiffResult:
    result = DiffResult()
    base_sps = base.sps if base else {}
    head_sps = head.sps

    base_ids = set(base_sps)
    head_ids = set(head_sps)

    result.added = sorted(head_ids - base_ids)
    result.removed = sorted(base_ids - head_ids)
    result.changed = sorted(
        eid
        for eid in (base_ids & head_ids)
        if base_sps[eid].fingerprint != head_sps[eid].fingerprint
    )
    if is_prod_sps(head.path) and result.added:
        result.rnp_notify = list(result.added)
    return result


def format_markdown(
    reports: list[FileReport],
    diffs: dict[Path, DiffResult],
    repo_url: str | None = None,
) -> str:
    lines = [MARKER, "## SATOSA SP metadata lint", ""]
    all_ok = all(r.ok for r in reports)
    lines.append(f"**Status:** {'pass' if all_ok else 'fail'}")
    lines.append("")

    for report in reports:
        rel = report.path.as_posix()
        lines.append(f"### `{rel}`")
        lines.append("")
        if report.errors:
            lines.append("**Errors:**")
            for err in report.errors:
                lines.append(f"- {err}")
            lines.append("")
        else:
            lines.append(f"- SPs: **{len(report.sps)}**")
            lines.append("- Lint: OK")
            lines.append("")

        diff = diffs.get(report.path)
        if diff:
            if diff.added:
                lines.append("**Added entityIDs:**")
                for eid in diff.added:
                    lines.append(f"- `{eid}`")
                lines.append("")
            if diff.removed:
                lines.append("**Removed entityIDs:**")
                for eid in diff.removed:
                    lines.append(f"- `{eid}`")
                lines.append("")
            if diff.changed:
                lines.append("**Changed entityIDs** (ACS/cert fingerprint):")
                for eid in diff.changed:
                    lines.append(f"- `{eid}`")
                lines.append("")
            if not (diff.added or diff.removed or diff.changed):
                lines.append("_No entityID add/remove/change vs base._")
                lines.append("")

            if diff.rnp_notify:
                template_link = RNP_TEMPLATE_PATH
                if repo_url:
                    template_link = f"{repo_url}/blob/main/{RNP_TEMPLATE_PATH}"
                lines.append("> **RNP_NOTIFY_REQUIRED**")
                lines.append(">")
                lines.append(
                    "> O satosa-prod é o SP perante a federação CAFe. "
                    "Novas aplicações em produção precisam de aviso manual à RNP."
                )
                lines.append(">")
                lines.append("> Novos entityIDs:")
                for eid in diff.rnp_notify:
                    lines.append(f"> - `{eid}`")
                lines.append(">")
                lines.append(
                    f"> Use o template: [{RNP_TEMPLATE_PATH}]({template_link})"
                )
                lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--metadata-dir",
        type=Path,
        default=Path("metadata"),
        help="Directory containing satosa-*-sps-*.xml",
    )
    parser.add_argument(
        "--base-dir",
        type=Path,
        default=None,
        help="Checkout of base ref for entityID diff (optional)",
    )
    parser.add_argument(
        "--markdown-out",
        type=Path,
        default=None,
        help="Write PR comment markdown to this path",
    )
    parser.add_argument(
        "--json-out",
        type=Path,
        default=None,
        help="Write machine-readable summary JSON",
    )
    parser.add_argument(
        "--repo-url",
        default=None,
        help="GitHub repo URL for template links (e.g. https://github.com/linea-it/static)",
    )
    args = parser.parse_args(argv)

    metadata_dir = args.metadata_dir
    if not metadata_dir.is_dir():
        print(f"ERROR: metadata dir not found: {metadata_dir}", file=sys.stderr)
        return 2

    files = discover_sps_files(metadata_dir)
    if not files:
        print(f"ERROR: no satosa-*-sps-*.xml under {metadata_dir}", file=sys.stderr)
        return 2

    reports = [parse_sps_file(path) for path in files]
    diffs: dict[Path, DiffResult] = {}

    for report in reports:
        if args.base_dir is None:
            # No base checkout: lint only, no add/remove/change summary
            continue
        candidate = args.base_dir / "metadata" / report.path.name
        if candidate.is_file():
            base_report = parse_sps_file(candidate)
        else:
            base_report = FileReport(path=report.path)
        diffs[report.path] = diff_sps(base_report, report)

    md = format_markdown(reports, diffs, repo_url=args.repo_url)
    print(md)

    if args.markdown_out:
        args.markdown_out.parent.mkdir(parents=True, exist_ok=True)
        args.markdown_out.write_text(md, encoding="utf-8")

    if args.json_out:
        payload = {
            "ok": all(r.ok for r in reports),
            "files": [
                {
                    "path": r.path.as_posix(),
                    "ok": r.ok,
                    "errors": r.errors,
                    "entity_ids": sorted(r.sps),
                    "added": diffs[r.path].added if r.path in diffs else [],
                    "removed": diffs[r.path].removed if r.path in diffs else [],
                    "changed": diffs[r.path].changed if r.path in diffs else [],
                    "rnp_notify": diffs[r.path].rnp_notify if r.path in diffs else [],
                }
                for r in reports
            ],
        }
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

    for report in reports:
        for err in report.errors:
            print(f"ERROR [{report.path.as_posix()}]: {err}", file=sys.stderr)

    return 0 if all(r.ok for r in reports) else 1


if __name__ == "__main__":
    raise SystemExit(main())
