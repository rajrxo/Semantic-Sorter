# quick setup

follow the steps below to get the sorter running.

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

pip install sentence-transformers scikit-learn numpy pillow pytesseract pypdf

this installs all required python packages.

---

# optional enable image ocr with tesseract

the sorter works without tesseract, but image text extraction will be disabled.

## mac (homebrew)

brew install tesseract

## linux (ubuntu or debian)

sudo apt update
sudo apt install tesseract-ocr

## windows

download tesseract from the official ub mannheim build:
https://github.com/UB-Mannheim/tesseract/wiki

after installing, make sure tesseract is added to your system path.

note: first run may take longer because the embedding model downloads locally.
