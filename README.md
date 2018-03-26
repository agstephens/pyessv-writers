# pyessv-writers

Writer scripts for all vocabs we managed with PYESSV.

## Installing dependencies

```
git clone https://github.com/agstephens/pyessv-writers
cd pyessv-writers/

virtualenv venv
. venv/bin/activate

pip install pyessv
```

## Usage

For example, with UKCP18:

```
python src/write_ukcp18_cvs.py --source=../UKCP18_CVs
```

Which writes CVs to:

```
~/.esdoc/pyessv-archive/ukcp/ukcp18
```
