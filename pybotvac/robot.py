import requests
import hashlib
import hmac
import time
import os.path

# Disable warning due to SubjectAltNameWarning in certificate
requests.packages.urllib3.disable_warnings()


class Robot:
    """Data and methods for interacting with a Neato Botvac Connected vacuum robot"""

    def __init__(self, serial, secret, traits, name=''):
        """
        Initialize robot

        :param serial: Robot serial
        :param secret: Robot secret
        :param name: Name of robot (optional)
        :param traits: Extras the robot supports
        """
        self.name = name
        self.serial = serial
        self.secret = secret
        self.traits = traits

        self._url = 'https://nucleo.neatocloud.com/vendors/neato/robots/{0}/messages'.format(self.serial)
        self._headers = {'Accept': 'application/vnd.neato.nucleo.v1'}
        self._commands = []
        self._parse_state(self.get_robot_state().json())

    def __str__(self):
        return "Name: %s, Serial: %s, Secret: %s Traits: %s" % (self.name, self.serial, self.secret, self.traits)

    def _message(self, json):
        """
        Sends message to robot with data from parameter 'json'
        :param json: dict containing data to send
        :return: server response
        """

        cert_path = os.path.join(os.path.dirname(__file__), 'cert', 'neatocloud.com.crt')
        response = requests.post(self._url,
                                 json=json,
                                 verify=cert_path,
                                 auth=Auth(self.serial, self.secret),
                                 headers=self._headers)
        response.raise_for_status()
        return response

    def _parse_state(self, state):
        self._commands = state["availableCommands"]
        self._navigation_mode = state["cleaning"]["navigationMode"]
        self._mode = state["cleaning"]["mode"]
        self._category = state["cleaning"]["category"]
        self._modifier = state["cleaning"]["modifier"]

    def start_cleaning(self):
        json = {'reqId': "1",
                'cmd': "startCleaning",
                'params': {
                    'category': self._category,
                    'mode': self._mode,
                    'navigationMode': self._navigation_mode,
                    'modifier': self._modifier}
                }
        state = self._message(json)
        self._commands = state.json()["availableCommands"]
        return state

    def pause_cleaning(self):
        state = self._message({'reqId': "1", 'cmd': "pauseCleaning"})
        self._commands = state.json()["availableCommands"]
        return state

    def resume_cleaning(self):
        state = self._message({'reqId': "1", 'cmd': "resumeCleaning"})
        self._commands = state.json()["availableCommands"]
        return state

    def stop_cleaning(self):
        state = self._message({'reqId': "1", 'cmd': "stopCleaning"})
        self._commands = state.json()["availableCommands"]
        return state

    def send_to_base(self):
        state = self._message({'reqId': "1", 'cmd': "sendToBase"})
        self._commands = state.json()["availableCommands"]
        return state

    def get_robot_state(self):
        return self._message({'reqId': "1", 'cmd': "getRobotState"})

    def enable_schedule(self):
        return self._message({'reqId': "1", 'cmd': "enableSchedule"})

    def disable_schedule(self):
        return self._message({'reqId': "1", 'cmd': "disableSchedule"})

    def get_schedule(self):
        return self._message({'reqId': "1", 'cmd': "getSchedule"})

    @property
    def schedule_enabled(self):
        return self.get_robot_state().json()['details']['isScheduleEnabled']

    @schedule_enabled.setter
    def schedule_enabled(self, enable):
        if enable:
            self.enable_schedule()
        else:
            self.disable_schedule()

    @property
    def state(self):
        return self.get_robot_state().json()

    @property
    def available_commands(self):
        return self._commands

class Auth(requests.auth.AuthBase):
    """Create headers for request authentication"""

    def __init__(self, serial, secret):
        self.serial = serial
        self.secret = secret

    def __call__(self, request):
        date = time.strftime('%a, %d %b %Y %H:%M:%S', time.gmtime()) + ' GMT'

        try:
            # Attempt to decode request.body (assume bytes received)
            msg = '\n'.join([self.serial.lower(), date, request.body.decode('utf8')])
        except AttributeError:
            # Decode failed, assume request.body is already type str
            msg = '\n'.join([self.serial.lower(), date, request.body])

        signing = hmac.new(key=self.secret.encode('utf8'),
                           msg=msg.encode('utf8'),
                           digestmod=hashlib.sha256)

        request.headers['Date'] = date
        request.headers['Authorization'] = "NEATOAPP " + signing.hexdigest()

        return request
