# ADR-009: Aligning Experiment-Related Basesections (v2) with the NeXus Schema

**Status**: Decided and implemented on `pynxtools`/`nomad-FAIR` (pynxtools branch `nexus-metainfo-phase5`, nomad-FAIR branch `basesections-v2-nexus-alignment`); pending H/S review. Decisions (b) and (c) partially superseded — see status update below.
**Date**: 2026-07-22 (decisions finalized); implemented 2026-07-28/29
**Deciders**: Lukas Pielsticker
**Discussion panel**: Hampus Näsström, Sarthak Kapoor, Area B core team

## Status update (2026-09-15)

Further team discussion revised two of the decisions below; recorded here rather
than rewritten in place, to keep the original reasoning intact.

- **Decision (c), `Activity.sub_activities`**: removed from
  `basesections-v2-nexus-alignment`. The team is redesigning same-entry
  activity nesting on a separate branch, `nomad-FAIR`'s
  `nesting-at-activity-level`, which unifies containment and cross-entry
  reference into one `ActivityStep`/`NestedActivityStep` mechanism and — a
  larger, not-yet-finalized change — plans to remove the `Experiment` class
  entirely (an activity containing activities, instead of a dedicated
  grouping class). Until that branch lands, `nomad-FAIR` has no
  sub-activity-nesting mechanism at all; pynxtools's `nexus-metainfo-phase5`
  `Entry.to_workflow()` override (which bridges `subentry` into
  `sub_activities`) will need to be adjusted once the new mechanism is ready,
  but that adjustment is out of scope until then.
- **Decision (b), `Measurement.samples`/`.instruments` → `.sample`/`.instrument`**:
  reverted back to plural (`samples`/`instruments`), matching NOMAD's own
  list-naming convention rather than NeXus's singular-name-per-field
  convention. `.results` → `.data` is **kept** as the canonical name (the team
  agreed `data` is the better name for raw measurement data, with `results`
  historically meaning more standardized/aggregated output), but `results` is
  restored as a NOMAD-native alias (`aliases=['results']`) for backward
  compatibility. Separately, this pluralization decision motivates a broader,
  still-open follow-up: pynxtools's own generated schema currently produces
  singular NeXus-derived names for repeating subsections and needs a
  pluralization pass (tracked outside this ADR).
  Known conflict: `nomad-measurements` already has three `Measurement`
  subclasses (`QDMeasurement`, `UVVisNirTransmission`, `MappingMeasurement`)
  that declare their own, unrelated `results` field (aggregated/computed
  results, not an alias of `data`). The `results` alias on the shared base
  class collides with those; they will need renaming before adopting this
  branch's `basesections.Measurement`. Not yet resolved.

## Summary

`nomad.datamodel.metainfo.basesections.v2`'s `Measurement`/`Instrument` shape and pynxtools's generated NeXus schema (`Entry`, `Instrument`, `Process`, ...) currently disagree in several concrete places, and the investigation behind this ADR also surfaced two foundational bugs unrelated to naming: (1) the entire generated schema currently targets **v1** basesections, not v2, despite the stated intent; (2) the schema's root class makes every generated NeXus class independently creatable as a standalone NOMAD entry, whether that's wanted or not. This revision folds fixes for both into the same pass as the original naming/shape decisions, since every decision below is moot if the underlying mapping still points at v1.

This ADR proposes:
- (a) renaming `basesections.Instrument` → `InstrumentEntry` and adding a new, general `basesections.Instrument` that composes a singular reference to it,
- (b) renaming `Measurement.samples`/`.instruments`/`.results` → `.sample`/`.instrument`/`.data`,
- (c) a new `Activity.sub_activities` containment primitive replacing the ad hoc workflow2-clobbering workaround originally proposed,
- (d) mapping `NXprocess` to the existing `basesections.Analysis` (no new class),
- (e) fixing `BASESECTIONS_MAP` and the schema root to actually target v2,
- (f) removing the universal `EntryData` leak from the schema root,
- (g) a new default of `Activity` (not `Measurement`) for generated `Entry`, with application definitions opting into `Measurement` explicitly,
- (h) mapping `NXsample`/`NXsample_component` onto v2's existing `System` directly (no porting of v1's `CompositeSystem`/`Component`), bridged to `System.sub_systems` via a `normalize()` override,
- (i) mapping `NXactivity` to the now-unused `basesections.Process`.

Both (a) and (b) are basesections v2 changes only — v1 (what `nomad-measurements` currently uses) is untouched by this ADR.

## Scope

This ADR covers the **design and pynxtools-side implementation**: the basesections v2 redesign, the matching `BASESECTIONS_MAP`/schema-root changes on the pynxtools side, and this document. The basesections v2 redesign itself touches `nomad-FAIR`'s `basesections/v2.py` — shared infrastructure `nomad-measurements` also depends on — so it **does** need H's review before implementation, even though pynxtools's own generated schema currently only depends on v1.

What this ADR's implementation does *not* include is `nomad-measurements` actually *adopting* this shape (migrating `xrd`/`transmission`/`quantumdesign`/`mapping` off v1) — that's a separate, later, larger cross-team effort, tracked as "Phase N" in the internal project plan, not gated to happen immediately after this ADR is decided.

## Context

NOMAD's basesections come in two generations: **v1** (`nomad/datamodel/metainfo/basesections.py`, what `nomad-measurements` currently uses) and **v2** (`nomad/datamodel/metainfo/basesections/v2.py`, currently almost unused downstream). Two facts make *now* the right moment to revisit the mapping rather than later:

1. v2 has no real downstream consumers yet — `nomad-measurements` is still on v1, and migrating it to v2 is already planned independent of NeXus, so doing the NeXus-alignment redesign *as part of* that v1→v2 cut means no one migrates twice.
2. The NeXus schema and basesections disagree on shape in several concrete spots, and application-definition classes (`Xps(Entry)` etc., per [ADR-006](ADR-006-application-definitions-are-entry-subclasses.md)) inherit those mismatches into every `pynxtools-*` plugin's schema, so fixing them once here is far cheaper than per-plugin later.

### Finding: the schema currently targets v1, not v2 — not a preference, a bug

`pynxtools/nomad/converters/_mapping.py`'s `BASESECTIONS_MAP` uses dotted paths like `nomad.datamodel.metainfo.basesections.Measurement`. These resolve to **v1**: `nomad/datamodel/metainfo/basesections/__init__.py` does `from .v1 import *` for backward compatibility, so the bare package namespace is v1, not v2. The same applies to the schema root, `pynxtools/nomad/metainfo/base_classes/object.py`: `class Object(basesections.BaseSection)` — also v1. Every decision in this ADR is moot unless this is fixed as part of the same implementation pass.

### Finding: the schema root makes everything an entry, today, already

`nomad/datamodel/data.py:311` is a literal alias: `Schema = EntryData`. Since `BaseSection(Schema)` **is** `BaseSection(EntryData)`, and `Object(basesections.BaseSection)` is the root of **every** generated NeXus class (227 files as of Phase 4), every one of them — `Data`, `Component`(NXcomponent), `CoordinateSystem`, `Transformations`, `History`, `Activity`(NXactivity), `Note`, etc. — is *already* independently creatable as a standalone entry via NOMAD's ELN "create new entry" picker. This is not a risk introduced by this ADR's other decisions; it's the current, shipped state, surfaced while investigating decision 3 (below).

### Finding: v2 has no Component/CompositeSystem/CompositeSystemReference — resolved by using System directly, not porting

`basesections/v2.py` has `System`/`SystemReference` but not `Component(ArchiveSection)`/`CompositeSystem(System)`/`CompositeSystemReference(EntityReference)` — those exist only in `v1.py` (lines 770/957/1116). **Decided**: do not port these v1 classes. Verified against the actual NXDL (not just the generated Python): both `NXsample` and `NXsample_component` genuinely `extends="NXcomponent"` at the schema level (not a pynxtools coincidence), and `System`'s own docstring ("any system of materials which is investigated or used to construct other systems") is a strong match for `NXsample`; `SampleComponent`'s actual generated fields (`chemical_formula`, `unit_cell_abc`/`alphabetagamma`/`volume`) read as a smaller-scale material system, matching `System` just as well. See decision 9.

### Findings — basesections v2 (`nomad/datamodel/metainfo/basesections/v2.py`)

- `Activity(BaseSection)`: `datetime`, `method`, `location`, `steps: SubSection(ActivityStep, repeats=True)`. No field for containing a sub-*Activity* directly — nesting only happened via `Experiment.steps[i].activity` (a *reference*, not containment), with `NestedExperimentStep` allowing inline definition normalized into that reference. This ADR adds a general containment primitive directly to `Activity` (decision 1).
- `Measurement(Activity)`: `samples: SubSection(SystemReference, repeats=True)`, `instruments: SubSection(InstrumentReference, repeats=True)`, `results: SubSection(MeasurementResult, repeats=True)`. `normalize()` sets `archive.workflow2.inputs` from `samples` and `.outputs` from `results`.
- `Process(Activity)`: same `samples`/`instruments`, plus `steps: SubSection(ProcessStep)`. `normalize()` sets `archive.workflow2.outputs` from `samples`. Represents a *physical* transformation (docstring: "results in physical changes in a specified input material"; synonyms "sample preparation," "material transformations") — **stays completely untouched by this ADR**; NXprocess does not map to it (see decision 4).
- `Analysis(Activity)`: `inputs: SubSection(SectionReference)`, `outputs: SubSection(AnalysisResult)`. `MeasurementResult(ActivityResult): pass` and `AnalysisResult(ActivityResult): pass` are identical, empty passthrough classes, differentiated only by name — a real structural inconsistency (each of `Process`/`Measurement`/`Analysis` hand-rolls near-identical `workflow2` population under different field names). **Explicitly out of scope for this ADR** — flagged as a future cleanup candidate, not fixed here; the shapes stay exactly as they are.
- `Instrument(Entity)`: static lab-inventory entity — `name`/`lab_id`/`description` only, **no per-measurement settings**. `InstrumentReference(EntityReference)`: `reference: Quantity(Instrument)` + `lab_id`, with an existing `normalize()` resolving `lab_id ↔ reference` via NOMAD search.
- `Experiment(Activity)`: groups Activities via `ExperimentStep.activity` (reference) / `NestedExperimentStep` (inline-then-normalized-to-reference). **Stays unchanged** — a distinct use case from decision 1's `sub_activities` (cross-entry reference-based grouping vs. same-entry direct containment).

### Findings — pynxtools generated NeXus schema (`pynxtools/nomad/metainfo/base_classes/`)

- `Entry(Object, basesections.Measurement, EntryData)`: SubSections `sample`, `instrument`, `data`, `process`, `subentry`, `user` (all `repeats=True, variable=True`, **singular** Python names — the NeXus convention). Uniformly mapping every `Entry` to `Measurement` is wrong for simulation-only entries (`NXmicrostructure_score_config`/`_results`, `NXem`/`NXapm` with only simulation filled) — see decision 6.
- `Subentry(Object)`: does not inherit any basesections type today. NXDL describes it as "virtually identical to NXentry," used for multi-modal measurements (e.g. SAXS+WAXS in one file) — same SubSection shape as `Entry`.
- `Root(Object, basesections.Experiment, EntryData)`: has `entry: SubSection(Entry, repeats=True, variable=True)` declared **directly**, bypassing `Experiment.steps`/`ExperimentStep` entirely (see [ADR-007](ADR-007-nxroot-handling.md)) — the existing precedent for decision 1's containment approach.
- `Instrument(Object)`: inherits no basesections type today. Has `fabrication: SubSection(Fabrication, repeats=True, variable=True)`; `Fabrication(Object, basesections.Instrument)` carries `vendor`/`model`/`serial_number`/`construction_date`/`capability`.
- `Process(Object, basesections.ActivityStep)`: represents NXprocess — `program`/`sequence_index`/`version`/`date` plus `note`/`parameters`/`data` children. Data-provenance, not physical-sample-transformation. `Entry.process`/`Subentry.process` are **peer SubSections**, never nested inside anyone's `.steps` list.
- `Data(Object, basesections.MeasurementResult)`: NXdata (plottable signal + axes). Revised during Phase 6 implementation from the originally-planned `ActivityResult`: `Measurement.results` renamed to `.data` (decision 2) means `Entry.data` and `Measurement.data` now share the same attribute name wherever an application mixes in `Measurement` (decision 6), so `Data` must satisfy `Measurement.data`'s `MeasurementResult` typing for that override to type-check. `MeasurementResult(ActivityResult): pass` is a plain, field-free subclass, so this costs nothing for non-`Measurement` entries (`Process`'s own `data` field is unrelated — `Analysis.outputs`, not `.data`, so no naming collision there).
- `Activity`(NXactivity): generated fields `start_time`/`end_time`/`description`/`note`. Docstring reads generically ("superclass for all activities"), but nothing in the NXDL corpus actually `extends="NXactivity"` — its only real usage is as `History.activity`'s repeating child type. `History`(NXhistory)'s own doc: "A set of activities that occurred to a physical entity prior/during experiment" — a log of physical treatments (annealing, polishing, etc.) applied to a sample. See decision 9 (`NXactivity`→`Process`).
- `Component`(NXcomponent): doc "Base class for components of an instrument — real ones or simulated ones"; both `NXsample` and `NXsample_component` genuinely `extends="NXcomponent"`. A generic NeXus organizing concept (contributes `fabrication`/`program`/`transformations`/`applied`), no NOMAD-basesections analog — stays unmapped.
- Also generated, currently **unmapped**, no decision made: `History`(NXhistory, container for `Activity` entries — no basesections analog itself), `Transformations`(NXtransformations), `CoordinateSystem`(NXcoordinate_system). Flagged as a follow-up gap, not resolved by this ADR.
- `NXimage`/`NXspectrum`/`NXparameters`/`NXproject`/`NXenvironment`/`NXlog`/`NXnote`: not yet generated; no mapping decision needed until they exist.
- Current `BASESECTIONS_MAP` (all currently v1 — see finding above): `NXentry→Measurement`, `NXprocess→ActivityStep`, `NXsample→CompositeSystem`, `NXsample_component→Component`, `NXfabrication→Instrument`, `NXdata→ActivityResult`. Post-ADR target (all v2): `NXentry→Activity` (decision 6, `Measurement` per-application override), `NXprocess→Analysis` (decision 4), `NXsample→System`, `NXsample_component→System` (decision 8), `NXfabrication→InstrumentEntry` (decision 3), `NXdata→MeasurementResult` (revised from `ActivityResult` during Phase 6 implementation — see finding above), `NXactivity→Process` (decision 9).

### Precedent from nomad-measurements' XRD plugin

`nomad-measurements`' `xrd/schema.py` (`XRayDiffraction(Measurement)`) already does **not** use `Measurement.instruments` at all — it embeds source configuration inline on a plain `XRDSettings` SubSection, with no reference to any static `Instrument` entry whatsoever. Independent, real-world confirmation that "instrument as static inventory record" doesn't fit what a measurement actually needs to record about its instrument.

## Decisions

**1. `NXsubentry` → `basesections.Activity`, via a new general `Activity.sub_activities` containment primitive.**

`Subentry(Object, basesections.Activity)` (joining `Entry`). `Entry.subentry[i]` becomes an `Activity` nested inside another.

Revised 2026-07-29 from the original `basesections.Measurement` mapping: `Subentry` already redeclares its own `sample`/`instrument`/`data` SubSections directly, so `Measurement` contributed nothing there, and its `normalize()`'s `workflow2.inputs`/`.outputs` population never actually fires for a nested subentry — NOMAD normalizes children before their parent, so `archive.workflow2` is still unset when a subentry's own `normalize()` runs. Unlike `Entry`, `Subentry` is a single generic base class, not generated per application, so it has no way to opt into `Measurement` only for apps that are real physical measurements (decision 6's own reasoning) — `Activity` matches `Entry`'s own default and doesn't overclaim "measurement" for what could be simulation-only content (e.g. a subentry nested inside an `Em` entry).

The original draft of this ADR proposed handling the resulting `workflow2`-clobbering risk (every populated `Subentry`, and every `Entry` inside a multi-entry `Root`, independently overwrites the one-per-archive `archive.workflow2`) with a parent-type-sniffing skip in `Activity.normalize()`. That approach was rejected as NeXus-shaped rather than general. Instead:

```python
class Activity(BaseSection):
    ...
    sub_activities = SubSection(section_def=Activity, repeats=True)
```

`Activity.normalize()` is rewritten so each sub-activity's own `Workflow` is composed as a nested task inside the parent's (NOMAD already supports nested workflows as a first-class concept — `Workflow(Task, EntryData)`'s docstring: "Workflows themselves can be tasks... allows building nested workflows"; `TaskReference` exists for cross-entry composition). Only the true archive-root `Activity` assigns the result to `archive.workflow2` — a natural consequence of building the `Workflow` object locally and only attaching it at the actual entry-root level, not a special case for NeXus.

`Experiment`/`ExperimentStep`/`NestedExperimentStep` **stay exactly as they are** — a distinct use case (cross-entry, reference-based grouping) from `sub_activities` (same-entry, direct containment). Both mechanisms are needed.

**2. `Measurement.samples` → `.sample`, `Measurement.instruments` → `.instrument`, `Measurement.results` → `.data`** (and the same on `Process`).

Matches the NeXus convention already used by `Entry.sample`/`Entry.instrument` (singular name, list value — intentional, not an oversight). `results`/`data`: `MeasurementResult` is minimal (just `name`), but every override across every `nomad-measurements` plugin fills it with exactly the kind of content `NXdata` holds — the measured signal plus its axes. NeXus and NOMAD independently arrived at the same concept under two different names; unifying to `data` is semantically justified. Real migration cost for `nomad-measurements` (Phase N, not this ADR): `transmission/schema.py` has six call sites on `self.instruments` plus `samples`/`results` overrides; `quantumdesign/schema.py` references `QDMeasurement.samples` as a class attribute.

**3. `basesections.Instrument` → `InstrumentEntry` (rename), plus a new general `basesections.Instrument` composing a singular reference.**

```python
class InstrumentEntry(Entity):          # renamed from Instrument, otherwise unchanged shape
    name = ...
    lab_id = ...
    description = ...

class InstrumentReference(EntityReference):
    reference = Quantity(type=InstrumentEntry, ...)   # was type=Instrument — follows the rename

class Instrument(ArchiveSection):        # NEW, general — not NeXus-specific
    instrument_entry = SubSection(section_def=InstrumentReference)   # singular, no repeats
```

`Fabrication(Object, basesections.Instrument)` → `Fabrication(Object, basesections.InstrumentEntry)` (mechanical follow-on).

The original draft proposed pynxtools bolting `instrument_entry` onto its own generated `Instrument` class locally. Revised: the composition lives in a new, general `basesections.Instrument` class instead, so the "in-use instrument references a static catalog entry" pattern is a reusable basesections primitive, not a NeXus-only fix. pynxtools's generated `Instrument(Object, basesections.Instrument)` inherits `instrument_entry` for free; only the NeXus-specific population logic (`instrument_entry.lab_id` from `fabrication[0].serial_number` when there's exactly one `Fabrication` child) stays as pynxtools's hand-written `normalize()` override.

**Why `ArchiveSection`, not `Entity`/`BaseSection`, for the new `Instrument` class**: `Schema = EntryData` (literal alias, `nomad/datamodel/data.py:311`), so `BaseSection`/`Entity` both transitively carry `EntryData` — inheriting either would make the new `Instrument` class selectable as its own standalone entry type in NOMAD's ELN picker, which is wrong for something that only ever exists nested inside a `Measurement`. Only the plain `ArchiveSection` (not going through `Schema`/`EntryData`) avoids this — the same reason `ActivityStep`/`SectionReference`/`ActivityResult` already use it.

No new reference class was needed: `InstrumentReference` already *is* "a reference to the static catalog entry" — renaming what it points to is enough.

**4. `NXprocess` → `basesections.Analysis`** (revised from the original draft's proposed new `AnalysisStep(ActivityStep)`).

```python
class Process(Object, basesections.Analysis):   # was: basesections.ActivityStep in the original draft
```

`basesections.Process` is explicitly a *physical* transformation and stays completely untouched — NXprocess (data-provenance: `program`/`version`/`sequence_index`/`date`) is semantically closer to `Analysis`'s inputs→outputs shape. The original draft rejected `Process(Analysis)` specifically because it would multiply `workflow2`-clobbering across sequential `NXprocess` steps — that objection is resolved by decision 1's `sub_activities` mechanism, which handles nested-workflow composition generically. No new class is needed.

**5. NXtransformations / `nomad_measurements.mapping.AffineTransformation` unification — explicitly out of scope for this ADR.** The math doesn't trivially unify (general 2D affine-with-shear vs. NeXus's chainable single-axis rotation-or-translation primitives); flagged as a discovered architectural parallel worth a future, separate investigation. Related but distinct: `NXtransformations`/`NXcoordinate_system` are already generated but unmapped in `BASESECTIONS_MAP` — noted as a possible "lift to basesections" candidate for that same future investigation, not decided here.

**6. `Entry` defaults to `basesections.Activity`, not `Measurement`; application definitions opt into `Measurement` explicitly.**

```python
class Entry(Object, basesections.Activity, EntryData):   # was: basesections.Measurement
```

Not every `NXentry` is a measurement — simulation-only entries (`NXmicrostructure_score_config`/`_results`, `NXem`/`NXapm` with only simulation filled) don't fit `Measurement`'s semantics. A new per-application override table (same pattern as `BASESECTIONS_MAP`, not auto-inferred from NXDL content — that classification is domain judgment) lets specific application definitions mix in `Measurement` where correct.

**Concrete classification for the 6 application definitions already shipped in Phase 4**: `em`, `apm` → bare `basesections.Activity` (can be simulation-only); `mpes`, `raman`, `spm`, `xps` → `basesections.Measurement` (real physical measurements in practice). This change has **no effect on the apps themselves** (`app_v2.py`/`*_app` search-app definitions don't depend on which of `Activity`/`Measurement` `Entry` mixes in).

**Real cost, not near zero**: application definitions on bare `Activity` lose `Measurement`'s `sample`/`instrument`/`data` SubSections and its `normalize()`-driven `workflow2` population — those application definitions would need their own, until a future `basesections.Simulation` class exists (explicitly out of scope here).

**7. Remove the universal `EntryData` leak from the schema root.**

```python
class Object(ArchiveSection):   # was: basesections.BaseSection (which is basesections.v1.BaseSection today — see Finding above)
```

Classes that *should* be entry-creatable (`Sample` via `CompositeSystem`→`System`→`Entity`→`BaseSection`, `Process`/`Measurement`/`Analysis`/`Entry` via `Activity`→`BaseSection` or explicit `EntryData`, `InstrumentEntry` via `Entity`) still get it correctly through their `BASESECTIONS_MAP`-driven mixins — this removes only the automatic, universal leak from `Object` itself.

**Cost, explicitly accepted and paid**: all 227+ already-generated files were regenerated (`pynx nomad generate-metainfo --all --force`); the `name`/`datetime`/`lab_id`/`description` `_quantity`-suffix collision-avoidance rule (Phase 4) was re-verified against the now-smaller set of classes that still inherit those fields; all 6 apps' Phase 4 test suites were re-run post-regeneration with no regressions. Done in the same pass rather than deferred — cheaper while Phase 4's regeneration/testing context was still warm than as an isolated later change.

**8. `NXsample`/`NXsample_component` → `basesections.System` directly, bridged to `sub_systems` via `normalize()`.**

No porting of v1's `CompositeSystem`/`Component` — `System` already provides what's needed (`formula`, `geometry`, entity identity via `Entity`).

```python
class Sample(Object, basesections.System):            # was: Component, basesections.CompositeSystem
    ...

class SampleComponent(Object, basesections.System):   # was: Component, basesections.Component
    ...
```

The structural mismatch: NXDL's `Sample.component` is a **direct** SubSection list (`repeats=True, variable=True`, no reference indirection — like `Entry.sample`), but `System.sub_systems` expects a list of `SubSystem`/`NestedSubSystem` **wrapper** objects (reference-or-nested-then-normalized, mirroring `Experiment`/`ExperimentStep` rather than `Activity.sub_activities`'s direct-containment style).

**Resolved without changing `basesections` further** (per this ADR's own constraint of only changing what's already decided): `Sample.component` stays pynxtools's own direct, NeXus-native SubSection; `Sample.normalize()` additionally populates `self.sub_systems` by wrapping each `component[i]` in a `NestedSubSystem(nested_system=component[i])`. This gives NeXus-derived samples visibility to any generic NOMAD tooling built against `System.sub_systems`, without requiring `basesections.System` itself to grow a direct-containment field to match.

`NXcomponent` (the common NXDL ancestor of both `NXsample` and `NXsample_component`, confirmed via `extends="NXcomponent"` in both NXDL files) stays unmapped — see Findings above.

**9. `NXactivity` → `basesections.Process`.**

```python
class Activity(Object, basesections.Process):   # NXactivity — was unmapped
```

`NXprocess` no longer targets `Process` (decision 4 moved it to `Analysis`), leaving `Process` with no generated NeXus consumer — `NXactivity`'s real usage (logged inside `NXhistory` as physical treatments applied to a sample) matches `Process`'s "planned process which results in physical changes in a specified input material" semantics precisely, better than the abstract superclass reading its own docstring suggests. Field overlap (`end_time`, `description`) is handled by Phase 4's existing reserved-name/scalar-override rule — no new generator work needed. `NXhistory` itself (the container of `Activity` entries) stays unmapped — a structural NeXus concept, no basesections analog of its own.

## Consequences

- `nomad-measurements` migrates v1→v2 in the same pass as adopting these renames, as its own later phase (Phase N) — not part of this ADR's implementation. Concrete touch points once that phase starts: `transmission` (6 `self.instruments` call sites + `samples`/`results` overrides), `quantumdesign` (`QDMeasurement.samples` class-attribute reference), `xrd` (lowest cost).
- `NEXUS_DATASET_MAP` in `nomad_measurements/xrd/nx.py` becomes a future simplification candidate once field names align, once Phase N happens.
- All 227+ already-generated pynxtools base/application classes were regenerated and re-validated against the `Object`-root fix (decision 7) and the v1→v2 retargeting — this was the largest concrete execution cost of this ADR, distinct from any single naming decision.
- All 6 Phase 4 application test suites (`mpes`/`raman`/`spm`/`em`/`apm`/`xps`) were re-run post-regeneration with no regressions; `em`/`apm`'s `Entry` base changed to `Activity` (decision 6) as expected, with no test changes required to the apps themselves.
- Gates Phase 6 (`NORMALIZER_MAP` porting): `NexusMeasurement.normalize()`'s porting target depends on the final `Measurement.sample`/`.instrument`/`.data` shape decided here.
- Explicitly deferred, not fixed by this ADR: the `Process`/`Measurement`/`Analysis` structural inconsistency (identical empty `MeasurementResult`/`AnalysisResult` passthrough classes, independently hand-rolled `workflow2` population); `NXhistory`/`NXcomponent` remain unmapped in `BASESECTIONS_MAP`; `NXtransformations`/`NXcoordinate_system` "lift to basesections" remains an open idea, not a decision.
- `Sample.normalize()` gained new logic (decision 8) to bridge `component` into `sub_systems` via `NestedSubSystem` wrapping — covered by a new unit test confirming both fields stay consistent after normalization.

## Implementation notes

Implemented on `nomad-FAIR`'s `basesections-v2-nexus-alignment` branch (`nomad/datamodel/metainfo/basesections/v2.py`, `tests/datamodel/metainfo/test_basesections.py` — 8 tests, all passing) and `pynxtools`'s `nexus-metainfo-phase5` branch (`BASESECTIONS_MAP` retargeted to v2 in `converters/_mapping.py`; all 227+ generated files regenerated `--all --force`; `Sample.normalize()` bridge added in `nomad/metainfo/base_classes/sample.py`). Both branches are currently unreviewed by H/S — this ADR's decisions are settled from L's side, but the "Decided" status above does not yet mean team sign-off.

Two gaps surfaced by a manual multi-entry/multi-subentry parse-through-`NexusParserV2` check (2026-07-29), both fixed, both undetected by any prior test because nothing previously called `.normalize()` end-to-end on a parsed archive:

- **`Measurement`/`Process.normalize()` crashed on any real file with sample data**: both assumed every `self.sample` item was `SystemReference`-shaped (`sample.reference`), but pynxtools's `Entry.sample` holds `System`/`Sample` sections directly (decision 2's intentional direct containment). Fixed with `getattr(sample, 'reference', sample)` — `Link.section` is already typed as plain `ArchiveSection`, so no shape change was needed. (`nomad-FAIR`, `basesections/v2.py`.)
- **`Entry.subentry` (a nested `Activity`) was never reflected in `workflow2.tasks`**: `Activity.to_workflow()` only walks `self.sub_activities`, and `subentry` populates a separate field — the same section instance can't safely be added to two `SubSection` containers at once (confirmed empirically: no error, but `m_parent_sub_section`/`m_parent_index` silently point at whichever container it was added to last, and serialization would very likely duplicate the section). Fixed on the pynxtools side only, via a `to_workflow()` override on `Entry` that folds each `subentry`'s own workflow in as a sub-task, without touching containment. A reference-wrapper approach (`ActivityReference`, mirroring `SystemReference`/`InstrumentReference`) was considered and would also work, but was not pursued — it would mean retyping `sub_activities` itself on the shared `nomad-FAIR` side, blurring the direct-containment-vs-cross-entry-reference distinction between `sub_activities` and `Experiment`/`ExperimentStep`. Covered by a new regression test in `tests/nomad/test_parsing_v2.py` (`test_multi_entry_subentry_normalize`).

## Alternatives considered

**Inheriting `InstrumentReference` into `Instrument`** — rejected (is-a/has-a conflation, `normalize()`-MRO risk; see decision 3).

**A new `basesections.AnalysisStep(ActivityStep)` class for `NXprocess`** — the original draft's proposal, rejected on revision: it only existed to dodge `workflow2`-clobbering, which decision 1's `sub_activities` mechanism fixes generically; reusing `basesections.Analysis` directly is simpler and avoids adding a class whose only purpose was working around a since-fixed problem.

**Skipping `workflow2` writes based on parent-type sniffing** (the original draft's "required prerequisite") — rejected as a NeXus-shaped workaround rather than a general basesections capability; replaced by `sub_activities` (decision 1).

**Keeping `Entry` uniformly on `basesections.Measurement`** — rejected: conflates real measurements with simulation-only entries (`em`/`apm`), which is semantically wrong regardless of migration cost.

**Porting `Component`/`CompositeSystem`/`CompositeSystemReference` from v1 to v2** — rejected: `System` already covers what `NXsample`/`NXsample_component` need (see decision 8), and adding parallel v1-shaped classes into v2 would recreate the same v1/v2 duplication this ADR is trying to resolve elsewhere.

**Mapping `NXactivity` to a hypothetical new abstract `basesections.Activity`-adjacent class**, matching its docstring literally ("superclass for all activities") — rejected: nothing in the NXDL corpus actually extends `NXactivity`, and its one real usage (inside `NXhistory`, logging physical treatments) matches `Process`'s existing semantics precisely; inventing a new class to match a docstring with no real structural backing would be exactly the kind of unnecessary abstraction this project's principles argue against.

**Leaving the schema root (`Object`) on `basesections.BaseSection`** — rejected despite the regeneration cost: the alternative is every generated NeXus class permanently, silently creatable as a standalone entry, which is a worse and harder-to-notice problem than a one-time regeneration pass.

**`Entry` maps to `Experiment` with `Subentry` referenced via `ExperimentStep`** — rejected (conflicts with [ADR-006](ADR-006-application-definitions-are-entry-subclasses.md)'s `Entry`-is-directly-an-`Activity`/`Measurement` design).

## Open questions for team discussion

- Timing for Phase N (the actual `nomad-measurements` migration) relative to other H/S commitments — not blocking this ADR's pynxtools-side implementation, but needs a real answer before Phase N can be scheduled.
- `NXhistory`/`NXcomponent` (already generated, currently unmapped) — no decision made on whether/how these should map into basesections v2.
- Whether `NXtransformations`/`NXcoordinate_system` are worth "lifting" into basesections as general primitives, alongside the (separately out-of-scope) `AffineTransformation` unification question.
- The `Process`/`Measurement`/`Analysis` structural inconsistency (identical empty result passthrough classes, independently hand-rolled `workflow2` population) — flagged as real, deliberately not addressed here; worth its own follow-up discussion.

## References

- [Internal project plan](../../../../.claude/plans/we-are-planning-a-compiled-valiant.md) §19 Phase 5 (this ADR's implementation) and Phase N (the nomad-measurements migration this ADR enables but does not include)
- [ADR-003](ADR-003-base-section-mapping.md) — base section mapping; this ADR resolves the `NXinstrument`/`basesections.Instrument` open question ADR-003 flagged
- [ADR-006](ADR-006-application-definitions-are-entry-subclasses.md) — `Entry`-is-directly-an-`Activity`/`Measurement` design, which decisions 1 and 6 extend and which the rejected `Experiment`/`ExperimentStep` alternative would have conflicted with
- [ADR-007](ADR-007-nxroot-handling.md) — establishes the `Root.entry` plain-SubSection-containment precedent decision 1 relies on
