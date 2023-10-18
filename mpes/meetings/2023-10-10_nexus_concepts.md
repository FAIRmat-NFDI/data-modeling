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
- How to proceed with base class inheritance? Can we fix transitional design principles? See discuussion here: https://github.com/FAIRmat-NFDI/nexus_definitions/pull/66

## Comments
Description of links: [Nxdl.xsd](https://github.com/nexusformat/definitions/blob/df84535e6b053e7c8c17d2ff6d732d3dca4d879f/nxdl.xsd#L544C11-L544C11)


Markus:
- Is a base class still the same if I leave one field out?


# Decisions
- We want to build documentation and examples for assembly of a file according to an appdef from multiple files
- The "main" file is the file which complies to the `NXmpes` application definition
- We want to include a concept in NeXus describing `isSameAs` relationships, but: there needs to be further discussion how many ontology-like concepts we want to have.
- NeXus should represent the top-level of our technology stack and the technical implementation should be solved by other frameworks below (i.e., for us this is hdf5/h5py/pynxtools...). This means NeXus does not deal with describing what endianess or bit depth a data has
- Having multiple application definitions while writing a file is no conceptual problem, because we have well defined concepts. It is just a naming conflict in the hdf5 path and we need to figure out a technical solution. (/entry/view[s] could be a solution)
    - We can make use of the fact that the base class `NXbeam` and `NXmpes/NXinstrument/NXbeam` are different concepts in NeXus.
- If we support multiple inheritance on the conceptual level `nyaml2nxdl` should figure out conflicts and stop us from writing the file. We will test and see if it works or if we have to add another mechanism.

## Inheritance (including for base classes) should follow these rules in nexus
- We are not allowed to overwrite concepts of the class that are extended.
    - Docstrings are fully inherited.
    - If you do want to change a field (e.g., use a different name for the field), you should add it and indicate that these are the same concept.
- It is allowed to add fields to the specialized class.
- Requirements in base classes:
    - You are not allowed to lower requirements in the inherited base class (i.e. if `name` is required in `NXbeam`, it cannot be recommended in `NXbeam_neutron`).
- If the field is an enumeration we are only allowed to restrict the item list (i.e., we are not allowed to add items).
- All properties of a field are inherited (e.g., dim, units...)

# ToDos
- Build an example for merging an NXmpes file from different parts of the appdef (e.g., NXmpes/NXinstrument/NXelectronanalyser) with solving merge conflicts (e.g. we have `/entry/instrument/beam` in two files which should be converted to `beam1`/`beam2` or `beam_pump`/`beam_probe`)
- Use capital `MAPPING` in NXmpes for now
- Example for NXpump_probe to build multiple appdefs in one file


# Backlog
- Checking if all required/recommeded elements are present and generate a list of missing parts in `pynxtools`
- Add verification
- Build an example for top-level recipe above NXentry. There are also time-dependent graph base classes prepared by Markus Kühbach which might help.
- We want to include a concept in NeXus describing `isSameAs` relationships, but: there needs to be further discussion how many ontology-like concepts we want to have.
- Eventually, we want to be able to connect enumeration items to ontology IRIs
- Our nexus concept paper (from 2022) should go to nomads learning documentation