#!/usr/bin/env python3
"""Reviewed re-scoping of the durable Phase G journal onto a corrected configuration.

The journal binds itself to one exact configuration-and-code scope and refuses to
open when either changes. A corrected controller therefore cannot reopen the journal
that already holds paid work. This migration re-scopes that journal WITHOUT removing
a single row or a single nanodollar: every call keeps its billing, its raw provider
receipt and its hashes, and the ledger totals are asserted identical before and after.

A call whose request body the new configuration still reproduces byte-for-byte keeps
its identifier and stays replayable, so it is never paid for twice. A call whose
request body the new configuration would no longer reproduce is moved to a superseded
identifier, so the corrected run dispatches that step afresh instead of colliding with
a stale body. Superseded rows remain in the ledger and keep counting against the caps.

This performs no network access and no inference. It refuses to run when any call is
unreconciled, when integrity hashes disagree, or when a reservation bound changed.
"""
from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path

from analysis.phase_g import strong_archaic_runtime as r

SUPERSEDED = "superseded"


def _totals(db):
    row = db.execute("SELECT COUNT(*),COALESCE(SUM(billed),0),COALESCE(SUM(reserved),0) FROM calls").fetchone()
    return {"calls": row[0], "billed_nusd": row[1], "reserved_nusd": row[2],
            "events": db.execute("SELECT COUNT(*) FROM events").fetchone()[0]}


def analyse(path, config, locks):
    """Classify every stored call under the new configuration. Read only."""
    scope = r.identifier(config, locks)
    db = sqlite3.connect(path, timeout=10, isolation_level=None)
    db.row_factory = sqlite3.Row
    try:
        recorded = db.execute("SELECT scope FROM run").fetchone()[0]
        rows = db.execute("SELECT * FROM calls ORDER BY created,id").fetchall()
        # Rows a previous reviewed migration already retired keep the identifier that
        # migration recorded: they stay in the ledger and are never renamed again.
        retired = {entry["superseded_id"]
                   for row in db.execute("SELECT payload FROM events")
                   for payload in [json.loads(row[0])]
                   if isinstance(payload, dict) and "old_scope" in payload
                   for entry in payload.get("superseded", [])}
        problems, replayable, superseded, already = [], [], [], []
        for row in rows:
            if row["state"] != "received":
                problems.append("unreconciled call %s in state %s" % (row["id"][:16], row["state"]))
                continue
            if r.identifier(row["role"], row["stage"], row["request"]) != row["request_hash"]:
                problems.append("request hash mismatch on %s" % row["id"][:16])
            if row["response"] is not None and r.digest(row["response"]) != row["response_hash"]:
                problems.append("response hash mismatch on %s" % row["id"][:16])
            if row["response"] is not None:
                billed = json.loads(row["response"]).get("billed_nusd")
                expected = billed if type(billed) is int and billed >= 0 else None
                if row["billed"] != expected:
                    problems.append("billing differs from the raw receipt on %s" % row["id"][:16])
            settings = config["roles"].get(row["role"])
            if settings is None:
                problems.append("role %s is absent from the new configuration" % row["role"])
                continue
            if row["reserved"] != settings["maximum_call_nusd"]:
                problems.append("reservation bound changed for role %s; a re-scope cannot repair that"
                                % row["role"])
                continue
            stored = json.loads(row["request"])
            rebuilt = r.canonical(dict(r.fixed_parameters(settings), messages=stored["messages"]))
            entry = {"id": row["id"], "role": row["role"], "stage": row["stage"],
                     "billed_nusd": row["billed"], "finish_reason":
                         (json.loads(row["response"]).get("finish_reason") if row["response"] else None)}
            if row["id"] in retired:
                entry["reason"] = "retired by an earlier reviewed migration; identifier and billing unchanged"
                already.append(entry)
            elif rebuilt == row["request"]:
                replayable.append(entry)
            else:
                entry["superseded_id"] = r.identifier(row["id"], SUPERSEDED, recorded)
                entry["reason"] = "the corrected configuration no longer reproduces this request body"
                superseded.append(entry)
        return {"journal": str(path), "recorded_scope": recorded, "new_scope": scope,
                "scope_change_required": recorded != scope, "totals_before": _totals(db),
                "replayable_without_payment": replayable, "superseded": superseded,
                "already_superseded": already, "problems": problems}
    finally:
        db.close()


def migrate(path, config, locks, reason, apply=False):
    report = analyse(path, config, locks)
    report["applied"] = False
    report["reason"] = reason
    if report["problems"]:
        raise r.Stop("journal migration refused: " + "; ".join(report["problems"]))
    if not report["scope_change_required"] and not report["superseded"]:
        report["note"] = "journal already matches this configuration; nothing to migrate"
        return report
    if not apply:
        report["note"] = "dry run; pass --apply to write"
        return report
    db = sqlite3.connect(path, timeout=10, isolation_level=None)
    db.row_factory = sqlite3.Row
    try:
        db.execute("PRAGMA synchronous=FULL")
        before = _totals(db)
        db.execute("BEGIN IMMEDIATE")
        try:
            for entry in report["superseded"]:
                db.execute("UPDATE calls SET id=? WHERE id=?", (entry["superseded_id"], entry["id"]))
            payload = {"old_scope": report["recorded_scope"], "new_scope": report["new_scope"],
                       "reason": reason, "migrated_at_utc": datetime.now(timezone.utc).isoformat(),
                       "superseded": [{k: entry[k] for k in ("id", "superseded_id", "role", "billed_nusd")}
                                      for entry in report["superseded"]],
                       "replayable_without_payment": [entry["id"] for entry in report["replayable_without_payment"]],
                       "rows_removed": 0, "nanodollars_removed": 0}
            body = r.canonical(payload)
            db.execute("INSERT OR IGNORE INTO events VALUES (?,?,?)",
                       (r.identifier("journal_scope_migration", report["recorded_scope"], report["new_scope"]),
                        body, r.digest(body)))
            db.execute("UPDATE run SET scope=? WHERE id=1", (report["new_scope"],))
            after = _totals(db)
            if after["calls"] != before["calls"] or after["billed_nusd"] != before["billed_nusd"] \
                    or after["reserved_nusd"] != before["reserved_nusd"]:
                raise r.Stop("migration would change the ledger; refusing")
            db.execute("COMMIT")
        except BaseException:
            if db.in_transaction:
                db.execute("ROLLBACK")
            raise
        report["totals_after"] = _totals(db)
        report["applied"] = True
        return report
    finally:
        db.close()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan", default="analysis/phase_g/u_arch_v3_sanity_compat/EXECUTION_PLAN.json")
    parser.add_argument("--journal")
    parser.add_argument("--reason", default="Stage 2 GPT-5 Mini completion-budget correction")
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    plan = json.loads((r.ROOT / args.plan).read_text(encoding="utf-8"))
    journal = Path(args.journal) if args.journal else r.ROOT / plan["journal_path"]
    report = migrate(journal, plan, plan["locks"], args.reason, apply=args.apply)
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
