
# Versioning of NeXus definitions

## Points to discuss
- Try to extract the version tag from the nexus definitions to incorporate it into a file <span style="color:red">new feature</span> <span style="color:green">discussion</span>
    - Should work with setuptools-scm.
    - Automatic versioning for nxs file. [pynxtools#124](https://github.com/FAIRmat-NFDI/pynxtools/pull/124) already did something on this but it just takes the version number of pynxtools (because back then nexus_definitions wasn't a python package). In principle one should just need to change the root of the version call to the one of the definitions and  it should work
- 	We plan to split AppDefs. How do we allow different sources to notify what exact version of NeXus they used for the split part? <span style="color:green">discussion</span>
    - The HDF5 file is composed with whatsoever fields we need. These nodes then have direct pointers to the versions and concept. Helps with partial/split AppDefs written, name resolution, no need for multi-inherit.	


# Decisions
- Implement `nexus_definitions` versioning with setuptools-scm as shown in [pynxtools#124](https://github.com/FAIRmat-NFDI/pynxtools/pull/124) for pynxtools.
- If you write a partial application definition you just write NXmpes into /entry/definitions and add the @partial attribute into NXroot to which concepts this partial appdef complies

# ToDos
- [X] Add @partial to NXroot ([ref](https://github.com/FAIRmat-NFDI/nexus_definitions/pull/52/commits/cc3b9a6712eddf531c1d38b7b35ea0d69f8d2272))
- Add writing of attributes in NXroot in pynxtools

# Backlog
- Example for attaching versions, vocabularity item etc to a field or group (see [examples](2023-10-10_nexus_concepts.md) here)
- Discuss with NIAC how to do `nexus_definitions` versioning
- Add version information of `nexus_definitions` in nexus file