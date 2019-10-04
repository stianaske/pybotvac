class NeatoException(Exception):
    pass

class NeatoLoginException(NeatoException):
    """
    To indicate there is a login issue.
    """
    pass

class NeatoRobotException(NeatoException):
    """
    To be thrown anytime there is a robot error.
    """
    pass

class NeatoUnsupportedDevice(NeatoRobotException):
    """
    To be thrown only for unsupported devices.
    """
    pass
