# pyoscar

Pythonic API to WMO OSCAR

[![Build Status](https://travis-ci.org/wmo-cop/pyoscar.png)](https://travis-ci.org/wmo-cop/pyoscar)
[![Coverage Status](https://coveralls.io/repos/github/wmo-cop/pyoscar/badge.svg?branch=master)](https://coveralls.io/github/wmo-cop/pyoscar?branch=master)

# Overview

pyoscar provides a Pythonic API atop the WMO [OSCAR](https://oscar.wmo.int/surface/index.html) HTTP API.

# Installation

## Requirements
- Python 3
- [virtualenv](https://virtualenv.pypa.io/) or [Conda](https://docs.conda.io)

### Dependencies
Dependencies are listed in [requirements.txt](requirements.txt). Dependencies
are automatically installed during pyoscar installation.

## Installing pyoscar

### For users

```bash
pip install pyoscar
```

### For developers

```bash
# setup virtualenv
python3 -m venv pyoscar
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

# all subcommands support the following options:
# --env (depl or prod, default depl)
# --verbosity (ERROR, WARNING, INFO, DEBUG, default NONE)

# get all station identifiers
pyoscar stations

# get all station identifiers by country
pyoscar stations --country=CAN

# get all station identifiers by program affiliation
pyoscar stations --program=GAW

# get a single station by WMO identifier
pyoscar station --identifier 71151

# get a single station by WIGOS identifier
pyoscar station --identifier 0-20000-0-71151

# get a single station by WIGOS identifier in WIGOS XML format
pyoscar station --identifier 0-20000-0-71151 --format=XML

# add verbose mode (ERROR, WARNING, INFO, DEBUG)
pyoscar station --identifier 0-20000-0-71151 --verbosity=DEBUG

# get contact by country
pyoscar contact -c Canada

# get contact by surname
pyoscar contact -s Karn

# get contact by organization
pyoscar contact -o "Environment Canada"

# upload WMDR XML (to production environment)
pyoscar upload -x /path/to/wmdr.xml -at API_TOKEN -e prod
```

## Using the pyoscar API

```python
from pyoscar import OSCARClient

client = OSCARClient()

# get all Canadian stations
stations = client.get_stations(country='CAN')

# get all Canadian stations
stations = client.get_stations(program='GAW')

# get invididual station report
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

## Releasing

```bash
python setup.py sdist bdist_wheel --universal
twine upload dist/*
```

### Code Conventions

* [PEP8](https://www.python.org/dev/peps/pep-0008)

### Bugs and Issues

All bugs, enhancements and issues are managed on [GitHub](https://github.com/wmo-cop/pyoscar/issues).

## Contact

* [Tom Kralidis](https://github.com/tomkralidis)
