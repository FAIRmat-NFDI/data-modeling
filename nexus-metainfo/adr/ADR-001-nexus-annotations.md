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

Three `AnnotationModel` subclasses are defined in `pynxtools.nomad.annotations`:

### `NeXusDefinition`

Attached to `Section.m_def` of every top-level generated class. Mirrors the NXDL
`<definition>` element.

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

### `NeXusQuantity`

Attached to every `Quantity` derived from a NXDL field or attribute. Mirrors an NXDL `<field>` or `<attribute>` element.

```python
class NeXusQuantity(AnnotationModel):
    kind: Literal["field","attribute"]
    name: str                              # original NXDL name (before Python renaming)
    parent_field: str | None = None        # for field-level attrs: owning field name
    type: str = "NX_CHAR"                  # NX primitive type
    units: str | None = None               # NX unit category
    name_type: Literal["specified","any","partial"] = "specified"
    optionality: Literal["required","recommended","optional"] = "optional"
    enumeration: list[str] | None = None
    open_enum: bool = False
    interpretation: str | None = None      # field only
    long_name: str | None = None           # field only
    deprecated: str | None = None
```

### Registration

```python
AnnotationModel.m_registry["nexus_definition"] = NeXusDefinition
AnnotationModel.m_registry["nexus_group"]      = NeXusGroup
AnnotationModel.m_registry["nexus_quantity"]   = NeXusQuantity
```

Registration happens at import time in `annotations.py`. No NOMAD core PR is required.

### Naming convention

Field names use bare NXDL attribute names (no `nx_` prefix) because the class name already provides the NeXus namespace. The sole exception is `nx_class`: `class` is a Python reserved keyword and cannot be used as a Pydantic field name.

### Annotation placement rule

| Situation | Annotation location |
|---|---|
| Top-level generated class | `a_nexus_definition` on `Section.m_def` |
| Named concept class (group with own quantities, same file) | `a_nexus_group` on concept class `m_def`; `SubSection` is clean |
| Cross-file group reference | `a_nexus_group` on the `SubSection` |
| Field or attribute | `a_nexus_quantity` on the `Quantity` |

## Alternatives considered

**Single flat annotation**: one annotation class with all fields, `kind` discriminates. Rejected: merges definition-level and instance-level concerns; makes `NeXusDefinition` fields mandatory on every SubSection.

**`section.more["nx_*"]`** (existing approach): untyped, not validatable, not
introspectable from plugin code via stable API. This ADR replaces it.

## Consequences

- Plugin code can introspect via `qty.m_def.m_get_annotations("nexus_quantity")`.
- The `optionality` field on `NeXusQuantity` enables the NOMAD GUI visibility filter described in ADR-002.
- The `type` field on `NeXusQuantity` preserves the original NX type even when NOMAD has no exact equivalent (e.g. `NX_UINT` → stored in annotation, mapped to `np.int64` in Python).
