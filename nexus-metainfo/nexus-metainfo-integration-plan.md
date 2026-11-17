# NeXus–NOMAD Metainfo Refactor: Work Plan

> Internal plan with full implementation detail: `we-are-planning-a-compiled-valiant.md` (private)
> ADRs: [`adr/`](adr/)

## Table of Contents

- [Overview](#overview)
  - [Problem & Goal](#problem)
  - [Target Architecture](#target-architecture)
  - [NeXus File to NOMAD Entry Mapping](#nexus-file-to-nomad-entry-mapping)
  - [Architecture Decision Records](#architecture-decision-records-adrs)
- [Design Decisions](#design-decisions)
  - [Naming Conventions](#naming-conventions)
    - [Section names](#section-class-names) · [Application class naming / Phase 2b](#naming-for-application-definition-classes-phase-2b-submodule-layout) · [Quantity names](#quantity-field-names) · [Conflict resolution](#name-conflict-resolution) · [Connection to NXDL](#connection-from-python-class-to-nxdl)
  - [Annotation Models](#annotation-models)
  - [Visibility Rule](#visibility-rule-option-3b)
  - [Base Section Mapping](#base-section-mapping)
  - [Entry Point Splitting](#performance-entry-point-splitting)
- [Schema Structure](#schema-structure)
  - [File Layout](#file-layout-as-actually-implemented-through-phase-3)
- [Generator & Tools](#generator--tools)
  - [Code Generator](#code-generator-nxdl--python-nxdl_to_metainfopy)
  - [Round-Trip Exporter](#round-trip-python--nxdl-metainfo_to_nxdlpy)
  - [Parser Migration](#parser-migration--implemented-as-parser_v2py-phase-3-complete)
  - [schema.py End State](#schemapy-end-state-80-lines)
- [Roadmap](#roadmap)
  - [Phases](#phases)
    - [Phase 0](#phase-0--architecture-alignment-weeks-1-no-code) · [Phase 1](#phase-1--infrastructure--base-class-generation-complete) · [Phase 2](#phase-2--application--contributed-definitions-complete) · [Phase 2.5](#phase-25--eln-annotations-on-generated-schema-complete-added-after-this-plan-was-first-written) · [Phase 3](#phase-3--new-parser--new-app-v2-complete--superseded-the-original-bridge-schemapy-plan-below) · [Phase 4](#phase-4--migrate-pynxtools--plugins-to-v2-code-complete) · [Phase 5](#phase-5--align-basesections-v2-with-the-nexus-schema) · [Phase N](#phase-n--nomad-measurements-migration) · [Phase 6](#phase-6--port-normalizer_map-logic-to-normalize-methods-not-started--newly-identified) · [Phase 7](#phase-7--backwards-converter-metainfo_to_nxdlpy-not-started--file-does-not-exist) · [Phase 8](#phase-8--cleanup-not-started)
  - [5-Week Milestone](#5-week-milestone-project-meeting)
- [Architecture & Strategy](#architecture--strategy)
  - [Long-Term Dependency Architecture](#long-term-dependency-architecture)
  - [Design Tensions](#architectural-design-tensions)
  - [NOMAD Core Asks](#nomad-core-asks)
  - [Versioning Strategy](#versioning-strategy)
- [References](#references)
  - [Open Issues](#relevant-open-issues)
  - [Verification](#verification)
  - [Open Questions](#open-questions-for-adr-process)

---

## Overview

### Problem

The NeXus integration in NOMAD is perceived as fundamentally different from other plugins.
Root causes:
- Runtime NXDL → Metainfo generation produces no reusable Python definitions
- Intermediate wrapper classes (`NexusBaseSection`, `NexusMeasurement`) diverge from NOMAD idioms
- Normalizers injected via `NORMALIZER_MAP` instead of class methods — not overridable
- Naming leaks into user-facing code (`start_time__field`, `ENTRY___default`)
- Large monolithic schema package slows appworker startup
- No UI filtering of optional inherited quantities — users see full NeXus taxonomy

### Goal

Create one authoritative FAIRmat characterization/measurement layer:
- NeXus sections defined as **Python Metainfo classes** — importable, type-checkable, extensible
- Directly inherit from NOMAD base sections — no intermediary wrappers
- Quantities named after their NXDL concept (`start_time`, not `start_time__field`)
- Full schema with optionality annotations; UI filters by `optionality` (required/recommended shown by default, optional hidden)
- Schema loads fast via entry point splitting — domain plugins load only what they need
- Designed to eventually live in `nomad-measurements`

### Target Architecture

```
NOMAD base sections (BaseSection, Measurement, Instrument, …)
            ↑ inherits
NeXus base classes — Python-native, generated from NXDL
(Entry, Sample, Instrument, Source, …)
            ↑ inherits
nomad-measurements standard sections
(XRayDiffraction, XPSMeasurement, UVVisNirTransmission, …)
            ↑ inherits / extends
Plugin-specific schemas (lab-custom, instrument-specific)
```

Long-term: only the schema package (`metainfo/`) moves to `nomad-measurements`. The NeXus parser, search app, and examples stay in pynxtools — NOMAD must always parse `.nxs` files.

### Architecture Decision Records (ADRs)

Design decisions that arise during implementation are captured as **Architecture Decision Records** — short documents (1–3 pages) stating the decision, alternatives considered, and rationale. ADRs in this project are **living documents**: they reflect the current best understanding and may be revised as implementation reveals new constraints.

ADRs live alongside this plan in [`adr/`](adr/):

| ADR | Topic |
|---|---|
| [ADR-001](adr/ADR-001-nexus-annotations.md) | six annotation models: `NeXusDefinition`, `NeXusGroup`, `NeXusField`, `NeXusAttribute`, `NeXusLink`, `NeXusChoice` |
| [ADR-002](adr/ADR-002-optionality-semantics.md) | NXDL optionality → NOMAD; GUI visibility rule |
| [ADR-003](adr/ADR-003-base-section-mapping.md) | Canonical NeXus ↔ NOMAD base section mapping |
| [ADR-004](adr/ADR-004-code-generator.md) | Code generator specification |
| [ADR-005](adr/ADR-005-entry-point-splitting.md) | Entry point splitting and domain plugin interface |
| [ADR-006](adr/ADR-006-application-definitions-are-entry-subclasses.md) | Application definitions inherit from Entry, not Object |
| [ADR-007](adr/ADR-007-nxroot-handling.md) | NXroot handling: every file gets a `Root(Experiment)` grouping child archive |
| [ADR-008](adr/ADR-008-eln-annotations.md) | ELN annotations on generated NeXus schema: `a_eln`/`a_display`/`SchemaAnnotation` |

When this plan and an ADR conflict, the ADR takes precedence — it captures the more recent and detailed decision.

---

### NeXus File to NOMAD Entry Mapping

**One NOMAD entry per NXentry**, plus one file-level grouping entry — resolved in Phase 3, see [ADR-007](adr/ADR-007-nxroot-handling.md). Each NXentry becomes one independent NOMAD entry directly (the mapping is still 1:1 for entry *content*). Additionally, `NexusParserV2` always creates a `Root(Object, basesections.Experiment, EntryData)` child archive (key `"root"`) for every file — even single-NXentry ones, not just multi-entry files — grouping the file's `NXentry` instances. This was originally planned as a "future, if needed" addition (see history below); it shipped as part of Phase 3 instead of being deferred.

---

## Design Decisions

### Naming Conventions

#### Section (class) names
Remove `NX` prefix, then convert to CamelCase (each `_`-separated word title-cased).
Implementation in `converters/_mapping.py:nxdl_to_class_name`.

```
NXsample → Sample,  NXentry → Entry, NXelectrondetector → ElectronDetector 
NXxrd → Xrd, NXarpes → Arpes, NXoptical_spectroscopy → OpticalSpectroscopy
NXmicrostructure_ipf → MicrostructureIpf
```

#### Naming for application definition classes (Phase 2b: submodule layout)

Application definitions (Phase 2, current state: **flat files** — one `.py` per application,
e.g. `applications/xps.py` defining `class Xps(Entry)`) target a **submodule layout** as a
future, non-breaking reorganisation (Phase 2b, deferred to Phase 8):

```
applications/arpes/
    __init__.py    # class Arpes(Entry): top-level for NXarpes
    instrument.py  # class ArpesInstrument(Instrument): if it has own quantities
```

Named concepts are only generated when a group has own quantities differing from the base
class — same rule as Phase 1, regardless of flat-vs-submodule layout. This section describes
the target shape, not the current one; do not assume the submodule import paths exist yet.

#### Quantity (field) names
- NXDL fields: use the NXDL name directly — `start_time`, `energy`, `title`
- Attributes on groups: `{attr_name}` — no suffix, emitted without the `@` prefix
- Attributes on fields: `{field_name}__{attr_name}` — e.g., `energy__units`
- Variadic (nameType=any/partial): `variable=True` on SubSection/Quantity

#### Name conflict resolution

Two suffix rules handle all collision cases:

`_quantity` suffix applied to fields:
1. **Reserved NOMAD names** (`name`, `datetime`, `lab_id`, `description`) → `name_quantity`, etc.
2. **Field-vs-group collision** — when a NXDL field and group in the same class (or ancestor chain) share a Python name (e.g. `NXsample` field `sample_component` vs. `NXsample_component` group). Field renamed to `sample_component_quantity`; SubSection keeps `sample_component`.

`_group` suffix applied to SubSections (symmetric inheritance rule):
3. **Group-vs-ancestor-field collision** — when a child class introduces a group whose Python name matches a Quantity (field) already declared by an ancestor class, the group is renamed to `{name}_group`. The ancestor holds the unqualified name. Example: `NXapm_ranging` defines a variadic `program` group; `NXprocess` (mapped ancestor) already has `program` as a `Quantity` → SubSection becomes `program_group`.

#### Connection from Python class to NXDL

The connection is carried by the `NeXusGroup` annotation on `Section.m_def`, not by
class-level string attributes:

```python
class Xrd(Measurement):
    m_def = Section(
        a_nexus_group=NeXusGroup(
            nx_class="NXxrd",
            category="application",
            optionality="required",
        ),
    )
```

---

### Annotation Models

Six annotation classes replace the hidden `section.more["nx_*"]` protocol — one per NXDL
node kind. See [ADR-001](adr/ADR-001-nexus-annotations.md) for full rationale and the
reasoning behind splitting `<field>` and `<attribute>` into separate classes.

```python
class NeXusDefinition(AnnotationModel):  # on Section.m_def of every top-level class
    nx_class: str; category: ...; restricts: bool; ignore_extra_*: bool
    symbols: dict[str, str] | None; deprecated: str | None

class NeXusGroup(AnnotationModel):       # on named concept m_def or cross-file SubSection
    nx_class: str; name: str | None; name_type: ...; optionality: ...
    min_occurs: int | None; max_occurs: int | None; deprecated: str | None

class NeXusField(AnnotationModel):       # on Quantity from a NXDL <field>
    name: str; type: str; units: str | None; name_type: ...; optionality: ...
    enumeration: ...; open_enum: bool; interpretation: str | None
    long_name: str | None; deprecated: str | None

class NeXusAttribute(AnnotationModel):   # on Quantity from a NXDL <attribute>
    name: str; parent_field: str | None  # set for field-level attributes
    type: str; name_type: ...; optionality: ...; enumeration: ...; deprecated: ...

class NeXusLink(AnnotationModel):        # on Quantity(type=str) from a NXDL <link>
    name: str; target: str              # schema-level default target path
    optionality: ...; deprecated: str | None

class NeXusChoice(AnnotationModel):      # on SubSection for one <choice> alternative
    nx_class: str; group_name: str      # shared across all alternatives in the choice
    optionality: ...; deprecated: str | None
```

Registered at plugin load time — no NOMAD core PR needed:
```python
AnnotationModel.m_registry["nexus_definition"] = NeXusDefinition
AnnotationModel.m_registry["nexus_group"]      = NeXusGroup
AnnotationModel.m_registry["nexus_field"]      = NeXusField
AnnotationModel.m_registry["nexus_attribute"]  = NeXusAttribute
AnnotationModel.m_registry["nexus_link"]       = NeXusLink
AnnotationModel.m_registry["nexus_choice"]     = NeXusChoice
```

---

### Visibility Rule (Option 3B)

The schema remains complete and NeXus-compliant. Filtering is a presentation concern only.

**Rule**: optional inherited quantities are hidden by default in ELN, metainfo viewer, and
search. Required and recommended quantities — and any optional quantity that is populated
in the uploaded file — are always visible.

**GUI toggle**: "Show all defined quantities" toggle (off by default) reveals the full
NeXus taxonomy for power users.

**Implementation**: requires a general NOMAD core mechanism — not ELN-specific. See
[NOMAD Core Asks](#nomad-core-asks) items 1–2 for the consolidated ask (visibility mechanism
options and the related search-indexing question) and what's needed before approaching the
NOMAD team.

---

## Schema Structure

### File Layout (as actually implemented through Phase 3)

```
src/pynxtools/nomad/
    annotations.py                   # NeXusDefinition + NeXusGroup + NeXusField + NeXusAttribute + NeXusLink + NeXusChoice
    converters/
        __init__.py
        _mapping.py                  # nxdl_to_class_name, BASESECTIONS_MAP, type mapping, field_conflicts_with_group
        nxdl_to_metainfo.py          # NXDL → Python generator (additive-only)
        metainfo_to_nxdl.py          # Phase 7: Python + annotations → NXDL XML (round-trip) — not started
        cli.py                       # pynx nomad generate-metainfo
        templates/
            nexus.py.j2         # Jinja2 template (universal; category-aware header)
    metainfo/
        __init__.py                  # public API: build_base_classes_package(), build_applications_package()
        _package.py                  # assembles NOMAD Package
        base_classes/                # 142 .py files (category="base")
            entry.py                # Entry(Object, basesections.Activity, EntryData) — post-Phase-5/ADR-009
            sample.py                # Sample(Component, basesections.System) — post-Phase-5/ADR-009
            root.py                  # Root(Object, basesections.Experiment, EntryData)
            ...
        applications/                # 85 flat .py files (category="application", Phase 2)
            arpes.py                 # Arpes(Entry)
            xps.py                   # Xps(Entry)
            ...                      # submodule-per-app layout is Phase 2b, deferred to Phase 8
    schema_packages/
        schema.py                    # OLD, v1 — untouched; becomes an ~80-line shim only in Phase 8
        dataconverter.py             # OLD, v1 — ELN→eln_data.yaml→NeXus flow; populate_nexus_subsection() is dead code; NexusDataConverter.normalize() dispatches via process_updated_raw_file()
    parsers/
        parser.py                    # OLD, v1 — untouched, stays default until Phase 4 plugin migration completes
        parser_v2.py                 # Phase 3: NEW, additive — NexusParserV2, annotation-based navigation
        _field_io.py                 # Phase 3: NEW — HDF5 statistics/scalar-extraction helpers
    apps/
        nexus_app.py                 # OLD, v1 app — untouched
        app_v2.py                    # Phase 3: NEW, additive — nexus_app_v2
```

Phase 3 added `parser_v2.py`/`app_v2.py` as new, parallel, additive entry points — it did **not**
rewrite `parser.py`/`schema.py`/`nexus_app.py` in place. Those old files are only removed/shimmed
in Phase 8, once Phase 4 (plugin migration) and Phase 6 (normalizer porting) are both done.

---

### Base Section Mapping

Defined in `converters/_mapping.py:BASESECTIONS_MAP`. **Transitional** — long-term, the
mapping should be declared on the NXDL classes directly, not a hardcoded dict.

**Updated for Phase 5/[ADR-009](adr/ADR-009-experiment-basesections-alignment.md)** (done, pending
H/S review) — the table below reflects the current, post-Phase-5 mapping. See ADR-009 for the
full rationale behind each rename.

| NXDL class | Generated Python class inherits from |
|---|---|
| `NXobject` | `Object` (→ `BaseSection`) |
| `NXentry` | `Object, basesections.Activity` (`Measurement` only for the per-app opt-in techniques: mpes/raman/spm/xps) |
| `NXprocess` | `Object, basesections.Analysis` |
| `NXsample` | `Component, basesections.System` |
| `NXsample_component` | `Component, basesections.System` |
| `NXfabrication` | `Object, basesections.InstrumentEntry` (renamed from `Instrument` — see ADR-009) |
| `NXdata` | `Object, basesections.MeasurementData` |
| Application defs (`category="application"`) | `Entry` (NXentry wrapper unwrapped — [ADR-006](adr/ADR-006-application-definitions-are-entry-subclasses.md), *not* a separate `Measurement, Schema, PlotSection` mixin) |
| All others | `Object` |

`NXentry → Object, Activity`: each NXentry becomes one NOMAD entry (1:1 mapping, plus one
`Root(Experiment)` grouping entry per file — [ADR-007](adr/ADR-007-nxroot-handling.md)).
ADR-009 settled the `samples`/`instruments`/`results` vs. `sample`/`instrument`/`data` question
raised as an open item here in earlier drafts, then **reverted part of that decision** (see
ADR-009's own status update): `samples`/`instruments` stay **plural**, matching NOMAD's own
list-naming convention; `.results` → `.data` is kept, with `results` restored as an alias.
pynxtools's generated schema (`Entry.sample`/`.instrument` etc.) was pluralized to match, on
branch `pluralize-subsections` (not yet merged) — see ADR-011's status update for the override-
matching bug that pluralization pass had to fix along the way. `basesections.Instrument` was
renamed to `InstrumentEntry` (freeing `Instrument` for the NeXus-shaped, per-measurement concept)
because it already has real downstream consumers in nomad-measurements' `transmission`/
`quantumdesign` plugins — see [ADR-011](adr/ADR-011-nomad-measurements-migration.md) for the
(corrected) per-plugin migration impact of this rename.

`normalize()` lives as a method directly on each generated class — that part of the design is
final. **Not yet true today**: the generator currently only emits a `super().normalize()` stub;
porting the old `NORMALIZER_MAP`'s hand-written normalizers onto these stubs is its own phase
([Phase 6](#phase-6--port-normalizer_map-logic-to-normalize-methods-not-started--newly-identified)),
not yet started. `NORMALIZER_MAP`/`NexusBaseSection` still exist in the old runtime-generated
schema until that phase completes. Once classes are regenerated, the additive-only constraint
protects hand-written `normalize()` bodies — `ast.parse()` detects existing methods and never
overwrites them, only appends new quantities.

---

### Performance: Entry Point Splitting

Replace the monolithic schema package with multiple entry points.

**Current state (Phase 1)** — single entry point in `metainfo/__init__.py`:
```toml
[project.entry-points."nomad.plugin"]
nexus_base_classes = "pynxtools.nomad.metainfo:nexus_base_classes"
```

**Target state (Phase 2+)** — one entry point per category:
```toml
[project.entry-points."nomad.plugin"]
nexus_base_classes   = "pynxtools.nomad.metainfo:nexus_base_classes"
nexus_applications   = "pynxtools.nomad.metainfo:nexus_applications"
```
All entry point classes live in `metainfo/__init__.py`; each delegates to its own `_package.py`.

In addition, we may later define entry points for specific applications, like `mpes`:

```python
# mpes/_package_.py
from pynxtools.nomad.metainfo.base_classes.entry import Entry
from pynxtools.nomad.metainfo.base_classes.instrument import Instrument
from pynxtools.nomad.metainfo.applications.mpes import Mpes
```

```
[project.entry-points."nomad.plugin"]
mpes   = "pynxtools.nomad.metainfo:mpes"
```

Each entry point loads independently; Python's import caching handles deduplication. No runtime lazy loading state machine needed.

---

## Generator & Tools

### Code Generator: NXDL → Python (`nxdl_to_metainfo.py`)

**Pipeline**:
```
NXDL (.nxdl.xml / .yaml)
    ↓ existing NexusNode API
NexusNode tree
    ↓ Jinja2 templates (one per class type: base class, appdef, contributed)
Python source string
    ↓ ruff format (formatting)
.py file written to disk
    ↓ CI validation step: import + m_def check
```

Direct template generation — no round-trip through in-memory Metainfo classes.
This avoids the fundamental limitation that compiled Python methods cannot be serialised
back to source. Jinja2 templates are readable, testable, and the single thing to update
when the output format changes. NOMAD compatibility is validated post-generation by
importing the produced file and checking `m_def`.

**What it generates per NXDL file:**
- One Python class per top-level NXDL definition (currently flat `.py` files per application —
  submodule-per-app is Phase 2b, deferred), plus one named-concept class per group with its own
  differing quantities
- All quantities from the full NXDL inheritance chain with correct `optionality`
- SubSections for all group members using a fully-qualified string (`section_def="pynxtools.nomad.metainfo.applications.em.EmMeasurementEventID"`), resolved lazily by NOMAD at `__init_metainfo__()` time — no explicit `m_def = Section(name=...)` override needed, since Python class names are already unique per module
- `optionality` set on all quantities; drives UI visibility once the NOMAD core mechanism is agreed (not yet implemented)
- All six annotations (`NeXusDefinition`, `NeXusGroup`, `NeXusField`, `NeXusAttribute`, `NeXusLink`, `NeXusChoice`) populated from `NexusNode` metadata
- `a_eln`/`a_display`/`SchemaAnnotation` populated where applicable (Phase 2.5, complete — see [ADR-008](adr/ADR-008-eln-annotations.md))
- `normalize()` stub calling `super().normalize(archive, logger)` — developers fill it in; porting the *old* `NORMALIZER_MAP` logic onto these stubs is Phase 6, not yet started

**Additive-only constraint**: before writing, parse the existing file with `ast.parse()`,
collect all member names. Only append members not already present — never remove or rename.
This preserves hand-authored `normalize()` implementations when NXDL adds new fields.

**CI enforcement**:
```bash
pynx nomad generate-metainfo --all --dry-run  # fails if committed files differ from generated output
```
Catches NXDL version drift. A human must review and approve any field type/name changes.

**CLI**:
```bash
pynx nomad generate-metainfo --nxdl NXdetector [--all] [--dry-run] [--force]
pynx nomad generate-metainfo --all \
    --output-dir ../nomad-measurements/src/nomad_measurements/nexus/metainfo/base_classes
pynx nomad export-nxdl [--nxdl NXxps] [--all] [--check-only]
```

`--output-dir` is `None` by default, which resolves to the pynxtools-internal
`metainfo/base_classes/` directory. Pass an explicit path when generating into a
different package. This is how the same tool serves both the current pynxtools home and
the future nomad-measurements home without any code changes.

---

### Round-Trip: Python → NXDL (`metainfo_to_nxdl.py`)

Reads all six annotation models → emits NXDL XML.
- Errors on type changes against existing NXDL
- Never emits removals — human must handle deprecations manually

Required by the constraint: Python authoring must be a strict superset of NXDL semantics.

---

### Parser Migration — implemented as `parser_v2.py` (Phase 3, complete)

New annotation-based navigation instead of `section.more["nx_*"]` and name suffixes. **Note**:
this was implemented as a new, additive `parsers/parser_v2.py` (`NexusParserV2`), not a rewrite
of the old `parser.py` in place — `parser.py` stays untouched and default until Phase 4 (plugin
migration) completes.

**Core algorithm (as built)**:
1. Walk HDF5 tree via `NexusFileHandler`/`NexusVisitor`
2. For each HDF5 group: find matching Python section class via a per-Section-class `_SectionIndex`, matching `NeXusGroup.nx_class` against the HDF5 `NX_class` attribute
3. For each HDF5 field/attribute: find matching Quantity by `NeXusField.name` or `NeXusAttribute.name`, resolved through `NexusSchemaResolver` for variadic/NXdata-hinted names
4. Populate quantities directly — no `__field` lookup, no `___` attribute names
5. Fields not in schema: fall through to NOMAD's custom quantity mechanism

---

### `schema.py` End State (~80 lines)

```python
from pynxtools.nomad.metainfo import build_package

nexus_metainfo_package = None

def init_nexus_metainfo():
    global nexus_metainfo_package
    if nexus_metainfo_package is not None:
        return
    nexus_metainfo_package = build_package()
    nexus_metainfo_package.init_metainfo()
    # expose as module-level attrs for parser.py backward compat
    import sys
    module = sys.modules[__name__]
    for section in nexus_metainfo_package.section_definitions:
        setattr(module, section.name, section.section_cls)

init_nexus_metainfo()
```

All XML-parsing, `_create_class_section`, `_create_group`, `_create_field`,
`BASESECTIONS_MAP`, `NORMALIZER_MAP` — removed.

---

## Roadmap

### Phases

#### Phase 0 — Architecture Alignment (weeks 1, no code)

*Agree on all design decisions before writing any code — annotations, naming, base section mapping, generator spec, entry point strategy.*

Deliverables: ADRs, not implementation.

Required ADRs:
- **[ADR-001](adr/ADR-001-nexus-annotations.md)**: `NeXusDefinition`, `NeXusGroup`, `NeXusField`, `NeXusAttribute`, `NeXusLink`, `NeXusChoice` field names and types
- **[ADR-002](adr/ADR-002-optionality-semantics.md)**: Optionality semantics — how NXDL optionality maps to NOMAD; GUI visibility rule
- **[ADR-003](adr/ADR-003-base-section-mapping.md)**: Canonical NeXus ↔ NOMAD base section mapping
- **[ADR-004](adr/ADR-004-code-generator.md)**: Code generator specification (NexusNode input; Python output; additive-only)
- **[ADR-005](adr/ADR-005-entry-point-splitting.md)**: Entry point splitting strategy and domain plugin interface

> ADRs are living design documents — decisions may evolve as implementation progresses.

Semantic mapping document: full table of NeXus base classes → NOMAD base sections (covers
all ~156 base classes, not just the current BASESECTIONS_MAP partial list).

Schema contribution pathway document:
```
custom plugin → nomad-measurements standard section → NeXus application definition (NIAC)
```

#### Phase 1 — Infrastructure + Base Class Generation (**complete**)

*Build the generator and produce importable Python metainfo classes for all ~142 NXDL base classes (`category="base"`).*

- [x] `annotations.py` with `NeXusDefinition` + `NeXusGroup` + `NeXusField` + `NeXusAttribute` + `NeXusLink` + `NeXusChoice` (all registered)
- [x] `converters/_mapping.py` with `nxdl_to_class_name`, `BASESECTIONS_MAP`, `nx_type_to_source`, `field_conflicts_with_group`
- [x] `converters/nxdl_to_metainfo.py` — generator using `generate_tree_from()` from `NexusNode` API; zero raw XML access
- [x] `metainfo/base_classes/*.py` — all 142 generated Python files; regenerated with all fixes
- [x] `metainfo/_package.py` — `build_base_classes_package()`; assembles NOMAD Package; graceful degradation. NOMAD's metaclass auto-creates a per-module `Package` for each imported file. `setattr(mod, "m_package", assembled_package)` overrides these to prevent double-registration in `all_metainfo_packages()`; without the override `all_metainfo_packages()` would find both and register each Section twice.
- [x] `nexus_tree.py` refactored: `generate_tree_from()` → `NexusDefinition`; `_NexusEntityBase`/`NexusField`/`NexusAttribute` split; `NexusDefinition.get_link()` for documentation URLs
- [x] Entry points: `nexus_base_classes` in `pyproject.toml`; `build_base_classes_package()` public API
- [x] `links=[url]` on every `Section` and `Quantity` via `node.get_link()`
- [x] RST stripped from descriptions; `strip_rst` in `nexus/utils.py`
- [x] `_quantity` suffix for all name conflicts; `field_conflicts_with_group` helper
- [x] Same-class field/group conflict resolution; additive-only guard improved
- [x] ADRs 001–005 written in `data-modeling/nexus-metainfo/adr/`
- [ ] **Tests**: package equivalence; annotation tests; `test_annotation_fixes.py`

**Phase 1 implementation is complete. Remaining: ADRs + tests.**

#### Open question: generated `description=` strings (branch `nexus-metainfo-docstrings`)

The NeXus descriptions are very much geared towards NeXus; often they are also rather verbose. We could change that for the NOMAD Metainfo items.

The NeXus manual link (`links=[url]`) is always present, so users can always reach the authoritative NXDL description. This means `description=` can be genuinely user-facing rather than a spec copy.

Three options — **no decision yet**:

1. **Unchanged NXDL strings** — keep original text verbatim. Faithful to NXDL; requires no maintenance. Still contains RST markup, ISO references, and NeXus-committee prose that is confusing in a NOMAD GUI context.

2. **Plain-stripped strings** (branch `nexus-metainfo-docstrings`) — RST markup removed via `strip_rst`. Clean text, ready now. Content is still NeXus-centric and often too long; just removes formatting noise without addressing meaning.

3. **AI-rewritten descriptions** — LLM rewrites each description as 1–2 plain-English sentences suitable for a NOMAD GUI. Requires a review pass for scientific correctness.

If the individual concepts from the NeXus Ontology get registered, we can even add links to the actual PIDs; that would be the best solution.

#### Phase 2 — Application + Contributed Definitions (**complete**)

*Extend the generator to all `category="application"` definitions (official + FAIRmat contributed), producing `Xps(Entry)` style specializations and the `nexus_applications` entry point.*

**Key Design Decision** (see [ADR-006](adr/ADR-006-application-definitions-are-entry-subclasses.md)):
Application definitions generate `Xps(Entry)`, **not** `Xps(Object, Measurement)`.
Every NXDL application definition wraps exactly one NXentry at the top level. The generator unwraps this: it finds the NXentry child, uses its children as the effective children for generation, and sets Entry as the Python base class. This makes the intent clear in the Python code: Xps is a specialized kind of Entry, not a container that holds entries.

- [x] Discovery by `category` attribute in NXDL `<definition>`, not folder
- [x] `metainfo/applications/*.py` — 85 flat generated files (Phase 2 target: flat; Phase 2b target: submodule layout)
- [x] Contributed definitions discovered and generated alongside official applications
- [x] NXentry unwrapping in generator; Entry as base class
- [x] Named concepts follow Phase 1 rule: only when a group has own quantities
- [x] Two entry points: `nexus_base_classes` (142 base classes) + `nexus_applications` (85 application classes)
- [x] All 280 generated files committed and integrated
- [x] Package assembly working; cross-package references resolved
- [x] 156 tests passing; no regressions

**Remaining for Phase 2 closure**: ADRs review; ADR-006 written for architectural decision

#### Phase 2.5 — ELN Annotations on Generated Schema (**complete**, added after this plan was first written)

*Make every generated quantity ELN-editable where it makes sense, so NeXus base/application classes can be used as ELN schemas ("Create entry from schema"), not only as read-only parser targets.*

- [x] `a_eln=ELNAnnotation(component=ELNComponentEnum.<X>, default=...)` emitted on every scalar, non-array, non-`Bytes` `Quantity` — mapping: `str`→`StringEditQuantity`, `Datetime`→`DateTimeEditQuantity`, `bool`→`BoolEditQuantity`, single/multi-value `MEnum`→`EnumEditQuantity` (single-value sets `default=`), numeric (incl. `np.complex128`)→`NumberEditQuantity`
- [x] `a_display={'unit': '<unit>'}` (dict form, not `QuantityDisplayAnnotation.defaultDisplayUnit`, which is deprecated) on `NumberEditQuantity` quantities with a default unit
- [x] `a_schema=SchemaAnnotation(label="<ClassName>", enabled=False)` on `Entry` and `Root` `m_def` — hides these two non-instantiable base classes from "Create entry from schema". **`label` is a required field on `SchemaAnnotation`** (no default) — omitting it crashes NOMAD at `__init_metainfo__()`.
- [x] Named-concept quantities overriding a multi-dimensional base-class field (no explicit `shape=` re-specified) are excluded from ELN annotation — NOMAD inherits the parent's shape at init time, and `ELNAnnotation` rejects anything with `len(shape) > 1` ("Only scalars or lists can be edited.")
- [ ] Arrays (no array ELN component in NOMAD): `HDF5Reference`/`H5WebAnnotation` (the `nomad_measurements.xrd.XRDResult1DHDF5` pattern) investigated as a future option — requires parser changes to write HDF5 references; not started
- [ ] Optionality-driven visibility (`SectionProperties.visible` / `a_display={'visible': False}`) — still blocked on the same NOMAD core `visible_by_default` ask as Phase 0's open question; not resolved by this work
- **Needs a retroactive ADR** (none was written before implementation — this work resolved the "ELN editability tension" via `archive.metadata.readonly` rather than a duplicate `ELNXps` class, which is worth a written record)

#### Phase 3 — New Parser + New App v2 (**complete** — superseded the original "Bridge `schema.py`" plan below)

*The implemented strategy differs from what was originally planned here: instead of a `USE_LEGACY` flag inside the existing `schema.py`/`parser.py`, two entirely new, additive entry points were added — `nexus_parser_v2` and `nexus_app_v2` — leaving the old `nexus_schema`/`nexus_parser`/`nexus_app` untouched and still default. No `nexus_schema_v2` was needed; `nexus_base_classes` + `nexus_applications` (Phase 2) already serve as the v2 schema.*

- [x] `parsers/parser_v2.py` (`NexusParserV2`): annotation-based navigation via a per-Section-class `_SectionIndex` (`nx_class_to_subsections`, `choice_subsections`, `field_map`, `attr_map`, `field_attr_map`, `link_map`) — no `section.more["nx_*"]`, no `_rename_nx_for_nomad`
- [x] `apps/app_v2.py` (`nexus_app_v2`): new explore app referencing v2 section/quantity paths
- [x] **New decision not in the original plan — NXroot handling resolved**: every NeXus file produces a `Root(Object, basesections.Experiment, EntryData)` child archive (key `"root"`), in addition to one archive per NXentry — even single-NXentry files get one. `Experiment` was chosen over the speculatively-mentioned `Measurement`. Documented in [ADR-007](adr/ADR-007-nxroot-handling.md).
- [x] `m_nx_data_path`: implemented as planned — `Quantity(type=str)` added manually to `entry.py` (additive-only-safe), one JSON dict per NXentry, paths relative to that NXentry
- [x] `NeXusLink` quantities now resolve the link target's type/unit/shape (e.g. a link to a `NX_FLOAT` field becomes `Quantity(type=np.float64, unit=...)` instead of always `type=str`) — minor addition to the annotation model's effect, the `NeXusLink` fields themselves are unchanged
- [~] **FIELD_STATISTICS partially implemented**: `parsers/_field_io.py` computes `__mean`/`__min`/`__max`/`__size`/`__ndim`, but only the mean is consumed by the parser; the generator does not emit parallel `__min`/`__max`/`__size`/`__ndim` quantities on `Data`-derived classes. Genuinely deferred to Phase 4, not done.
- [x] `use_full_storage`/`MQuantity.wrap` implemented for variadic quantities — resolves the original "`is_full_storage` decision" item
- [x] **Gate met**: `tests/nomad/test_parsing_v2.py` (449 lines) — ARPES golden-output, ellipsometry + NXlauetof smoke tests, structural parity test, prescan test, Root-archive tests. Full pynxtools suite: 473 passing.

**After Phase 3, the parser/app v2 stack exists in parallel with v1 — v1 remains default until Phase 4 plugin migration completes.**

#### Phase 4 — Migrate pynxtools-* Plugins to v2 (**code + test complete** — all 6 app migrations committed; `dataconverter.py` confirmed no-op; true end-to-end testing gap remains open by design, per-plugin docs rescoped)

*Application-definition classes (e.g. `Xps(Entry)`) are generated centrally in pynxtools, not owned per plugin — a plugin's `pynxtools.reader` entry point only produces a `.nxs` file; parsing it is owned entirely by the single, shared `nexus_parser_v2` entry point. So "switch schema base"/"replace `NORMALIZER_MAP` callbacks" are not per-plugin tasks under the architecture actually built — flipping the active parser/app is a one-time pynxtools-core decision, not per-plugin code.*

**What is real, per-plugin work** (confirmed by survey across all 10 `pynxtools-*` packages):
- **NOMAD apps — done, all 6.** `mpes_app`/`raman_app`/`spm_app` (the 3 that already shipped) migrated to v2 paths; `em_app`/`apm_app` (previously disabled, trivial stubs) re-enabled with the same pattern; **`xps_app` written from scratch** — NXxps never had a shipped NOMAD app before this work, unlike the other 5. Every `search_quantity`/`quantity` string verified against the real generated schema, not just pydantic-validated. Several v1-era references turned out to be structurally unsearchable and were dropped rather than faked: array-shaped quantities (`shape=["*"]`, e.g. `axes`, `incident_energy`, `incident_polarization`) are unconditionally excluded from NOMAD's dynamic search-quantity registration; several `spm_app` v1 concepts (scan region/mesh scan, bias-spectroscopy sweep, `SPM_POSITIONER` controller/z-controller, cantilever oscillator) no longer exist in the current `NXspm`/`NXsensor_scan` definitions at all (version drift since v1). `nomad-FAIR`'s app-search allowlist was also missing `'Entry'` and `'Spm'` — both added. All 6 apps added to `nomad.yaml`'s `plugins.entry_points.include`.
- **Found while writing `xps_app` field-by-field against the real schema (not copied from the other apps): `name_quantity` was stale everywhere it appeared.** The generator's actual rule only suffixes a reserved `BaseSection` name (`name`/`datetime`/`lab_id`/`description`) when the field is array-shaped — a scalar override, the common case for `Sample`/`Instrument`/`User.name`, stays unsuffixed. `app_v2.py`, `mpes_app`, and `raman_app` all still referenced `name_quantity`; fixed everywhere. `spm_app`/`em_app`/`apm_app` never referenced these paths.
- `mpes_app`/`xps_app` also reference FIELD_STATISTICS-derived columns (`energy__min`/`energy__max`/`data__size`) — **done, in two passes**: first re-implemented, scoped to numeric array quantities inside `Data`-derived classes (`node.nx_class == "NXdata"`), including variadic DATA/AXISNAME signals via a wildcard-shape fallback used only for the has_statistics decision (never written back onto the quantity's own declared shape — doing so initially broke real ARPES parsing, since it changed how the parser populates the field; fixed). No `{name}__mean` quantity exists — confirmed empirically that v1's own mean-into-bare-field write fails silently too (no working precedent to preserve); only `__min`/`__max`/`__size`/`__ndim` are generated, with `__ndim` as `np.int8` (NOMAD has no real unsigned-int type and silently downcasts `np.uint8`). **This first pass was incomplete**: it still missed concretely-named NXdata axes with no NXDL `<dimensions>` (e.g. NXmpes's `energy`/`kx`/`ky`/`delay`). **Now genuinely closed**: `is_effectively_array` widened to treat any field inside an `NXdata`-derived class as array-like regardless of naming pattern; all affected classes regenerated repo-wide via `pynx nomad generate-metainfo --all` (`NXentry`/`NXroot` correctly left untouched by the additive-only guard — confirmed via direct member-diff, nothing lost). Documented in pynxtools's `docs/learn/pynxtools/nexus-metainfo-generation.md`.
- **Also found and fixed**: a rebase-artifact `NameError` (`_qty_field_suffix_for` referenced in the generator's field-processing branch but never defined — a prior refactor had already removed this exact check from a sibling code path, but a later rebase left one copy behind) that broke `pynx nomad generate-metainfo --nxdl ... --force`.

  **Forward-looking, not in scope for Phase 4**: writing the mean into an array-shaped quantity is a workaround. See [NOMAD Core Asks](#nomad-core-asks) item 3 — the better long-term answer is `HDF5Reference` for NXdata's DATA/AXISNAME-derived axes/signal fields. Not blocking; FIELD_STATISTICS as implemented is the pragmatic answer until/unless that lands.
- **App-level testing — done.** Every one of the 6 apps has a comprehensive `tests/nomad/test_nomad_apps.py` (properties, schema/filters_locked, columns, menu structure, dashboard widgets) — mechanically upgraded from a single import-smoke-test each. `pynxtools-xps`'s additionally walks every `search_quantity` in the app and resolves it attribute-by-attribute against the real generated `Xps` class — confirmed to catch the `name_quantity` bug above automatically. Kept XPS-only by explicit choice, not backported to the other five.
- **Example uploads / true end-to-end — still open, by design.** Example uploads are lower risk than apps: they mostly glob raw example files, not pre-baked archive JSON. **No harness tests the true end-to-end path** (raw file → `.nxs` → `nexus_parser_v2` → archive) without running real NOMAD infrastructure; `pynxtools.testing.nomad_example.parse_nomad_examples` only validates bundled ELN schema/archive files via NOMAD's generic `ArchiveParser`, not actual NeXus parsing. Manually verified (example uploads run cleanly, correct `.nxs` output, apps load and show real examples) but not automated — deliberately left open to test later.
- **Docs — rescoped, not a Phase 4 blocker.** Per-plugin *schema* documentation isn't needed: the NeXus schema is self-documenting. What's still worth doing — documenting each plugin's entry points (readers, apps) — is independent of this work package.
- `dataconverter.py` — **no change needed (confirmed during Phase 4)**. `populate_nexus_subsection()` hardcodes `NexusParser` (v1) but is dead code: never imported or called by any plugin (introduced for nomad-measurements but never integrated — see [nomad-measurements#118](https://github.com/FAIRmat-NFDI/nomad-measurements/pull/118)). The live ELN path is `NexusDataConverter.normalize()`, which calls `process_updated_raw_file()` — this dispatches through NOMAD's configured `plugins.entry_points.include`, already routing to `nexus_parser_v2` in this dev environment. `populate_nexus_subsection()` is a Phase 8 cleanup candidate.
- **Gate**: each migrated app/plugin's own test suite passes on the v2 stack. Met for all 6 apps.
- **Coordination**: publish a compatibility matrix (which pynxtools-* version requires which pynxtools) as part of the v1 release announcement.

#### Phase 5 — Align Basesections v2 with the NeXus Schema (**done, pending H/S review** — `nomad-FAIR` branch `basesections-v2-nexus-alignment`, `pynxtools` branch `nexus-metainfo-phase5`; promoted from the former "Phase N" to a sequential phase between Phase 4 and Phase 6)

*Resolves two shape mismatches raised in team discussion: (a) `basesections.Instrument` describes a static piece of equipment, but NeXus's `NXinstrument` describes the instrument *in use* with live per-measurement settings — these need two different classes, not one inheriting the other (nomad-measurements' XRD plugin already sidesteps `basesections.Instrument` for this reason, embedding settings inline on `XRDSettings` instead); (b) `basesections.Measurement` has `samples`/`instruments`/`results` where the generated `Entry` has `sample`/`instrument`/`data`. See the internal plan (§19 Phase 5) for the full findings/decisions breakdown and ADR-009 (below and at `adr/ADR-009-experiment-basesections-alignment.md`). **Scope: the basesections v2 redesign, `BASESECTIONS_MAP`, and ADR-009 — needs H's review, since the redesign touches shared infrastructure `nomad-measurements` depends on.** What it does *not* include is migrating `nomad-measurements`' own plugin code — that's Phase N below, done later.*

- **Migration risk, not just naming**: `basesections.Instrument` already has real downstream consumers (nomad-measurements' `transmission`/`quantumdesign` plugins). Repurposing the same class name for a different meaning would silently change behavior for existing code. Resolution: **rename**, don't repurpose — the static concept becomes `InstrumentEntry`, freeing `Instrument` for the NeXus-shaped, per-measurement concept (composition via a `instrument_entry` SubSection, not inheritance).
- ADR-009 written and all 9 decisions implemented (`nomad-FAIR`: `basesections/v2.py` + 8 passing tests in `test_basesections.py`; `pynxtools`: `BASESECTIONS_MAP` retargeted to v2, all 227+ generated files regenerated).
- Requires Phase 1 base classes and Phase 2 application definitions to be available
- Gates Phase 6: `NexusMeasurement.normalize()`'s porting target depends on the final `Measurement` shape decided here
- Manual multi-subentry-file parse check and full pynxtools + all-6-apps test re-run both done (2026-07-29), all green — surfaced and fixed two real gaps along the way (`Measurement`/`Process.normalize()` crash on direct-containment samples; `Entry.subentry` not reflected in `workflow2.tasks`), see ADR-009's "Implementation notes".
- **Not yet done**: H/S review of ADR-009 and the branches — the only remaining item before this phase closes.

**Status update (2026-11-09)**: `nomad-FAIR`'s `basesections-v2-nexus-alignment` is otherwise
settled and clean — a rebase had left a syntax error and several stale/duplicated tests in
`test_basesections.py` (testing removed functionality, undefined names/fixtures); fixed, all 16
tests pass, `ruff check` clean across the branch diff. Two things moved since ADR-009 was first
decided, both already captured in its own status update: decision (b)'s singular naming was
reverted back to plural (`samples`/`instruments`); decision (c) (`Activity.sub_activities`) was
removed outright — same-entry activity nesting is being redesigned from scratch on a separate,
not-yet-settled branch (`nomad-FAIR`'s `nesting-at-activity-level`), which this phase does not
depend on. `basesections.MeasurementResult` is now `MeasurementData`. A parallel pynxtools-side
pluralization pass (branch `pluralize-subsections`, off `nexus-metainfo-phase5`, not yet merged)
keeps the generated schema's own naming (`Entry.samples`/`.instruments`/etc.) consistent with the
corrected decision (b) — see ADR-011's status update for a real override-matching bug that
surfaced and was fixed along the way. [ADR-012](adr/ADR-012-provenance-tracked-generator-regeneration.md)
(provenance-tracked regeneration) is implemented and usable from `nexus-metainfo-phase5` via
`pynx nomad generate-metainfo --all --fix`, but not yet merged to pynxtools `develop` either.
**Before Phase N starts**: pynxtools's own branch stack (`nexus-metainfo-phase5` →
`nexus-metainfo-phase6` → `pluralize-subsections`) needs consolidating onto one line and landing
on pynxtools `develop` — `phase5` has its own rebase-artifact commit (titled, literally, "rebase
issues") that hasn't been checked for the same kind of damage just found and fixed on the
nomad-FAIR side, and `pluralize-subsections` is currently 8 commits behind `phase5` with its own
work still entirely uncommitted in its worktree.

#### Phase N — nomad-measurements Migration (**not started** — separate from Phase 5, done later together with H/S; not part of the 0–8 sequence)

*`nomad-measurements` actually adopts the shape Phase 5 decides on (plus its independently-planned v1→v2 basesections migration, done in the same pass). A cross-team effort with its own pace, gated on Phase 5's decisions/ADR-009 being settled first but not required to start immediately after. See the internal plan (§19 Phase N) for the full nomad-measurements-side findings and per-plugin migration breakdown (XRD lowest cost, transmission highest cost).*

- `nomad-measurements` sections inherit from generated Python NeXus classes; XRD as pilot (already has `NEXUS_DATASET_MAP`): `class XRayDiffraction(XRD):`
- Engage H before this phase's migration work starts (beyond the Phase 5 ADR review H already did) — plan the actual `xrd`/`transmission`/`quantumdesign` code changes together, not just review
- Per-plugin findings and sequencing recorded in [ADR-011](adr/ADR-011-nomad-measurements-migration.md) — **its original naming targets are superseded, see its own status update** (samples/instruments stay plural; the quantumdesign class-attribute landmine it flagged no longer applies)
- `nomad-measurements` becomes the authoritative FAIRmat measurement schema layer

**Status update (2026-11-09)**:
- `nomad-measurements` now has its own `main`/`develop`/`release` branching model, mirroring
  pynxtools and its plugins (`develop` integration branch, `main` release-only, `release/vX.Y.Z`
  branches gate publishing) — PR [#208](https://github.com/FAIRmat-NFDI/nomad-measurements/pull/208),
  including a `compatibility-with-nomad-release.yml` check that installs against the latest
  *released* `nomad-lab` independently of whatever ref `develop`'s own `pyproject.toml` is pinned
  to during the migration.
- **Real, not-yet-resolved coupling risk**: until both `nomad-FAIR`'s basesections v2 work and
  pynxtools's generator branch stack are released, `nomad-measurements`'s `develop` branch can
  only generate/import against *unreleased* branches of both — any `nomad-lab` pin on `develop`
  during this window is necessarily a git ref, not a release, and a `nomad-measurements` build
  made from `develop` will not work against a released `nomad-lab`. This is expected during the
  migration and is exactly what `compatibility-with-nomad-release.yml` is meant to surface, not
  hide — it is the real gate before cutting a `release/*` branch, not a Phase N blocker on its
  own.
- **Phase 2b (submodule-per-appdef layout) reconsidered**: worth doing as part of Phase N after
  all, not deferred to Phase 8 — `nomad-measurements` has zero existing consumers of the
  generated schema today, so there is no backward-compat cost to generating straight into a
  submodule layout; waiting until after Phase N would mean touching `nomad-measurements`'
  plugin-side import paths (`xrd`/`transmission`/`quantumdesign`) twice instead of once. Sequencing:
  build and verify the submodule-layout generator output against pynxtools's own existing flat
  output first (structural diff, same technique already used for the pluralization reference
  files), as its own separate, verified step immediately before Phase N's actual transfer — not
  bundled into the same change as the transfer itself.
- The provenance manifest (`generated_manifest.json`, ADR-012) moves to `nomad-measurements`
  alongside the generated files it tracks, not left behind in pynxtools — it only makes sense
  relative to the specific files it annotates.

#### Phase 6 — Port `NORMALIZER_MAP` Logic to `normalize()` Methods (**implementation in progress** — identifier resolution and `NexusMeasurement` obsolescence resolved, see [ADR-010](adr/ADR-010-identifier-resolution-and-normalizer-porting.md))

*The old runtime-generated schema's `NORMALIZER_MAP` (`schema_packages/schema.py`) still dispatches hand-written normalizers per NXDL class. None of this has an equivalent on the Phase 1–3 generated classes yet — their `normalize()` stubs just call `super().normalize()`. Distinct from Phase 5 (which restructures basesections *shape*) — this phase ports *behavior* onto the shape that already exists.*

- **`identifierNAME` normalizer — resolved, see [ADR-010](adr/ADR-010-identifier-resolution-and-normalizer-porting.md).** No `AnchoredReference` class was built. Lands on `Object.normalize()`: the first identifier on an `Entity`-typed object sets its own `lab_id`; any further identifier resolves-or-creates a `basesections.EntityReference` via a new `resolve_or_create_entity()` helper.
- **`NexusMeasurement`/`Root`-level normalizer — confirmed obsolete, not ported, see ADR-010.** `NexusParserV2` already populates `sample`/`instrument`/`data` SubSections directly, so the old bucketing walk has no v2 equivalent to port. Each individual responsibility (workflow stamping, `method` label, results.eln.methods) was checked and found already handled elsewhere in v2.
- Smaller per-class normalizers (fabrication/sample/sample_component/entry/process/data naming logic) are lower-risk, mostly 1:1 ports.
- **Gate**: `NORMALIZER_MAP` cannot be removed (Phase 8) until every normalizer it dispatches to has a ported equivalent or a documented reason it's superseded.

#### Phase 7 — Backwards Converter (`metainfo_to_nxdl.py`) (**not started** — file does not exist)

*Reads all six annotation models → emits NXDL XML, so community schema authors can verify no semantic loss before migrating off the old stack. Required before Phase 8 deprecation begins — it is the safety net.*

- Warns on type changes against existing NXDL; never emits removals
- Detects description edits by comparing `description=` against the annotation's `doc=`
- **Gate**: round-trip NXDL → Python → NXDL recovers all structural content

#### Phase 8 — Cleanup (**not started**)

*Remove all legacy runtime generation code, shims, and intermediate compatibility layers. Hard gate: Phase 4, Phase 6 (normalizer porting), and Phase 7 all complete.*

- Remove XML-parsing generation code from `schema.py`
- Remove `NexusBaseSection`, `NexusMeasurement`, `NexusActivityStep`, `NexusActivityResult`
- Remove `_rename_nx_for_nomad` (or keep with `DeprecationWarning` for external users)
- Remove `BASESECTIONS_MAP`, `NORMALIZER_MAP`, `section_definitions` global
- Submodule layout for application definitions (Phase 2b, deferred here as non-breaking reorganisation)

---

### 5-Week Milestone (Project Meeting)

| Week | Focus | Status |
|---|---|---|
| 1 | Phase 0: ADRs 001–005 written; worktree merged; `test_fixes.py` → pytest | ADRs written; generator infrastructure complete |
| 2 | `annotations.py` + `converters/_mapping.py` + generator skeleton | Done |
| 3–4 | Generator working; all 142 base class Python files generated | Done |
| 5 | Entry points configured; package equivalence test | Entry points done; tests pending |

**Phase 1 status (as of 2026-06-02): implementation complete; tests and ADR review pending.**
- [x] `pynx nomad generate-metainfo --nxdl NXentry` produces a valid, importable Python file
- [x] `Entry(Object, basesections.Measurement)` with annotations on all quantities (`NeXusField`, `NeXusAttribute`, `NeXusLink`, `NeXusChoice`)
- [x] `optionality` correctly set from NXDL (required/recommended/optional)
- [x] `links=[url]` on every Section and Quantity pointing to NeXus manual
- [x] ADRs 001–005 written in `data-modeling/nexus-metainfo/adr/`
- [ ] ADRs reviewed and agreed by team
- [ ] Package equivalence tests passing

---

## Architecture & Strategy

### Long-Term Dependency Architecture

When the generated schema moves to `nomad-measurements`, the dependency graph must remain
one-directional:

```
nomad-measurements → pynxtools
```

**Why this is safe:**
- Generated files always import `from pynxtools.nomad.annotations import NeXusDefinition, NeXusGroup, NeXusField, NeXusAttribute, NeXusLink, NeXusChoice`.
  These annotations stay in pynxtools permanently — they follow the parser, not the schema.
- `pynxtools.parser` must NOT import schema classes from `nomad-measurements` at runtime.
  Instead it navigates the archive using NOMAD's reflection API
  (`section.m_def.m_get_annotations("nexus_group")`). The schema is already loaded by the
  time the parser runs (NOMAD's plugin system handles it). No direct import needed.

**Why the converter is permanently in pynxtools (two independent reasons):**

1. It depends on `nexus_tree.py` (`build_base_class_node`, `NexusEntity`, `NexusGroup`,
   `populate_direct_children`). These are core pynxtools internals that cannot move to
   nomad-measurements without reversing the dependency direction.
2. It depends on the NXDL definitions submodule, which lives in pynxtools.

The *output* side is just a path — now configurable via `--output-dir`. nomad-measurements
CI calls `pynx nomad generate-metainfo --all --output-dir <path>` to regenerate after NXDL
updates. No dependency inversion needed, ever.

**What this rules out:**
- Parser importing `from nomad_measurements.nexus.metainfo import Entry` — never do this.
- Moving the converter to nomad-measurements — it needs `nexus_tree.py` and the definitions
  submodule, both of which must stay in pynxtools.
- A separate `nexus-metainfo-tools` package — same issue: it would need pynxtools
  internals, and if nomad-measurements depends on it, you get a loop via pynxtools
  re-exporting the schema.

---

### Architectural Design Tensions

1. **`AnchoredReference` / identifiers — resolved, see [ADR-010](adr/ADR-010-identifier-resolution-and-normalizer-porting.md).**
   No `AnchoredReference` class was built. `identifierNAME` resolution lands on `Object.normalize()`
   plus a new `resolve_or_create_entity()` helper and an `Object.nexus_identifiers` SubSection —
   see ADR-010 for the full mechanism. This also resolves the "stay in pynxtools vs. move to
   nomad-measurements" question: the mechanism lives in `Object.normalize()`, which stays in
   pynxtools permanently per the Long-Term Dependency Architecture. The long-term goal of
   identifiers being instances of their own class (e.g. `Sample`) rather than abstract references
   remains open but is no longer blocked on this decision.

2. **NXdata special handling** — **resolved, not a tension**: the old runtime schema's
   `nxdata_ensure_definition`-style override is unused in the new system. `AXISNAME`/`DATA` are
   handled as ordinary variadic quantities; no special-casing was needed on the generated `Data`
   class. The corresponding dead code remains in the old `schema.py` until Phase 8 removes it.

3. **Application definitions extending base classes** — **resolved via
   [ADR-006](adr/ADR-006-application-definitions-are-entry-subclasses.md)**: not the
   container-wraps-entry pattern shown in earlier drafts of this plan (`ARPES(Measurement,
   Schema)` holding `ENTRY = SubSection(section_def=ARPESEntry)`). The generator instead
   "unwraps" the `NXentry` level directly: `Arpes(Entry)`, using the `NXentry` child's own
   children as the effective children for code generation. See [ADR-006](adr/ADR-006-application-definitions-are-entry-subclasses.md)
   for the full rationale.

4. **Long-term import paths** — still open. Plan the module paths for `nomad-measurements`
   migration now:
   ```python
   # pynxtools: current location
   from pynxtools.nomad.metainfo.base_classes.entry import Entry
   # nomad-measurements: future location
   from nomad_measurements.nexus.base_classes.entry import Entry
   ```

5. **ELN → `eln_data.yaml` → NeXus round-trip is convoluted** — raised during Phase 4, worth a
   real look rather than accepting as a given. Every plugin follows the same shape: archive
   section → flat YAML → NeXus → archive section again. This round-trip exists because the
   dataconverter's `Template`/`Writer` machinery only knows how to consume flat YAML/JSON, not
   NOMAD archive sections directly. A cleaner shape, worth a separate design pass (not blocking
   Phase 4/6): since `NexusParserV2` already navigates the generated Python metainfo directly (no
   flat-dict intermediate), the ELN side could plausibly skip `eln_data.yaml` entirely and
   populate the same generated `Entry`/application-class instance the parser would otherwise
   build — unifying "ELN-authored values" and "parsed-from-file values" as two ways of populating
   the *same* Python object graph. A real simplification opportunity surfaced by Phase 1–3
   already existing, but a separate, follow-on investigation, not a decision made here.

---

### NOMAD Core Asks

Consolidated list of capabilities this project needs from the NOMAD core team. Each should be
framed as a general NOMAD platform improvement, not a NeXus-specific request — the mechanism
must be useful to any schema, not just this one.

0. **Confirm `AnnotationModel.m_registry[...]` at import time is a stable, supported API.** The
   six annotation classes register themselves into this registry at plugin import time (see
   [ADR-001](adr/ADR-001-nexus-annotations.md)); this project depends on that pattern remaining
   supported rather than becoming an internal implementation detail NOMAD core is free to change.

1. **Optionality-driven visibility** (the most significant ask). Optional inherited quantities
   should be hidden by default in ELN, metainfo viewer, and search; required/recommended
   quantities — and any optional quantity actually populated in the uploaded file — stay
   visible. A "Show all defined quantities" GUI toggle (off by default) reveals the full
   taxonomy for power users. Implementation options: a general `visible_by_default: bool` flag
   on `Definition`/`Quantity` consumed by all UI surfaces (set from NXDL `optionality` during
   code generation), or NOMAD core reading `NeXusField.optionality`/`NeXusAttribute.optionality`
   directly. Needs a 1-page spec document (an ADR-002 derivative) before approaching the team.
   See [Visibility Rule](#visibility-rule-option-3b) for full context.

2. **Search index filtering for optional quantities.** Optional quantities populated in a file
   should be indexed; optional quantities with no value should not be. Coordination needed with
   NOMAD core on how search indexing currently handles this.

3. **`HDF5Reference` made more generally usable** (raised during Phase 4's FIELD_STATISTICS
   work — see [Phase 4](#phase-4--migrate-pynxtools--plugins-to-v2-code-complete)).
   Writing a representative mean into an array-shaped quantity is a workaround forced by the
   archive's storage model; the better long-term answer for NXdata's DATA/AXISNAME-derived
   axes/signal fields is `HDF5Reference` (already used by
   `nomad_measurements.xrd.XRDResult1DHDF5`) — these arrays aren't searchable as scalars today
   either, so nothing is lost by moving them there. Two gaps need closing first: (a)
   auto-writing an HDF5 file when an entry is created from the GUI/ELN with no underlying
   `.nxs` file to reference (nomad-measurements' `HDF5Handler` already does this per-plugin —
   ask whether it becomes a first-class `HDF5Reference` capability instead), and (b) searchable
   statistics by default on `HDF5Reference` quantities, which would obsolete hand-generating
   FIELD_STATISTICS per schema entirely. Not blocking — FIELD_STATISTICS as implemented is the
   pragmatic answer until/unless this lands.

**What NOT to ask**: everything else in this plan. Present decisions, not options, for anything
not listed here.

---

### Versioning Strategy

| Version | Content | Breaking changes |
|---|---|---|
| **0.x (current)** | Runtime-generated schema; old `__field` names; `NORMALIZER_MAP` | — |
| **1.0** | Old schema + parser + app unchanged and still the default. New Python-native metainfo available as opt-in entry points (`nexus_base_classes`, `nexus_applications`). `__getattr__` shims provided if easy; otherwise new schema is purely additive alongside the old. | None for existing users |
| **2.0** | New parser is canonical; old `nexus_schema` / `nexus_parser` / `nexus_app` entry points removed; `NexusBaseSection`, `NORMALIZER_MAP`, runtime XML generation removed. | Yes — plugin code using old names / `NORMALIZER_MAP` must migrate |

v1 is the transition window where both worlds coexist. v2 is the clean break.

**pynxtools-* family coordination**: pynxtools-xps, -mpes, -em, -apm, -xas, -xrd, -raman, -spm, -ellips must be informed before v2. A compatibility matrix should be published at the v2 release.

**Specific backward-compatibility promises for the v1 window**:
- `_quantity` suffix: generated Python files use clean names (`start_time`, not
  `start_time__field`). `__getattr__` shims on old `schema.py` classes may ease migration but
  aren't required for v1 — v1 keeps the old stack unchanged and the new schema is purely
  additive.
- Old entry points (`nexus_schema`, `nexus_parser`, `nexus_app`) stay untouched until Phase 3
  (new parser validated) *and* Phase 4 (all plugins migrated). `DeprecationWarning` added in
  Phase 8; removed at v2.0.
- `section.more["nx_*"]` stays populated (as deprecated) until the old parser is removed.
- `from pynxtools.nomad.schema import NexusMeasurement` must still work — re-export shim from
  `schema.py` until 2.0.
- `_rename_nx_for_nomad` stays available with a `DeprecationWarning` if any external code uses it.

**Rollout mechanism is deployment-wide, not per-plugin** — the original framing (imagining a
per-plugin v1/v2 toggle) was wrong. `NexusParserV2`/`nexus_app_v2` are `MatchingParser`/app entry
points that match *any* `.nxs` file system-wide — `is_mainfile()` doesn't filter by which
`pynxtools-*` reader produced the file — so "v2 for mpes only, v1 for everything else" isn't a
real choice; activation is necessarily deployment-wide via the existing `nomad.yaml`
`plugins.entry_points.include` allowlist. What remains genuinely open is a Phase 7/8 question:
when a production NOMAD distribution's *default* config (not this dev override) flips from v1 to
v2 — a deprecation-timing decision, not a Phase 4 blocker.
---

## References

### Relevant Open Issues

| Issue | Title | Phase |
|---|---|---|
| #765 | Schema caching cleanup | Phase 1 (Python import replaces JSON cache) |
| #708 | Split nexus package into smaller packages | Closeable — Phase 1/2 (`nexus_base_classes` + `nexus_applications`); multi-package search confirmed unlimited during Phase 4 |
| #542 | Search quantities in NOMAD | Phase 1 (`nx_optionality` drives indexing) |
| #534 | Unsigned int type mapping | Phase 1 (`NeXusField.type = "NX_UINT"`) |
| #702 | Parsing/normalization improvements | Parser rewrite: Phase 3 (complete); normalization improvements: Phase 6 |
| #551 | NXapm normalizer | Phase 6 (move to pynxtools-apm) |
| #737 | Memory for large datasets | Phase 4 (FIELD_STATISTICS, annotation-based type info for smarter stats) |
| #725 | Materials card not instantiated | Phase 6 (normalization via `normalize()` methods) |

---

### Verification

```bash
# Prerequisite baseline:
python -m pytest tests/nexus/ tests/dataconverter/ tests/eln_mapper/ tests/nomad/ -q

# Phase 1: package equivalence
python -m pytest tests/nomad/test_metainfo_equivalence.py -v
pynx nomad generate-metainfo --all --dry-run  # CI check

# Phase 3: parser v2 golden-output + parity (complete)
python -m pytest tests/nomad/test_parsing_v2.py -v

# Phase 7: round-trip (not started)
pynx nomad export-nxdl --all --check-only  # NXDL recovered from Python annotations

# Phase N: ELN visibility (not started)
# Parse NXxrd .nxs file via XRayDiffraction; verify only recommended/required
# quantities visible in ELN by default
```

---

### Open Questions (for ADR process)

- Attribute naming: `{field}__units` vs. storing units directly on the Quantity's `unit` parameter? — resolved in practice: units go on the Quantity's `unit` parameter (`a_nexus_field=NeXusField(units="NX_VOLTAGE")` records the NXDL unit *category*, separately from the resolved pint `unit=` on the Quantity itself).
- `AnchoredReference`/`identifierNAME`: stay in pynxtools or migrate to nomad-measurements? — tracked under [Architectural Design Tensions](#architectural-design-tensions) item 1, to be resolved as part of Phase 6.
- Backward compat period for `__field` suffix: already resolved by the Versioning Strategy above — no shim; v1 keeps the old stack unchanged and v2 is the clean break for plugin code using old names.
- **`_quantity` suffix rule for reserved `BaseSection` names** (`name`/`datetime`/`lab_id`/`description` → `name_quantity`/etc.) may not be necessary — NOMAD allows redefining an inherited quantity in a subclass (adding NXDL-specific annotations/`description=`) without renaming, as long as the type stays compatible (all four reserved names match their NXDL counterparts' types exactly). One thing to verify first: `BaseSection.normalize()`'s `entry_name`-from-`self.name` side effect only fires for the entry's top-level section, not nested SubSections — confirm before assuming the collapse is safe everywhere. **Not fixing now**: Phase 5's basesections-alignment work will anyway reconcile NeXus concepts with NOMAD's base sections, so this is deferred there rather than patched as a one-off generator tweak.