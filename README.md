# Semantic Sorter

a local ai-powered file organizer that understands what your files actually mean, not just what their extensions say.

semantic sorter clusters messy files using embeddings and vision-language models — fully offline and privacy-first.

---

## the problem

downloads and desktop folders become chaos fast.

screenshots pile up  
whatsapp images have useless names  
pdfs sit as untitled  
project files get scattered across formats  
manual sorting becomes friction you eventually ignore  

traditional file sorters rely on extensions or rigid rules. they miss semantic relationships between files.

the result is folders that are technically sorted but still mentally messy.

---

## what this project does differently

semantic sorter uses local machine learning to understand file meaning before organizing anything.

instead of rule-based sorting, it performs semantic clustering using embeddings and a vision-language model.

key characteristics:

- fully local. no cloud apis. no data leaves your machine  
- semantic understanding of filenames  
- vision-language image understanding via blip  
- pdf text extraction for stronger grouping  
- confidence-based project detection to avoid fake folders  
- conservative smart renaming only when names are truly useless  
- dry run mode for safe preview  
- full undo support with move logs  
- model purge utility to reclaim disk space  
- collision-safe file moves  

goal: fewer dumb folders, more meaningful structure.

---

## how it works

high level pipeline:

1. files are grouped into broad families (images, documents, cad, code, etc)  
2. semantic text is built from filename + pdf extraction + vision signals  
3. sentence-transformers generates embeddings locally  
4. agglomerative clustering groups related files  
5. confidence gating decides whether a true project folder should exist  
6. absurd filenames are intelligently renamed  
7. files are moved with full undo logging  

everything runs locally on your machine.

---

## quick setup

follow the steps below to get the sorter running.

### step 1 create virtual environment (optional but recommended)

python -m venv venv

this creates an isolated python environment for the project.

---

### step 2 activate the environment

mac or linux:

source venv/bin/activate

windows:

venv\Scripts\activate

after activation you should see (venv) in your terminal.

---

### step 3 install python dependencies

pip install sentence-transformers scikit-learn numpy pillow pypdf torch transformers

first run may take a few minutes while models download locally.

---

## usage

preview first (safe):

python semantic_sorter.py "/path/to/your/folder" --dry-run

example:

python semantic_sorter.py ~/Downloads --dry-run

---

apply for real:

python semantic_sorter.py "/path/to/your/folder"

---

undo last run:

python semantic_sorter.py "/path/to/your/folder" --undo

---

## reclaim disk space (optional)

to remove downloaded model caches:

python purge_models.py

to remove models and uninstall python packages:

python purge_models.py --full

---

## project status

this project is under active iteration. focus is on handling messy real-world folders reliably and locally.

---

## license

mit license
