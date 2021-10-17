# =================================================================
#
# Authors: Tom Kralidis <tomkralidis@gmail.com>
#
# Copyright (c) 2021 Tom Kralidis
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

__version__ = '0.4.0'

from datetime import date
import json
import logging
import os
import requests
from typing import Generator, Union

from bs4 import BeautifulSoup
import click
from lxml import etree

from pyoscar import cli_options

LOGGER = logging.getLogger(__name__)

FACILITY_TYPE_LOOKUP = [
    'seaMobile',
    'underwaterFixed',
    'underwaterMobile',
    'airMobile',
    'lakeRiverMobile',
    'seaOnIce',
    'landMobile',
    'landFixed',
    'lakeRiverFixed',
    'seaFixed',
    'airFixed',
    'landOnIce'
]


class OSCARClient:
    """OSCAR client API"""

    def __init__(self, env: str = 'depl', api_token: str = None,
                 timeout: int = 30):
        """
        Initialize an OSCAR Client.

        :returns: `pyoscar.OSCARClient`
        """

        self.env = env
        """OSCAR environment (depl or prod)"""

        self.api_url = None
        """URL to OSCAR API"""

        self.harvest_url = None
        """URL to OSCAR Harvester (OAI)"""

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
            self.api_url = 'https://oscar.wmo.int/surface/rest/api'
            self.harvest_url = 'https://oscar.wmo.int/oai/provider'
        else:
            self.api_url = 'https://oscardepl.wmo.int/surface/rest/api'
            self.harvest_url = 'https://oscardepl.wmo.int/oai/provider'

        if self.api_token is not None:
            self.headers['X-WMO-WMDR-Token'] = self.api_token

    def get_stations(self, program: str = None, country: str = None,
                     station_type: str = None, wigos_id: str = None) -> list:
        """
        get all stations

        :param program: program/network
        :param country: 3 letter country name
        :param station_type: station type:
                             - seaMobile
                             - underwaterFixed
                             - underwaterMobile
                             - airMobile
                             - lakeRiverMobile
                             - seaOnIce
                             - landMobile
                             - landFixed
                             - lakeRiverFixed
                             - seaFixed
                             - airFixed
                             - landOnIce
        :param wigos_id: WIGOS identifier

        :returns: `list` of all matching stations
        """

        request = f'{self.api_url}/search/station'

        LOGGER.info('Searching for stations')

        params = {}

        if wigos_id is not None:
            LOGGER.debug(f'WIGOS ID: {wigos_id}')
            params['wigosId'] = wigos_id
        else:
            if program is not None:
                LOGGER.debug(f'Program: {program}')
                params['programAffiliation'] = program
            if country is not None:
                LOGGER.debug(f'Country: {program}')
                params['territoryName'] = country
            if station_type is not None:
                LOGGER.debug(f'Station type: {station_type}')
                params['facilityType'] = FACILITY_TYPE_LOOKUP[station_type]

        response = requests.get(request, headers=self.headers, params=params)
        LOGGER.debug(f'Request: {response.url}')
        LOGGER.debug(f'Response: {response.status_code}')

        return response.json()

    def get_contact(self, country: str, surname: str,
                    organization: str) -> list:
        """
        get contact information

        :param country: Country name
        :param surname: Surname of contact
        :param organization: Organization of contact

        returns: `list` of matching contacts
        """

        ids = []
        matches = []

        LOGGER.debug('Fetching all contacts')

        request = f'{self.api_url}/contacts'
        response = requests.get(request, headers=self.headers)
        LOGGER.debug(f'Request: {response.url}')
        LOGGER.debug(f'Response: {response.status_code}')

        for c in response.json():
            if country is not None and country == c['countryName']:
                ids.append(c['id'])
            if surname is not None and surname == c['surname']:
                ids.append(c['id'])
            if organization is not None and organization == c['organization']:
                ids.append(c['id'])

        for id_ in ids:
            LOGGER.debug(f'Fetching contact {id_}')
            request = f'{self.api_url}/contacts/contact/{id_}'
            response = requests.get(request, headers=self.headers)
            LOGGER.debug(f'Request: {response.url}')
            LOGGER.debug(f'Response: {response.status_code}')
            matches.append(response.json())

        return matches

    def get_station_report(self, identifier: str,
                           format_: str = 'JSON') -> Union[str, dict]:
        """
        get station information by WIGOS identifier

        :param identifier: identifier (WIGOS identifier)
        :param format_: format (JSON [default] or XML)

        :returns: `dict` or raw XML `str` of matching station report
        """

        LOGGER.debug(f'Searching stations for WIGOS ID: {identifier}')
        response = self.get_stations(wigos_id=identifier)
        if not response or response['totalCount'] == 0:
            msg = f'Station {identifier} not found'
            LOGGER.debug(msg)
            raise RuntimeError(msg)

        identifier = str(response['stationSearchResults'][0]['id'])

        LOGGER.debug(f'Fetching station report {identifier}')
        if format_ == 'XML':
            LOGGER.debug('Trying WIGOS XML download')
            request = f'{self.api_url}/wmd/download/{identifier}'
        else:
            request = f'{self.api_url}/stations/station/{identifier}/stationReport'  # noqa

        response = requests.get(request, headers=self.headers)
        LOGGER.debug(f'Request: {response.url}')
        LOGGER.debug(f'Response: {response.status_code}')

        response.raise_for_status()

        if format_ == 'XML':
            return response.text
        else:
            return response.json()

    def harvest_records(self,
                        date_from: date = None) -> Generator[list, None, None]:
        """
        harvest contents of OSCAR/Surface

        :param date_from: `date` of records modified since

        :returns: `generator` of `lxml.etree._Element` objects
        """

        oai_ns = 'http://www.openarchives.org/OAI/2.0/'
        wmdr_ns = 'http://def.wmo.int/wmdr/2017'

        stop_harvest = False
        resumption_token = None

        while not stop_harvest:
            request = f'{self.harvest_url}?verb=ListRecords'

            if resumption_token is not None:
                request = f'{request}&resumptionToken={resumption_token}'
            else:
                request = f'{request}&metadataPrefix=wmdr'

                if date_from is not None:
                    request = f"{request}&{date_from.strftime('%Y-%m-%d')}"

            response = requests.get(request, headers=self.headers)
            LOGGER.debug(f'Request: {response.url}')
            LOGGER.debug(f'Response: {response.status_code}')

            xml = etree.fromstring(response.text.encode('utf-8'))
            LOGGER.debug(f'Raw XML response:\n{response.text}')
            element = f'{{{oai_ns}}}ListRecords/{{{oai_ns}}}resumptionToken'
            rt = xml.find(element)

            if rt is not None:
                LOGGER.debug(f'resumption token: {rt.text}')
                resumption_token = rt.text
            else:
                LOGGER.debug('stopping harvesting')
                stop_harvest = True

            records = f'{{{oai_ns}}}ListRecords/{{{oai_ns}}}record/{{{oai_ns}}}metadata/{{{wmdr_ns}}}WIGOSMetadataRecord'  # noqa

            identifiers = f'{{{oai_ns}}}ListRecords/{{{oai_ns}}}record/{{{oai_ns}}}header/{{{oai_ns}}}identifier'  # noqa

            yield zip([i.text for i in xml.findall(identifiers)],
                      xml.findall(records))

    def upload(self, xml_data: str, only_use_gml_ids: bool = True) -> dict:
        """
        upload WMDR XML to OSCAR M2M API

        :param xml: `str` of XML
        :param only_use_gml_ids: `bool` of whether to enforce matching
                                 gml:id for supporting elements

        :returns: `dict` of result
        """

        params = {
            'useOnlyGmlIds': 'FALSE'
        }

        if isinstance(only_use_gml_ids, bool):
            params['useOnlyGmlIds'] = str(only_use_gml_ids).upper()

        url = f'{self.api_url}/wmd/upload'

        response = requests.post(url, headers=self.headers, data=xml_data,
                                 params=params)

        if response.status_code != requests.codes.ok:
            LOGGER.debug(response.status_code)
            soup = BeautifulSoup(response.text, 'html.parser')
            err = soup.find_all(id='standardLayouterror')[0].get_text()

            return {
                'code': response.status_code,
                'description': err
            }

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
@cli_options.OPTION_COUNTRY
@cli_options.OPTION_ENV
@cli_options.OPTION_VERBOSITY
@click.option('--surname', '-s', help='Surname')
@click.option('--organization', '-o', help='Organization')
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
@cli_options.OPTION_ENV
@cli_options.OPTION_VERBOSITY
@click.option('--identifier', '-i', help='identifier (WIGOS identifier)')
@click.option('--format', '-f', 'format_', type=click.Choice(['JSON', 'XML']),
              default='JSON', help='Format')
def station(ctx, env, identifier, format_='JSON', verbosity=None):
    """get station report"""

    if identifier is None:
        raise click.ClickException(
            'WIGOS identifier is a required parameter (-i)')

    if verbosity is not None:
        logging.basicConfig(level=getattr(logging, verbosity))
    else:
        logging.getLogger(__name__).addHandler(logging.NullHandler())

    o = OSCARClient(env=env)

    try:
        response = o.get_station_report(identifier, format_)
    except RuntimeError as err:
        raise click.ClickException(err)

    if format_ == 'JSON':
        response = json.dumps(response, indent=4)

    click.echo(response)


@click.command('stations')
@click.pass_context
@cli_options.OPTION_COUNTRY
@cli_options.OPTION_ENV
@cli_options.OPTION_VERBOSITY
@click.option('--program', '-p', help='Program Affiliation')
@click.option('--station-type', '-st', help='Station type',
              type=click.Choice(FACILITY_TYPE_LOOKUP))
def stations(ctx, env, program=None, country=None, station_type=None,
             verbosity=None):
    """get list of OSCAR stations"""

    if verbosity is not None:
        logging.basicConfig(level=getattr(logging, verbosity))
    else:
        logging.getLogger(__name__).addHandler(logging.NullHandler())

    o = OSCARClient(env=env)
    matching_stations = o.get_stations(program=program, country=country)

    result = json.dumps(matching_stations, indent=4)
    click.echo(f'Number of stations: {len(matching_stations)}\nStations:\n{result}')  # noqa


@click.command()
@click.pass_context
@cli_options.OPTION_ENV
@cli_options.OPTION_LOG
@cli_options.OPTION_VERBOSITY
@click.option('--api-token', '-at', 'api_token', help='API token')
@click.option('--xml', '-x', help='WMDR XML')
@click.option('--only-use-gml-ids', '-g', is_flag=True, default=False,
              help='use GML ids')
def upload(ctx, api_token, env, xml, log, only_use_gml_ids=False,
           verbosity=None):
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
    click.echo(f'Sending {xml} to OSCAR {env} environment ({o.url})')

    with open(xml) as fh:
        data = fh.read()

    response = o.upload(data, only_use_gml_ids=only_use_gml_ids)

    response_str = json.dumps(response, indent=4)

    if log is None:
        click.echo(response_str)
    else:
        log.write(response_str + '\n')


@click.command()
@click.pass_context
@cli_options.OPTION_ENV
@cli_options.OPTION_LOG
@cli_options.OPTION_VERBOSITY
@click.option('--from', '-f', 'from_',
              help='Harvest records from a given date (YYYY-MM-DD)')
@click.option('--directory', '-d',
              type=click.Path(file_okay=False, writable=True),
              help='Output directory to save records')
def harvest(ctx, directory, env, from_, log, verbosity=None):
    """harvest OSCAR records"""

    if directory is None:
        raise click.ClickException('--directory/-d not specified')
    if not os.path.exists(directory):
        os.makedirs(directory)
    if verbosity is not None:
        logging.basicConfig(level=getattr(logging, verbosity))
    else:
        logging.getLogger(__name__).addHandler(logging.NullHandler())

    o = OSCARClient(env=env)

    click.echo('Harvesting records')
    for batch in o.harvest_records(from_):
        for identifier, record in batch:
            filename = f'{directory}/{identifier}.xml'
            click.echo(f'saving to {filename}')
            with open(filename, 'wb') as fh:
                fh.write(etree.tostring(record))


cli.add_command(contact)
cli.add_command(harvest)
cli.add_command(station)
cli.add_command(stations)
cli.add_command(upload)
