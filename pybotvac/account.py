"""Account access and data handling for beehive endpoint."""

import logging
import os
import shutil

import requests

from .exceptions import NeatoRobotException
from .robot import Robot
from .session import Session

_LOGGER = logging.getLogger(__name__)
class Account:
    """
    Class with data and methods for interacting with a pybotvac cloud session.

    :param email: Email for pybotvac account
    :param password: Password for pybotvac account

    """

    def __init__(self, session: Session):
        """Initialize the account data."""
        self._robots = set()
        self.robot_serials = {}
        self._maps = {}
        self._persistent_maps = {}
        self._session = session

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
            resp2 = self._session.get("users/me/robots/{}/maps".format(robot.serial))
            self._maps.update({robot.serial: resp2.json()})

    def refresh_robots(self):
        """
        Get information about robots connected to account.

        :return:
        """

        resp = self._session.get("users/me/robots")

        for robot in resp.json():
            try:
                robot_object = Robot(
                    name=robot['name'],
                    vendor=self._session.vendor,
                    serial=robot["serial"],
                    secret=robot["secret_key"],
                    traits=robot["traits"],
                    endpoint=robot["nucleo_url"],
                )
                self._robots.add(robot_object)
            except NeatoRobotException:
                _LOGGER.warning("Your robot %s is offline.", robot["name"])
                continue

        self.refresh_persistent_maps()
        for robot in self._robots:
            robot.has_persistent_maps = robot.serial in self._persistent_maps

    @staticmethod
    def get_map_image(url, dest_path=None, file_name=None):
        """
        Return a requested map from a robot.

        :return:
        """

        try:
            image = requests.get(url, stream=True, timeout=10)

            if dest_path:
                image_url = url.rsplit("/", 2)[1] + "-" + url.rsplit("/", 1)[1]
                if file_name:
                    image_filename = file_name
                else:
                    image_filename = image_url.split("?")[0]

                dest = os.path.join(dest_path, image_filename)
                image.raise_for_status()
                with open(dest, "wb") as data:
                    image.raw.decode_content = True
                    shutil.copyfileobj(image.raw, data)
        except (
            requests.exceptions.ConnectionError,
            requests.exceptions.HTTPError,
            requests.exceptions.Timeout,
        ) as ex:
            raise NeatoRobotException("Unable to get robot map") from ex

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
            resp2 = self._session.get(
                "users/me/robots/{}/persistent_maps".format(robot.serial)
            )

            self._persistent_maps.update({robot.serial: resp2.json()})
