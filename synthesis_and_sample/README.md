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
For example: sample and its related subclasses (substance, process_step, substrate, ...).

### the "NeXus harmonization" will be accomplished in detail later, for the moment let's address mainly structural questions. We will then be able to decorate them according to the emerging syntax rules (NeXus or NOMAD)

![Base Classes](https://box.hu-berlin.de/f/609490a1c373425babdb/?dl=1)

These base section have got an <em>a priori</em> **inheritance** structure. The user can further decide how to put together this bricks by means of **referencing**.
