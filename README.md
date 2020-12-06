# pybotvac

This is an unofficial API for controlling Neato Botvac Connected vacuum robots.
The code is based on https://github.com/kangguru/botvac and credit for reverse engineering the API goes to
[Lars Brillert @kangguru](https://github.com/kangguru)

## Disclaimer
This API is experimental. Use at your own risk. Feel free to contribute if things are not working.

## Installation
Install using pip

```bash
pip install pybotvac
```

Alternatively, clone the repository and run

```bash
python setup.py install
```

## Usage
### Robot
If the serial and secret for your robot is known, simply run

```python
>>> from pybotvac import Robot
>>> robot = Robot('OPS01234-0123456789AB', '0123456789ABCDEF0123456789ABCDEF', 'my_robot_name')
>>> print(robot)
Name: sample_robot, Serial: OPS01234-0123456789AB, Secret: 0123456789ABCDEF0123456789ABCDEF
```

The format of the serial should be 'OPSxxxxx-xxxxxxxxxxxx', and the secret should be a string of hex characters 32 characters long.
These can be found by using the Account class.

To start cleaning

```python
robot.start_cleaning()
```

If no exception occurred, your robot should now get to work.

Currently the following methods are available in the Robot class:

* get_robot_state()
* start_cleaning()
* start_spot_cleaning()
* pause_cleaning()
* stop_cleaning()
* send_to_base()
* enable_schedule()
* disable_schedule()
* get_schedule()

For convenience, properties exist for state and schedule

```python
# Get state
state = robot.state

# Check if schedule is enabled
robot.schedule_enabled

# Disable schedule
robot.schedule_enabled = False
```

### Account
If the serial and secret are unknown, they can be retrieved using the Account class.
You need a session instance to create an account.
There are three different types of sessions available.
It depends on your provider which session is suitable for you.

* **PasswordSession** lets you authenticate via E-Mail and Password. Even though this works fine, it is not recommended.
* **OAuthSession** lets you authenticate via OAuth2. You have to create an application [here](https://developers.neatorobotics.com/applications) in order to generate `client_id`, `client_secret` and `redirect_url`.
* **PasswordlessSession** is known to work for users of the new MyKobold App. The only known `client_id` is `KY4YbVAvtgB7lp8vIbWQ7zLk3hssZlhR`.

```python
from pybotvac import Account, Neato, OAuthSession, PasswordlessSession, PasswordSession, Vorwerk

email = "Your email"
password = "Your password"
client_id = "Your client it"
client_secret = "Your client secret"
redirect_uri = "Your redirect URI"

# Authenticate via Email and Password
password_session = PasswordSession(email=email, password=password, vendor=Neato())

# Authenticate via OAuth2
oauth_session = OAuthSession(client_id=client_id, client_secret=client_secret, redirect_uri=redirect_uri, vendor=Neato())
authorization_url = oauth_session.get_authorization_url()
print("Visit: " + authorization_url)
authorization_response = input("Enter the full callback URL: ")
token = oauth_session.fetch_token(authorization_response)

# Authenticate via One Time Password
passwordless_session = PasswordlessSession(client_id=client_id, vendor=Vorwerk())
passwordless_session.send_email_otp(email)
code = input("Enter the code: ")
passwordless_session.fetch_token_passwordless(email, code)

# Create an account with one of the generated sessions
account = Account(password_session)

# List all robots associated with account
for robot in account.robots:
    print(robot)
```

Information about maps and download of maps can be done from the Account class:

```python
>>> from pybotvac import Account
>>> # List all maps associated with a specific robot
>>> for map_info in Account(PasswordSession('sample@email.com', 'sample_password')).maps:
...     print(map_info)
```

A cleaning map can be downloaded with the account class. Returns the raw image response. Example shows latest map.
You need the url from the map output to do that:

```python
>>> from pybotvac import Account
>>> # List all maps associated with a specific robot
>>> map = Account(PasswordSession('sample@email.com', 'sample_password')).maps
>>> download_link = map['robot_serial']['maps'][0]['url']
>>> Account('sample@email.com', 'sample_password').get_map_image(download_link)
```
