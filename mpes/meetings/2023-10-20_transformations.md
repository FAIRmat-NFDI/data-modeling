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
- We want to refine coordinate system set to refer to physical properties properly
- We follow the [proposal](https://github.com/FAIRmat-NFDI/nexus_definitions/blob/mpes_subdefs/contributed_definitions/nyaml/NXmpes_arpes.yaml) for angles from Laurenz NXmpes_arpes (based on [pyarpes definition](https://arpes.readthedocs.io/en/latest/spectra.html)) and add enumerations to fix the depends_on chain
- We keep attaching NXtransformation to the instrument parts and bring it to the workshop discussion if there are any arguments against it
- We recommend using `transformation(NXtransformations)` (might be optional/recommended in most cases) in instrument parts instead of `(NXtransformations)` in the application definition.
    - In XPS two angles recommeded: `beam_to_analyzer`, `beam_to_sample`
- We want to use denoted fields in NXtransformations to show important transformations in the instrument (e.g., `beam_to_analyzer` or `liquid_jet_normal`, also Laurenz example...) which may or may not be linked to other transformations.

# ToDos
- Integrate the [new NXtransformations docs](https://hdf5.gitlab-pages.esrf.fr/nexus/nxtransformations_active/classes/base_classes/NXtransformations.html) (see [PR](https://github.com/nexusformat/definitions/pull/1278)) into our fairmat branch or discuss what is blocking there
- In NXcoordinate_system add NX_CHAR fields for spelling out where axis point (e.g., z points downwards), [ref](https://github.com/FAIRmat-NFDI/nexus_definitions/blob/base_class_templates/contributed_definitions/nyaml/NXcoordinate_system_set_parsed.yaml)
- Example for the liquid jet transformations
- Example for arpes/pyarpes appdef transformations


# Backlog
- We merge the coordinate system base classes in fairmat, build an example and try to generate 3D files with, e.g., nexus3d to see if it works well
- We will see if we outsource the pyarpes angles from the appdef based the discussion with the technology partners
- Find a way to relate to physical quantities independent of McStas coordinate system