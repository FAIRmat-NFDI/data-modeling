
# Additions to current NXmpes -> Instrument

## Points to discuss
- Use NXfabrication to specify Vendor, Model, S/N etc. of any given instrument, component <span style="color:blue">add from existing</span>
- Add a NXtransformation to NXenergydispersion <span style="color:blue">add from existing</span>
- Allow for torroidal analyzers <span style="color:blue">add from existing</span>
- Allow for multiple angular resolutions (perp/parallel to a slit) <span style="color:red">new feature</span>
- Is "Probe" redundant? <span style="color:green">discussion</span>

# Decisions
- We want to have a probe field to describe which type of beam we are using (e.g., electron, neutron, etc)

# Handling of docstring "inheritance" in nexus
- What happens if you write `doc` in the class inside an appdef? Does it replace the docstring from the base class or does it concatenate the docstrings? (see also [this](https://github.com/nexusformat/definitions/issues/1059) discussion)
    - We discussed this: It concatenates, i.e., specializes the docstring

# ToDos
- [X] Use NXfabrication to specify Vendor, Model, S/N etc. of any given instrument, component
- [X] We want to add photon to NXsource/probe and restrict the NXmpes/.../NXsource/probe to photons, x-ray... and make it optional ([ref](https://github.com/FAIRmat-NFDI/nexus_definitions/pull/52/commits/bd6b13afd6c8938eaf9780d2d5c1dc9031a6e8d7))
- Add a NXtransformation to NXenergydispersion
- Allow for torroidal analyzers
- Allow for multiple angular resolutions (perp/parallel to a slit)
- Is there a type in NXbeam? If so rename/remove it so we only have probe.
- Refactor NXsource docstring (there is no ring or facility!)


# Backlog
- Refactor NXdetector to use NXfabrication