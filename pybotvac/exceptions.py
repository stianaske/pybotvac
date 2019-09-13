class NeatoException(Exception):
    pass

class NeatoLoginException(NeatoException):
    pass

class NeatoRobotException(NeatoException):
    pass

class NeatoUnsupportedDevice(NeatoRobotException):
    pass