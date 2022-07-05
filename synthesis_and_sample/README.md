# 1 Common modules (base classes)

There are several components required in every experiment we describe, such as:

- operator
- sample (name, ID, source, etc.)
- instrument
- synthesis process
- characterization

![App Def examples](https://box.hu-berlin.de/f/af9fddf4e83b44568973/?dl=1)

Each of these elements is a base class, e. g., the set of terms that might be used in an instance of that class.
Consider the base classes as a set of components that are used to construct a data file (synthesis or measurement).
Now, let us collect here base classes that are required in every tasks of Area A, but may not have been written by other Areas so far.
For example: sample and its related subclasses (chemical_substances, process_step, substrate, ...).

### the "NeXus harmonization" will be accomplished in detail later, for the moment let's address mainly structural questions. We will then be able to decorate them according to the emerging syntax rules (NeXus or NOMAD)

## sample types (qualification)

after the 23rd of may task force meeting, this is the updated shape of sample class

![Sample examples](https://box.hu-berlin.de/f/b15794edd7d04f5bba97/?dl=1)

Summary:

What should be described in the SUBSTANCE Section:

- simple substance (element or chemical compound)

What should be described in SAMPLE Section:

- mixture (or single phase mixture, solution, suspension, alloy or colloid)
- multi phase sample (multi domain or composite)
- layer (or film or substrate)
- bulk
- gel
- dispersion
- policrystalline powder

What should be described in COMPONENT Section:

 - it decorates the SAMPLE or SUBSTANCE classes with non-intrinsic features, such as the amount or concentration used in a specific experiment

# 2 Application definitions

Consider an application definition as a contract between a data provider (such as the beam line control system) and a data consumer (such as a data analysis program for a scientific technique) that describes the information is certain to be available in a data file.
App defs are composed of base classes.
The app def should be as flexible as the user wants but it should be composed of standard classes  (e. g., user, instrument, process, sample, characterization).

We want to combine our base classes to design an app def, we also want to link app defs inside our own

![App Def examples](https://box.hu-berlin.de/f/be1c952371b74eeebc57/?dl=1)
