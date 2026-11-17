# ADR-010: Entity Identifiers via `Object.normalize()`, No `AnchoredReference` Class

**Status**: Decided and implemented (Phase 6)
**Date**: 2026-08
**Deciders**: Lukas Pielsticker
**Dicussion panel**: Area B core team

---

## Context

The old runtime-generated schema's `NORMALIZER_MAP` (`schema_packages/schema.py`) dispatches
hand-written normalizers per NXDL class. None of the Phase 1–3 generated classes had an
equivalent — their `normalize()` stubs just called `super().normalize()`. Two pieces of the old
normalizer behavior needed a home on the new generated classes:

1. **`identifierNAME`**: NeXus's loose convention for embedding entity identifiers (sample IDs,
   instrument IDs, etc.) as variadic fields. v1 handled this via `NexusIdentifiers.normalize()`
   and a speculative `AnchoredReference` class was floated as the v2 replacement.
2. **`NexusMeasurement.normalize()`**: the old `Root`/top-level normalizer that walked
   `m_all_contents()` to bucket sections by base type, because v1 had no properly-typed
   `sample`/`instrument`/`data` SubSections to populate directly.

## Decision

### `identifierNAME` resolution

No `AnchoredReference` class was built. `NexusIdentifiers.normalize()` lands directly on
`Object.normalize()` — the universal base every generated class inherits — not a separate
mixed-in class. It reads `self.__dict__.get("identifierNAME")` (a `dict[str, MQuantity]` for this
`variable=True` quantity, confirmed against `nomad-FAIR`'s `Quantity.__get__`/`__set__`
full-storage handling).

The first identifier on an `Entity`-typed object (`Sample`/`System`, `Fabrication`/
`InstrumentEntry`, ...) sets that object's own `lab_id` directly. Any further identifier, or any
identifier on a non-`Entity` object, is resolved-or-created as a plain `basesections.EntityReference`
via a new helper, `resolve_or_create_entity()` in `pynxtools/nomad/metainfo/_identified_entity.py`,
appended to a new `Object.nexus_identifiers: SubSection(EntityReference, repeats=True)` list.
`resolve_or_create_entity()` mirrors v1's raw-file-writing fallback (create a minimal standalone
`Entity` archive when search finds nothing) but with a readable file name
(`Entity_<slug>.archive.json`) instead of v1's MD5 hash.

### `NexusMeasurement.normalize()` — confirmed obsolete, not ported

Each of the old normalizer's responsibilities was checked individually and found already handled
elsewhere in v2, not requiring a port:

- `archive.workflow2.inputs`/`.outputs` stamping — already generic and automatic via
  `basesections.Measurement.normalize()` (inherited).
- `archive.results.eln.methods` — already handled, but at the *parser* level, not via a
  `normalize()` port.
- A human-readable `self.method` label — ported, but onto `Entry.normalize()` directly, not a
  `Root`-level normalizer.
- Nested-workflow `tasks` stamping for `subentry` — already implemented pre-Phase-6, via
  `Entry.to_workflow()`.

`NexusParserV2` already populates `sample`/`instrument`/`data` SubSections directly, which is why
the old bucketing walk over `m_all_contents()` has no v2 equivalent to port — the problem it
solved doesn't exist in the new architecture.

## Alternatives considered

**`AnchoredReference` class** (originally speculated as the v2 identifier mechanism): rejected.
No structural gap required it — `Object.normalize()` plus `resolve_or_create_entity()` and a
single `nexus_identifiers` SubSection cover the same ground without introducing a new annotation
concept. The long-term goal of identifiers being instances of their own class (e.g. a `Sample`)
rather than abstract references remains open, but is no longer blocked on this decision.

**Porting `NexusMeasurement.normalize()` as a `Root`-level method**: rejected once each of its
sub-responsibilities was traced individually and found already covered — porting it wholesale
would have reintroduced dead bucketing logic for SubSections the parser already populates
directly.

## Consequences

- `Object.normalize()` is now a load-bearing location for identifier resolution — any future
  `Object` subclass inherits `identifierNAME` handling for free, without opting in.
- `resolve_or_create_entity()`'s fallback file-creation behavior means an unresolvable identifier
  silently creates a new archive entry rather than failing loudly; this mirrors v1's behavior and
  was not revisited as part of this decision.
- This resolves the "stay in pynxtools vs. move to nomad-measurements" question for identifiers:
  the mechanism lives in `Object.normalize()`, which stays in pynxtools per the Long-Term
  Dependency Architecture (annotations and parser stay in pynxtools permanently).
