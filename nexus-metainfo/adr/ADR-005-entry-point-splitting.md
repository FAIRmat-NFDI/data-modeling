# ADR-005: Entry Point Splitting Strategy and Domain Plugin Interface

**Status**: Still slightly tbd — may evolve as implementation progresses  
**Date**: 2026-06  
**Deciders**: Lukas Pielsticker  
**Dicussion panel**: Hampus Näsström, Area B core team
---

**This ADR is WIP for now. The current document only reflects the current implementation. This may change upon discussion.**

## Context

The current pynxtools NOMAD integration registers all NeXus base classes and application definitions in a single monolithic schema package (`nexus_schema`). This has two problems:

1. **Startup cost**: all ~150 base classes and all application definitions are compiled from XML at every NOMAD startup, regardless of which techniques are actually used.
2. **Extension friction**: domain plugins (e.g. `pynxtools-xps`, `pynxtools-arpes`) cannot selectively load only the base classes relevant to their technique.

We need a splitting strategy that allows fine-grained loading while remaining compatible with NOMAD's plugin entry point system.

## Decision

### Phase 1: one entry point for base classes

A single `SchemaPackageEntryPoint` is registered for all generated base classes:

```toml
# pyproject.toml
[project.entry-points."nomad.plugin"]
nexus_base_classes = "pynxtools.nomad.metainfo:nexus_base_classes"
```

The entry point's `load()` calls `build_base_classes_package()` which imports all
~142 generated modules and assembles a single NOMAD `Package`.

### Phase 2: separate entry point for application definitions

When application definitions are generated (Phase 2), a second entry point is added:

```toml
nexus_applications = "pynxtools.nomad.metainfo:nexus_applications"
```

Base classes and application definitions remain in separate packages to allow NOMAD instances that only need base classes to load only `nexus_base_classes`.

### Domain plugin interface

**pynxtools reader plugins** (`pynxtools-xps`, `pynxtools-arpes`, etc.) are file
converters — they produce NeXus HDF5 files and populate NOMAD archives via the existing NeXus parser. They do not define NOMAD schema classes and remain essentially unchanged by this refactor.

**NOMAD schema plugins** (`nomad-measurements` and anything derived from it) are the intended consumers of the generated base classes. They inherit from the generated Python classes to define technique-specific sections:

```python
# In nomad-measurements (or a derived NOMAD plugin):
# Currently in pynxtools; may move to nomad-measurements long-term (see target architecture).
from pynxtools.nomad.metainfo.base_classes.entry import Entry

class XRDMeasurement(Entry):
    m_def = Section(...)
    # technique-specific quantities and subsections
```

These plugins declare their own `SchemaPackageEntryPoint`. NOMAD's plugin system loads all registered entry points (including `nexus_base_classes`) before resolving cross-package inheritance, so the base classes are available at class definition time.

### Package assembly pattern

NOMAD's metaclass auto-creates a per-module `Package` when a `Section` subclass is defined. With ~150 separate generated files this produces 150 per-module packages that would each appear twice in NOMAD's `all_metainfo_packages()` scan if not overridden.

`_package.py` overrides each module's `m_package` attribute with the assembled package after import, ensuring a single registration:

```python
setattr(mod, "m_package", assembled_package)
```

This mirrors the pattern used by `nomad-measurements` (where all classes are in a single module, so the override is not needed; our multi-file layout requires it explicitly).

### Naming

- `nexus_base_classes` — the Phase 1 entry point
- `nexus_applications` — Phase 2
- `nexus_contributed` — Phase 2 (contributed definitions from the FAIRmat namespace)

## Open questions (to be resolved before Phase 2)

- **Multi-package search**: NOMAD's Elasticsearch app is configured against one
  `SchemaPackage`. If `nexus_base_classes` and `nexus_applications` are separate
  packages, the search index may only cover one. This must be clarified with the NOMAD core team before Phase 2 starts.
- **Parser cross-package resolution**: the parser resolves section classes by name across all registered packages at parse time. This works because NOMAD registers all packages from all loaded entry points before parsing begins.

## Alternatives considered

**One entry point per technique** (e.g. `xps`, `arpes`): maximum
granularity. Rejected for Phase 1: requires generating and maintaining per-technique subsets of the base class hierarchy; we can do that later.

**Keep monolithic `nexus_schema`**: simplest. Rejected: does not address startup cost or extension friction that motivated this refactor.

## Consequences

- Issue #708 (split nexus package) is addressed by Phase 1 landing `nexus_base_classes` and Phase 2 adding `nexus_applications`. Could maybe close #708 after Phase 2.
- The `build_base_classes_package()` function is the programmatic equivalent of the entry point for code that needs the package without going through NOMAD's plugin system.
