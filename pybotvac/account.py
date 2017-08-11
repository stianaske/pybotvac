"""Account access and data handling for beehive endpoint."""

import binascii
import os
import urllib.parse
import requests


from .robot import Robot


class Account:
    """
    Class with data and methods for interacting with a pybotvac cloud session.

    :param email: Email for pybotvac account
    :param password: Password for pybotvac account

    """

    ENDPOINT = 'https://beehive.neatocloud.com/'

    def __init__(self, email, password):
        """Initialize the account data."""
        self._robots = set()
        self.robot_serials = {}
        self._maps = {}
        self._headers = {'Accept': 'application/vnd.neato.nucleo.v1'}
        self._login(email, password)

    def _login(self, email, password):
        """
        Login to pybotvac account using provided email and password.

        :param email: email for pybotvac account
        :param password: Password for pybotvac account
        :return:
        """
        response = (
            requests.post(urllib.parse.urljoin(self.ENDPOINT, 'sessions'),
                          json={'email': email,
                                'password': password,
                                'platform': 'ios',
                                'token': binascii.hexlify(os.urandom(64))
                                         .decode('utf8')},
                          headers=self._headers))

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
        for robot in self._robots:
            resp2 = (
                requests.get(urllib.parse.urljoin(self.ENDPOINT,
                                                  'users/me/robots/{}/maps'
                                                  .format(robot.serial)),
                             headers=self._headers))
            resp2.raise_for_status()
            self._maps.update({robot.serial: resp2.json()})

    def refresh_robots(self):
        """
        Get information about robots connected to account.

        :return:
        """
        resp = requests.get(urllib.parse.urljoin(self.ENDPOINT, 'dashboard'),
                            headers=self._headers)
        resp.raise_for_status()

        for robot in resp.json()['robots']:
            self._robots.add(Robot(name=robot['name'],
                                   serial=robot['serial'],
                                   secret=robot['secret_key'],
                                   traits=robot['traits']))

    @staticmethod
    def get_map_image(url):
        """
        Return a requested map from a robot.

        :return:
        """
        image = requests.get(url, stream=True, timeout=10)

        return image.raw
