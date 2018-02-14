# =================================================================
#
# Authors: Tom Kralidis <tomkralidis@gmail.com>
#
# Copyright (c) 2018 Tom Kralidis
#
# Permission is hereby granted, free of charge, to any person
# obtaining a copy of this software and associated documentation
# files (the "Software"), to deal in the Software without
# restriction, including without limitation the rights to use,
# copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the
# Software is furnished to do so, subject to the following
# conditions:
#
# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES
# OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
# HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
# WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
# FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
# OTHER DEALINGS IN THE SOFTWARE.
#
# =================================================================

import json
import logging
import os
import requests

import click

from pyoscar import __version__

LOGGER = logging.getLogger(__name__)


class OSCARClient(object):
    """OSCAR client API"""

    def __init__(self, url='https://oscar.wmo.int/surface/rest/api/',
                 username=None, password=None, timeout=30):
        """
        Initialize an OSCAR Client.
        :returns: instance of pyoscar.oscar.OSCARClient
        """

        LOGGER.debug('Setting URL: {}'.format(url))
        self.url = url
        """URL to OSCAR API"""

        self.version = None
        """API version"""

        self.username = username
        """username"""

        self.password = password
        """password"""

        self.timeout = password
        """timeout (seconds)"""

        self.token = None
        """authentication token"""

        self.headers = {
            'User-Agent': 'pyoscar: https://github.com/WMO-ET-WDC/pyoscar'
        }
        """HTTP headers dictionary applied with requests"""

        if username is not None and password is not None:
            raise NotImplementedError('Authentication not yet supported')

    def get_all_stations(self, program=None):
        """
        get all stations

        :param program: program/network (currently only GAW supported)

        :returns: list of all stations
        """

        LOGGER.info('Searching for all stations')

        params = {
            'q': '',
            'page': 1,
            'pageSize': 100000
        }

        LOGGER.debug('Fetching all WMO identifiers')

        if program is not None and program.lower() == 'gaw':
            LOGGER.debug('Fetching only GAW stations')
            request = os.path.join(self.url,
                                   'stations/approvedStations/gawIds')
        else:
            request = os.path.join(self.url,
                                   'stations/approvedStations/wmoIds')

        response = requests.get(request, headers=self.headers, params=params)
        LOGGER.debug('Request: {}'.format(response.url))
        LOGGER.debug('Response: {}'.format(response.status_code))

        wmoids = response.json()

        return [x['text'] for x in wmoids]

    def get_contact(self, country, surname, organization):
        """
        get contact information

        :param country: Country name
        :param surname: Surname of contact
        :param organization: Organization of contact

        returns: dictionary of matching contact
        """

        ids = []
        matches = []

        LOGGER.debug('Fetching all contacts')

        request = os.path.join(self.url, 'contacts')
        response = requests.get(request, headers=self.headers)
        LOGGER.debug('Request: {}'.format(response.url))
        LOGGER.debug('Response: {}'.format(response.status_code))

        for c in response.json():
            if country is not None and country == c['countryName']:
                ids.append(c['id'])
            if surname is not None and surname == c['surname']:
                ids.append(c['id'])
            if organization is not None and organization == c['organization']:
                ids.append(c['id'])

        for id_ in ids:
            LOGGER.debug('Fetching contact {}'.format(id_))
            request = os.path.join(self.url, 'contacts/contact', str(id_))
            response = requests.get(request, headers=self.headers)
            LOGGER.debug('Request: {}'.format(response.url))
            LOGGER.debug('Response: {}'.format(response.status_code))
            matches.append(response.json())

        return matches

    def get_station_report(self, identifier):
        """
        get station information by WIGOS or WMO identifier

        :param identifier: identifier (WIGOS or WMO identifier)

        :returns: dictionary of matching station report
        """

        if '-' in identifier:
            identifier_ = identifier.split('-')[-1]
        else:
            identifier_ = identifier

        found = False
        found_identifier = None

        params = {
            'q': '',
            'page': 1,
            'pageSize': 100000
        }

        request = os.path.join(self.url,
                               'stations/approvedStations/wmoIds')

        LOGGER.debug('Fetching all identifiers')
        response = requests.get(request, headers=self.headers,
                                params=params)
        LOGGER.debug('Request: {}'.format(response.url))
        LOGGER.debug('Response: {}'.format(response.status_code))

        i = response.json()
        for item in i:
            if '-' in identifier:
                if item['text'] == identifier:
                    found = True
                    found_identifier = item['id']
            else:
                if item['text'].endswith(identifier_):
                    found = True
                    found_identifier = item['id']

        if found:
            LOGGER.debug('Fetching station report {}'.format(found_identifier))
            request = os.path.join(self.url, 'stations/station',
                                   found_identifier, 'stationReport')

            response = requests.get(request, headers=self.headers)
            LOGGER.debug('Request: {}'.format(response.url))
            LOGGER.debug('Response: {}'.format(response.status_code))

            return response.json()
        else:
            LOGGER.warning('Station not found')
            return {}


class RequestError(Exception):
    """class exception stub"""
    pass


@click.group()
@click.version_option(version=__version__)
def cli():
    pass


@click.command()
@click.pass_context
@click.option('--country', '-c', help='Country')
@click.option('--surname', '-s', help='Surname')
@click.option('--organization', '-o', help='Organization')
@click.option('--verbosity', '-v',
              type=click.Choice(['ERROR', 'WARNING', 'INFO', 'DEBUG']),
              help='Verbosity')
def contact(ctx, country=None, surname=None, organization=None,
            verbosity=None):
    """get contact information"""

    if all([country is None, surname is None, organization is None]):
        raise click.ClickException(
            'one of --country/-c, --station/-s or --contributor/-o required')

    if verbosity is not None:
        logging.basicConfig(level=getattr(logging, verbosity))
    else:
        logging.getLogger(__name__).addHandler(logging.NullHandler())

    o = OSCARClient()

    response = json.dumps(o.get_contact(country, surname, organization),
                          indent=4)

    click.echo_via_pager(response)


@click.command()
@click.pass_context
@click.option('--identifier', '-i',
              help='identifier (WIGOS or WMO identifier')
@click.option('--verbosity', '-v',
              type=click.Choice(['ERROR', 'WARNING', 'INFO', 'DEBUG']),
              help='Verbosity')
def station(ctx, identifier, verbosity=None):
    """get station report"""

    if identifier is None:
        raise click.ClickException(
            'WIGOS or WMO identifier is a required parameter (-i)')

    if verbosity is not None:
        logging.basicConfig(level=getattr(logging, verbosity))
    else:
        logging.getLogger(__name__).addHandler(logging.NullHandler())

    o = OSCARClient()

    response = json.dumps(o.get_station_report(identifier), indent=4)

    click.echo_via_pager(response)


@click.command()
@click.pass_context
@click.option('--program', '-p', help='Program (currently only GAW supported)')
@click.option('--verbosity', '-v',
              type=click.Choice(['ERROR', 'WARNING', 'INFO', 'DEBUG']),
              help='Verbosity')
def all_stations(ctx, program=None, verbosity=None):
    """get all stations"""

    if verbosity is not None:
        logging.basicConfig(level=getattr(logging, verbosity))
    else:
        logging.getLogger(__name__).addHandler(logging.NullHandler())

    o = OSCARClient()

    response = json.dumps(o.get_all_stations(program=program), indent=4)

    click.echo_via_pager('Number of stations: {}\nStations:\n{}'.format(
        len(response), response))


cli.add_command(contact)
cli.add_command(station)
cli.add_command(all_stations)
