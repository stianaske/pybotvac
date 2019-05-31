import os

class Neato:
    name = 'neato'
    endpoint = 'https://beehive.neatocloud.com/'
    headers = 'application/vnd.neato.nucleo.v1'
    cert_path = cert_path = os.path.join(os.path.dirname(__file__), 'cert',
                                         'neatocloud.com.crt')
