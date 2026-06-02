# ADR-003: Canonical NeXus ↔ NOMAD Base Section Mapping

**Status**: Current design — may evolve as implementation progresses  
**Date**: 2026-06  
**Deciders**: Lukas Pielsticker, Hampus Näsström, Area B core team

---

## Context

Generated Python classes must inherit from appropriate NOMAD base sections so that NOMAD's search, normalisation, and ELN system recognise them as measurements, samples, instruments, etc. The mapping is not mechanical — it requires semantic judgment about which NeXus concept most closely corresponds to which NOMAD concept.

For classes not in the explicit map, a default (`BaseSection`) is used.

## Decision

The canonical mapping is defined in `pynxtools.nomad.converters._mapping.BASESECTIONS_MAP`:

| NXDL class | Generated Python class | NOMAD base section | Rationale |
|---|---|---|---|
| `NXobject` | `Object` | `BaseSection` | Root of all NeXus classes; no domain semantics |
| `NXentry` | `Entry` | `basesections.Measurement` | An entry represents a complete measurement |
| `NXprocess` | `Process` | `basesections.ActivityStep` | A data reduction/processing step |
| `NXsample` | `Sample` | `basesections.CompositeSystem` | A physical sample with composition |
| `NXsample_component` | `SampleComponent` | `basesections.Component` | A component of a composite sample |
| `NXfabrication` | `Fabrication` | `basesections.Instrument` | Fabrication is instrument-like in NOMAD |
| `NXdata` | `Data` | `basesections.ActivityResult` | NXdata holds the result of a measurement |

All other NXDL base classes inherit from `Object` (the generated `NXobject` class), giving the full NeXus class hierarchy in Python.

### Multiple inheritance rule

When a class has both a NeXus parent and a NOMAD base section, the signature is:

```python
class Entry(Object, basesections.Measurement): ...
```

The NOMAD base section is the **second** base — it provides NOMAD semantics without
shadowing the NeXus hierarchy. The NOMAD base is omitted if the NeXus parent already
provides it through the chain (prevents duplicate MRO entries).

### Import convention

NOMAD base sections are imported as the `basesections` **module**, not as individual
classes:

```python
from nomad.datamodel.metainfo import basesections
```

Class signatures use `basesections.Measurement`, `basesections.CompositeSystem`, etc.
This avoids name collisions when the generated NeXus class and the NOMAD base share the
same Python name (e.g. both could be named `Component`).

## Alternatives considered

**`NXentry` → `ActivityStep`**: rejected — an entry is a complete measurement, not a step
within one. Steps map to `NXprocess`.

**`NXinstrument` → `basesections.Instrument`**: not in the map because `NXinstrument` is meant to describe an instrument during measurement with allits  components (detectors, sources, etc.), not a static instrument itself.
`NXfabrication` is the closer semantic match for NOMAD's `Instrument` concept.

**All classes → `BaseSection`**: simplest, but loses NOMAD search and normalisation integration for the semantically meaningful classes.

## `BASESECTIONS_MAP` is transitional

The hardcoded `BASESECTIONS_MAP` dict in `converters/_mapping.py` is a **transitional mechanism**. Long-term, the base section for each NeXus class should be declared directly on the class itself — either via a convention in the NXDL definitions (an attribute or extension mechanism that signals the intended NOMAD mapping) or via an explicit annotation on the generated Python class. The generator would then read this from the class definition rather than from a hardcoded dict.

Until that mechanism exists, `BASESECTIONS_MAP` is the single source of truth. Any entry added to the map is a commitment to a semantic equivalence; removals or changes are breaking changes for downstream code that inherits from the affected class.

## Consequences

- `schema.py`'s `BASESECTIONS_MAP` (which maps to Python class objects) is superseded for new code; `converters/_mapping.py` is canonical.
- New NXDL classes with strong semantic matches to NOMAD concepts can be added by
  extending `BASESECTIONS_MAP` — this is a design decision, not a mechanical change.
- The `NXinstrument` / `basesections.Instrument` question may be revisited when
  `nomad-measurements` alignment begins (Phase N).
- When `BASESECTIONS_MAP` is eventually replaced by per-class declarations, the generator must be updated to read from the new source; the generated files will be regenerated without changing the inheritance in the Python classes.
