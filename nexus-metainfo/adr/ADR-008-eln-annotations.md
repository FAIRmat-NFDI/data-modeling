# ADR-008: ELN Annotations on the Generated NeXus Schema

**Status**: Decided (Phase 2.5 implementation)
**Date**: 2026-06
**Deciders**: Lukas Pielsticker  
**Dicussion panel**: Hampus Näsström, Area B core team

## Summary

Every generated `Quantity` whose Python type and shape make it sensibly editable gets a
best-effort `a_eln=ELNAnnotation(...)` annotation, computed by the generator from the
quantity's type/shape/name-type, not hand-curated per field. `Entry` and `Root` are hidden
from "Create entry from schema" via `SchemaAnnotation(enabled=False)`, since they are meant
to be used through parsing or through application-class subclasses, not instantiated
directly. The same generated class now serves both parser-populated (read-only) and
ELN-authored (editable) entries — no duplicate `ELNXps`-style class is needed.

```python
# Generated, e.g. on Xps(Entry):
sample_normal_polar_angle_of_tilt = Quantity(
    type=np.float64,
    a_nexus_field=NeXusField(name="...", type="NX_FLOAT", ...),
    a_eln=ELNAnnotation(component=ELNComponentEnum.NumberEditQuantity),
    a_display={"unit": "deg"},
)
```

## Context

The NeXus-derived generated schema (`Entry`, `Sample`, `Instrument`, application classes
like `Xps`, ...) was originally built purely as a *parsing target*: `NexusParserV2`
populates instances from `.nxs` files, and `archive.metadata.readonly = True` is set on
every parsed entry (`NexusParserV2._set_entry_metadata()` / `_create_root_entry()`).

A separate need surfaced: users should also be able to create entries of these same
classes directly in NOMAD's ELN ("Create entry from schema"), filling in values by hand
rather than only via parsing — e.g. for samples or instruments not yet captured in a NeXus
file, or for entries authored before a measurement happens. This raised a design question:
does this require a second, ELN-specific copy of each class (e.g. `ELNXps(Xps)` alongside
`Xps(Entry)`), or can the same generated class serve both roles?

### Resolution: one class, two read paths

NOMAD's frontend computes `entryIsEditable = editable && !readonly`, where `editable` is a
schema-wide property (does this class have `a_eln` annotations enabling ELN edit
components?) and `readonly` is an **instance-level** flag on `archive.metadata`. Since
`NexusParserV2` already sets `readonly = True` on every entry it creates, and ELN-created
entries default to `readonly = False`, a single class with `a_eln` annotations correctly
renders as editable when created via "Create from schema" and as read-only when populated
by the parser — confirmed working, no duplicate class needed.

This makes the remaining question purely about the generator: which quantities should get
an `a_eln` annotation, and with what component?

## Decision

The generator computes a best-effort ELN component per quantity from its Python
type/shape/name-type, applied uniformly across all 280 generated files — not hand-curated
field by field, and not requiring per-class developer review before becoming usable.

### Generator (`converters/nxdl_to_metainfo.py`)

`QuantityContext` gained two fields: `eln_component: str | None` and
`eln_default: str | None`. `_eln_component_for(python_type, shape, name_type, scalar_items)`
is a pure mapping function:

| Condition | Result |
|---|---|
| `shape` truthy (array) | No annotation — see "Excluded by design" below |
| `name_type in ("any", "partial")` (variadic) | No annotation |
| `python_type == "Bytes"` | No annotation |
| `python_type == "Datetime"` | `DateTimeEditQuantity` |
| `python_type == "bool"` | `BoolEditQuantity` |
| single-value `MEnum(...)` | `EnumEditQuantity`, `default=` set to the sole enum value |
| multi-value `MEnum(...)` | `EnumEditQuantity`, no default |
| `python_type == "str"` | `StringEditQuantity` |
| numeric (`np.float64`/`np.int64`/`np.complex128`/`int`/`float`) | `NumberEditQuantity` |

**Named-concept shape-inheritance fix**: in `_build_named_concept()`, after computing
`eln_component` for an overriding quantity, if the override has no explicit `shape` but the
corresponding field in the NX base class (looked up via `base_lookup`) has `shape` with
`len() > 1`, the ELN component is cleared. NOMAD's `__init_metainfo__()` inherits a
quantity's `shape` from the parent class when a subclass override doesn't re-specify it —
without this check, multi-dimensional array overrides (e.g. `vertices` in
`NXcg_face_list_data_structure`-derived named concepts) received an `ELNAnnotation` that
NOMAD's own validator rejects at startup:
`assert len(quantity.shape) <= 1, 'Only scalars or lists can be edited.'`. Scalar/1D
named-concept overrides are unaffected and still get `a_eln`.

### Template (`templates/nexus.py.j2`)

- Unconditional import: `from nomad.datamodel.metainfo.annotations import ELNAnnotation, ELNComponentEnum, SchemaAnnotation`.
- `a_eln=ELNAnnotation(component=ELNComponentEnum.{{ qty.eln_component }}, default=...)`
  emitted after the `a_nexus_field`/`a_nexus_attribute` block, in both the main quantities
  loop and the named-concept quantities loop.
- `a_display={'unit': '{{ qty.default_unit }}'}` (plain dict, no class import needed) emitted
  alongside `NumberEditQuantity` quantities that have a default unit. **Not**
  `ELNAnnotation.defaultDisplayUnit`, which is deprecated.
- `a_schema=SchemaAnnotation(label="{{ class_name }}", enabled=False)` on `m_def`, for
  `NXentry` and `NXroot` only — hides these two base classes from "Create entry from
  schema." They are meant to be reached via parsing or via application-class subclasses
  (`Xps(Entry)`, etc.), not instantiated directly as bare `Entry`/`Root`.

**Gotcha worth recording**: `SchemaAnnotation.label` is a required pydantic field with no
default. Omitting it crashes NOMAD at `__init_metainfo__()` with
`pydantic_core.ValidationError: Field required` — this surfaced as a startup failure
across the whole appworker the first time `SchemaAnnotation(enabled=False)` was emitted
without `label=`. Always pass `label=`.

### Excluded by design

- **Arrays**: no ELN component — NOMAD has no array-editing ELN component for raw NeXus
  arrays. `HDF5Reference` + `H5WebAnnotation` (the pattern used by
  `nomad_measurements.xrd.XRDResult1DHDF5`) was investigated as an alternative but requires
  changing the quantity's `type` and parser-side writes — deferred, not part of this
  decision.
- **`UserEditQuantity`/`AuthorEditQuantity`**: not applicable — no NeXus quantity has
  `type=User`/`type=Author`.
- **`np.complex128`**: kept on `NumberEditQuantity` — there is no dedicated complex-number
  editor in NOMAD, and this is an accepted simplification rather than a gap to close.
- **Optionality-driven UI visibility** (`SectionProperties.visible` /
  `a_display={'visible': False}`): not implemented here — still blocked on the same NOMAD
  core `visible_by_default` mechanism tracked as an open question elsewhere in this project.
  This ADR does not resolve it.

## Consequences

- Every generated class is usable as an ELN schema immediately upon regeneration — no
  per-class developer review or hand-authored annotation pass required before a class is
  ELN-usable.
- A single class serves both parser-populated and ELN-authored entries; no `ELNXps`-style
  duplication pattern is introduced or needed elsewhere in the schema.
- `Entry` and `Root` are excluded from the "Create entry from schema" dialog; all
  application-definition subclasses (`Xps`, `Arpes`, ...) remain selectable, since
  `SchemaAnnotation(enabled=False)` is only emitted for the two base wrapper classes.
- Named-concept quantities overriding a multi-dimensional base-class field never receive an
  `a_eln` annotation, even when the override could in principle be made scalar — this is
  conservative by construction (the generator doesn't currently distinguish "override
  narrows an array field to scalar" from "override leaves the array shape inherited");
  revisit if a real case needs it.
- Verified: 473 tests passing across `tests/nexus/`, `tests/dataconverter/`,
  `tests/eln_mapper/` after regenerating all 280 files with this change, no regressions.

## Alternatives Considered

### Duplicate ELN-specific class per application definition (e.g. `ELNXps(Xps)`)
- **Pro**: would let an ELN-specific class diverge from the parser-target class if their
  needs ever conflict.
- **Contra**: doubles the number of generated classes for no benefit once the
  `readonly`-flag mechanism was confirmed to already solve the actual problem; introduces a
  maintenance burden (two classes per application definition, kept in sync) with no
  corresponding gain.

### Hand-curate `a_eln` per quantity instead of a generator-computed default
- **Pro**: would allow nuanced, field-by-field judgment about which fields are "worth"
  exposing in the ELN.
- **Contra**: not feasible at this scale (thousands of quantities across 280 files);
  would require an indefinite review backlog before any class became ELN-usable. A
  best-effort generator default, refined later via the additive-only constraint
  (hand-written `normalize()`/annotation overrides survive regeneration), is the pragmatic
  choice given the additive-only generator already exists for exactly this purpose.

### Implement `HDF5Reference`/array ELN support now, rather than excluding arrays
- **Pro**: would make large detector/dataset arrays editable directly in the ELN, matching
  `nomad_measurements.xrd.XRDResult1DHDF5`'s pattern.
- **Contra**: requires changing the quantity's declared `type` and adding parser-side HDF5
  write support — a materially larger change than the type/shape-driven annotation mapping
  this ADR covers. Deferred to a later phase rather than bundled here.

## References

- [ADR-006](ADR-006-application-definitions-are-entry-subclasses.md) — application
  definitions inherit from `Entry`; this ADR's `SchemaAnnotation` exclusion applies to
  `Entry` itself, not to the application-definition subclasses ADR-006 establishes.
- [ADR-007](ADR-007-nxroot-handling.md) — companion Phase 3 decision; `Root` is excluded
  from "Create entry from schema" by the same mechanism as `Entry`, for the same reason
  (it's a parser/grouping construct, not meant to be hand-instantiated).
- `nomad/datamodel/metainfo/annotations.py` (`packages/nomad-FAIR`) — canonical definitions
  of `ELNAnnotation`, `ELNComponentEnum`, `SchemaAnnotation`, `valid_eln_components`.
