# ruff: noqa: S105

from pybotvac import Account, Neato, OAuthSession

# Set email and password if you plan to use password authentication.
# Set Client ID and Secret if you plan to use OAuth2.
# If you plan to use email OTP, all you need to do is specify your email and a ClientID.
email = "Your email"
password = "Your password"
client_id = "Your client it"
client_secret = "Your client secret"
redirect_uri = "Your redirect URI"

# Set your vendor
vendor = Neato()

##########################
# Authenticate via Email and Password
##########################
# session = PasswordSession(email=email, password=password, vendor=vendor)
# account = Account(session)

##########################
# Authenticate via OAuth2
##########################
session = OAuthSession(
    client_id=client_id,
    client_secret=client_secret,
    redirect_uri=redirect_uri,
    vendor=vendor,
)
authorization_url = session.get_authorization_url()
print("Visit: " + authorization_url)
authorization_response = input("Enter the full callback URL: ")
token = session.fetch_token(authorization_response)
account = Account(session)

##########################
# Authenticate via One Time Password
##########################
# session = PasswordlessSession(client_id=client_id, vendor=vendor)
# session.send_email_otp(email)
# code = input("Enter the code: ")
# session.fetch_token_passwordless(email, code)
# account = Account(session)

print("Robots:")
for robot in account.robots:
    print(robot)
    print()

    print("State:\n", robot.state)
    print()

    print("Schedule enabled:", robot.schedule_enabled)

    print("Disabling schedule")
    robot.schedule_enabled = False

    print("Schedule enabled:", robot.schedule_enabled)

    print("Enabling schedule")
    robot.schedule_enabled = True

    print("Schedule enabled:", robot.schedule_enabled)
    print()
