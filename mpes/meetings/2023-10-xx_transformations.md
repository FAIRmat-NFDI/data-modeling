
# Residual question from [last meeting](2023-10-18_additions_to_nxmpes_instrument.md)
- What happens if you write `doc` in the class inside an appdef? Does it replace the docstring from the base class or does it concatenate the docstrings? (see also [this](https://github.com/nexusformat/definitions/issues/1059) discussion)

# Transformations

## Points to discuss
- Definitions of angles: <span style="color:green">discussion</span>
    - In NeXus, the beam axis is the z-axis by default and every other elements is described with respect to the beam.
    - In traditional photoelectron spectroscopy, usually the starting point is the sample surface.
- need to also consider scanning beams, slight misalignments by gasket placements, ... <span style="color:green">discussion</span>
- Should there be one central place to collect transformations or should they stay attached to the instruments? <span style="color:green">discussion</span>
    - Markus: “My suggestion would be to keep them attached to the instrument and then have a summary along the lines of NXcoordinate_system(_set) with links to the individual transformations.”
- NXtransformation vs. specific view, like distance or angle <span style="color:green">discussion</span>


# Decisions
- 

# ToDos
-


# Backlog
- 