###############################################################################
#
# The MIT License (MIT)
# Copyright (c) 2018 Tom Kralidis
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to
# deal in the Software without restriction, including without limitation the
# rights to use, copy, modify, merge, publish, distribute, sublicense, and/or
# sell copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
# IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,
# DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR
# OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE
# USE OR OTHER DEALINGS IN THE SOFTWARE.
#
###############################################################################

import json
import io
import os
import unittest

from pyoscar.oscar import OSCARClient

try:
    from unittest import mock
    from unittest.mock import patch
except ImportError:
    from mock import patch
    import mock

THISDIR = os.path.dirname(os.path.realpath(__file__))


def read(filename, encoding='utf-8'):
    """read file contents"""
    full_path = os.path.join(os.path.dirname(__file__), filename)
    with io.open(full_path, encoding=encoding) as fh:
        contents = fh.read().strip()
    return contents


class OSCARTest(unittest.TestCase):
    """Test case for package pyoscar.oscar"""

    @patch('pyoscar.oscar.requests.get')
    def itest_all_stations(self, mock_get):
        """test listing of all stations"""

        mock_response = mock.Mock()
        mock_response.ok = True

        with open(get_abspath('test.all_stations_names.json')) as ff:
            mock_response.json.return_value = json.load(ff)

        mock_get.return_value = mock_response

        o = OSCARClient()
        all_stations = o.get_all_stations()
        self.assertIsInstance(all_stations, list)
        self.assertEqual(all_stations[0], 'A12-CPP')

    @patch('pyoscar.oscar.requests.get')
    def test_get_station_report(self, mock_get):
        """test single station report"""

        mock_response = mock.Mock()
        mock_response.ok = True

        with open(get_abspath('test.all_stations.wmoids.json')) as ff:
            se1 = json.load(ff)
        with open(get_abspath('test.station.json')) as ff:
            se2 = json.load(ff)

        fake_responses = [mock.Mock(), mock.Mock()]
        fake_responses[0].json.return_value = se1
        fake_responses[1].json.return_value = se2

        mock_get.side_effect = fake_responses

        o = OSCARClient()
        station = o.get_station_report('0-20000-0-71758')
        self.assertIsInstance(station, dict)
        self.assertEqual(station['name'], 'SYDNEY CS, NS')
        self.assertEqual(station['wmoIndex'], '0-20000-0-71758')

        mock_response = mock.Mock()
        mock_response.ok = False
        mock_response.status_code = 404
        mock_response.json.return_value = {}

        mock_get.side_effect = [mock_response]

        station = o.get_station_report('non-existent-station')
        self.assertIsInstance(station, dict)
        self.assertEqual(len(station), 0)


def get_abspath(filepath):
    """helper function absolute file access"""

    return os.path.join(THISDIR, filepath)


if __name__ == '__main__':
    unittest.main()
