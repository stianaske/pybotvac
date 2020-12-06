class NeatoException(Exception):
    """
    General neato exception.
    """


class NeatoLoginException(NeatoException):
    """
    To indicate there is a login issue.
    """


class NeatoRobotException(NeatoException):
    """
    To be thrown anytime there is a robot error.
    """


class NeatoUnsupportedDevice(NeatoRobotException):
    """
    To be thrown only for unsupported devices.
    """
