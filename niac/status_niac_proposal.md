# Open PRs and issues in NIAC repo

## strictly necessary PRs and issues

These PRs/issues _must_ be addresed before we can go towards the discussion of the application definitions.

### For MPES

| PR/issue    | name | link | affected classes/files | status | blocked by |
| -------- | ------- | ------- | ------- | ------- |  ------- |
| PR #1408 | additions and clarifications in NXbeam | https://github.com/nexusformat/definitions/pull/1408 | NXbeam | voted, but not enough votes | 
| PR #1410 | add reference attribute to NXdata | https://github.com/nexusformat/definitions/pull/1410 | NXdata | discussed, waiting for vote 
| PR #1413 | several new base classes in NXsample and NXsample_component | https://github.com/nexusformat/definitions/pull/1413 | NXsample, NXsample_component, NXsample_component_set, NXsubstance, NXunit_cell, NXsingle_crystal, NXrotation_set | to be discussed, , `*_set` must be refactored | #1419
| PR #1415 | use NXcoordinate_system together with NXtransformations | https://github.com/nexusformat/definitions/pull/1415 | NXcoordinate_system, NXcoordinate_system_set, NXtransformation | to be discussed, `*_set` must be refactored |
PR #1419 | additional base classes in NXinstrument | https://github.com/nexusformat/definitions/pull/1419 | NXactivity, Nxcalibration, NXhistory, NXinstrument, NXnote, NXresolution | awaiting final review |
| PR #1519 | move NXlens_em  to base_classes | https://github.com/nexusformat/definitions/pull/1519 | NXlens_em, NXsource | discussed, awaiting review/vote |
| PR #1528 | move NXpid to base_classes | https://github.com/nexusformat/definitions/pull/1528 | NXpid, NXactuator | no discussion yet
| PR #1424 | proposal on photoemission spectroscopy | https://github.com/nexusformat/definitions/pull/1424 | NXmpes, NXmpes_arpes, NXxps, NXfit, NXpeak, NXfit_function, NXfit_background, NXactuator, NXelectronanalyser, NXcollectioncolumn, NXenergydispersion, NXspindispersion, NXmanipulator | to be discussed | #1408, #1410, #1413, #1415, #1419, #1519, #1528

### For EM (additional)

| PR/issue    | name | link | affected classes/files | status | blocked by |
| -------- | ------- | ------- | ------- | ------- |  ------- |
| PR #1423 | proposal on EM | https://github.com/nexusformat/definitions/pull/1423 | @mkuehbach please fill here | to be discussed | #1408, #1413, #1415, #1419, #1519, #1528


@mkuehbach please add to this table if needed

### For APM (additional)

| PR/issue    | name | link | affected classes/files | status | blocked by |
| -------- | ------- | ------- | ------- | ------- |  ------- |
| PR #1422 | proposal on atom probe microscopy | https://github.com/nexusformat/definitions/pull/1422 | @mkuehbach please fill here | to be discussed | #1408, #1413, #1415, #1419, #1519, #1528 |

@mkuehbach please add to this table if needed

### For computational geometry

| PR/issue    | name | link | affected classes/files | status | blocked by |
| -------- | ------- | ------- | ------- | ------- |  ------- |
| PR #1421 | base classes to describe computational geometry | https://github.com/nexusformat/definitions/pull/1421 | @mkuehbach please fill here | to be discussed |
| PR #1532 | non-FAIRmat constructive solid geometry | https://github.com/nexusformat/definitions/pull/1421 | NXcsg, NXquadric, NXsolid_geometry | in discussion |

@mkuehbach please add to this table if needed

## helpful PRs and issues

These PRs are _not_ necessary for the application definitions, but would be definitely nice to have beforehand:

| PR/issue     | name | affected classes/files | link | status |
| -------- | ------- | ------- | ------- | ------- |
| PR #1521 | Allow for open enumerations | https://github.com/nexusformat/definitions/pull/1521 | nxdl.xsd, dev_tools/docs/nxdl.py, NXobject, NXsensor, NXsource, any validator | NIAC requested, to be discussed/voted on |
| issue #1523 | Clarify if a field in a specified NXdata is a AXISNAME or DATA | https://github.com/nexusformat/definitions/issues/1523 | NXdata? | no discussion yet |

## not needed at the moment

These PRs/issues could also be discussed at a later stage:

| PR/issue | name | affected classes/files | Link | status |
| -------- | ------- | ------- | ------- | ------- |
| #1525 | NXcomponent as a parent base class | https://github.com/nexusformat/definitions/pull/1525 | NXcomponent, lots of base classes extending NXcomponent | requested by NIAC, not discussed |
| #1428 | changes to dev_tools, groupings in manual | https://github.com/nexusformat/definitions/pull/1428 | dev_tools, manuals | not discussed |