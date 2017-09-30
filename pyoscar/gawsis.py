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

    def get_station_report(self, gawid, responseformat='JSON', pretty=False):
        """get station information by gawid"""

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

            print(responseformat)
            if responseformat == 'JSON':
                if pretty:
                    return json.dumps(response, indent=4)
                else:
                    return response
            else:
                raise NotImplementedError()

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
@click.option('--format', '-f', 'format_', default='JSON',
              help='Output format (XML or JSON [default])')
def station(ctx, gaw_id, format_):
    """get station report"""

    if gaw_id is None:
        raise click.ClickException(
            'GAW identifier is a required parameter (--gaw-id or -g)')

    g = GAWSISClient()

    click.echo_via_pager(g.get_station_report(gaw_id, responseformat=format_,
                         pretty=True))
