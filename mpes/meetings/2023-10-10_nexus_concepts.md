# Discussion points

## Conceptual, NeXus-related, open questions
- splitting AppDefs (who will assemble) discussion
- Scientists vs. vendor point-of-view 
    - How do we allow different sources to notify what exact version of NeXus they used for the split part? discussion
    - mapping tool / wizard / assemble too (in NOMAD, like the ELN examples, but also support external solution) new feature
    - how to handle different setups and their different requirements? discussion
- Should we make a base class of a generic scan? new feature discussion
    - NXscan (like workflow to describe sequence of actions/steps) 
    - Where do we store details of energy scan modes? E.g. jittered/dithered energy mode?
- Multiple inheritance, example: time_resolved and NXelectron_detection / NXphotoemission + spectroscopic properties
    - From the discussion: We could just not call it photoemission on the top level but rather something like `NXelectron_detection` from which we branch `NXphotoemission` -> `NXmpes` / -> `NXpeem` and `NXelectron_spectrosopy` -> `NXaes`, `NXleem`,...
- Possibility to express two fields as the same concept in the application definition. See [here](https://github.com/FAIRmat-NFDI/nexus_definitions/pull/72#issuecomment-1750608506) for a discussion and example