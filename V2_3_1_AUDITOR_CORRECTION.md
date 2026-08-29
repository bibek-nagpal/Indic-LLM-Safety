# V2.3.1 Auditor correction

Pilot diagnosis showed two distinct GPT-5 Mini issues: (1) it sometimes applied ScenarioNesting/RolePrompting requirements to SymbolicMasking; (2) incomplete structured responses were silently converted into substantive rejects.

Changes:
- Adds an explicit strategy-specific audit instruction: only the declared strategy structural contract is binding.
- Validates the full hard-audit schema and exact strategy_id before interpreting a judgment.
- Retries once only when the auditor response is malformed/incomplete. Genuine rejects are never retried.
- If the retry is also malformed, the builder records audit_error rather than a false rejection.
- No certification criterion was weakened or removed.
