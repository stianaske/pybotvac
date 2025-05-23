import hashlib
import hmac
import logging
from datetime import datetime, timezone
from email.utils import format_datetime

import requests
from voluptuous import (
    ALLOW_EXTRA,
    All,
    Any,
    Extra,
    MultipleInvalid,
    Range,
    Required,
    Schema,
)

from .exceptions import NeatoRobotException, NeatoUnsupportedDevice
from .neato import Neato  # For default Vendor argument

_LOGGER = logging.getLogger(__name__)

SUPPORTED_SERVICES = ["basic-1", "minimal-2", "basic-2", "basic-3", "basic-4"]
ALERTS_FLOORPLAN = [
    "nav_floorplan_load_fail",
    "nav_floorplan_localization_fail",
    "nav_floorplan_not_created",
]

RESULT_SCHEMA = Schema(
    Any(
        "ok",
        "invalid_json",
        "bad_request",
        "command_not_found",
        "command_rejected",
        "ko",
        # Everything below this line is not documented, but still present
        "not_on_charge_base",
    )
)
STANDARD_SCHEMA = Schema(
    {
        "version": int,
        "reqId": str,
        Required("result"): RESULT_SCHEMA,
        "data": {Extra: object},
    },
    extra=ALLOW_EXTRA,
)
STATE_SCHEMA = Schema(
    {
        "version": int,
        "reqId": str,
        Required("result"): RESULT_SCHEMA,
        "data": {Extra: object},
        Required("state"): int,
        "action": int,
        "error": Any(str, None),
        "alert": Any(str, None),
        "cleaning": {
            "category": int,
            "mode": int,
            "modifier": int,
            "navigationMode": int,
            "spotWidth": int,
            "spotHeight": int,
        },
        "details": {
            "isCharging": bool,
            "isDocked": bool,
            "dockHasBeenSeen": bool,
            "charge": All(int, Range(min=0, max=100)),
            "isScheduleEnabled": bool,
        },
        "availableCommands": {
            "start": bool,
            "stop": bool,
            "pause": bool,
            "resume": bool,
            "goToBase": bool,
        },
        Required("availableServices"): {
            "findMe": str,
            "generalInfo": str,
            "houseCleaning": str,
            "localStats": str,
            "manualCleaning": str,
            "maps": str,
            "preferences": str,
            "schedule": str,
            "spotCleaning": str,
            # Undocumented services
            "IECTest": str,
            "logCopy": str,
            "softwareUpdate": str,
            "wifi": str,
        },
        "meta": {"modelName": str, "firmware": str},
    },
    extra=ALLOW_EXTRA,
)


class Robot:
    """Data and methods for interacting with a Neato Botvac Connected vacuum robot"""

    def __init__(
        self,
        serial,
        secret,
        traits,
        vendor=Neato,
        name="",
        endpoint="https://nucleo.neatocloud.com:4443",
        has_persistent_maps=False,
    ):
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

        # pylint: disable=consider-using-f-string
        self._url = "{endpoint}/vendors/{vendor_name}/robots/{serial}/messages".format(
            endpoint=endpoint,
            vendor_name=vendor.name,
            serial=self.serial,
        )
        self._headers = {"Accept": vendor.nucleo_version}

        # Check if service_version is supported
        # We manually scan the state here to perform appropriate error handling
        state = self.get_robot_state().json()
        if (
            "availableServices" not in state
            or "houseCleaning" not in state["availableServices"]
            or state["availableServices"]["houseCleaning"] not in SUPPORTED_SERVICES
        ):
            raise NeatoUnsupportedDevice(
                "Service houseCleaning is not supported by your robot"
            )

    def __str__(self):
        # pylint: disable=consider-using-f-string
        return "Name: %s, Serial: %s, Secret: %s Traits: %s" % (
            self.name,
            self.serial,
            self.secret,
            self.traits,
        )

    def _message(self, json: dict, schema: Schema):
        """
        Sends message to robot with data from parameter 'json'
        :param json: dict containing data to send
        :return: server response
        """

        try:
            response = requests.post(
                self._url,
                json=json,
                verify=self._vendor.cert_path,
                auth=Auth(self.serial, self.secret),
                headers=self._headers,
                timeout=10,
            )
            response.raise_for_status()
            schema(response.json())
        except (
            requests.exceptions.ConnectionError,
            requests.exceptions.HTTPError,
        ) as ex:
            raise NeatoRobotException("Unable to communicate with robot") from ex
        except MultipleInvalid as ex:
            _LOGGER.warning(
                "Invalid response from %s: %s. Got: %s", self._url, ex, response.json()
            )

        return response

    def start_cleaning(
        self, mode=2, navigation_mode=1, category=None, boundary_id=None, map_id=None
    ):
        # mode & navigation_mode used if applicable to service version
        # mode: 1 eco, 2 turbo
        # navigation_mode: 1 normal, 2 extra care, 3 deep
        # category: 2 non-persistent map, 4 persistent map
        # boundary_id: the id of the zone to clean
        # map_id: the id of the map to clean

        # Default to using the persistent map if we support basic-3 or basic-4.
        if category is None:
            category = (
                4
                if self.service_version in ["basic-3", "basic-4"]
                and self.has_persistent_maps
                else 2
            )

        if self.service_version == "basic-1":
            json = {
                "reqId": "1",
                "cmd": "startCleaning",
                "params": {"category": category, "mode": mode, "modifier": 1},
            }
        elif self.service_version in ["basic-3", "basic-4"]:
            json = {
                "reqId": "1",
                "cmd": "startCleaning",
                "params": {
                    "category": category,
                    "mode": mode,
                    "modifier": 1,
                    "navigationMode": navigation_mode,
                },
            }
            if boundary_id:
                json["params"]["boundaryId"] = boundary_id
            if map_id:
                json["params"]["mapId"] = map_id
        elif self.service_version == "minimal-2":
            json = {
                "reqId": "1",
                "cmd": "startCleaning",
                "params": {"category": category, "navigationMode": navigation_mode},
            }
        else:  # self.service_version == 'basic-2'
            json = {
                "reqId": "1",
                "cmd": "startCleaning",
                "params": {
                    "category": category,
                    "mode": mode,
                    "modifier": 1,
                    "navigationMode": navigation_mode,
                },
            }

        response = self._message(json, STATE_SCHEMA)
        result = response.json().get("result", None)
        alert = response.json().get("alert", None)
        if result != "ok":
            _LOGGER.warning(
                "Result of robot.start_cleaning is not ok: %s, alert: %s", result, alert
            )

        # Fall back to category 2 if we tried and failed with category 4
        if (
            category == 4
            and alert in ALERTS_FLOORPLAN
            or result == "not_on_charge_base"
        ):
            json["params"]["category"] = 2
            response_fallback = self._message(json, STATE_SCHEMA)
            result = response_fallback.json().get("result", None)
            alert = response_fallback.json().get("alert", None)
            if result != "ok":
                _LOGGER.warning(
                    "Result of robot.start_cleaning is not ok after fallback: %s, alert: %s",
                    result,
                    alert,
                )
            return response_fallback

        return response

    def start_spot_cleaning(self, spot_width=400, spot_height=400, mode=2, modifier=2):
        # Spot cleaning if applicable to version
        # spot_width: spot width in cm
        # spot_height: spot height in cm

        if self.spot_cleaning_version == "basic-1":
            json = {
                "reqId": "1",
                "cmd": "startCleaning",
                "params": {
                    "category": 3,
                    "mode": mode,
                    "modifier": modifier,
                    "spotWidth": spot_width,
                    "spotHeight": spot_height,
                },
            }
        elif self.spot_cleaning_version == "basic-3":
            json = {
                "reqId": "1",
                "cmd": "startCleaning",
                "params": {
                    "category": 3,
                    "spotWidth": spot_width,
                    "spotHeight": spot_height,
                },
            }
        elif self.spot_cleaning_version == "minimal-2":
            json = {
                "reqId": "1",
                "cmd": "startCleaning",
                "params": {"category": 3, "modifier": modifier, "navigationMode": 1},
            }
        else:  # self.spot_cleaning_version == 'micro-2'
            json = {
                "reqId": "1",
                "cmd": "startCleaning",
                "params": {"category": 3, "navigationMode": 1},
            }

        return self._message(json, STATE_SCHEMA)

    def pause_cleaning(self):
        return self._message({"reqId": "1", "cmd": "pauseCleaning"}, STATE_SCHEMA)

    def resume_cleaning(self):
        return self._message({"reqId": "1", "cmd": "resumeCleaning"}, STATE_SCHEMA)

    def stop_cleaning(self):
        return self._message({"reqId": "1", "cmd": "stopCleaning"}, STATE_SCHEMA)

    def send_to_base(self):
        return self._message({"reqId": "1", "cmd": "sendToBase"}, STATE_SCHEMA)

    def get_robot_state(self):
        return self._message({"reqId": "1", "cmd": "getRobotState"}, STATE_SCHEMA)

    def enable_schedule(self):
        return self._message({"reqId": "1", "cmd": "enableSchedule"}, STANDARD_SCHEMA)

    def disable_schedule(self):
        return self._message({"reqId": "1", "cmd": "disableSchedule"}, STANDARD_SCHEMA)

    def get_schedule(self):
        return self._message({"reqId": "1", "cmd": "getSchedule"}, STANDARD_SCHEMA)

    def locate(self):
        return self._message({"reqId": "1", "cmd": "findMe"}, STANDARD_SCHEMA)

    def get_general_info(self):
        return self._message({"reqId": "1", "cmd": "getGeneralInfo"}, STANDARD_SCHEMA)

    def get_local_stats(self):
        return self._message({"reqId": "1", "cmd": "getLocalStats"}, STANDARD_SCHEMA)

    def get_preferences(self):
        return self._message({"reqId": "1", "cmd": "getPreferences"}, STANDARD_SCHEMA)

    def get_map_boundaries(self, map_id=None):
        return self._message(
            {"reqId": "1", "cmd": "getMapBoundaries", "params": {"mapId": map_id}},
            STANDARD_SCHEMA,
        )

    def get_robot_info(self):
        return self._message({"reqId": "1", "cmd": "getRobotInfo"}, STANDARD_SCHEMA)

    def dismiss_current_alert(self):
        return self._message(
            {"reqId": "1", "cmd": "dismissCurrentAlert"}, STANDARD_SCHEMA
        )

    @property
    def schedule_enabled(self):
        return self.get_robot_state().json()["details"]["isScheduleEnabled"]

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
        return self.state["availableServices"]

    @property
    def service_version(self):
        return self.available_services["houseCleaning"]

    @property
    def spot_cleaning_version(self):
        return self.available_services["spotCleaning"]


class Auth(requests.auth.AuthBase):
    """Create headers for request authentication"""

    def __init__(self, serial, secret):
        self.serial = serial
        self.secret = secret

    def __call__(self, request):
        # We have to format the date according to RFC 2616
        # https://tools.ietf.org/html/rfc2616#section-14.18

        now = datetime.now(timezone.utc)
        date = format_datetime(now, True)

        try:
            # Attempt to decode request.body (assume bytes received)
            msg = "\n".join([self.serial.lower(), date, request.body.decode("utf8")])
        except AttributeError:
            # Decode failed, assume request.body is already type str
            msg = "\n".join([self.serial.lower(), date, request.body])

        signing = hmac.new(
            key=self.secret.encode("utf8"),
            msg=msg.encode("utf8"),
            digestmod=hashlib.sha256,
        )

        request.headers["Date"] = date
        request.headers["Authorization"] = "NEATOAPP " + signing.hexdigest()

        return request
