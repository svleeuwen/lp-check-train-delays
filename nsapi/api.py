import base64
from datetime import datetime
import urllib2
from xml.etree import ElementTree

__author__ = 'Sander'



DATE_TIME_FORMAT = '%Y-%m-%dT%H:%M:%S'
DELAYED_MESSAGE = 'VERTRAAGD'


class NSApi(object):

    TIME_FROM = '08:55'
    TIME_UNTIL = '09:10'

    BASE_URL = "http://webservices.ns.nl/ns-api-treinplanner?fromStation=%(from_station)s&toStation=%(to_station)s&hslAllowed=%(include_highspeed)s&previousAdvices=%(num_previous_advices)s"

    def __init__(self, auth_string):
        self.auth_string = base64.urlsafe_b64encode(auth_string)

    def get(self, from_station, to_station, include_highspeed=True, num_previous_advices=0):
        url = self.BASE_URL % dict(from_station=from_station,
                                   to_station=to_station,
                                   include_highspeed=include_highspeed,
                                   num_previous_advices=num_previous_advices)

        request = urllib2.Request(url)
        request.add_header("Authorization", "Basic %s" % self.auth_string)
        xml = urllib2.urlopen(request)
        return self.parse_result(xml)

    def parse_result(self, xml):
        tree = ElementTree.parse(xml)
        travel_options = tree.findall('ReisMogelijkheid')
        delays = []
        for option in travel_options:
            if not option.find('Status').text == DELAYED_MESSAGE:
                #pass
                continue
            delay = {'departure_planned': self._parse_time(option.find('GeplandeVertrekTijd').text),
                     'departure_actual': self._parse_time(option.find('ActueleVertrekTijd').text),
                     'delay': option.find('VertrekVertraging').text,
                     'train_type': option.find('ReisDeel').find('VervoerType').text}
            delays.append(delay)
        return delays

    def _parse_time(self, datetime_string):
        return datetime.strptime(datetime_string[:-5], DATE_TIME_FORMAT).strftime('%H:%M')