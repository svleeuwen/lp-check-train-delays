import base64
from datetime import datetime
import urllib2
from xml.etree import ElementTree

__author__ = 'Sander'


class NSApi(object):
    DELAYED_MESSAGE = 'VERTRAAGD'
    DATE_TIME_FORMAT = '%Y-%m-%dT%H:%M:%S'
    TIME_FROM = '08:55'
    TIME_UNTIL = '09:10'

    BASE_URL = "http://webservices.ns.nl/ns-api-treinplanner?fromStation=%(from_station)s&toStation=%(to_station)s&dateTime=%(departure_time)s&hslAllowed=%(include_highspeed)s&previousAdvices=%(num_previous_advices)s"

    def __init__(self, auth_string):
        self.auth_string = base64.urlsafe_b64encode(auth_string)

    def get(self, from_station, to_station, departure_time, include_highspeed='true', num_previous_advices=0):
        url = self.BASE_URL % dict(from_station=from_station,
                                   to_station=to_station,
                                   departure_time=self._strftime(departure_time),
                                   include_highspeed=include_highspeed,
                                   num_previous_advices=num_previous_advices)
        print url

        request = urllib2.Request(url)
        request.add_header("Authorization", "Basic %s" % self.auth_string)
        xml = urllib2.urlopen(request)
        return self.parse_result(xml)

    def parse_result(self, xml):
        tree = ElementTree.parse(xml)
        travel_options = tree.findall('ReisMogelijkheid')
        delays = []
        for option in travel_options:
            if not option.find('Status').text == self.DELAYED_MESSAGE:
                #pass
                continue
            delays.append({
                'departure_planned': self._strptime(option.find('GeplandeVertrekTijd').text),
                'departure_planned_str': self._strptime(option.find('GeplandeVertrekTijd').text).strftime('%H:%M'),
                'departure_actual': self._strptime(option.find('ActueleVertrekTijd').text),
                'departure_actual_str': self._strptime(option.find('ActueleVertrekTijd').text).strftime('%H:%M'),
                'delay': option.find('VertrekVertraging').text,
                'train_type': option.find('ReisDeel').find('VervoerType').text
            })
        return delays

    def _strptime(self, datetime_string):
        # parse to datetime, strip timezone
        return datetime.strptime(datetime_string[:-5], self.DATE_TIME_FORMAT).time()

    def _strftime(self, date_time):
        return datetime.strftime(date_time, self.DATE_TIME_FORMAT)