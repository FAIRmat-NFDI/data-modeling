# ADR-011: nomad-measurements v1→v2 Migration — Per-Plugin Findings and Sequencing

**Status**: Findings and plan recorded; migration itself not started (Phase N, gated on Phase 5/ADR-009 settling first). Naming targets below superseded — see status update.
**Date**: 2026-08
**Deciders**: Lukas Pielsticker
**Dicussion panel**: Area B core team, Hampus, Sarthak (nomad-measurements)

## Status update (2026-11-09)

ADR-009's own decision (b) was reverted after this ADR was written (see ADR-009's status
update): `Measurement.samples`/`.instruments` stay **plural**, matching NOMAD's own
list-naming convention, not the singular `.sample`/`.instrument` this ADR's findings and
migration plan assume throughout. `.results` → `.data` is still correct (kept, with `results`
restored as an alias). Concretely, every "rename to singular" instruction below is wrong:

- **XRD**: no `samples`/`instruments` rename needed at all now (it already uses
  `Measurement.samples`'s plural v1 shape) — only the `results` → `data` rename and the v1→v2
  `SystemReference` type change still apply.
- **Transmission**: the six `self.instruments` call sites do **not** need to become
  `self.instrument` — leave them plural. Only `results` → `data` renames apply (and
  `samples`/`instruments` stay the SubSection names, just re-typed to v2's `SystemReference`/
  `InstrumentReference`).
- **Quantumdesign**: `QDMeasurement.samples` class-attribute reference stays `samples` —
  **no rename needed here either**, which removes the landmine this ADR flagged (§ Consequences).

Separately, pynxtools's own generated schema went through a parallel pluralization pass
(branch `pluralize-subsections`, not yet merged to pynxtools `develop`) so that `Entry.sample`/
`.instrument` etc. also read as `Entry.samples`/`.instruments` — keeping the generated
NeXus-derived schema's naming consistent with this ADR's (corrected) basesections target. That
branch also fixed a real bug this consistency work surfaced: a narrowing override in an
application definition (e.g. `Transmission`'s own single, non-repeating `instrument` field) has
to resolve to the *exact* same Python name as `Entry`'s own (pluralized) slot, or NOMAD's
name-based SubSection override silently splits into two unrelated fields instead of narrowing
the inherited one — see that branch's generator changes (`_entry_subsection_names` matching in
`nxdl_to_metainfo.py`) before assuming a field rename here is purely mechanical.

Also: `basesections.MeasurementResult` (referenced implicitly throughout this ADR's prose) has
since been renamed to `MeasurementData` in `nomad-FAIR`'s `basesections-v2-nexus-alignment`.

---

## Context

`nomad-measurements` is the intended eventual home of the generated NeXus metainfo schema
(`metainfo/` — see the Long-Term Dependency Architecture). Before that move, its existing v1
plugins (`xrd`, `transmission`, `quantumdesign`, `mapping`, `general.py`) need to migrate onto the
v2 basesections shape decided in Phase 5/ADR-009 (`Measurement.samples`/`.instruments`/`.results`
→ `.sample`/`.instrument`/`.data`, plus the `Instrument`→`InstrumentEntry` rename). This ADR
records the per-plugin audit findings and the migration sequencing agreed for Phase N, so the
work doesn't have to be re-derived when Phase N actually starts.

## Decision

### Per-plugin findings (v1, `packages/nomad-measurements/src/nomad_measurements/`)

- **`xrd/schema.py`**: `XRayDiffraction(Measurement)` overrides `results` → `XRDResult`
  (`intensity`/`two_theta`/`q_norm` fields). Does **not** use `Measurement.instruments` — embeds
  source details in `xrd_settings.source: XRayTubeSource` instead. Uses base
  `CompositeSystemReference` for samples, unnarrowed. Already has a hand-written
  `NEXUS_DATASET_MAP` (`xrd/nx.py`) bidirectionally mapping to `NXxrd_pan`.
- **`transmission/schema.py`**: `UVVisNirTransmission(Measurement)` overrides **both** `samples`
  (→ `TransmissionSampleReference`) and `results`, **and has live code reading/writing
  `self.instruments`** (`connect_instrument()`, `extract_light_source_data`,
  `extract_detector_data`, `extract_monochromator_data` — six call sites).
  `Spectrophotometer(Instrument, EntryData)` extends v1's `Instrument` directly with
  `detectors`/`light_sources`/`monochromators`.
- **`quantumdesign/schema.py`**: reads `len(self.samples)` and calls
  `self.m_add_sub_section(QDMeasurement.samples, sample)` — a **class-attribute** reference to
  the literal field name, not just instance access. Won't surface as an attribute error until
  runtime if missed.
- **`mapping/schema.py`**: `MappingMeasurement(Measurement)` has a hand-rolled
  `AffineTransformation` (general 2D affine, solved from 3 before/after point correspondences).
  Conceptually parallel to — but mathematically narrower-yet-more-general than, in different ways
  — NeXus's `NXtransformations`. The math does not trivially unify; deferred, not part of this
  migration (see Phase 5 decision 5).
- **`general.py`**: `ActivityReference`/`ProcessReference` (custom reference classes with
  `lab_id`-based search normalization, predating/paralleling v2's `EntityReference`),
  `InSituMeasurement(Measurement)` with a `process: SubSection(ProcessReference)` field —
  infrastructure that exists but is currently unused by any shipped technique plugin.

### Migration plan (v1 → v2, combined with NeXus alignment)

Sequencing: **XRD first** (lowest cost, validates the pattern), then transmission and
quantumdesign (higher-touch renames).

- **XRD**: lowest cost. No `instruments` usage to update. Needs: switch import to v2
  basesections, rename its `results` override to `data` (per Phase 5 decision 2), and the
  `samples`→`SystemReference` type change v1→v2 requires regardless. `NEXUS_DATASET_MAP` becomes
  a candidate for later simplification once field names align — not required for this migration.
- **Transmission**: highest cost. Six call sites referencing `self.instruments` become
  `self.instrument` (`connect_instrument()`, `extract_light_source_data()`,
  `extract_detector_data()`, `extract_monochromator_data()`); `samples`/`results` overrides
  rename to `sample`/`data`. `Spectrophotometer(Instrument, EntryData)` likely extends
  `InstrumentEntry` directly going forward — it's a static lab-equipment description, like
  `Fabrication`.
- **Quantumdesign**: `QDMeasurement.samples` class-attribute reference (used with
  `m_add_sub_section`) must become `QDMeasurement.sample` — grep-verify, since this won't surface
  as an attribute-access error until runtime.
- **Mapping**: no change required by the renames; the `AffineTransformation`/`NXtransformations`
  parallel is deferred (Phase 5 decision 5).
- **`general.py`**: `InSituMeasurement(Measurement)`'s `process: SubSection(ProcessReference)`
  field doesn't collide with anything renamed; worth a pass to check whether
  `ProcessReference`/`ActivityReference` are superseded by v2's `EntityReference` — a
  consolidation opportunity, not required for this migration.

**Verification**: migrate XRD first, run its test suite, then transmission and quantumdesign with
the higher-touch renames.

## Alternatives considered

**Migrate all five plugins simultaneously**: rejected — XRD's low cost makes it a validation
pilot for the rename pattern before touching the two plugins (transmission, quantumdesign) with
real behavioral dependencies on the renamed fields.

**Unify `AffineTransformation` with `NXtransformations` as part of this migration**: rejected —
the two are mathematically related but not trivially interchangeable; forcing unification here
would expand this migration into a separate design problem. Deferred to Phase 5 decision 5's
scope, not Phase N.

## Consequences

- This ADR is the durable record of the per-plugin audit that previously existed only in the
  internal working plan's Phase N section — the external/shareable plan doc's own Phase N section
  is a stub that points here now instead of back at an internal-only file.
- Phase N cannot start until Phase 5/ADR-009's basesections shape has H/S review sign-off, since
  the rename targets (`sample`/`instrument`/`data`) are exactly what Phase 5 decided.
- `quantumdesign`'s class-attribute reference is a known landmine for this migration — flagged
  explicitly here so it isn't rediscovered the hard way during Phase N.
