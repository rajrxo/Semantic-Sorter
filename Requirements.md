# quick setup

follow the steps below to get semantic sorter running locally.

## step 1 create virtual environment (optional but recommended)

python -m venv venv

this creates an isolated python environment for the project.

## step 2 activate the environment

mac or linux:

source venv/bin/activate

windows:

venv\Scripts\activate

after activation you should see (venv) in your terminal.

## step 3 install python dependencies

pip install sentence-transformers scikit-learn numpy pillow pypdf torch transformers

this installs all required python packages.

note: the first run may take a few minutes because the embedding and vision models download locally.

no external apis are used. everything runs fully offline after the initial download.
