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
            'User-Agent': 'pyoscar: https://github.com/OGCMetOceanDWG/pyoscar'
        }
        """HTTP headers dictionary applied with requests"""

        if username is not None and password is not None:
            raise NotImplementedError('Authentication not yet supported')

    def get_all_stations(self):
        """
        get all stations

        :returns: dictionary of all stations
        """

        LOGGER.info('Searching for all stations')
        request = os.path.join(self.url,
                               'stations/approvedStations/wmoIds')

        LOGGER.debug('Fetching all WMO identifiers')
        response = requests.get(request, headers=self.headers)
        print(response.status_code)
        response = requests.get(request, headers=self.headers).json()

        return response

    def get_station_report(self, wmoid):
        """
        get station information by wmoid

        :param wmoid: WMO identifier (WIGOS or legacy format)

        :returns: dictionary of station report
        """

        wmoid = wmoid.upper()

        LOGGER.info('Searching for WMO ID {}'.format(wmoid))
        try:
            request = os.path.join(self.url,
                                   'stations/approvedStations/wmoIds')

            LOGGER.debug('Fetching all WMO identifiers')
            response = requests.get(request, headers=self.headers).json()

            wmo_id = next(item for item in response if
                          item['name'] == wmoid)['id']

            request = os.path.join(self.url, 'stations/station',
                                   str(wmo_id), 'stationReport')

            LOGGER.debug('Fetching station report')
            response = requests.get(request, headers=self.headers).json()

            return response

        except StopIteration:
            msg = 'WMO ID not found'
            LOGGER.exception(msg)
            raise RequestError(msg)


class RequestError(Exception):
    """class exception stub"""
    pass


@click.group()
@click.version_option(version=__version__)
def cli():
    pass


@click.command()
@click.pass_context
@click.option('--wmo-id', '-w', 'wmo_id', help='WMO ID')
def station(ctx, wmo_id):
    """get station report"""

    if wmo_id is None:
        raise click.ClickException(
            'WMO identifier is a required parameter (--wmo-id or -w)')

    w = OSCARClient()

    response = json.dumps(w.get_station_report(wmo_id), indent=4)

    click.echo_via_pager(response)


@click.command()
@click.pass_context
def all_stations(ctx):
    """get all stations"""

    g = OSCARClient()

    response = json.dumps(g.get_all_stations(), indent=4)

    click.echo_via_pager(response)


cli.add_command(station)
cli.add_command(all_stations)
