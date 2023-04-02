# pyoscar

Pythonic API to WMO OSCAR

[![Build Status](https://github.com/wmo-cop/pyoscar/workflows/build%20%E2%9A%99%EF%B8%8F/badge.svg)](https://github.com/wmo-cop/pyoscar/actions)

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

To install the latest stable version:

```bash
pip install pyoscar
```

To keep up to date with stable updates:

```bash
pip install pyoscar -U
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

# upload WMDR XML (to production environment) and save results to file
pyoscar upload -x /path/to/wmdr.xml -at API_TOKEN -e prod -l results.log

# use only GML ids is TRUE by default; use --no-gml-ids to set to FALSE
pyoscar upload -x /path/to/wmdr.xml -at API_TOKEN -e prod -l results.log --no-gml-ids

# harvest all records
pyoscar harvest --env=prod --directory=/path/to/dir
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


# upload WMDR XML

## instantiate client to OSCAR DEPL (default)
client = OSCARClient(api_token='foo')

## ...or to OSCAR production
client = OSCARClient(api_token='foo', env='prod')

with open('some-wmdr-file.xml') as fh:
    data = fh.read()

response = client.upload(data)
```

## Development

### Running Tests

```bash
# install dev requirements
pip install -r requirements-dev.txt

# run tests like this:
cd tests
python run_tests.py

# or like this:
python setup.py test

# measure code coverage
coverage run --source pyoscar setup.py test
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
