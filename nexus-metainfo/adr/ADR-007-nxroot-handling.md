# ADR-007: NXroot Handling — Every File Gets a Root(Experiment) Grouping Entry

**Status**: Decided (Phase 3 implementation)
**Date**: 2026-06
**Deciders**: Lukas Pielsticker  
**Dicussion panel**: Hampus Näsström, Area B core team, Project Meeting participants

## Summary

Every NeXus file parsed by `NexusParserV2` produces a `Root` child archive — keyed `"root"` — in addition to one archive per `NXentry` group. `Root` inherits from `basesections.Experiment`, not `basesections.Measurement`. This grouping entry is always created, including for files with exactly one `NXentry`.

```python
class Root(Object, basesections.Experiment, EntryData):
    m_def = Section(
        a_nexus_definition=NeXusDefinition(nx_class="NXroot", category="base"),
    )
    entry = SubSection(section_def=Entry, repeats=True, variable=True, ...)
    # NXroot's own attributes: file_name, file_time, creator, NeXus_version, ...
```

```python
# NexusParserV2.is_mainfile()
return entry_names[1:] + ["root"]   # always includes "root", even for one-entry files
```

## Context

NeXus files have exactly one `NXroot` group at the file root, which contains one or more `NXentry` groups. Phase 1/2 of this refactor produced a `Root` Python class for `NXroot` (inheriting from `Object` only) but did not decide how — or whether — the parser should instantiate it. The original integration plan (§3, "NeXus File to NOMAD Entry Mapping") explicitly deferred this:

> **NXroot handling**: Out of scope for Phase 2. Revisit in Phase 2b when application classes exist: one option is to wrap all NXentry instances from a single file into a `basesections.Measurement` parent section (one measurement per file, multiple entries as steps).

Phase 3 (parser v2) had to resolve this to implement `is_mainfile()`/`parse()` for multi-entry files via NOMAD's child-archive mechanism, which requires a fixed, enumerable set of child keys per file.

### Options considered

**A. No grouping entry — one archive per NXentry only (1:1, original Phase 1/2 framing).**
Simplest; matches "one NOMAD entry per NXentry" stated in the original plan. But `NXroot`-level attributes (`file_name`, `file_time`, `creator`, `NeXus_version`, ...) and the relationship between NXentry siblings in the same file have nowhere to live. Multi-entry files would have N disconnected archives with no record that they came from the same file.

**B. Wrap into `basesections.Measurement` (as speculated in the original plan).**
A `Measurement` is the wrong semantic: NOMAD's `Measurement` represents a single measurement activity, but a `Root` is a per-file grouping of one or more measurements (one or more `NXentry` groups, each already mapped to its own `Measurement`-like `Entry`/application class). Nesting a `Measurement` inside a `Measurement` is confusing and not how `basesections.Measurement` is intended to be used.

**C. Wrap into `basesections.Experiment` (chosen).**
`basesections.Experiment` in NOMAD's base section library exists precisely to group multiple `Measurement`-like entries that share a common context (here: "came from the same file"). Each `NXentry` already produces its own `Entry`/application-class archive carrying the NXentry's own semantics; `Root` only needs to record the NXroot-level metadata and link the sibling entries.

## Decision

**Use Option C.** `Root(Object, basesections.Experiment, EntryData)` is always created as a `"root"` child archive, for every NeXus file, regardless of how many `NXentry` groups it contains.

### Always-create rationale (not conditional on entry count)

A conditional rule ("only create `Root` if there is more than one `NXentry`") was considered and rejected:
- It makes `is_mainfile()`'s child-key list depend on file content in a second way (beyond which entry names exist), adding a second prescan-dependent branch to maintain.
- Single-NXentry files still have `NXroot`-level attributes (`file_name`, `creator`, NeXus version, etc.) worth capturing somewhere; without `Root`, this data has no home for single-entry files specifically, an inconsistency with multi-entry files.
- A consistent "every file has exactly one `Root` archive" invariant is simpler to reason about for downstream consumers (the app, search, future round-trip exporter) than a count-dependent one.

## Implementation

- `NexusParserV2.is_mainfile()`: returns `entry_names[1:] + ["root"]` as child-archive keys (first entry is the main archive; remaining entries and `"root"` are children NOMAD pre-creates).
- `NexusParserV2.parse()`: populates each `NXentry` archive via its own `NomadVisitorV2`, then populates the `"root"` child archive's `Root()` instance with the `NXroot` group's own attributes and a `SubSection` reference to each entry.
- `m_nx_data_path` (per-NXentry HDF5→archive path mapping) stays on each `Entry` instance, not on `Root` — it is scoped per-entry, not per-file.

## Consequences

- The NOMAD search/explore app must account for `Root` as an additional entry type per file (already done in `app_v2.py`).
- Re-processing a file that was previously parsed by parser v1 (which produces one archive per `NXentry` with no grouping entry) will now also produce a `Root` archive when reprocessed under v2 — this is part of the broader v1→v2 migration, not a v2-only concern (see the v1.0/v2.0 roadmap's note on coordinated NOMAD-side data migration for the `__field`-suffix removal; the same migration window applies here).
- Phase N (`nomad-measurements` alignment) needs to be shown this archive shape (`Root` + per-`NXentry` archives) before nomad-measurements sections start inheriting from generated NeXus classes, since it changes what "one entry per file" means in practice.

## Alternatives Considered

### No grouping entry (Option A)
- **Pro**: matches the original 1:1 framing exactly; no new base-section dependency.
- **Contra**: `NXroot`-level attributes and cross-entry file relationships have no representation; doesn't scale cleanly to multi-entry files via NOMAD's child-archive mechanism.

### `basesections.Measurement` wrapper (Option B)
- **Pro**: was the option named in the original plan, so "least surprise" relative to prior documentation.
- **Contra**: semantically wrong — nests a measurement-shaped section around other measurement-shaped sections; `Experiment` already exists in NOMAD specifically for this grouping role.

## References

- [Integration plan §3](../nexus-metainfo-integration-plan.md) — original "NeXus File to NOMAD Entry Mapping" framing, now superseded by this ADR
- [ADR-003](ADR-003-base-section-mapping.md) — base section mapping (`NXroot` → `Object`; this ADR adds the parser-time `basesections.Experiment` mixin used only by the generated `Root` class)
- [ADR-006](ADR-006-application-definitions-are-entry-subclasses.md) — companion decision for how individual `NXentry` groups map to entries; this ADR addresses the file-level grouping above that
