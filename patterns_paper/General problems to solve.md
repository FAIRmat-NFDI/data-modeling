## Generation of (NeXus) ontology
* How do we show inheritance?
* Should be the last step in our thoughts
* What is the current status?
* Nexus was viewed as a file format in the past -> transition to ontology
* We are coming from FAIRmat that needs to be reflected
* Controlled vocabularity
* Glossary with definied terms
* Relationships between terms/concepts (language!)
* knowledge representation / data storage with metadata
* ontology as a ruleset of concepts (metadata definitions + their relationships)
* Ontology reasoners (data verification)
* Requirements for FAIR data modeling
* Role of data modeling in data management
* Possibly timestamping for every single data entry

## Requirements for verifying data compliance with a schema
* Edge cases in NXtest
* Diagram to show algorithmic flow
* NOMAD metainfo vs nexus
* Pay attention on language of knowledge representation
* Key point: Automated documentation, automated verification
* Independent of nexus
* It's something we should keep in mind for all of the other points
* Where to put the split between ontology rules and data items
* Validation (the data is true and useful) vs verification (the data is according to some(!!) rules)

## Represent multiple steps in experiment
* This is just data modeling
* Already an example in NXtransport
* Many example cases
* Contextualizaton: What are multiple steps in an experiment?
* Different format come from different views on data
	* What view do we want within Fairmat?
* Views are not tied to how data is stored
* Our appdefs not just views?
* Can we support different views with our approach? Example: Sample centric vs. measurement centric view

## Agreed and standardised NXsample and NXuser
* We have to agree on NXsample
* Visual description of our standard
* Argue why certain fields are included or excluded
* Standardised structure for sample and user
* Avoiding repetition and confusion
* Recognizability between appdefs
* Super-Appdef-class containing an agreed FAIRmat standard for build appdefs

## How to represent geometries and coordinate systems. This is connected to NXsample and NXtransformations development.
* Abstract transport description
* Having an example
* Very relevant
* Often missing coordinate systems kill data
	* Bring examples
* Should be specified
* What is the relevance of coordinates systems for different communities

## Cardinality
* Ensuring having multiple instances inside groups
* Setting constraints on data
* Like checkboxes in the data
* Can it also help us in inhertiance?
* Cardinality as an ontology/verification rule
* Optionality and being required as a rule is specified subset of cardinality

## Branching in appdefs (if - else)
* Convinience of if-else instead of multiple defs
* Maybe already solved by base class inheritance or should at least be solved with it

## Generic representation of measurement data, i.e. "dynamik" rank and using of NXdata as general container for data representation
* Decision making scheme
* Nailing down the fields for the data shape
* Enabling array to be link into the graph
* Array should be seen as dataitem
* Array should have attributes like shape and datatype
	* It is already part of hdf format but not of your description (nexus etc.)
* Granularization of information
* Unit and unit category
* Minimal precision
* Value ranges
* Unified entry point for all data (say an extended NXdata for all measured data)

## "Abstract" base classes and inheritance
* Thinning the line between base classes and appdefs
* What is the difference between appdef & base class?
* Contextualization: Explain what inheritance is, e.g. single inheritance etc.
* Who is our audience?
* If we are in nexus context what does it mean to have base class inheritance? If no fields are required it makes no sense
* Here we should view the whole picture of appdefs & base classes in nexus vs how it is in ontologies
* Understanding the nexus description and general multi-level single inheritance
* Nexus conventions/rules vs. nexus habits (best practices)


## The role of nexus
* Nexus is one example for ontologies
* How strong should be the focus on nexus in the paper
* We really have to decice if we want to stay in the context of nexus or not? Because inheritance is to different between nexus and ontologies.
* Community standardization process


## What is FAIRmat doing differently
* Our thoughts could be viewed by some people as overkill
* Not getting lost in the literature + technical details
* Be practical and useful for NFDI audience (very mixed)
* What are the key deliverables of this paper? Code? Concepts? Diagrams? Ontology? ....
* General discussion for our internal documentation vs for a general audience
* Keeping development process easy for the users of the data representation system
* Providing examples and guidelines


## Introduction
* need for ontology (also current ontology activities world-wide)
* NeXus as an attempt for data modelling based ontology
* challange: big data, lots of metdata


#area-b #nexus #general-patterns 
