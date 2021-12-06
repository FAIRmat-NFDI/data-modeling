# Application definition of variable angle spectroscopic ellipsometry
These are comments collected during the development of the application definition. The definition focuses on ellipsometry, where the above title is one of the moste generic type.

Comments of Markus K. to the draft for FAIRmat AreaB Sprint3:
angle_of_incidence: outer or inner surface normal?
  -- top, reflective surface of the substrate (T.H.)
instrument/company: suggesting "Name of the company which build the instrument" -- o.k.
instrument/hardware_version: you mean serial number -- no, version of the hardware
--- CS: Hardware can also have different version version: revision numbers
instrument/software_version: I would split name and version+buildnumber -- done
instrument/light_source: Would it make sense to have an enum or a free-text?
  -- not yet, because this can get complex. Many systems have multiple light sources.
instrument/ellipsometry_type: We should give a doi in the doc
  -- pointing to what document?
instrument/calibration/calibration_time: I would go for a specific date (including time) instead of a free text
  -- that was the original intention, text is the alternative, which we may drop
instrument/calibration/calibration_provided: The doc is confusing, would you like to say that the measured data from the calibration are included?
  -- I modified the data to data_type, and then we can add data for containing the calibration
    data array (if provided). It would be optimal to have it, but not necessary, if we trust
    the user.
  -- The data_type allows also 'not provided' for the case it is not given
  -- the whole branch is now: exists: recommended

instrument/calibration/calibration_data: Straight-through, is this a clear term for everybody?
  -- only to those who ever calibrated an ellipsometer

instrument/calibration/calibration_data/calibration_data: doc not defined what should be in there?
  -- added the doc, clarified a bit the definition
instrument/angle_of_incidence: How to you define positive rotations,
I assume right-handed, counter-clockwise?
  -- not needed. An angle of incidence is in the 0 - 90 degrees range, see any basic
     book about optics
dunno about the target syntax?
instrument/window: "its" in the last sentence is unclear, to what does it refer?
  -- the window; I tried rephrasing the doc
 CS: Woollam devices sometimes mentioned the delta offset parameters? Should we open a field for that?
should further fields from NXentry on timing (end_time, duration, etc.) be included?
  -- it may be necessary, for so called in-situ measurements (e.g. swelling of polymer films
     in vapor, or specific solvents.

wavelength doc string: "make the others accessible", you mean others values?
  -- I think, the sentence meant exactly that.

stage docstring reads too colloquial to me
  -- fixed
sample_rotation/alternative is unclear
there is a dangling calibration field under window? where should this belong?
  -- I think it is more clear now

# Comments within the fields

## Before the instrument definition:
(NXmonitor):
 -- commented it out, because it makes no sense... If we have a monitor, it is
    within the instrument; pls. check the documentation!

## Fields without NEXUS type definition
if the nx_class or type is nx_char i.e. model(NX_CHAR) we do not have to specify because this is the NeXus default type
      if the exists argument is optional, i.e. minOccurs = "0" we also do not have to specify

## bandwidth
This should be a vector with the length of the number of used wavelength
  -- then it is equivalent to the wavelength in sample... should we just link that?
  -- make it a link


## At stage_orientation
maybe it is useful here to start with which coordinate system you start with,
      if nothing is specified it would be the McSTAS one.
      okay, there are still two surface normals for the substrate layer,
      admittedly one - the one pointing into the sample - is not intuitive but here
      we better be verbose, i.e. outer surface unit normal.
        -- fixed in doc of angle_of_incidence (T.H.)
        -- we usually use a normal pointing out from a material, if the rest is the 'environment'

later a bit:
# does the beam illumination direction vector always be coupled to the stage or
 can you transform the stage, beam and sample?
 I thought sample is fixed on stage but stage can (move?) rotate relative to the beam?
 We should try to be even more clear here
   -- yes, there are stages that can rotate and samples which may have multiple surfaces (e.g. crystals)
   -- the process of reflection fixes the source / sample / detector triangle
   -- in transmission, the source / detector direction is fixed only
nice that you disentangled here the ZXZ Euler angle convention, alternatively
  -- if you look into the NEXUS definition, you always have an axis of rotation defined,
     thus the rotation matrix is not suitable; (I tried them earlier as well...)

## window and window effect
which class does it belong to? We cannot just start a nesting here or how does it connect to the above nodes?
  -- it belongs to the instrument, if the experiment is done in an environment other than air
  -- we can derive it from the NXaperture

## calibration samples / data
how should people specify samples, identifiers, we have an issue for this in sprint 03
would it make sense to store all calibration data in a specific (set) of properties rather than on in a group above and then another one here for the window?
  -- possible. In this grouping, it is here, because it belongs to the window,
     and only needed if window was used. No window, no calibration of its effect...

from the indenting, this looks like that it belongs to calibration, shall we shift it to instrument?

"whole unit" as a term is this clear enough what we mean here?
  -- like I do not want to know the amplifier within the camera,
     the grating within the spectrograph, etc.

### modulator / polarizer / analyzer revolution
"one" does this imply "for each" ?
  -- fixed
what should here be communicated the revolution rate?
 -- no (it is about how many revolution was used to calculate one element of data)

### fixed_revolution
but this does not exist as an NXDL field type, yeah, see the above comment
  -- fixed it using NX_FREQUENCY, but RPM may be better

### variable_revolution        #is  it safe to assume that the exact time history of the revolution is not
documented/accessible/relevant?
  -- yes, except if it was a home built instrument
length: 2 #instead, does the following work?
  -- yes, thanks for fixing the dimension

## sample
doc: human readable sample name
I feel the default docstring from NXsample for this member suffices.
  -- looks fine
Tamas: I thought the same name and identifier can be different we should allow for such flexibility
  -- I am not sure I understand the question...

### optical excitation
An interesting question if we could group the optical excitation parameters to an NX_subentry group, and put all belonging parameters into one.

### preparation time zone
interesting that for synchrotron samples this is not already inside NeXus these sample typically travel the most in-between labs and countries.
  -- it may be meant to be part of the ISO date time for preparation_date

preparation_description:
doc: Ideally reference to another application definition that gives details for the preparation of the sample. If such an application definition is not available, use this field to give preparation details.
  -- it is changed now to description simply

alternatively
sample_description:
doc: specification of the sample (involved materials and layer structure)
maybe we go for now with description, but we should think in the next sprint about a more covering description of samples/specimens which extends NXsample enabling their composite geometry and internal structure eventually enabling to go as deep as to atomic level description
ID:
  doc: unique ID for the sample
  unit: NX_DIMENSIONLESS, NX_CHARs are dimensionless by nature

### orientation matrix
the last comment in the bracket (in doc) is unclear
  -- I changed it to the existing field in NX_sample, because this makes sense
     other orientation is described by instrument/stage.

so this is the macroscopic orientation of the sample i.e. how a sample-affixed Cartesian coordinate system is oriented wrt to the McSTAS? I think I need to think longer about this. We should never give Wikipedia as a reference when dealing with rotations there is too much inconsistent material on in particular these conventions choices circulating in the inet.
  -- that is why my original comment contained the link to a specific section, with
    a well defined case...
position(NX_NUMBER): # what is the difference to the definition in stage section? Is there reference system defined?
  -- this is the one I said before that it is not needed, because it is merged into
    instrument / stage
doc: Specifiy the position (e.g. in a line scan) with respect to a reference point
dimensions:
 rank: 1
 dim: [[1, 3]]
unit: NX_LENGTH

do you want to keep track of this reference point in the laboratory coordinate system?
where should this be placed in the hierarchy?
  -- it is in the instrument / stage

### data identifier
what about uniqueness of the identifier?
  -- append it to the experiment identifier...

### wavelength
for RC2 m11 represents intensity which is not 1
full Mueller matrix should be stored,
\@nx_class: NX_NUMBER better transform this data field into an NXdata
  -- NX_Data is for something else!

### stage
Having a stage here is confusing, what is again the need for this?
  -- only if you are looking at the data but not the instrument...
/instrument/stage #I think the specific value is not a part of the schema definition
which type of link?

### medium
I feel this should better go to the sample description
  -- this is the sample description...

## derived parameters
my argument against using such mere collection of things is that derived parameters follow from a process or at least a set of rules and recipes applied how to derive them. Why not make this an NXprocess ?
  -- a good question, probebly it would work better
---

# Consolidation 2
## links
[NEXUS](https://manual.nexusformat.org/design.html#design-links) defines the links in a document as HDF5 hard links. Always specify an absolute address.
However, it is also clear that the path should be also identified as target in the definition, so let us do it that way:
  - define @target in /instrument/wavelength
  - use it in links, (this should be translated to the --> NEXUS operator).

## wavelength
(Tamas:) The measurement wavelengths are requested ad three places:
  - /instrument/wavelength
  - /instrument/calibration_data/wavelength
  - /sample/waveelength
and potentially at /instrument/bandwirdht. This last one is superfluous, i remove it from the definition.

## data --> measured data
I have changed the data name, because it seems to generate confusion. The measured data is a numeric structure. NXdata should denote representations of the original data, used for default plotting.

## length of runs
The problem with this field is that it is a bit misleading. Length of a run is something like how many measurements were run or for how long (time). Now, what we mean is that how many parameter was varied beyond the waveelngths and incident angles.
