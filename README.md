# latex_utils
Utils files to work with latex and publications


# Automatically clean your bibliography
Use
`python3 clean_bibli.py` to clean bibliography.bib using data from [dblp](dblp.org) and [SemanticScholar](semanticscholar.org).

The script check if published versions are available, if so, download their bibtex, and removes useless fields (pages, ...etc) and replace the bibtex without changing the used key, such that you can directly use the generated cleaned bibliography.

![](images/reference_examples.png)

# Todo

## Bibtex cleaning
* check for duplicate

## Rest
* Create pandas table from latex and vice versa
