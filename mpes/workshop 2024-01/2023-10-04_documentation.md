# General

- Where to store the minutes of our meetings? Repo in FAIRmat-NFDI?
    - Put it in `FAIRmat-NFDI/data-modeling`
- Can we enable issues on nexus_definitions?
    - Is enabled
- Where to create a Board for the MPES related issues/tasks?

# Documentation, Accessibility, Tutorials

- all fields/attributes/groups should come with clear docs (also if only present in a base class) `documentation`
- Basic Examples/Tutorial page for NeXus (Important questions to answer: How do appdef names translate into entries in the file, how does the pynxtools template notation work), e.g., I have my experiment here, how do I construct a datafile from it? `documentation`
- Align how we will document with the nomad documentation and add pages for nexus (e.g. separate or combined docs) `documentation`
- Synchronization between base class and appdef docstrings on the proposal page documentation `new feature`
- show all subgroups/fields/attributes defined for a given element `new feature`

## From NXdata discussion
- Tutorial+Example for NXdata

# Decisions
- We will bring the documentation of nexus + pynxtools + north examples to nomad docs
- We store examples in nomad (large files should be stored and downloaded separately).
    - CI/CD test in nomad at each level, which means nexus parsing, generation and ipynb example (in container)
    - ipynb examples test in container in north repo
    - nyaml2nxdl and read_nexus tests to nexus_definitions from `pynxtools`
- There will be a common tutorial between area A+B: Before and after metadata standardization
- One Tutorial: Generate a nexus file and load it into nomad
- One Tutorial: A primer on nexus
- Writing specific how-tos: 
    - I have a nexus file, how to upload to nomad
    - I have a nexus file and additional metadata, what do I do?
    - I have a supported vendor file but no eln data how can I make a corresponding nomad eln?
    - I have multiple nexus files and want to combine them into one nexus (master) file which is compliant to an application definition (future discussion: how do we want to support/distribute this in nomad/pynxtools?)

# ToDo
- Review docstrings in appdefs and base classes
- Write Tutorial: Generate a nexus file and load it into nomad
- Move mpes, ellips, xps, sts examples from north to nomad

# Backlog
- Bring documentation of nexus + pynxtools + north examples to nomad docs
- Move examples to nomad
- Update CI/CD at each level & in each repo (nomad, north, pynxtools, nexus-defs)
- Add documentation for super-concepts visible via css/javascript
- Give option to show all inherited direct children (to support searchability and auto-expansion)