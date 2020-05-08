# =================================================================
#
# Authors: Tom Kralidis <tomkralidis@gmail.com>
#
# Copyright (c) 2020 Tom Kralidis
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

__version__ = '0.1.0'

import json
import logging
import os
import requests

import click

LOGGER = logging.getLogger(__name__)


class OSCARClient(object):
    """OSCAR client API"""

    def __init__(self, env='depl', api_token=None, timeout=30):
        """
        Initialize an OSCAR Client.

        :returns: `pyoscar.OSCARClient`
        """

        self.env = env
        """OSCAR environment (depl or prod)"""

        self.url = None
        """URL to OSCAR API"""

        self.version = None
        """API version"""

        self.api_token = api_token
        """authentication token"""

        self.timeout = timeout
        """timeout (seconds)"""

        self.headers = {
            'User-Agent': 'pyoscar: https://github.com/wmo-cop/pyoscar'
        }
        """HTTP headers dictionary applied with requests"""

        LOGGER.debug('Setting URL')
        if self.env == 'prod':
            self.url = 'https://oscar.wmo.int/surface/rest/api/'
        else:
            self.url = 'https://oscardepl.wmo.int/surface/rest/api/'

        if self.api_token is not None:
            self.headers['X-WMO-WMDR-Token'] = self.api_token

    def get_stations(self, program=None, country=None):
        """
        get all stations

        :param program: program/network
        :param country: 3 letter country name

        :returns: `list` of all matching stations
        """

        request = os.path.join(self.url, 'search/station')

        LOGGER.info('Searching for stations')

        params = {}

        if program is not None:
            LOGGER.debug('Program: {}'.format(program))
            params['programAffiliation'] = program
        if country is not None:
            LOGGER.debug('Country: {}'.format(program))
            params['territoryName'] = country

        response = requests.get(request, headers=self.headers, params=params)
        LOGGER.debug('Request: {}'.format(response.url))
        LOGGER.debug('Response: {}'.format(response.status_code))

        return response.json()

    def get_contact(self, country, surname, organization):
        """
        get contact information

        :param country: Country name
        :param surname: Surname of contact
        :param organization: Organization of contact

        returns: `dict` of matching contact
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

    def get_station_report(self, identifier, format_='JSON'):
        """
        get station information by WIGOS or WMO identifier

        :param identifier: identifier (WIGOS or WMO identifier)
        :param format_: format (JSON [default] or XML)

        :returns: `dict` of matching station report
        """

        LOGGER.debug('Fetching station report {}'.format(identifier))
        if format_ == 'XML':
            LOGGER.debug('Trying WIGOS XML download')
            request = os.path.join(self.url, 'wmd/download', identifier)
        else:
            request = os.path.join(self.url, 'stations/station',
                                   identifier, 'stationReport')

        response = requests.get(request, headers=self.headers)
        LOGGER.debug('Request: {}'.format(response.url))
        LOGGER.debug('Response: {}'.format(response.status_code))

        response.raise_for_status()

        if format_ == 'XML':
            return response.text
        else:
            return response.json()

    def upload(self, xml_data):
        """
        upload WMDR XML to OSCAR M2M API

        :param xml: `str` of XML

        :returns: `dict` of result
        """

        url = os.path.join(self.url, 'wmd/upload')

        response = requests.post(url, headers=self.headers, data=xml_data)

        return response.json()


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
@click.option('--env', '-e', default='depl',
              type=click.Choice(['depl', 'prod']),
              help='OSCAR environment to run against (default=depl)')
@click.option('--surname', '-s', help='Surname')
@click.option('--organization', '-o', help='Organization')
@click.option('--verbosity', '-v',
              type=click.Choice(['ERROR', 'WARNING', 'INFO', 'DEBUG']),
              help='Verbosity')
def contact(ctx, env, country=None, surname=None, organization=None,
            verbosity=None):
    """get contact information"""

    if all([country is None, surname is None, organization is None]):
        raise click.ClickException(
            'one of --country/-c, --surname/-s or --organization/-o required')

    if verbosity is not None:
        logging.basicConfig(level=getattr(logging, verbosity))
    else:
        logging.getLogger(__name__).addHandler(logging.NullHandler())

    o = OSCARClient(env=env)

    response = json.dumps(o.get_contact(country, surname, organization),
                          indent=4)

    click.echo(response)


@click.command()
@click.pass_context
@click.option('--env', '-e', default='depl',
              type=click.Choice(['depl', 'prod']),
              help='OSCAR environment to run against (default=depl)')
@click.option('--identifier', '-i',
              help='identifier (WIGOS or WMO identifier')
@click.option('--format', '-f', 'format_', type=click.Choice(['JSON', 'XML']),
              default='JSON', help='Format')
@click.option('--verbosity', '-v',
              type=click.Choice(['ERROR', 'WARNING', 'INFO', 'DEBUG']),
              help='Verbosity')
def station(ctx, env, identifier, format_='JSON', verbosity=None):
    """get station report"""

    if identifier is None:
        raise click.ClickException(
            'WIGOS or WMO identifier is a required parameter (-i)')

    if verbosity is not None:
        logging.basicConfig(level=getattr(logging, verbosity))
    else:
        logging.getLogger(__name__).addHandler(logging.NullHandler())

    o = OSCARClient(env=env)

    if format_ == 'XML':
        response = o.get_station_report(identifier, format_)
    else:
        response = json.dumps(
            o.get_station_report(identifier, format_), indent=4)

    click.echo(response)


@click.command('stations')
@click.pass_context
@click.option('--env', '-e', default='depl',
              type=click.Choice(['depl', 'prod']),
              help='OSCAR environment to run against (default=depl)')
@click.option('--program', '-p', help='Program Affiliation')
@click.option('--country', '-c', help='Country (3 letter country code)')
@click.option('--verbosity', '-v',
              type=click.Choice(['ERROR', 'WARNING', 'INFO', 'DEBUG']),
              help='Verbosity')
def stations(ctx, env, program=None, country=None, verbosity=None):
    """get list of OSCAR stations"""

    if verbosity is not None:
        logging.basicConfig(level=getattr(logging, verbosity))
    else:
        logging.getLogger(__name__).addHandler(logging.NullHandler())

    o = OSCARClient(env=env)
    matching_stations = o.get_stations(program=program, country=country)

    click.echo('Number of stations: {}\nStations:\n{}'.format(
        len(matching_stations), json.dumps(matching_stations, indent=4)))


@click.command()
@click.pass_context
@click.option('--api-token', '-at', 'api_token', help='API token')
@click.option('--env', '-e', default='depl',
              type=click.Choice(['depl', 'prod']),
              help='OSCAR environment to run against (default=depl)')
@click.option('--xml', '-x', help='WMDR XML')
@click.option('--verbosity', '-v',
              type=click.Choice(['ERROR', 'WARNING', 'INFO', 'DEBUG']),
              help='Verbosity')
def upload(ctx, api_token, env, xml, verbosity=None):
    """upload WMDR XML"""

    if verbosity is not None:
        logging.basicConfig(level=getattr(logging, verbosity))
    else:
        logging.getLogger(__name__).addHandler(logging.NullHandler())

    if xml is None:
        raise click.ClickException('--xml/-x required')

    if api_token is None:
        raise click.ClickException('--api-token/-at required')

    o = OSCARClient(api_token=api_token, env=env)
    click.echo('Sending {} to OSCAR {} environment ({})'.format(
               xml, env, o.url))

    with open(xml) as fh:
        data = fh.read()

    response = o.upload(data)

    click.echo(json.dumps(response, indent=4))


cli.add_command(contact)
cli.add_command(station)
cli.add_command(stations)
cli.add_command(upload)
