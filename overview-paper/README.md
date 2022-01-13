# Paper draft for NORTH and NeXus tools for uploading (meta)data of experiments into NOMAD

This is the skeleton to our paper where we want to communicate the technical implementation and overview of the NORTH and NeXus tools.

## Paper structure

The document is to be compiled from a set of LaTeX files which can be selectively included 
to reduce unnecessary re-compilation time during the writing and reviewing stage.

- FairMatAreaBNeXusPaper.tex is the main paper which holds the *.tex files and controls the inclusions of *.tex files.

There are some infrastructure/utility *.tex file which define, 
apart from the usual LaTeX package includes, common user-defined commands, 
and formatting guides, these files are:

- PaperHeader.tex
- PaperUserCommands.tex
- PaperTitleAuthAffils.tex

The body of the paper consists of:
- PaperAbstract.tex
- PaperIntroduction.tex
- PaperMethods*.tex
- PaperResults.tex
- PaperDiscussion.tex

We should place our text snippets for specific methods into the appropriate/respective place *Methods*

Plus several appendices commonly needed for such a paper:
- PaperAcknowledgements.tex (Data availability, author contributions, acknowledgements, funding)

For journal which require authors to put tables, and figures (with captions), separately:
- PaperTables.tex 
- PaperFigureCaptions.tex (where to place, guess what, captions for figures ...)
- PaperFigures.tex (... and the figures)

## How to add references?
All references should be placed in PaperBibliography.bib. If placing something there, format it properly, meaning:
@Article/Book/Electronic/InProceedings{FirstAuthorSurnameYYYY,
author = {A. Surname and B. Surname and C. Surname},
doi = {fill a doi in},
year = {YYYY},
}

At this point giving a DOI + author + year suffices. 
List all authors! For references which do not have a DOI, fill in all relevant pieces of information to the best of your knowledge, feel free to take the examples in the bib file for inspiration on formatting.
