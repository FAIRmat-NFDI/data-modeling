# ADR-002: Optionality Semantics — How NXDL Optionality Maps to NOMAD

**Status**: Decided (Phase 1 implementation) — the GUI visibility mechanism itself remains pending on NOMAD core (see #542)  
**Date**: 2026-06  
**Deciders**: Lukas Pielsticker, Hampus Näsström  
**Dicussion panel**: Area B core team

---

## Context

NXDL defines three optionality levels for fields and groups:

- `required` — must be present in a conforming file
- `recommended` — should be present; its absence is a validation warning
- `optional` — may or may not be present; no warning if absent

The existing pynxtools NOMAD integration does not surface these levels in the schema. All quantities are equally visible in the NOMAD GUI, producing an overwhelming list of fields for any moderately complex NeXus class.

We need to:
1. Correctly derive optionality from NXDL context during code generation
2. Store it on `NeXusField` and `NeXusAttribute` annotations so the parser and GUI can act on it
3. Define the future visibility rule for the NOMAD GUI (pending NOMAD core ask)

## Decision

### Deriving optionality from NXDL

NXDL optionality is set by XML attributes and group-level flags. The `NexusNode`
(`nexus_tree.py`) resolves this through the inheritance chain and exposes it as
`node.optionality: Literal["required", "recommended", "optional"]`.

Rules applied by `NexusNode._set_optionality()`:
- `@required="true"` or `@minOccurs > 0` → `"required"`
- `@recommended="true"` → `"recommended"`
- `@optional="true"` or `@minOccurs == 0` (explicit) → `"optional"`
- No attribute present → `"optional"` (NXDL default)
- Application definition context overrides base class optionality

### Storage

`optionality` is stored on `NeXusGroup`, `NeXusField`, and `NeXusAttribute` annotations (see
ADR-001). The value is the direct NXDL-derived string — no remapping.

### Future visibility rule (pending NOMAD core ask)

The GUI visibility rule is **independent of (though related to) `NexusNode.optionality`**. `NexusNode.optionality` is a validation concept — it describes whether a field is required for a conforming HDF5 file. GUI visibility is a presentation concept — it describes whether a field should be shown to the user by default.

The intended presentation rule combines both axes:

| | Declared in this class | Inherited only |
|---|---|---|
| `required` / `recommended` | visible | visible |
| `optional` | **visible** | **hidden** |

- `required` and `recommended` quantities visible by default regardless of where they are declared
- `optional` quantities hidden by default **unless they are explicitly declared in the class itself** (not merely inherited from a parent class)

The distinction matters: a quantity that a domain author has intentionally included in their schema (explicit declaration → visible) differs from one that is only present because it was inherited from the full NeXus base class hierarchy (inheritance-only → hidden by default). This prevents the GUI from being flooded with hundreds of inherited optional NeXus fields for every entry.

This requires a `visible_by_default: bool` (or equivalent) mechanism on NOMAD's
`Definition` / `Quantity` that applies across ELN, metainfo viewer, search, and GUI. Not yet implemented. Must be framed as a general NOMAD feature (not NeXus-specific) when presented to the NOMAD core team.

Until that mechanism exists, all quantities remain visible.

## Alternatives considered

**Binary required/optional**: collapse recommended into optional. Rejected: loses
information useful for validation feedback and future filtering granularity.

**Store as int (0/1/2)**: avoids string comparison. Rejected: less readable; no performance benefit for this use case.

## Consequences

- The `optionality` field is present on all six annotation models regardless of whether the GUI filtering mechanism exists yet.
- Issue #542 (search quantity filtering) depends on NOMAD core delivering the visibility mechanism; this ADR defines our side of the interface.
- Parser and validation code can use `NeXusField.optionality` / `NeXusAttribute.optionality` to decide whether a   missing field produces an error or a warning.
