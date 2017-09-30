# pyoscar

Pythonic API to WMO OSCAR

[![Build Status](https://travis-ci.org/OGCMetOceanDWG/pyoscar.png)](https://travis-ci.org/OGCMetOceanDWG/pyoscar)
[![Coverage Status](https://coveralls.io/repos/github/OGCMetOceanDWG/pyoscar/badge.svg?branch=master)](https://coveralls.io/github/OGCMetOceanDWG/pyoscar?branch=master)

# Overview

TODO

# Installation

## Requirements
- Python 3.  Should work with 2.7
- [virtualenv](https://virtualenv.pypa.io/)

### Dependencies
Dependencies are listed in [requirements.txt](requirements.txt). Dependencies
are automatically installed during pyoscar installation.

## Installing pyoscar

```bash
# setup virtualenv
virtualenv --system-site-packages -p python3 pyoscar
cd pyoscar
source bin/activate

# clone codebase and install
git clone https://github.com/OGCMetOceanDWG/pyoscar.git
cd pyoscar
python setup.py build
python setup.py install
```

## Running pyoscar

```bash
# run GAWSIS query via pygawsis
pygawsis station --gaw-id LEO

```

## Development

### Running Tests

```bash
# install dev requirements
pip install -r requirements-dev.txt

# run tests like this:
cd pyoscar/tests
python run_tests.py

# or like this:
python setup.py test

# measure code coverage
coverage run --source=pyoscar -m unittest pyoscar.tests.run_tests
coverage report -m
```

### Code Conventions

* [PEP8](https://www.python.org/dev/peps/pep-0008)

### Bugs and Issues

All bugs, enhancements and issues are managed on [GitHub](https://github.com/OGCMetOceanDWG/pyoscar/issues).

## Contact

* [Tom Kralidis](https://github.com/tomkralidis)
