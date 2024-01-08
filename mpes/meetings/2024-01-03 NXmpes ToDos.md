## Update mpes example
## NXresolution in NXmpes
- PR: https://github.com/FAIRmat-NFDI/nexus_definitions/pull/124
- Spelled out names (e.g., `energy_resolution`, `spatial_resolution`) or just `(NXresolution)`
    - Remove named fields from NXelectronanalyser and keep them in NXmpes
- `resolution(NXdata)` or `resolution(NX_FLOAT)` with `resolution_errors(NX_FLOAT)`
    - keep `resolution(NX_FLOAT)` with `resolution_errors(NX_FLOAT)`
- Status: <span style="color:green">merged</span>
## Extend energy scan mode in NXenergydispersion
- PR: https://github.com/FAIRmat-NFDI/nexus_definitions/pull/127
- missing docs for tranmission and jittered/dither modes
    - Basic explanation by Laurenz, discuss at workshop
- Status: <span style="color:green">merged</span>
- ## Use new base classes for NXsample in NXmpes
- PR: https://github.com/FAIRmat-NFDI/nexus_definitions/pull/68
- What to do with NXsensor?
    - Move NXsensor groups into NXmanipulator
- Status: <span style="color:orange">under review</span>
## Should we remove or keep sample history?
- PR: https://github.com/FAIRmat-NFDI/nexus_definitions/pull/82
    - We keep it for now and will remodel it in the future with linking and base class inheritance
- - Status: <span style="color:green">PR closed in favor of #68</span>
## Physical quantities as axis names
- PR: https://github.com/FAIRmat-NFDI/nexus_definitions/pull/92
- explicitly spelled out axis names vs. `AXISNAME_depends`
    - add `AXISNAME_depends` to `NXdata`
    - add `NXdata_mpes` with explicitly spelled axis names
    - remove from NXmpes, keep energy axis
- Status: <span style="color:orange">under review</span>

## NXsource in NXmpes
- docstring
    - clarify what `source_TYPE` does
    - change first sentence
- enumeration of probe
    - Remove
- Make NXsource recommended
- Status: <span style="color:green">done</span>

## NXcollectioncolumn
- scheme
    - spatial_dispersive, angular_dispersive, non_dispersive
    - Add new fields: spatial_acceptance, angular_acceptance (optional)
- Status: <span style="color:gree">done</span>

## Documentation
- Two basic tutorials
- Status: <span style="color:orange">in progress</span>


## Sub-appdefs
- ARPES
    - merge until workshop
- Liquidjet
- XPS
    - change once MPES is merged
- PEEM
    - discuss during workshop
- NXphotoemission
    - discuss during workshop
- Status: <span style="color:red">tbd</span>
 
## General
- Fermi level referencing? Not the same as E-Ef!
    - Add vacuum level to reference_peak in NXprocess/energy_referencing
    - Status: <span style="color:green">done</span> 
- mpes-refactor rebase, solve ci/cd issues
- Merge + create static from mpes-refactor to latest

## Future ideas
- Base class inheritance
- Base class of a generic scan
- Connection of terms to ontology concepts