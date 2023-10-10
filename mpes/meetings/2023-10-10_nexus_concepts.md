# Points to discuss

## Conceptual, NeXus-related, open questions
- How to split and assemble parts of an application definitions? Who is responsible for merging?
- Scientists vs. vendor point-of-view 
    - How do we allow different sources to notify what exact version of NeXus they used for the split part?
    - mapping tool / wizard / assemble too (in NOMAD, like the ELN examples, but also support external solution) `new feature`
    - how to handle different setups and their different requirements? 
- Should we make a base class of a generic scan? `new feature`
    - NXscan (like workflow to describe sequence of actions/steps) 
    - Where do we store details of energy scan modes? E.g. jittered/dithered energy mode?
- Multiple inheritance, example: time_resolved and NXelectron_detection / NXphotoemission + spectroscopic properties
    - From the discussion: We could just not call it photoemission on the top level but rather something like `NXelectron_detection` from which we branch `NXphotoemission` -> `NXmpes` / -> `NXpeem` and `NXelectron_spectrosopy` -> `NXaes`, `NXleem`,...
- Possibility to express two fields as the same concept in the application definition. [Here](https://github.com/FAIRmat-NFDI/nexus_definitions/pull/72#issuecomment-1750608506) is an example:
```yaml=
(NXprocess):
  transmission_correction(NXcalibration):
    transmission_function(NXdata):
      exists: recommended
      isSameAs: NXcalibration/mapping
      # here should be the identifier that 
      # this is the same concept as _mapping_ defined in NXcalibration
      
(NXcalibration):
  mapping(NXdata):
```
- How to proceed with base class inheritance? Can we fix transitional design principles?

# Decisions
- We want to build documentation and examples for assembly of a file according to an appdef from multiple files
- The "main" file is the file which complies to the `NXmpes` application definiton

# ToDos
- Build an example for merging an NXmpes file from different parts of the appdef (e.g., NXmpes/NXinstrument/NXelectronanalyser) with solving merge conflicts (e.g. we have `/entry/instrument/beam` in two files which should be converted to `beam1`/`beam2` or `beam_pump`/`beam_probe`)


# Backlog
- Checking if all required/recommeded elements are present and generate a list of missing parts in `pynxtools`
- Add verification
- Build an example for top-level recipe above NXentry. There are also time-dependent graph base classes prepared by Markus Kühbach which might help.