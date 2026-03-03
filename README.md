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

### Before
<img width="1303" height="781" alt="image" src="https://github.com/user-attachments/assets/579779e4-7864-43b2-afe6-181b0ffcfc1c" />
<img width="131" height="124" alt="image" src="https://github.com/user-attachments/assets/416c9282-6cb0-4856-b9f4-8d6584140edf" />

### After
<img width="1319" height="963" alt="image" src="https://github.com/user-attachments/assets/18b5987f-6207-405f-8455-a62092972f87" />
<img width="127" height="122" alt="image" src="https://github.com/user-attachments/assets/edaa6e71-5037-429c-abbc-89310aa54a6a" />
Lets ignore that.



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

Install Python(skip this if you have python already installed)

### Windows
winget install Python.Python.3.12

### Mac or Linux
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
(run the commands homebrew asks you to run)
brew install python

### step 0 Set directory to the folder Semantic_Sorter.py is 

cd /path/to/the/folder/wherescriptis

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

first run may take a few minutes while models download locally so bear with it 

---

## usage

preview first (safe):

python Semantic_Sorter.py "/path/to/your/folder" --dry-run

example:

python Semantic_Sorter.py ~/Downloads --dry-run

---

apply for real:

python Semantic_Sorter.py "/path/to/your/folder"

---

undo last run:

python Semantic_Sorter.py "/path/to/your/folder" --undo

---

## reclaim disk space (optional)

to remove downloaded model caches:

python Purge_Models.py

to remove models and uninstall python packages:

python Purge_Models.py --full

---

## project status

this project is under active iteration. focus is on handling messy real-world folders reliably and locally.

---

## license

mit license
