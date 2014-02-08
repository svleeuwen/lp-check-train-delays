import base64
import urllib2
from xml.etree import ElementTree

__author__ = 'Sander'


class NSApi(object):

    DATE_TIME_FORMAT = 'YYYY-MM-DDTHH:mm:ssZ'
    INCLUDE_HIGHSPEED = True
    NUM_PREVIOUS_ADVICES = False

    TIME_FROM = '08:55'
    TIME_UNTIL = '09:10'

    BASE_URL = "http://webservices.ns.nl/ns-api-treinplanner?fromStation=%(from_station)s&toStation=%(to_station)s&hslAllowed=%(include_highspeed)s&previousAdvices=%(num_previous_advices)s"

    def __init__(self, auth_string):
        self.auth_string = base64.urlsafe_b64encode(auth_string)

    def get(self, from_station, to_station):
        url = self.BASE_URL % dict(from_station=from_station,
                                   to_station=to_station,
                                   include_highspeed=self.INCLUDE_HIGHSPEED,
                                   num_previous_advices=self.NUM_PREVIOUS_ADVICES)

        request = urllib2.Request(url)
        request.add_header("Authorization", "Basic %s" % self.auth_string)
        xml = urllib2.urlopen(request)

        return self.parse_result(xml)


    def parse_result(self, xml):

        tree = ElementTree.parse(xml)

        travelOptions = tree.findall('ReisMogelijkheid')


        return travelOptions