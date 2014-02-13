import base64
from datetime import datetime
import urllib
import urllib2
from xml.etree import ElementTree

__author__ = 'Sander'


class NSApi(object):
    DELAYED_MESSAGE = 'VERTRAAGD'
    CANCELED_MESSAGE = 'GEANNULEERD'
    DATE_TIME_FORMAT = '%Y-%m-%dT%H:%M:%S'
    TIME_FROM = '08:55'
    TIME_UNTIL = '09:10'

    BASE_URL = "http://webservices.ns.nl/ns-api-treinplanner?"

    def __init__(self, auth_string):
        self.auth_string = base64.urlsafe_b64encode(auth_string)

    def get(self, from_station, to_station, departure_time, include_highspeed='true', num_previous_advices=0):
        params = dict(fromStation=str(from_station),
                      toStation=str(to_station),
                      dateTime=self._strftime(departure_time),
                      hslAllowed=include_highspeed,
                      previousAdvices=num_previous_advices)
        urlparams = urllib.urlencode(params)

        url = self.BASE_URL + urlparams

        request = urllib2.Request(url)
        request.add_header("Authorization", "Basic %s" % self.auth_string)
        print request.get_full_url()

        try:
            xml = urllib2.urlopen(request)
        except IOError as e:
            return ""
        return self.parse_result(xml)

    def parse_result(self, xml):
        tree = ElementTree.parse(xml)
        travel_options = tree.findall('ReisMogelijkheid')
        delays = []
        for option in travel_options:
            status = option.find('Status').text
            if not status in [self.DELAYED_MESSAGE, self.CANCELED_MESSAGE]:
                #pass
                continue
            #import pdb; pdb.set_trace()
            delay = {
                'departure_planned': self._strptime(option.find('GeplandeVertrekTijd').text if option.find('GeplandeVertrekTijd') is not None else ''),
                'departure_actual': self._strptime(option.find('ActueleVertrekTijd').text if option.find('ActueleVertrekTijd') is not None else ''),
                'delay': option.find('VertrekVertraging').text if option.find('VertrekVertraging') is not None else '?',
                'train_type': option.find('ReisDeel').find('VervoerType').text,
            }
            delay.update({
                'departure_planned_str': delay['departure_planned'].strftime('%H:%M'),
                'departure_actual_str': delay['departure_actual'].strftime('%H:%M'),
            })

            if status == self.CANCELED_MESSAGE:
                delay.update({
                    'delay': 'Rijdt niet'
                })
            delays.append(delay)

        return delays

    def _strptime(self, datetime_string):
        # parse to datetime, strip timezone
        try:
            return datetime.strptime(datetime_string[:-5], self.DATE_TIME_FORMAT).time()
        except ValueError:
            return datetime.now()

    def _strftime(self, date_time):
        return datetime.strftime(date_time, self.DATE_TIME_FORMAT)