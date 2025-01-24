###############################################################################
#
# The MIT License (MIT)
# Copyright (c) 2023 Tom Kralidis
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

from lxml import etree

from pyoscar import OSCARClient, get_typed_value, get_xpath

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
    """Test case for package pyoscar"""

    @patch('pyoscar.requests.get')
    def itest_stations(self, mock_get):
        """test listing of all stations"""

        mock_response = mock.Mock()
        mock_response.ok = True

        with open(get_abspath('test.all_stations_names.json')) as ff:
            mock_response.json.return_value = json.load(ff)

        mock_get.return_value = mock_response

        o = OSCARClient()
        stations = o.get_stations()
        self.assertIsInstance(stations, list)
        self.assertEqual(stations[0], 'A12-CPP')

    @patch('pyoscar.requests.get')
    def test_get_station_report(self, mock_get):
        """test single station report"""

        mock_response = mock.Mock()
        mock_response.ok = True

        with open(get_abspath('test.station-wigos.json')) as ff:
            sel0 = json.load(ff)
        with open(get_abspath('test.station.json')) as ff:
            sel1 = json.load(ff)

        fake_responses = [mock.Mock(), mock.Mock()]
        fake_responses[0].json.return_value = sel0
        fake_responses[0].text = str(sel0)
        fake_responses[1].json.return_value = sel1
        fake_responses[1].text = str(sel1)

        mock_get.side_effect = fake_responses

        o = OSCARClient()
        station = o.get_station_report('0-20000-0-71758')
        self.assertIsInstance(station, dict)
        self.assertEqual(station['name'], 'SYDNEY CS, NS')
        self.assertEqual(station['wmoIndex'], '0-20000-0-71758')

        mock_response = mock.Mock()
        mock_response.ok = False
        mock_response.status_code = 200
        mock_response.json.return_value = {}

        mock_get.side_effect = [mock_response]

        with self.assertRaises(RuntimeError):
            station = o.get_station_report('non-existent-station')
            self.assertIsInstance(station, dict)
            self.assertEqual(len(station), 0)

    def test_get_station_report_summary(self):
        """test single station report in summary mode"""

        o = OSCARClient()

        data_xml = etree.parse(get_abspath('test.station.xml'))

        summary = o.get_station_report_summary(data_xml)

        keys = [
            'barometer_height',
            'elevation',
            'facility_type',
            'latitude',
            'longitude',
            'station_name',
            'territory_name',
            'wigos_station_identifier',
            'wmo_region'
        ]

        self.assertEqual(sorted(summary.keys()), keys)

    @patch('pyoscar.requests.post')
    def test_upload(self, mock_post):
        """test upload"""

        # test success
        mock_response = mock.Mock()
        mock_post.return_value = mock_response
        mock_response.status_code = 200

        with open(get_abspath('test.upload_success.json')) as fh:
            mock_response.json.return_value = json.load(fh)

        o = OSCARClient()
        result = o.upload('<foo/>')
        self.assertIsInstance(result, dict)
        self.assertEqual(result['id'], 67610)
        self.assertEqual(result['xmlStatus'], 'SUCCESS_WITH_WARNINGS')

        # test error handling
        mock_response = mock.Mock()
        mock_post.return_value = mock_response
        mock_response.status_code = 401

        with open(get_abspath('test.upload_error.html')) as fh:
            mock_response.text = fh.read()

        o = OSCARClient()
        result = o.upload('<foo/>')
        self.assertIsInstance(result, dict)
        self.assertEqual(result['code'], 401)

    def test_get_xpath(self):
        """test get_xpath"""

        data = '''<root>
            <person department="monitoring">
                <firstname>John</firstname>
                <lastname>A</lastname>
            </person>
            <person department="prediction">
                <firstname>Bob</firstname>
                <lastname>B</lastname>
            </person>
        </root>
        '''

        data = etree.fromstring(data)

        person1 = get_xpath(data, '//person/firstname')
        self.assertIsInstance(person1, str)
        self.assertEqual(person1, 'John')

        person1_department = get_xpath(data, '//person/@department')
        self.assertIsInstance(person1_department, str)
        self.assertEqual(person1_department, 'monitoring')

        persons = get_xpath(data, '//person/firstname', first=False)
        self.assertIsInstance(persons, list)
        self.assertEqual(len(persons), 2)

    def test_get_typed_value(self):
        """test get_typed_value"""

        self.assertIsInstance(get_typed_value('1'), int)
        self.assertIsInstance(get_typed_value('1.2'), float)
        self.assertIsInstance(get_typed_value('1.2.0'), str)
        self.assertIsInstance(get_typed_value('foo'), str)


def get_abspath(filepath):
    """helper function absolute file access"""

    return os.path.join(THISDIR, filepath)


if __name__ == '__main__':
    unittest.main()
