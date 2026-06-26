# ADR-004: Code Generator Specification

**Status**: Decided (Phases 1–3 implementation); the nested-class submodule layout below remains deferred to Phase 7  
**Date**: 2026-06  
**Deciders**: Lukas Pielsticker  
**Dicussion panel**: Hampus Näsström, Area B core team

---

## Context

The existing schema generation in `schema.py` builds NOMAD `Section` and `Quantity` objects at import time by parsing NXDL XML directly. This produces no reusable Python artifacts, couples NXDL parsing to NOMAD schema registration, and makes the schema impossible to inspect, version, or extend without running NOMAD.

We need a code generator that reads NXDL through the NexusNode API and writes one
importable Python file per NXDL base class.

## Decision

### Entry point

`generate_tree_from(nx_name)` in `pynxtools.nexus.nexus_tree` is the single entry
point into NXDL data. The generator accesses **no raw XML** — all NXDL attributes are read through typed `NexusNode` properties which resolve inheritance automatically.

### Output

One Python file per NXDL class, written to `metainfo/base_classes/` (category `"base"`) or `metainfo/applications/` (category `"application"`, added in Phase 2 — includes both official and community-contributed application definitions, discovered by `category`, not by file path; see ADR-005). Each file:
- Defines one top-level Section class (the primary class)
- May define named concept classes (Section subclasses for groups that have own quantities)
- Has `__all__ = ["PrimaryClassName"]`
- Carries `links=[url]` on every Section and Quantity pointing to the NeXus manual
- Is linted and formatted with `ruff`

### NXDL node kinds handled by the generator

| NXDL element | Generated artifact | Annotation |
|---|---|---|
| `<field>` | `Quantity` | `NeXusField` |
| `<attribute>` (group-level or field-level) | `Quantity` | `NeXusAttribute` |
| `<group>` | `SubSection` (+ optional named concept class) | `NeXusGroup` |
| `<link>` | `Quantity(type=str)` | `NeXusLink` |
| `<choice>` | One `SubSection` per alternative | `NeXusChoice` |

**`<link>` handling**: emitted as `Quantity(type=str)` carrying `a_nexus_link`. The `target` field stores the schema-level default target path from the NXDL. The actual HDF5 target is resolved by the parser at read time. Links share the quantity name namespace with fields (a link name that conflicts with a field name would be a NXDL error).

**`<choice>` handling**: each alternative group inside the `<choice>` block becomes a separate `SubSection` named `{choice_name}_{class_suffix}` (e.g. `pixel_shape_off_geometry`, `pixel_shape_cylindrical_geometry`). All alternatives carry `NeXusChoice` with the shared `group_name`. The parser selects the matching SubSection by comparing `NeXusChoice.nx_class` against the HDF5 group's `NX_class` attribute. Only alternatives whose target class is already in `base_classes/` are generated (same rule as for regular groups).

### Additive-only write policy

The generator never removes existing members. When a file already exists:
- **No user additions**: rewrite if content differs (propagates description changes, new members, annotation updates)
- **User additions present** (methods or quantities not in new output): skip; protect customizations. Use `--force` to override.
- **`--dry-run`**: report whether the file would change; no write

This allows `normalize()` methods added by plugin developers to survive regeneration.

### Naming conventions

- **Class names**: strip `NX` prefix, CamelCase.
- **Quantity names**: NXDL field names as-is; `_quantity` suffix for:
  - Reserved NOMAD `BaseSection` names (`name`, `datetime`, `lab_id`, `description`)
  - Field-vs-group collisions (group wins the unqualified name)
- **Subsection names**: NXDL group name; `_quantity` suffix for reserved names
- **Field-attribute quantities**: `{field_name}__{attr_name}` (double underscore)

### Naming for application definition nested classes (deferred from Phase 2 to Phase 7)

**This idea was not implemented yet. We punted the decision about it towards a later phase.**

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
The long name (`ARPESEntry`) is only needed inside NOMAD's package registry to avoid
collisions between base-class and application-definition classes with the same short name.

### Dependency ordering

Files are written in topological order (using `toposort_flatten`) so that each file's imports are already on disk when it is generated. Cycles are detected and reported.

### Template

Jinja2 template at `converters/templates/nexus.py.j2`. The generator passes a context dict built from `NexusNode` properties — no template accesses XML directly.

### CLI

```bash
pynx nomad generate-metainfo --nxdl NXentry        # single class
pynx nomad generate-metainfo --all-base                 # base classes only
pynx nomad generate-metainfo --all-applications          # application/contributed classes only
pynx nomad generate-metainfo --all                      # applications first, then base (Phase 2+)
pynx nomad generate-metainfo --all --force              # overwrite all
pynx nomad generate-metainfo --all --dry-run            # CI diff check
```

Exactly one of `--nxdl`, `--all`, `--all-base`, `--all-applications` must be given (flags added beyond the original single-`--all` design as Phase 2's applications/base split made selective regeneration necessary).

## Alternatives considered

**Runtime generation (current approach)**: builds Section objects at import time.
Rejected: no reusable artifacts; hard to inspect; slow startup.

**Single giant Python file**: all classes in one file. Rejected: unmaintainable at ~150 classes; no per-class version history; circular import risk.

**AST rewriting instead of Jinja2**: patch existing files with AST transforms.
Rejected: fragile for structural changes; Jinja2 + additive check is simpler and
produces clean, readable output.

## Consequences

- Generated files are committed to the repository and treated as source artifacts. They must be regenerated whenever the NXDL definitions change.
- The `--dry-run` flag enables CI to enforce that committed files match generator output.
- The `--force` flag is needed to propagate non-structural changes (descriptions,
  annotation values) to files that have no user additions.
- Named concept classes are internal implementation detail; `__all__` exposes only the primary class. Imports of named concepts are possible but not part of the public API.
