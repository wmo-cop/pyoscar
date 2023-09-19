# =================================================================
#
# Authors: Tom Kralidis <tomkralidis@gmail.com>
#
# Copyright (c) 2023 Tom Kralidis
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

__version__ = '0.6.4'

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

FACILITY_TYPE_LOOKUP = {
    'seaMobile': 'Sea (mobile)',
    'underwaterFixed': 'Underwater (fixed)',
    'underwaterMobile': 'Underwater (mobile)',
    'airMobile': 'Air (mobile)',
    'lakeRiverMobile': 'Lake/River (mobile)',
    'seaOnIce': 'Sea (on ice)',
    'landMobile': 'Land (mobile)',
    'landFixed': 'Land (fixed)',
    'lakeRiverFixed': 'Lake/River (fixed)',
    'seaFixed': 'Sea (fixed)',
    'airFixed': 'Air (fixed)',
    'landOnIce': 'Land (on ice)'
}


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
            if country is not None and country.casefold() == c['countryName'].casefold():  # noqa:
                ids.append(c['id'])
            if surname is not None and surname.casefold() == c.get('surname', c.get('surnameName')).casefold():  # noqa
                ids.append(c['id'])
            if organization is not None and organization.casefold() == c['organization'].casefold():  # noqa
                ids.append(c['id'])

        for id_ in ids:
            LOGGER.debug(f'Fetching contact {id_}')
            request = f'{self.api_url}/contacts/contact/{id_}'
            response = requests.get(request, headers=self.headers)
            LOGGER.debug(f'Request: {response.url}')
            LOGGER.debug(f'Response: {response.status_code}')
            matches.append(response.json())

        return matches

    def get_station_report(self, identifier: str, summary=False,
                           format_: str = 'JSON') -> Union[dict, etree.Element]:  # noqa
        """
        get station information by WIGOS identifier

        :param identifier: identifier (WIGOS identifier)
        :param summary: whether to provide a summary report (default `False`)
        :param format_: format (JSON [default] or XML)

        :returns: `dict` of JSON payload or summary, or `etree.Element` of
                  matching station report WMDR XML
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
            response = etree.fromstring(response.content)
        else:
            response = response.json()

        if summary:
            LOGGER.debug('Generating report summary')
            return self.get_station_report_summary(response)
        else:
            return response

    def get_station_report_summary(self, station: Union[dict, etree.Element]) -> dict:  # noqa
        """
        Provide station summary report

        :param station: `dict` of JSON or `etree.Element` of WMDR XML

        :returns: `dict` of summary
        """

        summary = {}

        if isinstance(station, dict):  # dict
            summary['station_name'] = station['name']
            summary['wigos_station_identifier'] = station['wigosIds'][0]['wid']
            summary['facility_type'] = station['typeName']
            summary['latitude'] = station['locations'][0]['latitude']
            summary['longitude'] = station['locations'][0]['longitude']
            summary['elevation'] = station['locations'][0].get('elevation')
            summary['barometer_height'] = None
            summary['territory_name'] = station['territories'][0]['territoryName']  # noqa
            summary['wmo_region'] = station['wmoRaId']

        else:  # etree.Element
            station_name = get_xpath(
                station, '//wmdr:ObservingFacility/gml:name')

            wigos_station_identifier = get_xpath(
                station, '//wmdr:ObservingFacility/gml:identifier').split(',')[0]  # noqa

            facility_type = get_xpath(
                station, '//wmdr:ObservingFacility//wmdr:facilityType/@xlink:href')  # noqa

            if not facility_type:
                facility_type = None
            else:
                facility_type = facility_type.split('/')[-1]

            wmo_region = get_xpath(
                station, '//wmdr:ObservingFacility//wmdr:wmoRegion/@xlink:href')  # noqa

            if not wmo_region:
                wmo_region = None
            else:
                wmo_region = wmo_region.split('/')[-1]

            territory_name = get_xpath(
                station, '//wmdr:ObservingFacility//wmdr:territoryName/@xlink:href')  # noqa

            if not territory_name:
                territory_name = None
            else:
                territory_name = territory_name.split('/')[-1]

            summary['station_name'] = station_name
            summary['wigos_station_identifier'] = wigos_station_identifier
            summary['facility_type'] = FACILITY_TYPE_LOOKUP[facility_type]
            summary['wmo_region'] = wmo_region
            summary['territory_name'] = territory_name

            geometry = get_xpath(
                station, '//wmdr:ObservingFacility//wmdr:geoLocation//gml:pos')

            if geometry is None:
                LOGGER.debug('No facility geometry found')

            geometry = geometry.split()
            summary['latitude'] = get_typed_value(geometry[0])
            summary['longitude'] = get_typed_value(geometry[1])

            if geometry is not None and len(geometry) == 3:
                LOGGER.debug('Found elevation')
                summary['elevation'] = get_typed_value(geometry[2])
            else:
                summary['elevation'] = None

            xpath = '//wmdr:Process//wmdr:Deployment//wmdr:Equipment[gml:identifier/@codeSpace="http://codes.wmo.int/wmdr/ObservedVariableAtmosphere/216"]//wmdr:geoLocation//gml:pos'  # noqa

            barometer_height = get_xpath(station, xpath)
            if barometer_height is not None:
                summary['barometer_height'] = get_typed_value(
                    barometer_height.split()[-1])
            else:
                summary['barometer_height'] = barometer_height

        return summary

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

            xml = etree.fromstring(response.text).getroot()
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

        use_only_gml_ids_str = str(only_use_gml_ids).upper()

        LOGGER.debug(f'useOnlyGmlIds: {use_only_gml_ids_str}')

        params = {
            'useOnlyGmlIds': use_only_gml_ids_str
        }

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


def get_xpath(element: etree.Element, xpath: str,
              first: bool = True) -> Union[str, list]:
    """
    Helper function to retrieve a given XPath fron a WMDR document.

    :param element: `etree.Element` of WMDR XML
    :param xpath: `str` of valid W3C XPath expression
    :param first: `bool` of whether to return all matches (default `True`)

    :returns: value of matching XPath(s)
    """

    namespaces = {
        'wmdr': 'http://def.wmo.int/wmdr/2017',
        'gml': 'http://www.opengis.net/gml/3.2',
        'xlink': 'http://www.w3.org/1999/xlink'
    }

    LOGGER.debug(f'Searching for xpath {xpath}')
    value = element.xpath(xpath, namespaces=namespaces)

    if not first:
        LOGGER.debug('Returning all matching nodes')
        return value

    LOGGER.debug(f'Value: {value}')

    if len(value) == 0:
        LOGGER.debug('No matches')
        return None

    LOGGER.debug('Returning first matching node')
    value = value[0]

    if isinstance(value, str):
        return value
    else:
        return value.text


def get_typed_value(value) -> Union[float, int, str]:
    """
    Derive true type from data value

    :param value: value

    :returns: value as a native Python data type
    """

    try:
        if '.' in value:  # float?
            value2 = float(value)
        elif len(value) > 1 and value.startswith('0'):
            value2 = value
        else:  # int?
            value2 = int(value)
    except ValueError:  # string (default)?
        value2 = value

    return value2


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
@click.argument('identifier')
@click.option('--summary', '-s', 'summary', is_flag=True, default=False,
              help='Provide summary report')
@click.option('--format', '-f', 'format_', type=click.Choice(['JSON', 'XML']),
              default='JSON', help='Format')
def station(ctx, env, identifier, summary=False, format_='JSON',
            verbosity=None):
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
        response = o.get_station_report(identifier, summary, format_)
    except RuntimeError as err:
        raise click.ClickException(err)

    if summary:
        click.echo(json.dumps(response, indent=4))
        return

    if format_ == 'XML':
        response = etree.tostring(response, pretty_print=1)
    else:
        response = json.dumps(response, indent=4)

    click.echo(response)


@click.command('stations')
@click.pass_context
@cli_options.OPTION_COUNTRY
@cli_options.OPTION_ENV
@cli_options.OPTION_VERBOSITY
@click.option('--program', '-p', help='Program Affiliation')
@click.option('--station-type', '-st', help='Station type',
              type=click.Choice(FACILITY_TYPE_LOOKUP.keys()))
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
@click.option('--gml-ids/--no-gml-ids', default=True, help='use GML ids')
def upload(ctx, api_token, env, xml, log, gml_ids=True,
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

    click.echo(f'Sending {xml} to OSCAR {env} environment ({o.api_url})')

    with open(xml) as fh:
        data = fh.read()

    response = o.upload(data, only_use_gml_ids=gml_ids)

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
