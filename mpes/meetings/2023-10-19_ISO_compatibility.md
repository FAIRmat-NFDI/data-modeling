
# ISO compatibility

## Points to discuss
 - Relevant standards: https://datashare.mpcdf.mpg.de/s/rxPOpfm9OsEGfUc
- Follow ISO 18155 Naming structure documentation <span style="color:green">discussion</span>
    - ISO 18115:: use the names of techniques/terms
    - Get copy of ISO Standard (ISO 18115-1:2023) (+Ontologies??) and work through it. What could we use from it and how?
- shall we support an extra field for this? <span style="color:green">discussion</span>
- Follow the "Minimum reporting requirement" -> there is an ISO standard https://www.iso.org/standard/66294.html?browse=tc <span style="color:orange">documentation</span>
 <span style="color:purple">research</span>
 
## Proposal for implementing references in yaml 
ISO example:
```yaml
energy_referencing(NXcalibration):
  exists: optional
  xref:
    spec: ISO 18115-1:2023
    term: 12.74
    url: https://www.iso.org/obp/ui/en/#iso:std:iso:18115:-1:ed-3:v1:en:term:12.74
    
  doc: |
    For energy referencing, the measured ...
```
This should be converted in nyaml2nxdl to show up at the end of the docstring as:
```
    This concept is related to term `12.74`_ ff. of the ISO 18115-1:2023 standard.
.. _12.74: https://www.iso.org/obp/ui/en/#iso:std:iso:18115:-1:ed-3:v1:en:term:12.74
```

Ontology example:
```yaml
xref:
  spec: OEO
  term: time series
  url: http://openenergy-platform.org/ontology/oeo/oeo-shared/OEO_00030034
```


  

# Decisions
- Propose to NIAC to support relationships between a given concept and a concept defined somewhere else (e.g., in an ontology) 
- Rule: In NXDL, you need to put a specific text at the end of the docstring to indicate a relationships to a foreign concept.
    - in nyaml, add field `xref` like this:
    ```yaml
    xref:
      spec: <spec>
      term: <term>
      url: <url>
    ```
    - in nyaml2nxdl, this should be converted at the end of the docstring to: 
    ```
        This concept is related to term `<term>`_ of the <spec> standard.
    .. _<term>: <url>
    ```
- We drop the convenience that you do not need to write (NX_CHAR) in nyaml (in order to avoid confusing the data field `xref(NX_CHAR)` and the control `xref`).

# ToDo
- Add `xref` control in nyaml2nxdl
- Remove the convenience in nyaml2nxdl that you do not need to write `(NX_CHAR)` in nyaml


# Backlog
- Add a more detailed description of control keys (`exists`, `enumeration`, `unit`, `xref`, ...) to nyaml2nxdl (see [here](https://github.com/FAIRmat-NFDI/nexus_definitions/tree/fairmat/dev_tools/nyaml2nxdl))