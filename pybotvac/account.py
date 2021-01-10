"""Account access and data handling for beehive endpoint."""

import logging
import os
import shutil

import requests
from voluptuous import (
    ALLOW_EXTRA,
    All,
    Any,
    Extra,
    MultipleInvalid,
    Optional,
    Range,
    Required,
    Schema,
    Url,
)

from .exceptions import NeatoRobotException, NeatoUnsupportedDevice
from .robot import Robot
from .session import Session

_LOGGER = logging.getLogger(__name__)

ROBOT_SCHEMA = Schema(
    {
        Required("serial"): str,
        "prefix": Any(str, None),
        Required("name"): str,
        "model": str,
        Required("secret_key"): str,
        "purchased_at": Any(str, None),
        "linked_at": Any(str, None),
        Required("traits"): list,
        # Everything below this line is not documented, but still present
        "firmware": str,
        "timezone": str,
        Required("nucleo_url"): Url,
        "mac_address": str,
        "created_at": str,
    },
    extra=ALLOW_EXTRA,
)
MAP_SCHEMA = Schema(
    {
        "version": int,
        Required("id"): str,
        Required("url"): Url,
        "url_valid_for_seconds": int,
        Optional("run_id"): str,  # documented, but  not present
        "status": Any("complete", "incomplete", "canceled"),
        "launched_from": Any("robot", "schedule", "app"),
        "error": Any(str, None),
        "category": int,
        "mode": int,
        "modifier": int,
        "start_at": str,
        "end_at": str,
        "end_orientation_relative_degrees": All(int, Range(min=0, max=360)),
        "run_charge_at_start": All(int, Range(min=0, max=100)),
        "run_charge_at_end": All(int, Range(min=0, max=100)),
        "suspended_cleaning_charging_count": int,
        "time_in_suspended_cleaning": int,
        "time_in_error": int,
        "time_in_pause": int,
        "cleaned_area": float,
        "base_count": int,
        "is_docked": bool,
        "delocalized": bool,
        # Everything below this line is not documented, but still present
        "generated_at": str,
        "persistent_map_id": Any(str, None),
        "cleaned_with_persistent_map_id": Any(str, None),
        "valid_as_persistent_map": bool,
        "navigation_mode": int,
    },
    extra=ALLOW_EXTRA,
)
MAPS_SCHEMA = Schema(
    {"stats": {Extra: object}, Required("maps"): [MAP_SCHEMA]},
    extra=ALLOW_EXTRA,
)
PERSISTENT_MAP_SCHEMA = Schema(
    {
        Required("id"): str,
        Required("name"): str,
        Required("url"): Url,
        "raw_floor_map_url": Url,
        "url_valid_for_seconds": int,
    },
    extra=ALLOW_EXTRA,
)
PERSISTENT_MAPS_SCHEMA = Schema(Required([PERSISTENT_MAP_SCHEMA]))


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
            url = f"users/me/robots/{robot.serial}/maps"
            resp2 = self._session.get(url)
            try:
                MAPS_SCHEMA(resp2.json())
                self._maps.update({robot.serial: resp2.json()})
            except MultipleInvalid as ex:
                _LOGGER.warning(
                    "Invalid response from %s: %s. Got: %s", url, ex, resp2.json()
                )

    def refresh_robots(self):
        """
        Get information about robots connected to account.

        :return:
        """

        resp = self._session.get("users/me/robots")

        for robot in resp.json():
            _LOGGER.debug("Create Robot: %s", robot)
            try:
                ROBOT_SCHEMA(robot)
                robot_object = Robot(
                    name=robot["name"],
                    vendor=self._session.vendor,
                    serial=robot["serial"],
                    secret=robot["secret_key"],
                    traits=robot["traits"],
                    endpoint=robot["nucleo_url"],
                )
                self._robots.add(robot_object)
            except MultipleInvalid as ex:
                # Robot was not described accordingly by neato
                _LOGGER.warning(
                    "Bad response from robots endpoint: %s. Got: %s", ex, robot
                )
                continue
            except NeatoUnsupportedDevice:
                # Robot does not support home_cleaning service
                _LOGGER.warning("Your robot %s is unsupported.", robot["name"])
                continue
            except NeatoRobotException:
                # The state of the robot could not be received
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
            url = f"users/me/robots/{robot.serial}/persistent_maps"
            resp2 = self._session.get(url)

            try:
                PERSISTENT_MAPS_SCHEMA(resp2.json())
                self._persistent_maps.update({robot.serial: resp2.json()})
            except MultipleInvalid as ex:
                _LOGGER.warning(
                    "Invalid response from %s: %s. Got: %s", url, ex, resp2.json()
                )
