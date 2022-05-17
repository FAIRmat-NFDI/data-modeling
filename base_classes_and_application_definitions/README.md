# common modules, base classes
There are a couple of components required in every experiments we describe, such as:
- operator
- sample description (name, ID, source, etc.)

Now, let us collect here modules that are required in every tasks of Area A, but may not have been written by other Areas so far.
For example: chemical_substances, or process_step.

# removing experimenter
the experimenter file was a redo of NXuser. Tune the NXuser instead as it is needed.
### the "nexus harmonization" will be accomplished in detail later


# sample types (qualification)
Sample types as already listed in Andreas presentation in task force meeting on 16th of May 2022:

- simple substance (element or chemical compound)
- mixture (or single phase mixture, solution, suspension, alloy or colloid)
- multi phase sample (multi domain or composite)
- layer (or film or substrate)
- bulk
- gel
- dispersion
- policrystalline powder

# Application definitions
As mentioned, the app def should be as flexible as the user wants but it should be composed of standard classes  (e. g., user, instrument, process, sample, characterization). Here the files "synthesis_app-def.yaml" and "melt_czochralski_app-def.yaml" offer two possible examples of how two organize the whole set of data for an experiment (application definition)
