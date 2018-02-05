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

    def get_all_stations(self):
        """
        get all stations

        :returns: list of all stations
        """

        LOGGER.info('Searching for all stations')

        params = {
            'q': '',
            'page': 1,
            'pageSize': 100000
        }

        LOGGER.debug('Fetching all WMO identifiers')
        request = os.path.join(self.url,
                               'stations/approvedStations/wmoIds')
        LOGGER.debug('URL: {}'.format(request))
        response = requests.get(
            request, headers=self.headers, params=params)
        wmoids = response.json()

        return [x['text'] for x in wmoids]

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

        LOGGER.info('Searching for identifier {}'.format(identifier_))
        LOGGER.debug('Fetching station report')
        request = os.path.join(self.url, 'stations/station',
                               identifier_, 'stationReport')

        LOGGER.debug('URL: {}'.format(request))
        response = requests.get(request, headers=self.headers)

        if not response.ok:
            LOGGER.debug('Request not ok')
            if response.status_code == 404:
                LOGGER.debug('Station not found')
                return {}
            else:
                msg = 'API request error {}'.format(response.status_code)
                LOGGER.warning(msg)
                raise RequestError(msg)

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
@click.option('--identifier', '-i',
              help='identifier (WIGOS or WMO identifier')
def station(ctx, identifier):
    """get station report"""

    if identifier is None:
        raise click.ClickException(
            'WIGOS or WMO identifier is a required parameter (-i)')

    o = OSCARClient()

    response = json.dumps(o.get_station_report(identifier), indent=4)

    click.echo_via_pager(response)


@click.command()
@click.pass_context
def all_stations(ctx):
    """get all stations"""

    o = OSCARClient()

    response = json.dumps(o.get_all_stations(), indent=4)

    click.echo_via_pager('Number of stations: {}\nStations:\n{}'.format(
        len(response), response))


cli.add_command(station)
cli.add_command(all_stations)
