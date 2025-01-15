# Open PRs and issues in NIAC repo

## strictly necessary PRs and issues

These PRs/issues _must_ be addresed before we can go towards the discussion of the application definitions.

### For MPES

| PR/Issue | Name | Link | Affected Classes/Files | Status | Blocked By | Modifications Needed |
|--------------------------|--------------------------------------------------|------------------------------------------------------------------------------------------|------------------------------------------------------------------------------------------------------------------|-----------------------------------------|-----------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| PR #1408 | Additions and clarifications in NXbeam | [#1408](https://github.com/nexusformat/definitions/pull/1408) | NXbeam  | Voted, but not enough votes | | Add `NXbeam_element`, use `next/previous_element` | 
| PR #1410 | Add target attribute to NXdata | [#1410](https://github.com/nexusformat/definitions/pull/1410) | NXdata | Discussed, waiting for vote | | Fix CI/CD |
| PR #1413 | several new base classes in NXsample and NXsample_component | [#1413](https://github.com/nexusformat/definitions/pull/1413) | NXsample, NXsample_component, NXsample_component_set, NXsubstance, NXunit_cell, NXsingle_crystal, NXrotation_set | to be discussed, , `*_set` must be refactored | | move `NXsample_component`,  `NXsubstance` to contributed (#1427), keep only `NXactivity`, `NXfabrication`, `NXhistory` in `NXsample` for this PR, move `NXunit_cell`, `NXsingle_crystal` to `NXem` proposal |
| PR #1415 | use NXcoordinate_system together with NXtransformations | [#1415](https://github.com/nexusformat/definitions/pull/1415) | NXcoordinate_system, NXcoordinate_system_set, NXtransformation | to be discussed, `*_set` must be refactored | | |
| PR #1419 | additional base classes in NXinstrument | https://github.com/nexusformat/definitions/pull/1419 | NXactivity, Nxcalibration, NXhistory, NXinstrument, NXnote, NXresolution | awaiting final review |
| PR #1519 | move NXlens_em  to base_classes | https://github.com/nexusformat/definitions/pull/1519 | NXlens_em, NXsource | discussed, awaiting review/vote  | | |
| PR #1528 | move NXpid to base_classes | https://github.com/nexusformat/definitions/pull/1528 | NXpid, NXactuator | no discussion yet |
| issue #326 (FAIRmat repo) | NXmpes: NXentry/NXinstrument/NXdetector is required, but none of its sub-elements | https://github.com/FAIRmat-NFDI/nexus_definitions/issues/326 | NXmpes | to be discussed (with Laurenz) |


### For EM (additional)

| PR/Issue | Name | Link | Affected Classes/Files | Status | Blocked By | Modifications Needed |
|--------------------------|--------------------------------------------------|------------------------------------------------------------------------------------------|------------------------------------------------------------------------------------------------------------------|-----------------------------------------|-----------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| PR #1423 | proposal on EM | https://github.com/nexusformat/definitions/pull/1423 | @mkuehbach please fill here | to be discussed | #1408, #1413, #1415, #1419, #1519, #1528 | add `NXunit_cell`, `NXsingle_crystal`

@mkuehbach please add to this table if needed

### For APM (additional)

| PR/Issue | Name | Link | Affected Classes/Files | Status | Blocked By | Modifications Needed |
|--------------------------|--------------------------------------------------|------------------------------------------------------------------------------------------|------------------------------------------------------------------------------------------------------------------|-----------------------------------------|-----------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| PR #1422 | proposal on atom probe microscopy | https://github.com/nexusformat/definitions/pull/1422 | @mkuehbach please fill here | to be discussed | #1408, #1413, #1415, #1419, #1519, #1528 |

@mkuehbach please add to this table if needed

### For computational geometry

| PR/Issue | Name | Link | Affected Classes/Files | Status | Blocked By | Modifications Needed |
|--------------------------|--------------------------------------------------|------------------------------------------------------------------------------------------|------------------------------------------------------------------------------------------------------------------|-----------------------------------------|-----------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| PR #1421 | base classes to describe computational geometry | https://github.com/nexusformat/definitions/pull/1421 | @mkuehbach please fill here | to be discussed |
| PR #1532 | non-FAIRmat constructive solid geometry | https://github.com/nexusformat/definitions/pull/1421 | NXcsg, NXquadric, NXsolid_geometry | in discussion |

@mkuehbach please add to this table if needed

## helpful PRs and issues

These PRs are _not_ necessary for the application definitions, but would be definitely nice to have beforehand:

| PR/Issue | Name | Link | Affected Classes/Files | Status | Blocked By | Modifications Needed |
|--------------------------|--------------------------------------------------|------------------------------------------------------------------------------------------|------------------------------------------------------------------------------------------------------------------|-----------------------------------------|-----------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| PR #1521 | Allow for open enumerations | https://github.com/nexusformat/definitions/pull/1521 | nxdl.xsd, dev_tools/docs/nxdl.py, NXobject, NXsensor, NXsource, any validator | NIAC requested, to be discussed/voted on |
| issue #1523 | Clarify if a field in a specified NXdata is a AXISNAME or DATA | https://github.com/nexusformat/definitions/issues/1523 | NXdata? | no discussion yet |

## not needed at the moment

These PRs/issues could also be discussed at a later stage:

| PR/Issue | Name | Link | Affected Classes/Files | Status | Blocked By | Modifications Needed |
|--------------------------|--------------------------------------------------|------------------------------------------------------------------------------------------|------------------------------------------------------------------------------------------------------------------|-----------------------------------------|-----------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| #1525 | NXcomponent as a parent base class | https://github.com/nexusformat/definitions/pull/1525 | NXcomponent, lots of base classes extending NXcomponent | requested by NIAC, not discussed |
| #1428 | changes to dev_tools, groupings in manual | https://github.com/nexusformat/definitions/pull/1428 | dev_tools, manuals | not discussed |
| PR #1412 | new fields for experiment description in NXentry and NXsubentry | https://github.com/nexusformat/definitions/pull/1412 | NXentry, NXsubsentry | not discussed with NIAC | | deprecate `*_identifier` and add `identifier_*`, make NXsubsentry extend NXentry |