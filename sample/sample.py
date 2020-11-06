import sys

from pybotvac import Account, Vorwerk

if sys.version_info[0] < 3:
    input = raw_input

email = input("Enter email\n")
password = input("Enter password\n")

vendor = Vorwerk()


account = Account(email, password, vendor)

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
