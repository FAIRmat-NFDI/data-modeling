# Executive summary:
Workshop on Tuesday April 12 between 13:00 and 16:00
Present: Yue, Carola, Sebastian, Laurenz, Sherjeel, Tommaso, Sandor, Andrea, Tamás, MarkusK

# Individual task
> For each we defined, all capital summary, urgency (1 high, 3 lower), coordinating responsible person.

> What are our clear expectations why we invest time into describing materials (structure) at all with NeXus?
  (Relevant for paper and scientific communication)
  How should we extend NeXus to describe their (skeptical people) needs, self-evident that each experiment and material 
  should be described to relevant detail, we are convinced about it in FAIRmat, pros: open to extension, long-standing processes,
  community standardization, automated documentation, ontology, verification, visualization tools
  WHY NEXUS?, 1, done!

> Description of elements and molecules (starting from smiles and inchi, mapping of atom type and position, binding topology
  to string representations), how to integrate area A, expected time frame, people, coarse-grained molecular dynamics, integration of area C?
  component, ionic, radical, elements, and molecules
  CHEMICAL SPECIES, CROSS-AREA EXCHANGE -> make base classes out of it, 1, area A activity, Tamás, Andrea, (Sebastian) 

> Description of the sample geometry, including the geometry of individual "features" (objects) in the sample?
  Description of multi-layers (which level of detail to begin with, qualitative, stacking of e.g. NXlayer base classes, or
  detailed computational geometry description, i.e. a layer is a space in between two surfaces ...?
  surface roughness long term perspective
  SHAPE, GEOMETRY, MORPHOLOGY, 1, MarkusK

> NXbase classes to model graph relations between elements inside NeXus or is it sufficient what comes shipped with NeXus?
  NEXUS FILE CONTENT, 1, Sandor, kick-off meeting

> Beyond crystallinity (amorphous, thermodynamic state (liquid, etc.) interfacing and/or using NeXus to describe crystal, new base classes to
  describe beyond crystallinity?, information at which level, example amorphous (macroscale SAXS, atomic scale, amorphized layers STEM measurements)
  use cases, different examples of collodial systems in Tamás backpack, these are statistically described
  STATE OF MATTER, CONSTITUTION, 1
> (e.g. lamellar structures, grain boundary energy), domain classification, dimensionality, all descriptors packed together
  "representation of structural units, representing the organization of the units via a individual hierarchies", 
  (i.e. volume1 grain1, grain2 > atom_set for grain 1, etc...?
  DOMAIN DESCRIPTORS, 1, Támas

> Position of objects/illumination/beam wrt to regions-of-interest, learn and build upon the mpes or NXmx examples how to use NXtransformations,
  need and how to of more abstract (geometrical?) description how objects (beam) and e.g. specimen/detector are arranged in space.
  strategies how to avoid manually-written docstrings which describe the context of an NXtransformation. "super-base line depends_on" ?
  CONTEXT FOR AND USE OF NXTRANSFORMATIONS, 1, Laurenz, request to have a follow up meeting

> How to represent the length and time scales of observations, synchronicity, asynchronous, time series data not fully-overlapping,
  several records monitoring the same experiment not synced via a common clock.
  NXsnapshot base class for enabling collections of snapshot data, whose childs again then branch further
  HANDLING TIME SERIES DATA, 3, Pepe?
 
> Integration of descriptors for spatio-temporal mechanisms/phenomena during the experiment 
  which lead alter the state of the sample and its structure "damage" accounting, radiation damage work group, 
  is damage monitoring not just a case of time series data?, for sample-based description (indeed connection to HANDLING TIME SERIES),
  however, in the documentation domain specific extra information can be relevant and thus should be detected (dose history, overall dose
  history, or point-by-point), very experiment-specific, (Yue Sun/Sandor, pressure change history, maybe adding it to NXmonitor?).
  TIME-DEPENDENT DOMAIN DESCRIPTION OF E.G. DAMAGE, 3 / CHANGE HISTORY, Sandor, (Laurenz)

PROCEDURAL ASPECTS / ACTION POINTS / HOW TO PROCEED
> When to discuss the individual points in more detail and how to sync with implementation, half-year perspective
  
> Begin with implementing NXbase classes or method-specific application definitions?
  i.e. how to implement our definitions, how important to build then, when to start building them?
  IMPLEMENTATION, starting from base class

> Who would like to/should like to contribute how much to the implementation?

> How to discuss: weekly 1pm meeting task force meeting should not be polluted with detailed discussion
  about the above-mentioned points, responsible persons should invite (have a Thursday morning e.g.?), use slack

> Use areab-appdef gitlab for storage of results and codes

FYI:
> Next NIAC meeting, April 26th, new file formats, please come, tell how you can contribute

