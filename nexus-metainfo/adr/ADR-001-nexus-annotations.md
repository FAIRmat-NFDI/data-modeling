# ADR-001: NeXus Annotation Models for NOMAD Metainfo

**Status**: Accepted  
**Date**: 2026-06  
**Deciders**: Lukas Pielsticker, Hampus Näsström
**Dicussion panel**: Area B core team

---

## Context

The existing pynxtools–NOMAD integration stores NeXus metadata in `section.more["nx_*"]` dict entries — an undocumented, untyped side-channel that cannot be validated, introspected, or extended by plugins. Any code that needs to know whether a quantity is a NeXus field or attribute, what its NXDL type is, or whether it is required, must parse these string keys by convention.

We need a typed, registered annotation system so that:
- Generated Section and Quantity definitions carry structured NeXus metadata
- Plugin code can introspect annotations via the stable NOMAD API (`m_def.m_get_annotations`)
- Annotations survive serialization/deserialization of the metainfo schema

## Decision

Six `AnnotationModel` subclasses are defined in `pynxtools.nomad.annotations`, one per NXDL node kind that needs to be represented at runtime. The model hierarchy mirrors the `NexusNode` class hierarchy in `nexus_tree.py`, but serves a different purpose: the `NexusNode` tree is a generator-side working model with XML parsing logic and tree navigation; the `AnnotationModel` classes are runtime metadata embedded in the generated Python files and queryable via NOMAD's reflection API.

### `NeXusDefinition`

Attached to `Section.m_def` of every top-level generated class. Mirrors the NXDL `<definition>` element.

```python
class NeXusDefinition(AnnotationModel):
    nx_class: str                          # e.g. "NXentry"
    category: Literal["base","application","contributed"] = "base"
    restricts: bool = False
    ignore_extra_groups: bool = False
    ignore_extra_fields: bool = False
    ignore_extra_attributes: bool = False
    symbols: dict[str, str] | None = None  # {symbol_name: doc_string}
    deprecated: str | None = None
```

### `NeXusGroup`

Attached to named concept class `m_def` (for groups defined inline) or to cross-file `SubSection` definitions (for groups whose target class is in a separate file). Mirrors an NXDL `<group>` element.

```python
class NeXusGroup(AnnotationModel):
    nx_class: str
    name: str | None = None                # fixed name; None = variadic
    name_type: Literal["specified","any","partial"] = "specified"
    optionality: Literal["required","recommended","optional"] = "optional"
    min_occurs: int | None = None
    max_occurs: int | None = None
    deprecated: str | None = None
```

### `NeXusField`

Attached to every `Quantity` derived from a NXDL `<field>` element. Fields carry typed data arrays and may have unit categories, interpretation hints, and long names.

```python
class NeXusField(AnnotationModel):
    name: str                              # original NXDL name (before Python renaming)
    type: str = "NX_CHAR"                  # NX primitive type
    units: str | None = None               # NX unit category
    name_type: Literal["specified","any","partial"] = "specified"
    optionality: Literal["required","recommended","optional"] = "optional"
    enumeration: list[str] | None = None
    open_enum: bool = False
    interpretation: str | None = None
    long_name: str | None = None
    deprecated: str | None = None
```

### `NeXusAttribute`

Attached to every `Quantity` derived from a NXDL `<attribute>` element — either a group-level attribute or a field-level attribute. Field-level attributes set `parent_field` to the owning field's name.

```python
class NeXusAttribute(AnnotationModel):
    name: str                              # original NXDL attribute name
    parent_field: str | None = None        # for field-level attrs: owning field name
    type: str = "NX_CHAR"
    name_type: Literal["specified","any","partial"] = "specified"
    optionality: Literal["required","recommended","optional"] = "optional"
    enumeration: list[str] | None = None
    open_enum: bool = False
    deprecated: str | None = None
```

### `NeXusLink`

Attached to every `Quantity(type=str)` derived from a NXDL `<link>` element. A link is a named HDF5 reference to another node in the file; the `target` is the schema-level default path and the parser resolves the actual target at read time.

```python
class NeXusLink(AnnotationModel):
    name: str
    target: str                            # schema-level default target path
    optionality: Literal["required","recommended","optional"] = "optional"
    deprecated: str | None = None
```

### `NeXusChoice`

Attached to each `SubSection` that represents one alternative in a NXDL `<choice>` block. A choice allows exactly one of several NX classes to occupy a named slot. One SubSection is generated per alternative; all share the same `group_name`.

Naming convention: `{choice_name}_{nx_class_suffix}` where the suffix is the NX class name with `NX` prefix removed and lowercased (e.g. `pixel_shape_off_geometry`, `pixel_shape_cylindrical_geometry`).

```python
class NeXusChoice(AnnotationModel):
    nx_class: str
    group_name: str                        # the <choice name="..."> attribute, shared
    optionality: Literal["required","recommended","optional"] = "optional"
    deprecated: str | None = None
```

### Registration

```python
AnnotationModel.m_registry["nexus_definition"] = NeXusDefinition
AnnotationModel.m_registry["nexus_group"]      = NeXusGroup
AnnotationModel.m_registry["nexus_field"]      = NeXusField
AnnotationModel.m_registry["nexus_attribute"]  = NeXusAttribute
AnnotationModel.m_registry["nexus_link"]       = NeXusLink
AnnotationModel.m_registry["nexus_choice"]     = NeXusChoice
```

Registration happens at import time in `annotations.py`. No NOMAD core PR is required.

### Naming convention

Field names use bare NXDL attribute names (no `nx_` prefix) because the class name already provides the NeXus namespace. The sole exception is `nx_class`: `class` is a Python reserved keyword and cannot be used as a Pydantic field name.

### Annotation placement rule

| Situation | Annotation | Location |
|---|---|---|
| Top-level generated class | `a_nexus_definition` | `Section.m_def` |
| Named concept class (group with own quantities, same file) | `a_nexus_group` | concept class `m_def`; SubSection is clean |
| Cross-file group reference | `a_nexus_group` | the `SubSection` |
| NXDL `<field>` | `a_nexus_field` | the `Quantity` |
| NXDL `<attribute>` (group-level or field-level) | `a_nexus_attribute` | the `Quantity` |
| NXDL `<link>` | `a_nexus_link` | the `Quantity(type=str)` |
| One alternative in a NXDL `<choice>` | `a_nexus_choice` | the `SubSection` |

## Why `NeXusField` and `NeXusAttribute` are separate classes (not a `kind` discriminator)

`<field>` and `<attribute>` are structurally distinct in NXDL: fields carry `units`, `interpretation`, and `long_name`; attributes never do. Encoding this as `kind: Literal["field","attribute"]` on a shared class would require documenting which fields apply to which `kind` and would make the distinction invisible from the annotation type alone.

Separate classes mirror the `NexusField`/`NexusAttribute` split in `nexus_tree.py` and make the distinction structural rather than documentary. Consumers (parser, GUI) select the annotation by name: `m_def.m_get_annotations("nexus_field")` vs. `m_def.m_get_annotations("nexus_attribute")`.

## Alternatives considered

**Single `NeXusQuantity` with `kind` discriminator** (original Phase 1 design): one class with all fields, `kind="field"/"attribute"`. Rejected in Phase 1 cleanup: merges semantically distinct concepts; units/interpretation/long_name appear on attribute annotations where they are not applicable; requires runtime `kind` checks instead of annotation type dispatch.

**`NeXusChoice` as multiple `NeXusGroup` annotations**: mark choice alternatives with `is_choice=True` on `NeXusGroup`. Rejected: `group_name` has no natural home on `NeXusGroup` (which describes a group's own identity, not its membership in a choice block); the shared `group_name` field is the key semantic of choice membership and deserves its own annotation type.

**Single flat annotation**: one annotation class with all fields, `kind` discriminates. Rejected: merges definition-level and instance-level concerns; makes `NeXusDefinition` fields mandatory on every SubSection.

**`section.more["nx_*"]`** (existing approach): untyped, not validatable, not
introspectable from plugin code via stable API. This ADR replaces it.

## Consequences

- Plugin code introspects via `qty.m_def.m_get_annotations("nexus_field")` or `"nexus_attribute"`.
- `NeXusField.optionality` / `NeXusAttribute.optionality` enable the GUI visibility filter described in ADR-002.
- `NeXusField.type` / `NeXusAttribute.type` preserve the original NX type even when NOMAD has no exact equivalent (e.g. `NX_UINT` → stored in annotation, mapped to `np.int64` in Python).
- `NeXusLink` enables the round-trip exporter (Phase 4) to reconstruct `<link>` elements; without it, links would be silently dropped.
- `NeXusChoice` lets the parser select the correct SubSection by matching `NX_class` on the HDF5 group against `NeXusChoice.nx_class`.
- All six annotation classes must be imported before any schema package loads — this is guaranteed by `pynxtools.nomad.annotations` being the first import in every generated file.
