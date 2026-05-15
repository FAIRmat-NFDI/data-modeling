# Plan: Converge pynxtools plugin ecosystem onto MultiFormatReader

## Context

The pynxtools plugin ecosystem has diverged into two camps. The **MFR-aligned** group (xps, mpes, raman, xas, xrd, igor) all extend `MultiFormatReader` and use flat JSON configs with `@attrs:` / `@data:` / `@eln:` tokens. The **MFR-deviating** group (em, apm, spm) extend
`BaseReader` directly.

**Reference implementation for MFR**: `pynxtools-xps`: clean separation of parsers (format detection → flat metadata/data dicts) from config-driven mapping (JSON config per format variant).

**Key design principle**: The JSON config is the primary customization surface for plugin users. Via the `-c` flag, users can override the default config entirely. Any capability expressible in the config (unit conversion, expression evaluation, datetime parsing) should live there (not in plugin Python code) so users can adapt behavior without forking.

**Existing MFR gaps blocking config-level expressiveness**:
- No formula / expression evaluation (PR [#524](https://github.com/FAIRmat-NFDI/pynxtools/pull/524) draft exists, broken regex + stray `print`)
- No unit conversion (done ad hoc in each plugin: XRD uses pint Quantities; XPS validates post-hoc; SPM in `_get_data_unit_and_others`; EM/APM via Python `mapping_functors_pint.py`)
- No datetime string normalization (PR [#252](https://github.com/FAIRmat-NFDI/pynxtools/pull/252) proposed for json_map; never landed)
- `@attr:` (XRD) vs `@attrs:` (everyone else) — naming inconsistency

---

## Current-state inventory

### MFR-aligned plugins

| Plugin | Deviations from XPS reference |
|--------|-------------------------------|
| **xps** | ✅ Reference. Multi-config (one JSON per format variant). Unit strings passed as-is from parsers; `check_units` validates post-hoc. |
| **mpes** | Clean. No default config (user must supply). `get_eln_data` uses `path` directly, not key-first lookup. |
| **raman** | Monkey-patches `self.post_process` per format handler. `get_eln_data` has heuristic NXclass case-stripping. Dumps unknown rod keys into `COLLECTION[unused_rod_keys]`. |
| **xas** | Extends `XPSReader`. Broken: `handle_xy_file` calls non-existent `parse_file()` with `print` statements. **Skip — still in development.** |
| **xrd** | Uses `@attr:` (singular) — typo. Pint `Quantity` unwrapping in `convert_quantity_to_value_units` before config fill. Config hardcoded in `__init__` with no `-c` override. |
| **igor** | ✅ Aligned. Extends MFR properly. `get_entry_names()` supports multi-entry from a `.entry` YAML file. Actual file parsing deferred to `post_process()` (IBW/PXP loaded there). Minor: `handle_eln_file` calls `parse_yml` without `convert_dict` or `parent_key`. `set_config_file` skips (not replaces) on re-registration. `get_eln_data` uses `path` arg directly (same pattern as mpes). |

### Plugins with non-MFR infrastructure

| Plugin | Architecture |
|--------|-------------|
| **spm** | `BaseReader`. `SPMformatter` mini-framework: nested YAML config with `raw_path` end-dicts; `walk_though_config_nested_dict` walker; `_grp_to_func` dispatch; `_nxdata_grp_from_conf_description`. `@default_link:` link syntax. Pint for type inspection. |
| **em** | `BaseReader`. No JSON config. 15+ tech-partner parsers write directly to template via Python-DSL in `mapping_functors_pint.add_specific_metadata_pint(cfg, src, id, template)` — takes `(src_path, ureg.Unit, target_unit)` tuples. Custom pint registry. `EmUseCaseSelector` routes files. Entry ID hardcoded to 1. |
| **apm** | `BaseReader`. Same Python-DSL pattern (near-identical `mapping_functors_pint.py`). `IfesReconstructionParser` already uses `pint.Quantity` objects. |

---

## Workpackages

### Workpackage 1: pynxtools core — MFR enhancements

**Primary file**: `packages/pynxtools/src/pynxtools/dataconverter/readers/multi/reader.py`

#### 1a. Formula evaluation: `@formula:` prefix

**Motivation**: Enable unit conversion, arithmetic transforms, axis construction, and datetime normalization to be expressed directly in config files without plugin Python code.

PR #524 has a skeleton but is broken: the regex `r"(\/[\w\[\]\_\-/]+)"` only matches `/`-prefixed keys, misses other forms; `evaluate_expression` has a stray `print`. The `formula_callback` mechanism (adding `"@formula"` to `special_key_map`) is correct.

**Design — `evaluate_formula(expression, reader_instance, template_key) -> Any`**:

1. Extract all `@prefix:path` sub-tokens from `expression` using regex `r"@(attrs|data|eln):([^\s,)\"']+)"`.
2. Resolve each sub-token via the corresponding callback on `reader_instance`.
3. Substitute resolved values into the expression string as Python literals (using `repr()` for strings, `str()` for numbers, `"np.array(...)"` for arrays).
4. `eval(modified_expr, safe_ns)` where `safe_ns` contains:
   - `np` → `numpy`
   - `convert_unit` → pint-based conversion (see 1b)
   - `parse_datetime` → ISO 8601 normalization (see 1c)
   - `__builtins__` → `{}` (no built-ins; security mitigation — same concern as PR #252, acceptable here since config files are developer-authored, not end-user input)
5. On any exception: log warning, return `None`.

Register in `ParseJsonCallbacks.__init__`:
```python
"@formula": lambda key, value: evaluate_formula(value, self._reader_ref, key)
```

`ParseJsonCallbacks` needs a `_reader_ref` back-reference to the reader instance so `evaluate_formula` can call `get_attr`, `get_data`, `get_eln_data`.

**Config examples**:
```json
"/ENTRY/field": "@formula:np.linspace(@attrs:start, @attrs:stop, int(@attrs:n_points))",
"/ENTRY/voltage": "@formula:convert_unit(@data:raw_voltage, @attrs:voltage_unit, 'V')",
"/ENTRY/start_time": "@formula:parse_datetime(@attrs:timestamp, '%d.%m.%Y %H:%M:%S')"
```

#### 1b. `convert_unit` function in formula namespace

**Location**: `packages/pynxtools/src/pynxtools/units/conversion.py` (new file), exported from `pynxtools.units`.

```python
from pynxtools.units import ureg   # = NOMAD's ureg when NOMAD is installed
import numpy as np
from typing import Any

def convert_unit(value: Any, from_unit: str, to_unit: str) -> Any:
    """Convert value from from_unit to to_unit using pint. Returns magnitude only."""
    qty = ureg.Quantity(np.asarray(value) if hasattr(value, '__iter__') else value, from_unit)
    return qty.to(to_unit).magnitude
```

**Registry boundary**: `convert_unit` uses `pynxtools.units.ureg` — the standard NOMAD registry. It handles standard SI conversions expressible in JSON configs. Domain-specific unit aliases used inside EM/APM parsers (e.g., `nx_unitless`, `dose_rate`) are handled within the parser before values are returned to the reader — parsers always return plain Python scalars/arrays + unit strings, never `pint.Quantity` objects.

This replaces:
- XRD's `convert_quantity_to_value_units()` (can delegate to this)
- SPM's pint usage in `_get_data_unit_and_others` (once migrated)
- Standard-unit conversions in EM/APM configs (non-custom-registry conversions)

#### 1c. `parse_datetime` function in formula namespace

```python
from datetime import datetime, timezone

def parse_datetime(value: Any, fmt: str | None = None, tz: str = "UTC") -> str:
    """Parse a datetime string to ISO 8601. If fmt is None, tries fromisoformat first."""
    if fmt is None:
        return datetime.fromisoformat(str(value)).isoformat()
    dt = datetime.strptime(str(value), fmt)
    if tz == "UTC":
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.isoformat()
```

Replaces ad hoc datetime handling in raman, spm, and xps ELN parsers.

#### 1d. Fix `@attr:` / `@attrs:` inconsistency (pynxtools-xrd)

In `packages/pynxtools-xrd/src/pynxtools_xrd/reader.py`:
- `_mapping_to_config()` maps data paths to `"@attr:..."` — rename to `"@attrs:..."`.
- Verify `get_attr` is registered under `"@attrs"` in `ParseJsonCallbacks.special_key_map` (it already is in MFR, so only the XRD-side string needs fixing).

#### 1e. Documentation

Update `docs/learn/multi-format-reader.md` and `docs/how-tos/use-multi-format-reader.md` (PR #524 started this) to document:
- All `@`-prefixes and their semantics (`@attrs:`, `@data:`, `@eln:`, `@link:`, `@formula:`)
- The `@formula:` prefix: available namespace (`np`, `convert_unit`, `parse_datetime`), sub-token resolution syntax, security model
- `get_attr` / `get_data` / `get_eln_data` / `get_data_dims` callback contract with signatures
- How to set a default config file vs user override with `-c`
- The `!@...` prefix for optional-group trimming

**Test**: `python -m pytest packages/pynxtools/tests/ -q` + new dedicated formula unit tests covering: arithmetic, `convert_unit`, `parse_datetime`, fallback lists, sub-token resolution.

---

### Workpackage 2: pynxtools-raman cleanup

**File**: `packages/pynxtools-raman/src/pynxtools_raman/reader.py`

#### 2a. Remove `post_process` monkey-patching

Replace with a dispatch table keyed by detected format:

```python
_post_process_map: dict[str, Callable] = {
    ".rod": post_process_rod,
    ".txt": post_process_witec,
}

def handle_rod_file(self, filepath) -> dict:
    self._detected_format = ".rod"
    ...

def post_process(self) -> None:
    fn = self._post_process_map.get(getattr(self, "_detected_format", None))
    if fn:
        fn(self)
```

#### 2b. Fix `get_eln_data` heuristic

Replace the NXclass case-stripping heuristic with a two-pass lookup matching XPS:

```python
def get_eln_data(self, key: str, path: str) -> Any:
    if key in self.eln_data:
        return self.eln_data[key]
    # Strip entry instance name and retry
    generic_key = re.sub(r"(/ENTRY)\[[^\]]+\]", r"\1", key)
    return self.eln_data.get(generic_key)
```

#### 2c. Drop `COLLECTION[unused_rod_keys]`

Remove the dump of unmatched rod keys into an unconstrained NXcollection. Log skipped keys at DEBUG level. Users who need uncaptured fields should extend the config.

**Test**: `python -m pytest packages/pynxtools-raman/tests/ -q`

---

### Workpackage 3: pynxtools-spm migration to MFR

#### Step A: Wire SPM into MFR pipeline

**File**: `packages/pynxtools-spm/src/pynxtools_spm/reader.py`

Change `SPMReader(BaseReader)` → `SPMReader(MultiFormatReader)`. Register extension handlers:

```python
self.extensions = {
    ".yml": self.handle_eln_file,
    ".yaml": self.handle_eln_file,
    ".json": self.set_config_file,
    ".sxm": self.handle_spm_file,
    ".dat": self.handle_spm_file,
    ".sm4": self.handle_spm_file,
}
```

`handle_spm_file(file_path)`: reads ELN for `experiment_technique`, selects formatter class, stores in `self._formatter`. Returns `{}`.

`post_process()`: calls `self._formatter.get_nxformatted_template()` which writes directly to `self.template`. MFR's `fill_from_config` does not run (no JSON config_file set at MFR level — the formatter drives its own YAML config walk).

Remove the manual None-filtering loop in `read()` — MFR handles None stripping.

#### Step B: Migrate SPM configs to MFR flat JSON (per formatter)

**Translation mapping** for each nested YAML construct:

| SPM nested YAML | MFR flat JSON |
|-----------------|---------------|
| `field: {raw_path: "/path"}` | `"parent/field": "@data:/path"` |
| `field: {raw_path: "/path", "@units": "/path/unit"}` | `"parent/field": "@data:/path"` + `"parent/field/@units": "@data:/path/unit"` |
| `raw_path: ["/p1", "/p2"]` (fallback list) | `"['@data:/p1', '@data:/p2']"` |
| `@default_link: /ENTRY/...` | `@link:/ENTRY/...` |
| NXdata group description dict | `post_process()` or future `@nxdata:` construct |
| `_grp_to_func` special group | Extract to `post_process()` method |
| arithmetic on raw value | `@formula:convert_unit(...)` or `@formula:np.expr(...)` |

**Per-formatter migration steps** (apply to each of the four formatters independently):

For each formatter (`NanonisSxmSTM`, `OmicronSM4STM`, `NanonisSxmAFM`, `NanonisDatSTS`):

1. Write a flat JSON config `config/<formatter_name>.json` translating all `raw_path` end-dicts that do not require `_grp_to_func` dispatch.
2. Implement `get_data(key, path)` and `get_attr(key, path)` on the reader to look up in `self.raw_data` (populated by `SPMParser`). For paths with unit conversion, use `@formula:convert_unit(...)` in the config.
3. Move the `_grp_to_func` special-group logic into `post_process()` with explicit method dispatch (no longer driven by config key prefixes).
4. For NXdata group construction (`_nxdata_grp_from_conf_description`): keep in `post_process()` for now, calling the same method with hard-coded group descriptions. Long-term candidate for a `@nxdata:` config construct in MFR.
5. Replace `@default_link:` with `@link:` in the JSON config.
6. Validate: NXS output before/after migration is byte-equivalent for the same input file.

After all formatters are migrated, `SPMformatter.walk_though_config_nested_dict` and `_get_data_unit_and_others` can be removed. The `SPMformatter` base class becomes a thin shim that populates `self.raw_data`.

**Test**: `python -m pytest packages/pynxtools-spm/tests/ -q` — all existing tests must pass after each step before proceeding to the next formatter.

---

### Workpackage 4: pynxtools-em migration

#### Existing pint mapping DSL

EM's `concepts/mapping_functors_pint.add_specific_metadata_pint(cfg, src_data, id, template)` takes a Python dict config where values are `(src_path, ureg.Unit, target_unit)` tuples and handles type normalization + unit conversion + dtype coercion + template write in one call. This is functionally equivalent to `@formula:convert_unit(...)` in JSON configs. The migration replaces the Python tuple DSL with JSON configs using `@formula:`.

#### Architecture target

```
EMReader(MultiFormatReader)
  supported_nxdls = ["NXem"]

  __init__:
    extensions = {
      ".yml/.yaml": handle_eln_file,
      ".json": set_config_file,
      ".tiff/.tif": handle_tiff_file,
      ".h5/.hdf5/.nxs": handle_hdf5_file,
      ".png": handle_png_file,
    }

  handle_<format>_file(path):
    meta, data = <FormatParser>(path).parse()   # no template writes
    self.metadata.update(meta)
    self.data.update(data)
    return {}

  handle_eln_file(path):
    self.eln_data = parse_yml(path, convert_dict=EM_CONVERT_DICT, parent_key="/ENTRY[entry1]")
    return {}

  get_entry_names() -> ["entry1"]
  get_attr(key, path) -> self.metadata.get(path)
  get_data(key, path) -> self.data.get(path)
  get_eln_data(key, path) -> self.eln_data.get(key) or self.eln_data.get(path)

  config/NXem_tfs.json           # one JSON config per tech-partner format
  config/NXem_bruker.json
  config/NXem_edax_oim.json
  config/NXem_edax_apex.json
  config/NXem_oxford.json
  config/NXem_zeiss.json
  config/NXem_jeol.json
  config/NXem_hitachi.json
  config/NXem_point_electronic.json
  config/NXem_tescan.json
  config/NXem_fei_legacy.json
  config/NXem_velox.json
  config/NXem_gatan.json
  config/NXem_mrc.json
  config/NXem_mtex.json
  config/NXem_nion.json
  config/NXem_diffraction_pattern_set.json
  config/NXem_protochips.json
```

#### Entry naming

`get_entry_names()` returns `["entry1"]` to match EM's current `entry_id = 1` convention and maintain backward compatibility with existing parsed NXS files.

#### Refactoring each parser

**Current pattern** (Python DSL + template writes):
```python
class TfsTiffParser:
    def parse(self, template: dict) -> None:
        cfg = {"/ENTRY[entry1]/field": ("src/path", ureg.meter, ureg.nanometer)}
        add_specific_metadata_pint(cfg, self.flat_dict_meta, entry_id, template)
```

**Target pattern** (flat dict output, no template writes):
```python
class TfsTiffParser:
    def parse(self) -> tuple[dict, dict]:
        """Return (metadata, data) — no template writes."""
        return self._extract_metadata(), self._extract_data()

    def _extract_metadata(self) -> dict[str, Any]:
        return {
            "instrument/pixel_width": self.flat_dict_meta["EScan/PixelWidth"],
            "instrument/pixel_width/@units": "m",   # unit as string, never pint.Quantity
            ...
        }

    def _extract_data(self) -> dict[str, Any]:
        return {"image": self._get_image_array(), ...}
```

Unit conversion expressed in JSON config:
```json
"/ENTRY[entry1]/instrument/pixel_width": "@formula:convert_unit(@attrs:instrument/pixel_width, @attrs:instrument/pixel_width/@units, 'nm')",
"/ENTRY[entry1]/instrument/pixel_width/@units": "nm"
```
Or pass-through when already in target units:
```json
"/ENTRY[entry1]/instrument/pixel_width": "@attrs:instrument/pixel_width",
"/ENTRY[entry1]/instrument/pixel_width/@units": "@attrs:instrument/pixel_width/@units"
```

#### `NxEmAppDef` → `setup_template()`

`NxEmAppDef.parse(template)` populates static NXem required fields. In MFR this becomes `setup_template()` returning those static key-value pairs.

#### `EmUseCaseSelector` → format detection in handlers

The file-combination routing logic moves into MFR's handler dispatch. Each handler does its own `is_mainfile()`-style check or relies on extension registration. `processing_order` controls priority.

Parsers with required sidecar files (`JeolTiffParser`, `HitachiTiffParser`, `RsciioMrcParser`) need a two-file registration approach:
- Register both extensions; on first file, store path; on second file, trigger parse with both.
- Or: override `post_process()` to detect when both files are present and dispatch.

#### `NxEmDefaultPlotResolver` and `NxEmAtomTypesResolver`

Move into `post_process()` instead of being called directly in `read()`.

#### Migration order (by complexity, lowest first)

1. `FeiLegacyTiffParser` — simplest TIFF format, minimal metadata
2. `TfsTiffParser` — well-studied, used as reference
3. `ZeissTiffParser`, `PointElectronicTiffParser`, `HitachiTiffParser` — TIFF family
4. `TescanTiffParser` — optional sidecar
5. `JeolTiffParser` — required sidecar (two-file handling)
6. `ProtochipsPngSetParser` — PNG set
7. `RsciioVeloxParser`, `RsciioGatanParser`, `RsciioMrcParser` — rsciio-backed readers
8. `HdfFiveBrukerEspritParser`, `HdfFiveEdaxOimAnalysisParser`, `HdfFiveEdaxApexParser`, `HdfFiveOxfordInstrumentsParser` — HDF5 EBSD formats
9. `NxEmNxsMtexParser`, `NionProjectParser`, `DiffractionPatternSetParser` — community formats

#### Validation requirement

**Output equivalence**: for each parser, the NXS file produced by the migrated reader must contain identical datasets and attributes to pre-migration output. Establish reference NXS files before migration; compare with `h5diff` after.

**Test**: `python -m pytest packages/pynxtools-em/tests/ -q`

---

### Workpackage 5: pynxtools-apm migration

#### Existing pint DSL

APM's `mapping_functors_pint.py` is nearly identical to EM's. `IfesReconstructionParser` already uses `pint.Quantity` objects extensively (e.g., `xyz = ureg.Quantity(..., "nm")`), then writes `template[...] = xyz.magnitude` and `template[...+"/@units"] = f"{xyz.units}"`. This is already the cleanest structure — value and unit separated — making it the easiest to migrate.

#### Architecture target

```
APMReader(MultiFormatReader)
  supported_nxdls = ["NXapm"]

  __init__:
    extensions = {
      ".yml/.yaml": handle_eln_file,
      ".json": set_config_file,
      ".pos/.epos/.apt/.rng/.rrng/...": handle_data_file,
    }

  get_entry_names() -> ["entry1"]
  get_attr(key, path) -> self.metadata.get(path)
  get_data(key, path) -> self.data.get(path)
  get_eln_data(key, path) -> self.eln_data.get(key) or self.eln_data.get(path)

  config/NXapm_ifes_reconstruction.json
  config/NXapm_ifes_ranging.json
  config/NXapm_eln.json
```

#### Refactoring each parser

**`IfesReconstructionParser`**: Already returns pint Quantity objects — refactor to return flat dicts:
```python
def parse(self) -> tuple[dict, dict]:
    xyz = ...  # pint Quantity
    return (
        {"reconstruction/xyz/@units": str(xyz.units)},
        {"reconstruction/xyz": xyz.magnitude}
    )
```
Config:
```json
"/ENTRY[entry1]/reconstruction/xyz": "@data:reconstruction/xyz",
"/ENTRY[entry1]/reconstruction/xyz/@units": "@attrs:reconstruction/xyz/@units"
```

**`IfesRangingDefinitionsParser`**: Same pattern — extract to flat dicts, write JSON config.

**`NxApmNomadOasisElnSchemaParser`**: Becomes `handle_eln_file()` with appropriate `CONVERT_DICT`. Existing YAML parsing logic is nearly identical to `parse_yml()`.

**`NxApmNomadOasisConfigParser`**: Becomes a registered JSON config file (the YAML config is user-customizable — equivalent to the `-c` flag). Map its schema to JSON config format.

**`NxApmAppDef.parse(template)`**: Becomes `setup_template()` returning static fields.

#### `apm_default_plot_generator` and `remove_uninstantiated_sensors`

Move into `post_process()`.

#### `mapping_functors_pint.py` and the custom unit registry (both EM and APM)

After migration, `add_specific_metadata_pint` is replaced by JSON configs with `@formula:convert_unit(...)`. `mapping_functors_pint.py` can then be removed from both packages.

**The `pint_custom_unit_registry.py` must stay in each plugin — it must NOT be consolidated into `pynxtools.units`.** The custom registry imports `pynxtools.units.ureg` (which is NOMAD's `ureg` when NOMAD is installed) and mutates it by adding domain-specific unit aliases (`Hours`, `Secs`, `Volt`, `um2`, `nx_unitless`, `nx_dimensionless`, `nx_any`, `dose_rate`). Merging these into `pynxtools.units` would mean the `pynxtools` unit registry deviates from NOMAD.

The `convert_unit()` function (WP1b) uses `pynxtools.units.ureg` for standard SI conversions. For conversions requiring EM/APM-specific aliases (e.g., `dose_rate` → SI), the parser resolves the value internally and returns a plain Python value + SI unit string — never a `pint.Quantity` object reaching the reader.

#### Validation requirement

Same as EM: output equivalence against pre-migration reference NXS files.

**Test**: `python -m pytest packages/pynxtools-apm/tests/ -q`

---

## Phased roadmap

The workpackages above are the full specification. The phases below sequence them into deliverable increments — each phase leaves the ecosystem in a working state.

### Phase 1 — Foundation (prerequisite for everything else)

**WP1a + WP1b + WP1c + WP1d** in pynxtools core. Delivers:
- `@formula:` prefix in MFR with `convert_unit`, `parse_datetime`, and numpy in the eval namespace
- `@attr:` → `@attrs:` fix in XRD

No plugin changes yet. All existing tests continue to pass unchanged.

**Prerequisite for**: All subsequent workpackages that use `@formula:` in configs.

### Phase 2 — MFR-aligned plugin cleanup

**WP2** (raman) + **WP1e** (docs). Self-contained. Can run in parallel with Phase 1 delivery. Delivers clean reference implementations of the MFR pattern across the aligned group.

### Phase 3 — SPM wired into MFR, config migration started

**WP3A** first (wire SPM into MFR pipeline — preserves all existing YAML configs and tests unchanged). Then **WP3B** formatter-by-formatter config migration, starting with the simplest formatter.

Dependency: WP1 must be complete before WP3B uses `@formula:convert_unit`.

### Phase 4 — EM migration (parser-by-parser)

**WP4** in migration order above. Each parser is migrated independently with validation against reference NXS output before merging. Can be parallelized across multiple contributors once the first parser establishes the reference pattern.

Dependency: WP1 (formula eval for unit conversion in configs).

### Phase 5 — APM migration

**WP5** in parallel with or immediately after Phase 4.

Dependency: WP1. `mapping_functors_pint.py` removal from both packages happens only after WP4 and WP5 are both complete.

---

## What is explicitly out of scope

- **XAS** (`pynxtools-xas`): currently broken (`handle_xy_file` calls non-existent method). Skip until the implementation is stabilized.
- **Nested YAML as a second MFR config format**: rejected. All plugins migrate to flat JSON.
- **Multi-entry support for EM/APM**: they hardcode `entry_id = 1` / `get_entry_names() -> ["entry1"]`; this convention is preserved for output compatibility.

---

## Critical files

| Workpackage | Files |
|-------------|-------|
| **WP1a** (formula eval) | `pynxtools/src/pynxtools/dataconverter/readers/multi/reader.py` |
| **WP1b** (convert_unit) | `pynxtools/src/pynxtools/units/conversion.py` (new), `units/__init__.py` (export) |
| **WP1d** (xrd typo) | `pynxtools-xrd/src/pynxtools_xrd/reader.py` |
| **WP1e** (docs) | `pynxtools/docs/learn/multi-format-reader.md`, `docs/how-tos/use-multi-format-reader.md` |
| **WP2** (raman) | `pynxtools-raman/src/pynxtools_raman/reader.py`, `rod/rod_reader.py`, `witec/witec_reader.py` |
| **WP3A** (spm wire) | `pynxtools-spm/src/pynxtools_spm/reader.py` |
| **WP3B** (spm configs) | `pynxtools-spm/src/pynxtools_spm/nxformatters/base_formatter.py` |
|  | `nxformatters/nanonis/nanonis_sxm_stm.py`, `nanonis_sxm_afm.py`, `nanonis_dat_sts.py` |
|  | `nxformatters/omicron/omicron_sm4_stm.py` |
|  | `pynxtools-spm/src/pynxtools_spm/config/` (new JSON files, one per formatter) |
| **WP4** (em) | `pynxtools-em/src/pynxtools_em/reader.py` |
|  | `pynxtools-em/src/pynxtools_em/parsers/*.py` (all parsers refactored) |
|  | `pynxtools-em/src/pynxtools_em/config/NXem_*.json` (new, one per parser) |
|  | `pynxtools-em/src/pynxtools_em/concepts/mapping_functors_pint.py` (remove) |
|  | `pynxtools-em/src/pynxtools_em/utils/io_case_logic.py` (remove or simplify) |
| **WP5** (apm) | `pynxtools-apm/src/pynxtools_apm/reader.py` |
|  | `pynxtools-apm/src/pynxtools_apm/parsers/*.py` (all parsers refactored) |
|  | `pynxtools-apm/src/pynxtools_apm/config/NXapm_*.json` (new, one per parser) |
|  | `pynxtools-apm/src/pynxtools_apm/concepts/mapping_functors_pint.py` (remove) |
