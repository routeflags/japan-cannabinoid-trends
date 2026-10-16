---
name: ddd-architect
description: Discover and document domain boundaries, ubiquitous language, context maps, agent ownership contracts, incremental migration plans, and architecture verification for AI-agent-driven repositories.
---

# DDD Architect スキル

## When to use
Use when introducing DDD to an existing repository; mapping domain concepts; planning bounded contexts; splitting agent work; reviewing dependency boundaries; or converting architecture policies into automated tests.

## Inputs
- Repository root and relevant source/test/docs paths.
- Desired outcome and explicit constraints.
- Current agent/CI conventions, if present.
- Known business language, workflows, and integration points.

If information is missing, inspect the repository first. Do not manufacture domain facts.

## Procedure
### Step 1 — Inventory (read-only by default)
Inspect README, architecture docs, module boundaries, imports, tests, CI, and agent instruction files. Produce an evidence table:

| Claim | Classification | Evidence | Confidence |
|---|---|---|---|
| ... | Observed / Inferred / Proposed / Unknown | `path:symbol` | High / Medium / Low |

### Step 2 — Ubiquitous language
Create or propose `docs/domain/glossary.md`:

| Term | Definition | Context | Source | Ambiguity |
|---|---|---|---|---|
| ... | ... | ... | ... | ... |

Keep homonyms with different context meanings separate.

### Step 3 — Context design
Create or propose `docs/domain/context-map.md` with:
- Business capabilities and candidate subdomains (core/supporting/generic).
- Bounded contexts, their distinct domain models, and key invariants.
- Upstream/downstream relationships and integration methods.
- Explicitly unresolved boundary decisions.

**Boundary decision checklist:** different vocabulary/model? independent invariant? change cadence? team or agent coordination? integration cost? Avoid one-context-per-directory and one-context-per-agent as default assumptions.

### Step 4 — Agent contracts
For each context, create or propose `docs/domain/contracts/<context>.md`:

```markdown
# <Context> — Agent Contract
## Purpose and domain vocabulary
## Owned paths (advisory ownership)
## Invariants and acceptance criteria
## Public interfaces / integration events
## Allowed dependencies
## Forbidden dependencies
## Cross-context change protocol
## Required tests and CI checks
## Escalation and human approval triggers
```

If the platform supports per-directory agent instruction files, create them **only after checking its precedence and discovery rules**. Contracts describe work coordination, not filesystem security.

### Step 5 — Migration design
Offer three options with trade-offs:
- **Minimal:** glossary, context map, and ADR; no source restructuring.
- **Balanced (default):** minimal + agent contracts + one architecture test + one pilot context.
- **Full:** staged restructuring, tactical patterns where justified, compatibility tests, and context-specific CI.

Plan small vertical slices, record affected interfaces, and include rollback conditions. Never perform broad restructuring solely to make folders match a template.

### Step 6 — Architecture verification
Choose a tool compatible with the existing stack. Verify, where applicable:
1. Forbidden cross-context imports / dependency direction.
2. Public-contract compatibility and integration tests.
3. Domain invariants and context-level tests.
4. Ownership and documentation drift (advisory checks).

Record exact commands, outputs, and unverified assumptions. A policy without an executable check is not a verified boundary.

## Definition of done
- [ ] Observed facts distinguished from proposals and unknowns.
- [ ] Glossary terms mapped to contexts.
- [ ] Bounded-context decisions and alternatives documented.
- [ ] Cross-context interfaces and ownership explicit.
- [ ] Agent contracts include escalation rules.
- [ ] Incremental plan has acceptance criteria and rollback.
- [ ] Checks executed or clearly marked `not run`.
- [ ] No unapproved destructive changes or behavior changes.

## Deliverable structure (adapt to existing repository)
```text
docs/domain/
  glossary.md
  context-map.md
  architecture-rules.md
  contracts/<context>.md
  adr/NNNN-<decision>.md
```

## Response format
**Recommendation** → **Evidence** → **Alternatives/trade-offs** → **Proposed artifacts** → **Verification status** → **Next smallest step**.

Keep the main answer concise; place details in files. If domain facts or platform compatibility cannot be established, say so explicitly.
