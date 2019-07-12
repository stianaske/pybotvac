"""Account access and data handling for beehive endpoint."""

import binascii
import os
import shutil
import requests

try:
    from urllib.parse import urljoin
except ImportError:
    from urlparse import urljoin

from .robot import Robot
from .neato import Neato    # For default Account argument


class Account:
    """
    Class with data and methods for interacting with a pybotvac cloud session.

    :param email: Email for pybotvac account
    :param password: Password for pybotvac account

    """

    def __init__(self, email, password, vendor=Neato):
        """Initialize the account data."""
        self._robots = set()
        self.robot_serials = {}
        self._vendor = vendor
        self._endpoint = vendor.endpoint
        self._maps = {}
        self._headers = {'Accept': vendor.headers}
        self._login(email, password)
        self._persistent_maps = {}

    def _login(self, email, password):
        """
        Login to pybotvac account using provided email and password.

        :param email: email for pybotvac account
        :param password: Password for pybotvac account
        :return:
        """
        response = requests.post(urljoin(self._endpoint, 'sessions'),
                                 json={'email': email,
                                       'password': password,
                                       'platform': 'ios',
                                       'token': binascii.hexlify(os.urandom(64)).decode('utf8')},
                                 headers=self._headers)

        response.raise_for_status()
        access_token = response.json()['access_token']

        self._headers['Authorization'] = 'Token token=%s' % access_token

    @property
    def robots(self):
        """
        Return set of robots for logged in account.

        :return:
        """
        if not self._robots:
            self.refresh_robots()

        return self._robots

    @property
    def maps(self):
        """
        Return set of userdata for logged in account.

        :return:
        """
        self.refresh_maps()

        return self._maps

    def refresh_maps(self):
        """
        Get information about maps of the robots.

        :return:
        """
        for robot in self.robots:
            resp2 = (
                requests.get(urljoin(self._endpoint, 'users/me/robots/{}/maps'.format(robot.serial)),
                             headers=self._headers))
            resp2.raise_for_status()
            self._maps.update({robot.serial: resp2.json()})

    def refresh_robots(self):
        """
        Get information about robots connected to account.

        :return:
        """
        resp = requests.get(urljoin(self._endpoint, 'dashboard'),
                            headers=self._headers)
        resp.raise_for_status()

        for robot in resp.json()['robots']:
            if robot['mac_address'] is None:
                continue    # Ignore robots without mac-address

            try:
                self._robots.add(Robot(name=robot['name'],
                                       vendor=self._vendor,
                                       serial=robot['serial'],
                                       secret=robot['secret_key'],
                                       traits=robot['traits'],
                                       endpoint=robot['nucleo_url']))
            except requests.exceptions.HTTPError:
                print ("Your '{}' robot is offline.".format(robot['name']))
                continue

        self.refresh_persistent_maps()
        for robot in self._robots:
            robot.has_persistent_maps = robot.serial in self._persistent_maps

    @staticmethod
    def get_map_image(url, dest_path=None):
        """
        Return a requested map from a robot.

        :return:
        """
        image = requests.get(url, stream=True, timeout=10)

        if dest_path:
            image_url = url.rsplit('/', 2)[1] + '-' + url.rsplit('/', 1)[1]
            image_filename = image_url.split('?')[0]
            dest = os.path.join(dest_path, image_filename)
            image.raise_for_status()
            with open(dest, 'wb') as data:
                image.raw.decode_content = True
                shutil.copyfileobj(image.raw, data)

        return image.raw

    @property
    def persistent_maps(self):
        """
        Return set of persistent maps for logged in account.

        :return:
        """
        self.refresh_persistent_maps()

        return self._persistent_maps

    def refresh_persistent_maps(self):
        """
        Get information about persistent maps of the robots.

        :return:
        """
        for robot in self._robots:
            resp2 = (requests.get(urljoin(
                self._endpoint,
                'users/me/robots/{}/persistent_maps'.format(robot.serial)),
                headers=self._headers))
            resp2.raise_for_status()
            self._persistent_maps.update({robot.serial: resp2.json()})
