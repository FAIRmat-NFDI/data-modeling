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
    - [Phase 0](#phase-0--architecture-alignment-weeks-1-no-code) · [Phase 1](#phase-1--infrastructure--base-class-generation-complete) · [Phase 2](#phase-2--application--contributed-definitions-complete) · [Phase 2.5](#phase-25--eln-annotations-on-generated-schema-complete-added-after-this-plan-was-first-written) · [Phase 3](#phase-3--new-parser--new-app-v2-complete--superseded-the-original-bridge-schemapy-plan-below) · [Phase 4](#phase-4--migrate-pynxtools--plugins-to-v2-not-started--active-focus) · [Phase 5](#phase-5--port-normalizer_map-logic-to-normalize-methods-not-started--newly-identified) · [Phase 6](#phase-6--backwards-converter-metainfo_to_nxdlpy-not-started--file-does-not-exist) · [Phase 7](#phase-7--cleanup-not-started) · [Phase N](#phase-n--nomad-measurements-alignment-early-draft-deprioritized-while-phase-4-is-the-active-focus)
  - [5-Week Milestone](#5-week-milestone-project-meeting)
- [Architecture & Strategy](#architecture--strategy)
  - [Long-Term Dependency Architecture](#long-term-dependency-architecture)
  - [Design Tensions](#architectural-design-tensions)
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
future, non-breaking reorganisation (Phase 2b, deferred to Phase 7):

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

Groups always win the unqualified name. `_quantity` suffix applied for:
1. **Reserved NOMAD names** (`name`, `datetime`, `lab_id`, `description`) → `name_quantity`, etc.
2. **Field-vs-group collision** — when a NXDL field and group in the same class (or ancestor chain) share a Python name (e.g. `NXsample` field `sample_component` vs. `NXsample_component` group). Field renamed to `sample_component_quantity`; SubSection keeps `sample_component`.

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

**Implementation**: requires a general NOMAD core mechanism — not ELN-specific. Options:
- General `visible_by_default: bool` flag on `Definition` / `Quantity` consumed by all UI
  surfaces, set from `nx_optionality` during code generation
- Or: NOMAD core reads `NeXusField.optionality` / `NeXusAttribute.optionality` annotation directly

This is the most significant NOMAD core ask. A 1-page spec document (ADR-002 derivative)
is required before approaching the NOMAD team. The mechanism must be general enough for
non-NeXus use cases — framed as "optionality-driven visibility" not "NeXus visibility".

**Search indexing**: optional quantities that are populated in a file are indexed. Optional
quantities with no value in the file are not indexed. Coordination with NOMAD core needed.

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
        metainfo_to_nxdl.py          # Phase 6: Python + annotations → NXDL XML (round-trip) — not started
        cli.py                       # pynx nomad generate-metainfo
        templates/
            base_class.py.j2         # Jinja2 template (universal; category-aware header)
    metainfo/
        __init__.py                  # public API: build_base_classes_package(), build_applications_package()
        _package.py                  # assembles NOMAD Package
        base_classes/                # 142 .py files (category="base")
            entry.py                # Entry(Object, basesections.Measurement, EntryData)
            sample.py                # Sample(Component, basesections.CompositeSystem)
            root.py                  # Root(Object, basesections.Experiment, EntryData)
            ...
        applications/                # 85 flat .py files (category="application", Phase 2)
            arpes.py                 # Arpes(Entry)
            xps.py                   # Xps(Entry)
            ...                      # submodule-per-app layout is Phase 2b, deferred to Phase 7
    schema_packages/
        schema.py                    # OLD, v1 — untouched; becomes an ~80-line shim only in Phase 7
        dataconverter.py             # OLD, v1 — ELN→eln_data.yaml→NeXus flow; still imports v1 NexusParser (Phase 4 touch point)
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
in Phase 7, once Phase 4 (plugin migration) and Phase 5 (normalizer porting) are both done.

---

### Base Section Mapping

Defined in `converters/_mapping.py:BASESECTIONS_MAP`. **Transitional** — long-term, the
mapping should be declared on the NXDL classes directly, not a hardcoded dict.

| NXDL class | Generated Python class inherits from |
|---|---|
| `NXobject` | `Object` (→ `BaseSection`) |
| `NXentry` | `Object, basesections.Measurement` |
| `NXprocess` | `Object, basesections.ActivityStep` |
| `NXsample` | `Component, basesections.CompositeSystem` |
| `NXsample_component` | `Component, basesections.Component` |
| `NXfabrication` | `Object, basesections.Instrument` |
| `NXdata` | `Object, basesections.ActivityResult` |
| Application defs (`category="application"`) | `Entry` (NXentry wrapper unwrapped — [ADR-006](adr/ADR-006-application-definitions-are-entry-subclasses.md), *not* a separate `Measurement, Schema, PlotSection` mixin) |
| All others | `Object` |

`NXentry → Object, Measurement`: each NXentry becomes one NOMAD entry (1:1 mapping, plus one
`Root(Experiment)` grouping entry per file — [ADR-007](adr/ADR-007-nxroot-handling.md)).
`Measurement` is the right base — it provides `instruments`/`samples`/`steps` subsections
(see [Phase N](#phase-n--nomad-measurements-alignment-early-draft-deprioritized-while-phase-4-is-the-active-focus)
for a proposed rename to `instrument`/`sample`/`data`, not yet decided) and is what
nomad-measurements classes (`XRayDiffraction`, …) already inherit from on basesections v1.

`normalize()` lives as a method directly on each generated class — that part of the design is
final. **Not yet true today**: the generator currently only emits a `super().normalize()` stub;
porting the old `NORMALIZER_MAP`'s hand-written normalizers onto these stubs is its own phase
([Phase 5](#phase-5--port-normalizer_map-logic-to-normalize-methods-not-started--newly-identified)),
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
- `normalize()` stub calling `super().normalize(archive, logger)` — developers fill it in; porting the *old* `NORMALIZER_MAP` logic onto these stubs is Phase 5, not yet started

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

#### Phase 4 — Migrate pynxtools-* Plugins to v2 (**not started — active focus**)

*Application-definition classes (e.g. `Xps(Entry)`) are generated centrally in pynxtools, not owned per plugin — a plugin's `pynxtools.reader` entry point only produces a `.nxs` file; parsing it is owned entirely by the single, shared `nexus_parser_v2` entry point. So "switch schema base"/"replace `NORMALIZER_MAP` callbacks" are not per-plugin tasks under the architecture actually built — flipping the active parser/app is a one-time pynxtools-core decision, not per-plugin code.*

**What is real, per-plugin work** (confirmed by survey across all 10 `pynxtools-*` packages):
- **NOMAD apps**: only 3 of 10 plugins have a real, shipped app (`pynxtools-mpes`, `pynxtools-raman`, `pynxtools-spm`); two more have one disabled (`pynxtools-em`/`pynxtools-apm`, `# em_app =`/`# apm_app =` commented out) — worth re-enabling if low-effort once the pattern is established. `apps/app_v2.py` (`nexus_app_v2`) is the reference pattern: same `App`/`Column`/`Menu` DSL, just v2's clean paths (no `__field`, no `ENTRY[*]` wrapping) — migrating the three real apps is a mechanical per-string rewrite, not a new framework.
- `mpes_app` also references FIELD_STATISTICS-derived columns (`energy__min`/`energy__max`/`data__size`) that don't exist in the v2 schema yet — **complete FIELD_STATISTICS first** (carried over from Phase 3), scoped to numeric array quantities inside `Data`-derived classes only (`node.nx_class == "NXdata"` at generation time), not generically.
- **Example uploads**: lower risk than apps — they mostly glob raw example files, not pre-baked archive JSON. Risk is any bundled ELN/template `.archive.yaml` files referencing old paths. **No existing harness tests the true end-to-end path** (raw file → `.nxs` → `nexus_parser_v2` → archive) without running real NOMAD infrastructure; the existing helper (`pynxtools.testing.nomad_example.parse_nomad_examples`) only validates bundled ELN schema/archive files via NOMAD's generic `ArchiveParser`, not actual NeXus parsing.
- **Docs**: backlog, not migration — no plugin has dedicated NOMAD/NeXus data-model docs yet. Write after the app migrations land.
- The shared ELN→NeXus conversion path (`nomad/schema_packages/dataconverter.py`) still hardcodes `from pynxtools.nomad.parsers.parser import NexusParser` (v1) — needs switching to `NexusParserV2` as part of this phase.
- **Gate**: each migrated app/plugin's own test suite passes on the v2 stack.
- **Coordination**: publish a compatibility matrix (which pynxtools-* version requires which pynxtools) as part of the v1 release announcement.

#### Phase 5 — Port `NORMALIZER_MAP` Logic to `normalize()` Methods (**not started** — newly identified)

*The old runtime-generated schema's `NORMALIZER_MAP` (`schema_packages/schema.py`) still dispatches hand-written normalizers per NXDL class. None of this has an equivalent on the Phase 1–3 generated classes yet — their `normalize()` stubs just call `super().normalize()`. Distinct from Phase N (which restructures basesections *shape*) — this phase ports *behavior* onto the shape that already exists.*

- The `identifierNAME` normalizer (`NexusIdentifiers.normalize()`): turns NeXus's loose `identifierNAME` convention into a real, searchable NOMAD entity reference (`AnchoredReference`). Needs v2 naming (no `__field` suffix, variadic via `MQuantity`) and likely belongs on the universal `Object` base, not scattered per-class.
- The old `NexusMeasurement`/`Root`-level normalizer: walked `m_all_contents()` to bucket sections by base type because v1 had no properly-typed `sample`/`instrument`/`data` SubSections to populate directly. **Likely obsolete, not just renameable** — `NexusParserV2` already populates those SubSections directly. What may still be needed: the `method` label and `archive.workflow2` stamping — requires real investigation during the phase, not a decision made in advance.
- Smaller per-class normalizers (fabrication/sample/sample_component/entry/process/data naming logic) are lower-risk, mostly 1:1 ports.
- **Gate**: `NORMALIZER_MAP` cannot be removed (Phase 7) until every normalizer it dispatches to has a ported equivalent or a documented reason it's superseded.

#### Phase 6 — Backwards Converter (`metainfo_to_nxdl.py`) (**not started** — file does not exist)

*Reads all six annotation models → emits NXDL XML, so community schema authors can verify no semantic loss before migrating off the old stack. Required before Phase 7 deprecation begins — it is the safety net.*

- Warns on type changes against existing NXDL; never emits removals
- Detects description edits by comparing `description=` against the annotation's `doc=`
- **Gate**: round-trip NXDL → Python → NXDL recovers all structural content

#### Phase 7 — Cleanup (**not started**)

*Remove all legacy runtime generation code, shims, and intermediate compatibility layers. Hard gate: Phase 4, Phase 5 (normalizer porting), and Phase 6 all complete.*

- Remove XML-parsing generation code from `schema.py`
- Remove `NexusBaseSection`, `NexusMeasurement`, `NexusActivityStep`, `NexusActivityResult`
- Remove `_rename_nx_for_nomad` (or keep with `DeprecationWarning` for external users)
- Remove `BASESECTIONS_MAP`, `NORMALIZER_MAP`, `section_definitions` global
- Submodule layout for application definitions (Phase 2b, deferred here as non-breaking reorganisation)

#### Phase N — nomad-measurements Alignment (**early draft, deprioritized while Phase 4 is the active focus**)

*`nomad-measurements` inherits from the generated NeXus base classes, becoming the authoritative FAIRmat measurement schema layer. The design below is a first pass, not yet reviewed by the team — see the internal plan for the full findings/decisions/migration breakdown and the ADR-009 draft.*

- `nomad-measurements` sections inherit from generated Python NeXus classes
- XRD as pilot (already has `NEXUS_DATASET_MAP`): `class XRayDiffraction(XRD):`
- Requires a nomad-measurements-specific mapping-table/backward-compat ADR (not yet written — not numbered until it is, per this project's "name ADRs as they're written" convention) and ADR-009 (basesections alignment, drafted in the internal plan, not yet written here)
- Requires Phase 1 base classes and Phase 2 application definitions to be available
- `nomad-measurements` becomes the authoritative FAIRmat measurement schema layer

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

1. **`AnchoredReference` / identifiers** — open, now has a concrete home: `identifierNAME` →
   entity-reference logic is NeXus-specific; porting the old `identifierNAME` normalizer
   (`NexusIdentifiers.normalize()`) onto the generated v2 classes is in-scope for
   [Phase 5](#phase-5--port-normalizer_map-logic-to-normalize-methods-not-started--newly-identified).
   The "stay in pynxtools vs. move to nomad-measurements" question, and the long-term goal of
   identifiers being instances of their class (e.g. `Sample`) rather than abstract references,
   should be resolved there rather than left open indefinitely.

2. **NXdata special handling** — **resolved, not a tension**: the old runtime schema's
   `nxdata_ensure_definition`-style override is unused in the new system. `AXISNAME`/`DATA` are
   handled as ordinary variadic quantities; no special-casing was needed on the generated `Data`
   class. The corresponding dead code remains in the old `schema.py` until Phase 7 removes it.

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
---

### Versioning Strategy

| Version | Content | Breaking changes |
|---|---|---|
| **0.x (current)** | Runtime-generated schema; old `__field` names; `NORMALIZER_MAP` | — |
| **1.0** | Old schema + parser + app unchanged and still the default. New Python-native metainfo available as opt-in entry points (`nexus_base_classes`, `nexus_applications`). `__getattr__` shims provided if easy; otherwise new schema is purely additive alongside the old. | None for existing users |
| **2.0** | New parser is canonical; old `nexus_schema` / `nexus_parser` / `nexus_app` entry points removed; `NexusBaseSection`, `NORMALIZER_MAP`, runtime XML generation removed. | Yes — plugin code using old names / `NORMALIZER_MAP` must migrate |

v1 is the transition window where both worlds coexist. v2 is the clean break.

**pynxtools-* family coordination**: pynxtools-xps, -mpes, -em, -apm, -xas, -xrd, -raman, -spm, -ellips must be informed before v2. A compatibility matrix should be published at the v2 release.
---

## References

### Relevant Open Issues

| Issue | Title | Phase |
|---|---|---|
| #765 | Schema caching cleanup | Phase 1 (Python import replaces JSON cache) |
| #708 | Split nexus package into smaller packages | Phase 1 (entry point splitting) |
| #542 | Search quantities in NOMAD | Phase 1 (`nx_optionality` drives indexing) |
| #534 | Unsigned int type mapping | Phase 1 (`NeXusField.type = "NX_UINT"`) |
| #702 | Parsing/normalization improvements | Parser rewrite: Phase 3 (complete); normalization improvements: Phase 5 |
| #551 | NXapm normalizer | Phase 5 (move to pynxtools-apm) |
| #737 | Memory for large datasets | Phase 4 (FIELD_STATISTICS, annotation-based type info for smarter stats) |
| #725 | Materials card not instantiated | Phase 5 (normalization via `normalize()` methods) |

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

# Phase 6: round-trip (not started)
pynx nomad export-nxdl --all --check-only  # NXDL recovered from Python annotations

# Phase N: ELN visibility (not started)
# Parse NXxrd .nxs file via XRayDiffraction; verify only recommended/required
# quantities visible in ELN by default
```

---

### Open Questions (for ADR process)

- Attribute naming: `{field}__units` vs. storing units directly on the Quantity's `unit` parameter? — resolved in practice: units go on the Quantity's `unit` parameter (`a_nexus_field=NeXusField(units="NX_VOLTAGE")` records the NXDL unit *category*, separately from the resolved pint `unit=` on the Quantity itself).
- `AnchoredReference`/`identifierNAME`: stay in pynxtools or migrate to nomad-measurements? — tracked under [Architectural Design Tensions](#architectural-design-tensions) item 1, to be resolved as part of Phase 5.
- Backward compat period for `__field` suffix: already resolved by the Versioning Strategy above — no shim; v1 keeps the old stack unchanged and v2 is the clean break for plugin code using old names.