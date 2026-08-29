#!/usr/bin/env python3
"""Small, dependency-free state ledger for the Plugin Manager workflow."""
from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def state_path(root: Path) -> Path:
    return root / ".plugin-manager" / "state.json"


def load(root: Path) -> dict[str, Any]:
    path = state_path(root)
    if not path.is_file():
        raise SystemExit(f"state file not found: {path}; run init first")
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise SystemExit(f"cannot read state file: {exc}")
    if not isinstance(payload, dict) or payload.get("schema_version") != 1:
        raise SystemExit("unsupported or invalid state schema")
    return payload


def save(root: Path, payload: dict[str, Any]) -> None:
    directory = state_path(root).parent
    directory.mkdir(parents=True, exist_ok=True)
    payload["updated_at"] = now()
    temporary = directory / f"state.json.{os.getpid()}.tmp"
    temporary.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    temporary.replace(state_path(root))


def add_unique(items: list[dict[str, Any]], item: dict[str, Any], key: str) -> None:
    if any(existing.get(key) == item.get(key) for existing in items):
        raise SystemExit(f"duplicate {key}: {item.get(key)}")
    items.append(item)


def cmd_init(args: argparse.Namespace) -> None:
    root = Path(args.project_root).expanduser().resolve()
    path = state_path(root)
    if path.exists() and not args.force:
        raise SystemExit(f"state already exists: {path} (use --force to replace)")
    hosts = args.hosts or ["unspecified"]
    payload: dict[str, Any] = {
        "schema_version": 1,
        "created_at": now(),
        "updated_at": now(),
        "phase": "spike",
        "project": {"name": args.name, "root": str(root), "required_hosts": hosts},
        "requirements": [],
        "decisions": [],
        "tasks": [],
        "findings": [],
        "hosts": [{"name": host, "required": True, "status": "unverified", "evidence": []} for host in hosts],
        "gates": {key: False for key in (
            "requirements_complete", "design_complete", "plan_complete", "code_self_checks",
            "task_reviews", "checker_static", "host_verification", "blockers_zero", "delivery",
        )},
    }
    save(root, payload)
    print(path)


def cmd_requirement(args: argparse.Namespace) -> None:
    root = Path(args.project_root).expanduser().resolve()
    payload = load(root)
    item = {"id": args.id, "text": args.text, "provenance": args.provenance,
            "confidence": args.confidence, "status": "open", "evidence": [], "created_at": now()}
    add_unique(payload["requirements"], item, "id")
    save(root, payload)
    print(f"added requirement {args.id}")


def cmd_task(args: argparse.Namespace) -> None:
    root = Path(args.project_root).expanduser().resolve()
    payload = load(root)
    item = {"id": args.id, "title": args.title, "status": "planned", "acceptance": args.acceptance or [],
            "evidence": [], "created_at": now()}
    add_unique(payload["tasks"], item, "id")
    save(root, payload)
    print(f"added task {args.id}")


def cmd_finding(args: argparse.Namespace) -> None:
    root = Path(args.project_root).expanduser().resolve()
    payload = load(root)
    item = {"id": args.id, "task_id": args.task_id, "layer": args.layer, "severity": args.severity,
            "violated": args.violated, "evidence": args.evidence or [], "impact": args.impact,
            "fix": args.fix, "reverify": args.reverify, "status": "open", "created_at": now()}
    add_unique(payload["findings"], item, "id")
    save(root, payload)
    print(f"added finding {args.id}")


def cmd_verify(args: argparse.Namespace) -> None:
    root = Path(args.project_root).expanduser().resolve()
    payload = load(root)
    blockers = [f for f in payload["findings"] if f.get("severity") == "blocker" and f.get("status") != "resolved"]
    required_hosts = [h for h in payload["hosts"] if h.get("required")]
    hosts_ok = bool(required_hosts) and all(h.get("status") == "passed" and h.get("evidence") for h in required_hosts)
    gates = payload["gates"]
    gates["blockers_zero"] = not blockers
    gates["host_verification"] = hosts_ok
    gates["delivery"] = all(gates.get(name) for name in ("requirements_complete", "design_complete", "plan_complete", "code_self_checks", "task_reviews", "checker_static", "host_verification", "blockers_zero"))
    save(root, payload)
    report = {"phase": payload.get("phase"), "delivery": gates["delivery"], "open_blockers": [f["id"] for f in blockers], "hosts": {h["name"]: h["status"] for h in required_hosts}, "gates": gates}
    print(json.dumps(report, indent=2))
    raise SystemExit(0 if gates["delivery"] else 2)


def cmd_gate(args: argparse.Namespace) -> None:
    root = Path(args.project_root).expanduser().resolve()
    payload = load(root)
    if args.gate not in payload["gates"]:
        raise SystemExit(f"unknown gate: {args.gate}")
    payload["gates"][args.gate] = args.value == "pass"
    save(root, payload)
    print(f"gate {args.gate}: {args.value}")


def cmd_host(args: argparse.Namespace) -> None:
    root = Path(args.project_root).expanduser().resolve()
    payload = load(root)
    for host in payload["hosts"]:
        if host.get("name") == args.name:
            host["status"] = args.status
            if args.evidence:
                host.setdefault("evidence", []).extend(args.evidence)
            save(root, payload)
            print(f"host {args.name}: {args.status}")
            return
    raise SystemExit(f"unknown host: {args.name}")


def cmd_resolve(args: argparse.Namespace) -> None:
    root = Path(args.project_root).expanduser().resolve()
    payload = load(root)
    for finding in payload["findings"]:
        if finding.get("id") == args.id:
            finding["status"] = "resolved"
            finding["resolution"] = {"summary": args.summary, "evidence": args.evidence or [], "resolved_at": now()}
            save(root, payload)
            print(f"finding {args.id}: resolved")
            return
    raise SystemExit(f"unknown finding: {args.id}")


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Manage Plugin Manager workflow state")
    sub = p.add_subparsers(dest="command", required=True)
    init = sub.add_parser("init"); init.add_argument("--project-root", required=True); init.add_argument("--name", required=True); init.add_argument("--hosts", nargs="*"); init.add_argument("--force", action="store_true"); init.set_defaults(func=cmd_init)
    req = sub.add_parser("add-requirement"); req.add_argument("--project-root", required=True); req.add_argument("--id", required=True); req.add_argument("--text", required=True); req.add_argument("--provenance", choices=("user_stated", "agent_inferred", "industry_default"), required=True); req.add_argument("--confidence", choices=("explicit", "inferred", "default"), required=True); req.set_defaults(func=cmd_requirement)
    task = sub.add_parser("add-task"); task.add_argument("--project-root", required=True); task.add_argument("--id", required=True); task.add_argument("--title", required=True); task.add_argument("--acceptance", nargs="*"); task.set_defaults(func=cmd_task)
    finding = sub.add_parser("add-finding"); finding.add_argument("--project-root", required=True); finding.add_argument("--id", required=True); finding.add_argument("--task-id"); finding.add_argument("--layer", choices=("code", "plan", "design", "requirements", "platform"), required=True); finding.add_argument("--severity", choices=("blocker", "major", "minor", "info"), required=True); finding.add_argument("--violated", required=True); finding.add_argument("--evidence", nargs="*"); finding.add_argument("--impact", required=True); finding.add_argument("--fix", required=True); finding.add_argument("--reverify", required=True); finding.set_defaults(func=cmd_finding)
    gate = sub.add_parser("set-gate"); gate.add_argument("--project-root", required=True); gate.add_argument("--gate", required=True); gate.add_argument("--value", choices=("pass", "fail"), required=True); gate.set_defaults(func=cmd_gate)
    host = sub.add_parser("set-host"); host.add_argument("--project-root", required=True); host.add_argument("--name", required=True); host.add_argument("--status", choices=("unverified", "passed", "failed"), required=True); host.add_argument("--evidence", nargs="*"); host.set_defaults(func=cmd_host)
    resolve = sub.add_parser("resolve-finding"); resolve.add_argument("--project-root", required=True); resolve.add_argument("--id", required=True); resolve.add_argument("--summary", required=True); resolve.add_argument("--evidence", nargs="*"); resolve.set_defaults(func=cmd_resolve)
    verify = sub.add_parser("verify"); verify.add_argument("--project-root", required=True); verify.set_defaults(func=cmd_verify)
    return p


if __name__ == "__main__":
    try:
        args = parser().parse_args()
        args.func(args)
    except BrokenPipeError:
        sys.exit(1)
