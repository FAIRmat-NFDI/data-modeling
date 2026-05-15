# NeXus–NOMAD Metainfo Refactor: Work Plan

## Problem

The NeXus integration in NOMAD is perceived as fundamentally different from other plugins.
Root causes:
- Runtime NXDL → Metainfo generation produces no reusable Python definitions
- Intermediate wrapper classes (`NexusBaseSection`, `NexusMeasurement`) diverge from NOMAD idioms
- Normalizers injected via `NORMALIZER_MAP` instead of class methods — not overridable
- Naming leaks into user-facing code (`start_time__field`, `ENTRY___default`)
- Large monolithic schema package slows appworker startup
- No UI filtering of optional inherited quantities — users see full NeXus taxonomy

## Goal

Create one authoritative FAIRmat characterization/measurement layer:
- NeXus sections defined as **Python Metainfo classes** — importable, type-checkable, extensible
- Directly inherit from NOMAD base sections — no intermediary wrappers
- Quantities named after their NXDL concept (`start_time`, not `start_time__field`)
- Full schema with optionality annotations; UI filters by `nx_optionality` (required/recommended shown by default, optional hidden)
- Schema loads fast via entry point splitting — domain plugins load only what they need
- Designed to eventually live in `nomad-measurements`

## Target Architecture

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

Long-term: only the schema package (`metainfo/`) moves to `nomad-measurements`. The NeXus
parser, search app, and examples stay in pynxtools — NOMAD must always parse `.nxs` files.

## NeXus File to NOMAD Entry Mapping

**One NOMAD entry per NXentry** (first iteration). The NeXus file is not mapped to an
outer experiment section — each NXentry becomes one independent NOMAD entry directly.
Multi-entry files produce one NOMAD entry per NXentry; the mapping is 1:1.

Future: if a file-level experiment wrapper is needed, it can be added as an outer section
in a later phase without breaking the 1:1 base.

---

## Naming Conventions

### Section (class) names
Remove `NX` prefix, then convert to CamelCase. Abbreviations stay uppercase via a lookup table:

```python
ABBREVIATIONS = {"xrd","xps","arpes","mpes","em","apm","xas","afm","stm","sem","tem","spm","ipf"}

def nxdl_to_class_name(nx_name: str) -> str:
    stem = nx_name[2:] if nx_name.startswith("NX") else nx_name
    parts = stem.split("_")
    return "".join(p.upper() if p.lower() in ABBREVIATIONS else p.capitalize()
                   for p in parts if p)
# NXxrd → XRD, NXarpes → ARPES, NXoptical_spectroscopy → OpticalSpectroscopy
# NXsample → Sample, NXentry → Entry, NXinstrument → Instrument
# NXmicrostructure_ipf → MicrostructureIPF
```

### Naming for nested specialisations (application definitions)

Application definitions use a **submodule file layout** with short Python class names.
NOMAD schema name uniqueness (required within a `Package`) is enforced via an explicit
`m_def = Section(name="...")` — the generator derives it from the module path:

```
applications/arpes/
    __init__.py    # class ARPES(Measurement, Schema)
    entry.py       # class Entry(base_entry.Entry): m_def = Section(name="ARPESEntry")
    instrument.py  # class Instrument(...):         m_def = Section(name="ARPESInstrument")
```

Plugin developers use the short name: `from ...applications.arpes.entry import Entry`.

### Quantity (field) names
- NXDL fields: use the NXDL name directly — `start_time`, `energy`, `title`
- Attributes on groups: `{attr_name}` or `{attr_name}_attr` (context-dependent — TBD in ADR-001)
- Attributes on fields: `{field_name}__{attr_name}` — e.g., `energy__units`
- Variadic (nameType=any/partial): `variable=True` on SubSection/Quantity

### Connection from Python class to NXDL

The connection is carried by the `NeXusGroup` annotation on `Section.m_def`, not by
class-level string attributes:

```python
class XRD(Measurement):
    m_def = Section(
        a_nexus_group=NeXusGroup(
            nx_class="NXxrd",
            category="application",
            optionality="required",
        ),
    )
```

---

## Annotation Models

Two annotation classes replace the hidden `section.more["nx_*"]` protocol.

Field names use bare names — the annotation namespace is provided by the registry key
(`nexus_group`, `nexus_quantity`), not by field name prefixes. `nx_class` is the one
exception because it is the NeXus concept identifier.

```python
class NeXusGroup(AnnotationModel):
    """Attached to Section.m_def and SubSection definitions for groups."""
    nx_class: str                    # "NXinstrument"
    name: str | None = None          # fixed name if specified; None = variadic
    name_type: Literal["specified","any","partial"] = "specified"
    category: Literal["base","application","contributed"] = "base"
    optionality: Literal["required","recommended","optional"] = "optional"
    restricts: bool = False
    ignore_extra_groups: bool = False
    ignore_extra_fields: bool = False
    ignore_extra_attributes: bool = False
    symbols: dict[str, str] | None = None
    min_occurs: int | None = None
    max_occurs: int | None = None
    deprecated: str | None = None

class NeXusQuantity(AnnotationModel):
    """Attached to Quantity definitions for fields and attributes."""
    kind: Literal["field","attribute"]
    name: str                        # original NXDL name
    parent_field: str | None = None  # for field-level attributes: owning field name
    type: str = "NX_CHAR"            # NX type category: "NX_FLOAT", "NX_CHAR", …
    units: str | None = None         # NX unit category: "NX_ENERGY", "NX_LENGTH"
    name_type: Literal["specified","any","partial"] = "specified"
    optionality: Literal["required","recommended","optional"] = "optional"
    enumeration: list[str] | None = None
    open_enum: bool = False
    interpretation: str | None = None
    long_name: str | None = None
    deprecated: str | None = None
```

Registered at plugin load time — no NOMAD core PR needed:
```python
# annotations.py
AnnotationModel.m_registry["nexus_group"] = NeXusGroup
AnnotationModel.m_registry["nexus_quantity"] = NeXusQuantity
```

---

## Visibility Rule (Option 3B)

The schema remains complete and NeXus-compliant. Filtering is a presentation concern only.

**Rule**: optional inherited quantities are hidden by default in ELN, metainfo viewer, and
search. Required and recommended quantities — and any optional quantity that is populated
in the uploaded file — are always visible.

**GUI toggle**: "Show all defined quantities" toggle (off by default) reveals the full
NeXus taxonomy for power users.

**Implementation**: requires a general NOMAD core mechanism — not ELN-specific. Options:
- General `visible_by_default: bool` flag on `Definition` / `Quantity` consumed by all UI
  surfaces, set from `nx_optionality` during code generation
- Or: NOMAD core reads `NeXusQuantity.nx_optionality` annotation directly

This is the most significant NOMAD core ask. A 1-page spec document (ADR-002 derivative)
is required before approaching the NOMAD team. The mechanism must be general enough for
non-NeXus use cases — framed as "optionality-driven visibility" not "NeXus visibility".

**Search indexing**: optional quantities that are populated in a file are indexed. Optional
quantities with no value in the file are not indexed. Coordination with NOMAD core needed.

---

## New File Layout

```
src/pynxtools/nomad/
    annotations.py                   # NeXusGroup + NeXusQuantity
    metainfo/
        __init__.py                  # public API: all_sections(), build_package()
        _package.py                  # assembles Package; resolves forward refs
        base_classes/                # ~156 .py files
            __init__.py
            entry.py               # Entry(Measurement)
            instrument.py          # Instrument(basesections.Instrument)
            sample.py              # Sample(CompositeSystem)
            data.py                # Data(ActivityResult)
            object.py              # Object(BaseSection)
            source.py
            detector.py
            ...
        applications/                # ~50 submodules
            __init__.py
            arpes/                 # submodule per application definition
                __init__.py        # ARPES(Measurement, Schema)
                entry.py           # Entry(base_entry.Entry): m_def Section(name="ARPESEntry")
                instrument.py      # ...
            xps/
                __init__.py        # XPS(Measurement, Schema)
                entry.py
                ...
        contributed/                 # ~96 .py files
            __init__.py
            ...
    converters/
        __init__.py
        _naming.py                   # nxdl_to_class_name, topological sort
        nxdl_to_metainfo.py          # NXDL → Python generator (additive-only)
        metainfo_to_nxdl.py          # Python + annotations → NXDL XML (round-trip)
    schema.py                        # thin shim (~80 lines) for parser compatibility
    parser.py                        # rewritten: annotation-based navigation
```

---

## Base Section Mapping

Direct Python inheritance replaces `BASESECTIONS_MAP`:

| NXDL class | Python class inherits from |
|---|---|
| `NXobject` | `BaseSection` |
| `NXentry` | `Measurement` |
| `NXprocess` | `ActivityStep` |
| `NXsample` | `CompositeSystem` |
| `NXsample_component` | `Component` |
| `NXfabrication` | `basesections.Instrument` |
| `NXdata` | `ActivityResult` |
| Application defs (extends NXobject) | `Measurement, Schema, PlotSection` |
| Everything else | `BaseSection` |

`NXentry → Measurement`: each NXentry becomes one NOMAD entry (1:1 mapping). `Measurement`
is the right base — it provides `instruments`, `samples`, `steps` subsections and is what
nomad-measurements classes (`XRayDiffraction`, `MpesData`, …) already inherit from.

`normalize()` lives as a method directly on each generated class. No `NORMALIZER_MAP`. No
`NexusBaseSection` wrapper. The generator emits a stub on first generation; developers
fill it in. Subsequent regenerations (for NXDL updates) use the additive-only constraint
— `ast.parse()` detects existing methods and never overwrites them, only appends new
quantities.

---

## Performance: Entry Point Splitting

Replace the monolithic schema package with multiple entry points:

```toml
[project.entry-points."nomad.plugin"]
nexus_base_classes   = "pynxtools.nomad.metainfo.base_classes:NexusBaseClassesEntryPoint"
nexus_applications   = "pynxtools.nomad.metainfo.applications:NexusApplicationsEntryPoint"
nexus_contributed    = "pynxtools.nomad.metainfo.contributed:NexusContributedEntryPoint"
```

Domain plugins (e.g., `pynxtools-mpes`) import only what they need:

```python
# pynxtools_mpes/schema.py
from pynxtools.nomad.metainfo.base_classes.entry import Entry
from pynxtools.nomad.metainfo.base_classes.instrument import Instrument
from pynxtools.nomad.metainfo.applications.mpes import MPES
```

Each entry point loads independently; Python's import caching handles deduplication.
No runtime lazy loading state machine needed.

---

## Code Generator: NXDL → Python (`nxdl_to_metainfo.py`)

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
- One Python class (or submodule for application defs) inheriting from the base section
- `m_def = Section(name="...")` for application-def nested classes (package-unique name)
- All quantities from the full NXDL inheritance chain with correct `nx_optionality`
- SubSections for all group members using `SectionProxy("full.module.path.ClassName")`
  (resolved at SchemaPackage init time in `_package.py`)
- `nx_optionality` set on all quantities; drives UI visibility once NOMAD core mechanism is agreed
- All `NeXusGroup` / `NeXusQuantity` annotations populated from `NexusNode` metadata
- `normalize()` stub calling `super().normalize(archive, logger)` — developers fill it in

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
pynx nomad generate-metainfo [--nx-class NXdetector] [--all] [--dry-run] [--force]
pynx nomad export-nxdl [--nx-class NXxps] [--all] [--check-only]
```

---

## Round-Trip: Python → NXDL (`metainfo_to_nxdl.py`)

Reads `NeXusGroup` + `NeXusQuantity` annotations → emits NXDL XML.
- Warns (does not error) on type changes against existing NXDL
- Never emits removals — human must handle deprecations manually

Required by the constraint: Python authoring must be a strict superset of NXDL semantics.

---

## Parser Migration (`parser.py`)

New annotation-based navigation instead of `section.more["nx_*"]` and name suffixes.

**Core algorithm**:
1. Walk HDF5 tree
2. For each HDF5 group: find matching Python section class by `NeXusGroup.nx_class`
   matching the HDF5 `NX_class` attribute
3. For each HDF5 field/attribute: find matching Quantity by `NeXusQuantity.nx_name`
4. Populate quantities directly — no `__field` lookup, no `___` attribute names
5. Fields not in schema: fall through to NOMAD's custom quantity mechanism

---

## `schema.py` End State (~80 lines)

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

## Phases

### Phase 0 — Architecture Alignment (weeks 1, no code)
Deliverables: ADRs, not implementation.

Required ADRs:
- **ADR-001**: `NeXusGroup` + `NeXusQuantity` field names and types
- **ADR-002**: `nx_optionality` semantics — how optionality is set from NXDL context
- **ADR-003**: Canonical NeXus ↔ NOMAD base section mapping (full table)
- **ADR-004**: Code generator specification (input: NexusNode; output: Python; additive-only)
- **ADR-005**: Entry point splitting strategy and domain plugin interface

Semantic mapping document: full table of NeXus base classes → NOMAD base sections (covers
all ~156 base classes, not just the current BASESECTIONS_MAP partial list).

Schema contribution pathway document:
```
custom plugin → nomad-measurements standard section → NeXus application definition (NIAC)
```

### Phase 1 — Infrastructure + Base Class Generation (weeks 2–5, largely complete)
- [x] `annotations.py` with `NeXusGroup` + `NeXusQuantity` (bare field names; registered with NOMAD annotation system)
- [x] `converters/_naming.py` with `nxdl_to_class_name`, `BASESECTIONS_MAP`, topological sort, `nx_type_to_source`
- [x] `converters/nxdl_to_metainfo.py` — generator using `build_base_class_node()` from `NexusNode` API; zero raw XML access
- [x] `metainfo/base_classes/*.py` — 142 generated Python files
- [x] `metainfo/_package.py` — assembles NOMAD `Package`; graceful degradation for cross-category refs
- [x] `nexus_tree.py` additions: `build_base_class_node()`, `populate_direct_children()`, typed attrs (`deprecated`, `category`, `restricts`, `ignore_extra_*`, `symbols`, `interpretation`, `long_name`)
- [ ] Entry points in `pyproject.toml` for base classes
- [ ] **Tests**: package equivalence (same section names, quantity types as current schema for base classes)

Note: `nexus-inheritance-concept-paths` merge is **not** a prerequisite for Phase 1. The
generator uses `build_base_class_node()` added to `dataconverter/nexus_tree.py` on master.
The new symbols will be re-exported from the shim in that branch when it merges.

### Phase 2 — Application + Contributed Definitions (post week 5)
- `metainfo/applications/*.py` — ~50 files
- `metainfo/contributed/*.py` — ~96 files
- Application definitions specialize base class groups with AD-specific optionality
- **Round-trip tests**: NXDL → Python → NXDL recovers field names, types, hierarchy

### Phase 3 — Bridge `schema.py`
- `create_metainfo_package()` → `metainfo._package.build_package()`
- `schema.py` becomes ~80-line shim
- Old XML-parsing code present but unreachable (behind `USE_LEGACY` flag)
- **Gate**: parser test suite passes; identical archive output for reference `.nxs` files

### Phase 4 — Parser Migration
- Rewrite `parser.py` to use `NeXusGroup.nx_class` / `NeXusQuantity.nx_name` for navigation
- Drop `section.more["nx_*"]` dependencies
- Drop `__field` / `___` name construction
- `HandleNexus` / `NomadParser` HDF5 walker unchanged
- **Tests**: parse reference `.nxs` files; `archive.m_to_dict()` matches golden outputs

### Phase 5 — Cleanup
- Remove XML-parsing generation code from `schema.py`
- Remove `NexusBaseSection`, `NexusMeasurement`, `NexusActivityStep`, `NexusActivityResult`
- Remove `_rename_nx_for_nomad` (or keep with `DeprecationWarning` for external users)
- Remove `BASESECTIONS_MAP`, `NORMALIZER_MAP`, `section_definitions` global
- `metainfo_to_nxdl.py` round-trip exporter (may start earlier alongside Phase 2)

### Phase N — nomad-measurements Alignment (parallel to Phases 2–5)
- `nomad-measurements` sections inherit from generated Python NeXus classes
- XRD as pilot (already has `NEXUS_DATASET_MAP`): `class XRayDiffraction(XRD):`
- Requires ADRs 006 (mapping table) and 007 (backward compat)
- Requires Phase 1 base classes and Phase 2 application definitions to be available
- `nomad-measurements` becomes the authoritative FAIRmat measurement schema layer

---

## 5-Week Milestone (Project Meeting)

| Week | Focus |
|---|---|
| 1 | Phase 0: ADRs 001–005 written; worktree merged; `test_fixes.py` → pytest |
| 2 | `annotations.py` + `converters/_naming.py` + generator skeleton |
| 3–4 | Generator working; first 20–30 base class Python files generated |
| 5 | Entry points configured; package equivalence test passing for generated base classes |

**Demonstrable at week-5 meeting:**
- `pynx nomad generate-metainfo --nx-class NXentry` produces a valid, importable Python file
- `Entry(Measurement)` with `NeXusGroup` + `NeXusQuantity` annotations on all quantities
- `optionality` correctly set from NXDL (required/recommended/optional)
- ADRs 001–005 reviewed and agreed
- Semantic mapping document complete

---

## Architectural Design Tensions (to resolve before/during implementation)

1. **`AnchoredReference` / identifiers**: `identifierNAME` → `EntityReference` logic is
   NeXus-specific. Decision needed: does it stay in pynxtools or move to nomad-measurements?
   Long-term, identifiers should be instances of their class (e.g., `Sample`) not abstract
   references — plan for this in Phase N.

2. **NXdata special handling**: `_ensure_definition` override for variadic DATA/AXISNAME
   matching must become a proper method on the generated `Data` class.

3. **Application definitions extending base classes**: `NXarpes` extends `NXobject` with
   added groups. In Python, `ARPES(Measurement, Schema)` needs `ENTRY = SubSection(
   section_def=ARPESEntry)` where `ARPESEntry(Entry)` adds app-specific groups. Generator
   must handle nested specialization.

4. **Long-term import paths**: Plan the module paths for `nomad-measurements` migration now:
   ```python
   # pynxtools: current location
   from pynxtools.nomad.metainfo.base_classes.entry import Entry
   # nomad-measurements: future location
   from nomad_measurements.nexus.base_classes.entry import Entry
   ```
   Provide re-export shim in pynxtools for backward compat.

---

## Versioning Strategy

| Version | Content | Breaking changes |
|---|---|---|
| **0.x (current)** | Runtime-generated schema; `__field` names; `NORMALIZER_MAP` | — |
| **1.0** | Phases 0–3: Python-native `metainfo/` files; `NeXusGroup`/`NeXusQuantity` annotations; entry point splitting; `schema.py` thin shim. All `__field`-based code still works via backward-compat `__getattr__` shim. | None (additive only) |
| **2.0** | Phases 4–5: parser rewritten; `__field`/`___` suffixes removed; `NexusBaseSection`, `NORMALIZER_MAP` removed | Yes — plugin code using `__field`, `section.more["nx_*"]`, or `NORMALIZER_MAP` must migrate |

**Rationale:**
- 0.x → 1.0 signals "schema API is now stable and importable" — plugin authors can start inheriting from `Entry`, `Sample`, `XRD`, etc. without touching `__field` code
- The 1.x series is the migration window — every `__field` access emits `DeprecationWarning` via `__getattr__` shim; plugin authors have a full release cycle
- 2.0 is the clean break, announced in advance, with a migration guide and compatibility codemods

**pynxtools-* family coordination**: pynxtools-xps, -mpes, -em, -apm, -xas, -xrd, -raman, -spm, -ellips must be informed before 1.0 ships so they can plan 2.0 migrations. A compatibility matrix (which pynxtools-* version requires which pynxtools) should be published at the 1.0 release.

---

## Relevant Open Issues

| Issue | Title | Phase |
|---|---|---|
| #765 | Schema caching cleanup | Phase 1 (Python import replaces JSON cache) |
| #708 | Split nexus package into smaller packages | Phase 1 (entry point splitting) |
| #542 | Search quantities in NOMAD | Phase 1 (`nx_optionality` drives indexing) |
| #534 | Unsigned int type mapping | Phase 1 (`NeXusQuantity.nx_type = "NX_UINT"`) |
| #702 | Parsing/normalization improvements | Phase 4 (parser rewrite) |
| #551 | NXapm normalizer | Phase 5 (move to pynxtools-apm) |
| #737 | Memory for large datasets | Phase 4 (annotation-based type info for smarter stats) |
| #725 | Materials card not instantiated | Phase 4 (normalization in `normalize()` methods) |

---

## Verification

```bash
# Prerequisite baseline:
python -m pytest tests/nexus/ tests/dataconverter/ tests/eln_mapper/ tests/nomad/ -q

# Phase 1: package equivalence
python -m pytest tests/nomad/test_metainfo_equivalence.py -v
pynx generate-metainfo --all --dry-run  # CI check

# Phase 3: parser parity
python -m pytest tests/nomad/test_parser.py -v  # golden archive outputs

# Phase 5: round-trip
pynx nomad export-nxdl --all --check-only  # NXDL recovered from Python annotations

# Phase N: ELN visibility
# Parse NXxrd .nxs file via XRayDiffraction; verify only recommended/required
# quantities visible in ELN by default
```

---

## Open Questions (for ADR process)

- Attribute naming: `{field}__units` vs. storing units directly on the Quantity's `unit` parameter?
- `AnchoredReference`: stay in pynxtools or migrate to nomad-measurements?
- Backward compat period for `__field` suffix: shim in `schema.py` or version-gated?
  -> this should probably change with a major version