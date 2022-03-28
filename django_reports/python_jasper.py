
import requests


class JasperServer(object):

    def __init__(self, endpoint, username, password):
        self.endpoint = endpoint
        self.username = username
        self.password = password

    def run_report(self, location, params):
        auth = (self.username, self.password)
        url = '{endpoint}{location}'.format(**{
            'endpoint': self.endpoint,
            'location': location,
        })
        return requests.get(url, auth=auth, params=params)
