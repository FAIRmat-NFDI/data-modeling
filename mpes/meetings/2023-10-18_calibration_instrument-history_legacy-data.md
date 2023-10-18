# Calibration, instrument history, legacy data discussion

## Points to discuss
- calibration and calibration-history, or instrument history <span style="color:red">new feature</span>
<span style="color:green">discussion</span>
    - NXprocedure and/or NXinstrument_history? Similar to NXsample_history?
    - Instrument history: calibrations, lifetime, ... 
    - How do we deal which a history of instrument calibration? Do we only give the latest? Is there some sort of quality factor depending on how much time has passed since the last calibration? <span style="color:green">discussion</span>
- There was the request to have an NXcalibration class to be attached to e.g. any voltage or so, which can contain calibration data, and e.g. also a DOI link. <span style="color:blue">add from existing</span>
- devise a generic NXresolution base class, that allows specifying how the resolution is determined, and instanciating this for the respective resolutions. make those recommended <span style="color:red">new feature</span> <span style="color:green">discussion</span>
- Legacy data management: what are current standard procedures? <span style="color:purple">research</span>

# Decisions
- We use the proposed NXresolution in the NXmpes refactor branch
- We consider a nexus file as a snapshot of an experimental setup, so it should not contain all possible histories but it may contain links/references to these histories (e.g., in nomad).
    - We keep NXprocess based NXcalibration
    - We want to discuss whether to remove sample history in a PR (also stating that we consider nexus as a snapshot)

# ToDos
- Use @target instead of NXlink in NXresolution
- Add doi field to NXcalibration to link to external calibration
- Remove sample history in a PR and discuss there ([this](https://github.com/FAIRmat-NFDI/nexus_definitions/pull/56) is the PR introducing sample history)


# Backlog
- Add proper resolution for upper case variables (see nexus [documentation](https://manual.nexusformat.org/defs_intro.html#index-8) of this)
    - Add documentation + formalism!
    - `NAME_name` should use `NAME` as variable part
    - For multiple required fields, e.g., `NAME_one` and `NAME_two` the fields should be named the same. Typical example values + error, e.g., `AXIS` and `AXIS_error` (see nexusformat.org:NXdata documentation)
    - Also the upper-case notation should allow variable names, e.g., `NAME`