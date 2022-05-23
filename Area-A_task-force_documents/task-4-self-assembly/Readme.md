# Area A task 4 self-assembly
This is the area to work on self-assembly synthesis definition.
The application definition describes how one can produce samples
formed primarily by non-covalent, weak interactions (up to
hydrogeb bonds). Chemical reactions are also part of the process,
but not the primary driving force.

The formation process is driven by the physical attraction of the elements also
also influenced by thermal diffusion. Most self-assembly processes are strudied
in liquid environment, but the participating elements may have fully dissolved
or seggregated forms, that is particles, droplets, microgels. Exotic variants
would include gas bubbles or particle aggregates in aerosols.
What is still common: the forces driving attraction are most often electrostatic
in nature, spreading from London - van der Waals forces to Coulomb attraction or
repulsion. Many ordered structures (colloidal crystals) are formed by electro-
static repulsion.

How to form structures with self-assembly:
- one has to achieve a colloidal dispersed system
- bring the components in close enough vicinity
- generate structured surfaces:
  - via lithography (most generic name)
  - cutting
  - etching
  - direct writing...

The definition includes a couple of possible preparation steps, such as:
* coating techniques
 * spin coating
 * dip coating
 * drop casting
* separation steps
 * filtration
 * centrifugation
 * electrophoresis
* etc.

All these steps are individual experimental methods, which require
their own base classes to be drafted.
A first version is built up here, to be moved around with time to
a better, common repo.

# sample description, parameters
What are the most common parameters describing a self-assembled, structured sample?
- the type of phases (solid, liquid, gasous, plasma)
- the average size and size distribution of these
- average distance and distance distribution between similar phases
- there are some generic discriptions such as bicontinuous, lamellar, spherical, cylindrical formations

# general structure of preparation process
## preprocess
Steps that prepare the sample for the actual reaction, e.g. plasma activation

## process
steps to run the reaction

## postprocess
e.g. synthering

For every step, have a base class defining the parameters and properties of the instrument used.

## Setup
Generate a list of equipment based on the names / model / company from the base classes used
in a specific experiment (application definition).

# Methods for characterizing self-assembled systems
- Film thickness determination;
  - ellipsometry
  - surface plasmon resonance spectroscopy (SPR)
  - quartz crystal microbalane with dissipation (QCM-D)
  - optical profilometer (interferometric)
- surface topography:
  - scanning electron microscopy (SEM)
  - scanning probe microscopy (SPM)
  - atomic force microscopy (AFM)
  - scanning tunnelling microscopy (STM)
  - optical microscopy
    - bright field
    - dark field
    - differential interference contrast (DIC)
    - phase contrast
    - reflection interference contrast (RICM)
    - fluorescence
    - STED
    - Raman spectromicroscopy and CARS
- surface composition
  - contact angle (qualitative only)
    - sessile drop (static and oscillating)
    - captive bubble (static and oscillating)
  - ARPES / XPS
  - TIR-FTIR
  - tip enhanced Raman or IR spectroscopy
  - EDX in SEM
  - MALDIT-TOF MS
- layer structure analysis
  - gazing incidence small-angle X-ray scattering
  - X-ray reflectometry
  - neutron reflectometry
  - time-of-flight scanning ion mass spectrometry (TOF-SIMS)
- particle size, distribution, internal structure
  - small-angle X-ray scattering
  - X-ray diffraction
  - neutron scattering
  - static-light scattering
  - dynamic light scattering
  - electrophoretic mobility DLS — ζ-sizer
