import hashlib
import hmac
import locale
import os.path
import re
import requests
import time

# Disable warning due to SubjectAltNameWarning in certificate
requests.packages.urllib3.disable_warnings()

SUPPORTED_SERVICES = ['basic-1', 'minimal-2', 'basic-2', 'basic-3', 'basic-4']


class UnsupportedDevice(Exception):
    pass


class Robot:
    """Data and methods for interacting with a Neato Botvac Connected vacuum robot"""

    def __init__(self, serial, secret, traits, vendor, name='',
                 endpoint='https://nucleo.neatocloud.com:4443',
                 has_persistent_maps=False):
        """
        Initialize robot

        :param serial: Robot serial
        :param secret: Robot secret
        :param name: Name of robot (optional)
        :param traits: Extras the robot supports
        """
        self.name = name
        self._vendor = vendor
        self.serial = serial
        self.secret = secret
        self.traits = traits
        self.has_persistent_maps = has_persistent_maps

        self._url = '{endpoint}/vendors/{vendor_name}/robots/{serial}/messages'.format(
            endpoint=re.sub(':\d+', '', endpoint),  # Remove port number
            vendor_name=vendor.name,
            serial=self.serial)
        self._headers = {'Accept': 'application/vnd.neato.nucleo.v1'}

        if self.service_version not in SUPPORTED_SERVICES:
            raise UnsupportedDevice("Version " + self.service_version + " of service houseCleaning is not known")

    def __str__(self):
        return "Name: %s, Serial: %s, Secret: %s Traits: %s" % (self.name, self.serial, self.secret, self.traits)

    def _message(self, json):
        """
        Sends message to robot with data from parameter 'json'
        :param json: dict containing data to send
        :return: server response
        """

        response = requests.post(self._url,
                                 json=json,
                                 verify=self._vendor.cert_path,
                                 auth=Auth(self.serial, self.secret),
                                 headers=self._headers)
        response.raise_for_status()
        return response

    def start_cleaning(self, mode=2, navigation_mode=1, category=None, boundary_id=None, map_id=None):
        # mode & navigation_mode used if applicable to service version
        # mode: 1 eco, 2 turbo
        # navigation_mode: 1 normal, 2 extra care, 3 deep
        # category: 2 non-persistent map, 4 persistent map
        # boundary_id: the id of the zone to clean
        # map_id: the id of the map to clean

        # Default to using the persistent map if we support basic-3 or basic-4.
        if category is None:
            category = 4 if self.service_version in ['basic-3', 'basic-4'] and self.has_persistent_maps else 2

        if self.service_version == 'basic-1':
            json = {'reqId': "1",
                    'cmd': "startCleaning",
                    'params': {
                        'category': category,
                        'mode': mode,
                        'modifier': 1}
                    }
        elif self.service_version == 'basic-3' or 'basic-4':
            json = {'reqId': "1",
                    'cmd': "startCleaning",
                    'params': {
                        'category': category,
                        'mode': mode,
                        'modifier': 1,
                        "navigationMode": navigation_mode}
                    }
            if boundary_id:
                json['params']['boundaryId'] = boundary_id
            if map_id:
                json['params']['mapId'] = map_id
        elif self.service_version == 'minimal-2':
            json = {'reqId': "1",
                    'cmd': "startCleaning",
                    'params': {
                        'category': category,
                        "navigationMode": navigation_mode}
                    }
        else:   # self.service_version == 'basic-2'
            json = {'reqId': "1",
                    'cmd': "startCleaning",
                    'params': {
                        'category': category,
                        'mode': mode,
                        'modifier': 1,
                        "navigationMode": navigation_mode}
                    }

        response = self._message(json)
        response_dict = response.json()

        # Fall back to category 2 if we tried and failed with category 4
        if category == 4 and 'alert' in response_dict and response_dict['alert'] == 'nav_floorplan_load_fail':
            json['params']['category'] = 2
            return self._message(json)

        return response
        
    def start_spot_cleaning(self, spot_width=400, spot_height=400):
        # Spot cleaning if applicable to version
        # spot_width: spot width in cm
        # spot_height: spot height in cm

        if self.service_version == 'basic-1':
            json = {'reqId': "1",
                    'cmd': "startCleaning",
                    'params': {
                        'category': 3,
                        'mode': 1,
                        'modifier': 1,
                        'spotWidth': spot_width,
                        'spotHeight': spot_height}
                    }
        elif self.service_version == 'basic-3':
            json = {'reqId': "1",
                    'cmd': "startCleaning",
                    'params': {
                        'category': 3,
                        'spotWidth': spot_width,
                        'spotHeight': spot_height}
                    }
        elif self.service_version == 'minimal-2':
            json = {'reqId': "1",
                    'cmd': "startCleaning",
                    'params': {
                        'category': 3,
                        'modifier': 1,
                        "navigationMode": 1}
                    }
        else:   # self.service_version == 'micro-2'
            json = {'reqId': "1",
                    'cmd': "startCleaning",
                    'params': {
                        'category': 3,
                        "navigationMode": 1}
                    }

        return self._message(json)

    def pause_cleaning(self):
        return self._message({'reqId': "1", 'cmd': "pauseCleaning"})

    def resume_cleaning(self):
        return self._message({'reqId': "1", 'cmd': "resumeCleaning"})

    def stop_cleaning(self):
        return self._message({'reqId': "1", 'cmd': "stopCleaning"})

    def send_to_base(self):
        return self._message({'reqId': "1", 'cmd': "sendToBase"})

    def get_robot_state(self):
        return self._message({'reqId': "1", 'cmd': "getRobotState"})

    def enable_schedule(self):
        return self._message({'reqId': "1", 'cmd': "enableSchedule"})

    def disable_schedule(self):
        return self._message({'reqId': "1", 'cmd': "disableSchedule"})

    def get_schedule(self):
        return self._message({'reqId': "1", 'cmd': "getSchedule"})

    def locate(self):
        return self._message({'reqId': "1", 'cmd': "findMe"})
    
    def get_general_info(self):
        return self._message({'reqId': "1", 'cmd': "getGeneralInfo"})
    
    def get_local_stats(self):
        return self._message({'reqId': "1", 'cmd': "getLocalStats"})
    
    def get_preferences(self):
        return self._message({'reqId': "1", 'cmd': "getPreferences"})
    
    def get_map_boundaries(self, map_id=None):
        return self._message({'reqId': "1", 'cmd': "getMapBoundaries", 'params': {'mapId': map_id}})
    
    def get_robot_info(self):
        return self._message({'reqId': "1", 'cmd': "getRobotInfo"})

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
    def available_services(self):
        return self.state['availableServices']

    @property
    def service_version(self):
        return self.available_services['houseCleaning']


class Auth(requests.auth.AuthBase):
    """Create headers for request authentication"""

    def __init__(self, serial, secret):
        self.serial = serial
        self.secret = secret

    def __call__(self, request):
        # Due to https://github.com/stianaske/pybotvac/issues/30
        # Neato expects and supports authentication header ONLY for en_US
        saved_locale = locale.getlocale(locale.LC_TIME)
        locale.setlocale(locale.LC_TIME, 'en_US.utf8')
        
        date = time.strftime('%a, %d %b %Y %H:%M:%S', time.gmtime()) + ' GMT'

        locale.setlocale(locale.LC_TIME, saved_locale)

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
