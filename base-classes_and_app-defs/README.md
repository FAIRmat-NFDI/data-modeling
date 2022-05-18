# 1 Common modules (base classes)
There are several components required in every experiments we describe, such as:
- operator
- sample (name, ID, source, etc.)
- instrument
- synthesis process
- characterization

Each of these elements is a base class, e. g., the set of terms that might be used in an instance of that class. 
Consider the base classes as a set of components that are used to construct a data file (synthesis or measurement).
Now, let us collect here modules (base classes) that are required in every tasks of Area A, but may not have been written by other Areas so far.
For example: chemical_substances, or process_step.

### removing experimenter
the experimenter file was a redo of NXuser. Tune the NXuser instead as it is needed.
#### the "nexus harmonization" will be accomplished in detail later


### sample types (qualification)
Sample types as already listed in Andreas presentation in task force meeting on 16th of May 2022:

- simple substance (element or chemical compound)
- mixture (or single phase mixture, solution, suspension, alloy or colloid)
- multi phase sample (multi domain or composite)
- layer (or film or substrate)
- bulk
- gel
- dispersion
- policrystalline powder

# 2 Application definitions
Consider an application definition as a contract between a data provider (such as the beam line control system) and a data consumer (such as a data analysis program for a scientific technique) that describes the information is certain to be available in a data file.
App defs are composed of base classes.
The app def should be as flexible as the user wants but it should be composed of standard classes  (e. g., user, instrument, process, sample, characterization). 
