# =================================================================
#
# Authors: Tom Kralidis <tomkralidis@gmail.com>
#
# Copyright (c) 2017 Tom Kralidis
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

LOGGER = logging.getLogger(__name__)


class GAWSISClient(object):
    """GAWSIS client API"""

    def __init__(self, url='https://gawsis.meteoswiss.ch/GAWSIS/rest/api/',
                 username=None, password=None):
        """
        Initialize a GAWSIS Client.
        :returns: instance of pyoscar.gawsis.GAWSISClient
        """

        LOGGER.debug('Setting URL: {}'.format(url))
        self.url = url
        """URL to GAWSIS API"""

        self.username = username
        """username"""

        self.password = password
        """password"""

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

        :returns: dictionary of all GAW stations
        """

        LOGGER.info('Searching for all GAW stations')
        try:
            request = os.path.join(self.url,
                                   'stations/approvedStations/gawIds')

            LOGGER.debug('Fetching all GAWSIS identifiers')
            response = requests.get(request, headers=self.headers).json()

            return response

        except StopIteration:
            msg = 'GAW ID not found'
            LOGGER.exception(msg)
            raise RequestError(msg)

    def get_station_report(self, gawid):
        """
        get station information by gawid

        :param gawid: GAW identifier (WIGOS or legacy format)

        :returns: dictionary of station report
        """

        gawid = gawid.upper()

        LOGGER.info('Searching for GAW ID {}'.format(gawid))
        try:
            request = os.path.join(self.url,
                                   'stations/approvedStations/gawIds')

            LOGGER.debug('Fetching all GAWSIS identifiers')
            response = requests.get(request, headers=self.headers).json()

            gawsis_id = next(item for item in response if
                             item['name'] == gawid)['id']

            request = os.path.join(self.url, 'stations/station',
                                   str(gawsis_id), 'stationReport')

            LOGGER.debug('Fetching station report')
            response = requests.get(request, headers=self.headers).json()

            return response

        except StopIteration:
            msg = 'GAW ID not found'
            LOGGER.exception(msg)
            raise RequestError(msg)


class RequestError(Exception):
    """class exception stub"""
    pass


@click.command()
@click.pass_context
@click.option('--gaw-id', '-g', 'gaw_id', help='GAW ID')
def station(ctx, gaw_id):
    """get station report"""

    if gaw_id is None:
        raise click.ClickException(
            'GAW identifier is a required parameter (--gaw-id or -g)')

    g = GAWSISClient()

    response = json.dumps(g.get_station_report(gaw_id), indent=4)

    click.echo_via_pager(response)


@click.command()
@click.pass_context
def all_stations(ctx):
    """get all stations"""

    g = GAWSISClient()

    response = json.dumps(g.get_all_stations(), indent=4)

    click.echo_via_pager(response)
