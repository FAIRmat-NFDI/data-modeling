# ADR-006: Application Definitions Inherit from Entry, Not Object

**Status**: Decided (Phase 2 implementation)  
**Date**: 2026-06-05

## Summary

NXDL application definitions (e.g. `NXxps`, `NXarpes`) shall generate Python classes that inherit from `Entry`, not from `Object` or `Measurement`.

```python
# Correct (Phase 2 implementation):
class Xps(Entry):
    m_def = Section(
        a_nexus_definition=NeXusDefinition(nx_class="NXxps", category="application"),
    )
    # SubSections and Quantities from inside NXxps's NXentry group
    # with XPS-specific optionality

# Incorrect (not used):
class Xps(Object, basesections.Measurement):
    # ...
```

## Context

In NeXus, every application definition (e.g. `NXxps.nxdl.xml`) wraps exactly one `NXentry` group at the top level. This is a syntactic constraint: the root of the definition file is always an `NXentry`.

There are two possible interpretations in Python:

### Interpretation A: "Xps describes an entry"
`Xps(Entry)` — Xps is a **specialized kind of Entry**, with XPS-specific constraints on which subgroups are present and required, and with specific optionality for each field.

### Interpretation B: "Xps contains an entry"
`Xps(Object, Measurement)` — Xps is a **container type that holds an Entry** as a SubSection. This requires unwrapping the NXentry in the schema definition to expose it as a named SubSection.

### The NeXus Ontological Intent

In the NeXus data model:
- Files contain one or more `NXentry` groups (the root entry points to actual data).
- Application definitions (e.g. `NXxps.nxdl.xml`) define the **shape and constraints** of an `NXentry` in a specific measurement context — they are **constraint templates**, not entity types.
- A file in XPS format is a file whose `NXentry` satisfies the `NXxps` template.

Therefore, in Python/NOMAD:
- A NOMAD entry created from a NeXus file is an instance of the specialized Entry class (e.g. `Xps`).
- `Xps` is not a wrapper around an entry — it **is** the entry, specialized for XPS.

## Decision

**Use Interpretation A: `Xps(Entry)`**.

### Rationale

1. **Ontological Correctness**: NOMAD expects one entry per NXentry in a file (1:1 mapping). The entry type directly reflects the NXentry's application definition. Wrapping would introduce a redundant level of indirection.

2. **Schema Clarity**: In the generated Python code, `Xps` inheriting from `Entry` immediately tells the reader that this is a specialized kind of entry for XPS. The intent is clear without extra documentation.

3. **Inheritance Chain**: The NOMAD base sections are designed as inheritance chains:
   ```
   BaseSection
   → Object
   → Entry (the measurement type)
   → Xps (XPS-specific specialization)
   ```
   Interpretation B breaks this chain by introducing a container pattern that doesn't exist in NOMAD's base hierarchy.

4. **Parser Integration**: The parser directly creates instances of `Xps` (or whichever application def matches the NXxps NX_class attribute). No additional SubSection traversal needed.

5. **Naming and Optionality**: Subgroups of the NXentry in the NXDL become direct SubSections on `Xps` with application-specific optionality. This is consistent with how base classes inherit from NXentry.

## Generator Implementation

When processing an NXDL application definition:

1. Detect `category="application"` in the `<definition>` element.
2. Find the primary `NXentry` group child.
3. Use the NXentry's children as the effective children for the application class.
4. Set the Python base class to `Entry` (not following the NXDL `extends` attribute, which typically extends `NXobject`).
5. Exception: if the application extends another application (e.g. `NXafm extends NXspm`), use that as the base instead of Entry.

## Named Concepts

Groups with own quantities or different optionality become named concept classes, inheriting from the base:

```python
class Xps(Entry):
    # ...
    coordinate_system = SubSection(section_def=XpsCoordinateSystem)

class XpsCoordinateSystem(CoordinateSystem):
    # own quantities and different optionality
```

The name is derived from the group name and application name. Circular inheritance (when a group name matches the base class name) is disambiguated via reprefix logic: e.g. `ApmApmMeasurement(ApmMeasurement)`.

## Backward Compatibility

- Old runtime-generated schema with intermediate wrappers (`NexusMeasurement`) remains in `schema.py` until Phase 3/4 complete.
- Parser v1 continues using old entry points; parser v2 (Phase 3) uses new Entry-based classes.
- Shim for old `NexusMeasurement` imports stays until v2.0.

## Alternatives Considered

### Interpretation B: Xps(Object, Measurement) with nested Entry
- **Pro**: Preserves a "file-level wrapper" semantic if needed in the future.
- **Contra**: Introduces a redundant nesting level that doesn't match NOMAD's entry model; complicates parser logic; breaks inheritance chain.

### Interpretation C: Flatten entirely (Xps subclasses Object directly, inherits Entry's fields)
- **Pro**: Simplest schema.
- **Contra**: Loses the semantic connection to Entry; breaks NOMAD's base-section expectations.

## References

- [NXDL specification](https://github.com/NeXusDefinitions/NXDL) — application definitions as constraint templates
- [ADR-003](ADR-003-base-section-mapping.md) — base section mapping (NXentry → Entry)
- [ADR-001](ADR-001-nexus-annotations.md) — annotation models capturing NXentry semantics
