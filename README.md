# pybotvac

This is an unofficial API for controlling Neato Botvac Connected vacuum robots.
The code is based on https://github.com/kangguru/botvac and credit for reverse engineering the API goes to
[Lars Brillert @kangguru](https://github.com/kangguru)

## Disclaimer
This API is experimental. Use at your own risk. Feel free to contribute if things are not working.

## Installation
Install by running setup.py

    python setup.py install

## Usage
### Robot
If the serial and secret for your robot is known, simply run

    >>> from pybotvac import Robot
    >>> robot = Robot('OPS01234-0123456789AB', '0123456789ABCDEF0123456789ABCDEF', 'my_robot_name')
    >>> print(robot)
    Name: sample_robot, Serial: OPS01234-0123456789AB, Secret: 0123456789ABCDEF0123456789ABCDEF

The format of the serial should be 'OPSxxxxx-xxxxxxxxxxxx', and the secret should be a string of hex characters 32 characters long.
These can be found by using the Account class.

To start cleaning

    robot.start_cleaning()

If no exception occurred, your robot should now get to work.

Currently the following methods are available in the Robot class:

* get_robot_state()
* start_cleaning()
* pause_cleaning()
* stop_cleaning()
* send_to_base()
* enable_schedule()
* disable_schedule()
* get_schedule()

For convenience, properties exist for state and schedule

    # Get state
    state = robot.state

    # Check if schedule is enabled
    robot.schedule_enabled

    # Disable schedule
    robot.schedule_enabled = False

### Account
If the serial and secret is unknown, they can be retrieved using the Account class.

    >>> from pybotvac import Account
    >>> # List all robots associated with account
    >>> for robot in Account('sample@email.com', 'sample_password').robots:
        print(robot)

    Name: my_robot_name, Serial: OPS01234-0123456789AB, Secret: 0123456789ABCDEF0123456789ABCDEF, Traits: ['maps']

Information about maps and download of maps can be done from the Account class:

    >>> from pybotvac import Account
    >>> # List all maps associated with a specific robot
    >>> for map_info in Account('sample@email.com', 'sample_password').maps:
        print(map_info)

A cleaning map can be downloaded with the account class. Returns the raw image response. Example shows latest map.
 You need the url from the map output to do that:

    >>> from pybotvac import Account
    >>> # List all maps associated with a specific robot
    >>> map = Account('sample@email.com', 'sample_password').maps
    >>> download_link = map['robot_serial']['maps'][0]['url']
        Account('sample@email.com', 'sample_password').get_map_image('download_link')
