# pyoscar

Pythonic API to WMO OSCAR

[![Build Status](https://travis-ci.org/wmo-cop/pyoscar.png)](https://travis-ci.org/wmo-cop/pyoscar)
[![Coverage Status](https://coveralls.io/repos/github/wmo-cop/pyoscar/badge.svg?branch=master)](https://coveralls.io/github/wmo-cop/pyoscar?branch=master)

# Overview

pyoscar provides a Pythonic API atop the WMO [OSCAR](https://oscar.wmo.int/surface/index.html)
and [GAWSIS](https://gawsis.meteoswiss.ch/GAWSIS/index.html) HTTP APIs.

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
git clone https://github.com/wmo-cop/pyoscar.git
cd pyoscar
python setup.py build
python setup.py install
```

## Running pyoscar via the Command Line

```bash
# help
pyoscar --help

# get version
pyoscar --version

# get all station identifiers
pyoscar all_stations 

# get a single station by WMO identifier
pyoscar station --identifier 71151

# get a single station by WIGOS identifier
pyoscar station --identifier 0-20000-0-71151

# add verbose mode (ERROR, WARNING, INFO, DEBUG)
pyoscar station --identifier 0-20000-0-71151 --verbosity=DEBUG

# get contact by country
pyoscar contact -c Canada

# get contact by surname
pyoscar contact -s Karn

# get contact by organization
pyoscar contact -o "Environment Canada"

# gawsis

# get all stations
pygawsis all_stations
# get station report by GAW ID
pygawsis station --gaw-id LEO
```

## Using the pyoscar API

```
from pyoscar.gawsis import GAWSISClient

client = GAWSISClient()

all_stations = client.get_all_stations()
stn_leo = client.get_station_report('LEO')
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

All bugs, enhancements and issues are managed on [GitHub](https://github.com/wmo-cop/pyoscar/issues).

## Contact

* [Tom Kralidis](https://github.com/tomkralidis)
