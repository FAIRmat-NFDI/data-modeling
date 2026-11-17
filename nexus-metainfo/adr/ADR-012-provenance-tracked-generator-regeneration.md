# ADR-012: Provenance-Tracked Regeneration for the NXDL→Metainfo Generator

**Status**: Decided and implemented; pynxtools branch `nexus-generator-provenance` (worktree `packages/pynxtools/.worktrees/provenance`, off `master`); merged by now
**Date**: 2026-09-15
**Deciders**: Lukas Pielsticker
**Discussion panel**: —

---

## Context

Two bugs surfaced while reviewing pynxtools PR #833 (`nexus-metainfo-phase4`):

1. **Inherited-member leak**: `build_context()`'s per-child emission loop (see
   ADR-004, "NXDL node kinds handled by the generator") only filtered *groups*
   by ownership (`child.nxdl_base != primary_nxdl`); fields, attributes, and
   links were emitted unconditionally, so a derived NXDL definition
   re-declared members it actually inherits from a parent. Example:
   `is_experimental` is declared once in `NXxas`; every `NXxas_*` subclass
   (`XasHerfd`, `XasTey`, ...) re-emitted it, plus `energy`/`intensity_errors`.
   Measured blast radius: 25 files, spanning both `contributed_definitions/`
   and accepted NIAC `applications/`; 0 base classes affected. Every dropped
   member's origin class is in the derived class's own Python MRO, so nothing
   is lost — it becomes available through inheritance instead of being
   re-declared. Fixed by replacing the group-only guard with a uniform
   ownership rule applied to every member kind.

2. **The fix exposed a propagation problem**: the generator was additive-only.
   `write_class()` left a file untouched whenever it had a member the fresh
   template lacked, or a shared member (`normalize()`) whose body differed. It
   could not distinguish a member the generator *used to wrongly emit and now
   correctly drops* from one a human *hand-added* — both just look like
   "existing file has something the template doesn't." So bug 1's fix could
   not propagate into already-generated files without a `--force` regen, which
   would delete real hand edits (`Entry.m_nx_data_path`,
   `Root.m_entry_paths`, `Root.normalize`'s ExperimentStep-resolution body).

## Decision

Track provenance explicitly via a sidecar manifest, `generated_manifest.json`,
committed alongside the generated `.py` package (`base_classes/`/
`applications/`). Per module and class, it records the members and imports the
generator owns, plus a content fingerprint of each (whitespace-normalized, so a
pure reformat doesn't read as a change).

On regeneration, each existing member/import is classified against the
manifest:

- **owned, fingerprint unchanged** → untouched generated content; refreshed
  from the fresh template (or dropped, per the tier policy below, if the
  template no longer emits it).
- **owned, fingerprint changed** → hand-modified generated content; preserved.
- **not owned** → hand-added; preserved.

**Tier policy** for dropping an obsolete generated member (one the template no
longer emits): `contributed_definitions/` (volatile — content can change at any
time) always drops it. Accepted NIAC `base_classes/`/`applications/` (stable
standards) are add-only by default — a routine regeneration never removes an
existing generated member — and only drop it under an explicit `--fix` pass (a
generator-bug-fix regeneration), so a routine NXDL bump can't silently shrink
the stable schema.

**Seeding is explicit, not automatic.** `bootstrap_manifest()` is a plain
function, run once by hand on an already-generated tree — it renders the
generator's current output, records those fingerprints, and touches no `.py`
file. There is no CLI flag for it (a one-time action doesn't need permanent CLI
surface) and no naming-convention heuristic (an earlier draft tried inferring
ownership from an `m_`-prefix convention on first run; rejected — see
Alternatives). Until a module has a manifest entry, `write_class()` refuses to
touch its existing file rather than guess.

## Alternatives considered

**Auto-bootstrap via an `m_`-prefix naming heuristic**: the first draft
classified a member as generator-owned unless it was clearly hand content — an
`m_`-prefixed helper (matching NOMAD's own `m_*` framework-attribute
convention) or a generated member whose body differed from fresh output.
Implemented and unit-tested, then rejected: it silently depended on a naming
coincidence (the two real hand-added members happen to be `m_`-prefixed) for a
classification that only ever needs to happen once. Replaced with the explicit
`bootstrap_manifest()`, which is deterministic (the owned set is exactly what
the generator produces, not inferred) and needs no convention.

**A permanent `--bootstrap-manifest` CLI flag**: rejected once bootstrapping
became a one-time, explicit action — a flag implies routine/repeatable use,
which this isn't. A plain function callable from Python is enough.

**In-file provenance** (a machine-readable block inside each generated `.py`):
rejected in favor of a sidecar file, to keep the LGPL-licensed generated
schema files clean and human-readable, and to keep provenance as one diffable
artifact rather than scattered across every file.

## Consequences

- `generated_manifest.json` must be committed alongside the generated package
  it describes (it is a build input, read only by the generator itself — never
  read at runtime, so it is excluded from the packaged wheel/sdist; already
  true of the existing `package-data`/`MANIFEST.in` rules, no packaging change
  needed). Given a REUSE annotation as Apache-2.0 (generator metadata, not
  derived NXDL content) in `REUSE.toml`, overriding the `metainfo/**` LGPL rule
  for this one file.
- CLI: added `--fix` (drop obsolete members from the accepted tier too, for a
  generator-fix pass). Target flags (`--nxdl`/`--all`/`--all-base`/
  `--all-applications`) and `--force`/`--fix` are enforced mutually exclusive
  by a `click.Option` subclass at parse time, not by a manual check in the
  command body.
- Splicing hand content back into freshly generated source (line-range based,
  via `ast`) had two real bugs found by testing the CLI directly rather than
  only via synthetic-source unit tests: a hand member's leading `#` comment
  was dropped (not part of its AST node range), and a hand-added member
  drifted to the end of the class (after any methods) instead of staying
  grouped with the other quantities. Both fixed; a synthetic-source unit test
  added for each so a unit-test run alone would have caught them.
- `tests/nomad/converters/test_provenance.py`: 8 fast unit tests against small
  synthetic source strings (fingerprinting, the three merge cases, tier
  policy, hand-added imports, the empty-manifest fallback, splice fidelity,
  idempotency) — no NXDL parsing or schema build, so they run in seconds.
- Two pre-existing tests in `test_nxdl_to_metainfo.py` broke against the new
  `write_class` and needed updating: a fixture that seeded an existing file
  with no manifest entry (the new design correctly leaves that file alone,
  matching what a real non-dry run would do — the old assertion encoded the
  pre-provenance "just diff raw content" dry-run semantics), and a stub
  `write_class` replacement missing the new `fix`/`manifest`/`reports`
  keyword arguments (now takes `**kwargs` so a future new parameter doesn't
  silently break it the same way again).
