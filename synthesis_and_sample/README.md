# 1 Common modules (base classes)

There are several components required in every experiment we describe, such as:

- operator
- sample (name, ID, source, etc.)
- instrument
- synthesis process
- characterization

![App Def examples](https://box.hu-berlin.de/f/dae06cc0ec674accb1d0/?dl=1)


Each of these elements is a base class, e. g., the set of terms that might be used in an instance of that class.
Consider the base classes as a set of components that are used to construct a data file (synthesis or measurement).
Now, let us collect here base classes that are required in every tasks of Area A, but may not have been written by other Areas so far.
For example: sample and its related subclasses (chemical_substances, process_step, substrate, ...).

### the "NeXus harmonization" will be accomplished in detail later, for the moment let's address mainly structural questions. We will then be able to decorate them according to the emerging syntax rules (NeXus or NOMAD)

## sample types (qualification)

after the 23rd of may task force meeting, this is the updated shape of sample class

![Sample examples](https://box.hu-berlin.de/f/ef3e2eca64b94b8396b5/)


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

We want to combine our base classes to design an app def, we also want to link app defs inside our own

![App Def examples](https://box.hu-berlin.de/f/9661b5d0f9ab40d1a929/?dl=1)
