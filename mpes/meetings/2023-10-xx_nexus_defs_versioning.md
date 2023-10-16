
# Versioning of NeXus definitions

## Points to discuss
- Try to extract the version tag from the nexus definitions to incorporate it into a file <span style="color:red">new feature</span> <span style="color:green">discussion</span>
    - Should work with setuptools-scm.
    - Automatic versioning for nxs file. [pynxtools#124](https://github.com/FAIRmat-NFDI/pynxtools/pull/124) already did something on this but it just takes the version number of pynxtools (because back then nexus_definitions wasn't a python package). In principle one should just need to change the root of the version call to the one of the definitions and  it should work
- 	We plan to split AppDefs. How do we allow different sources to notify what exact version of NeXus they used for the split part? <span style="color:green">discussion</span>


# Decisions
- 

# ToDos
-

# Backlog
- 