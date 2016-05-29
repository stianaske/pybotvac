from pybotvac import Account

email = input('Enter email\n')
password = input('Enter password\n')

account = Account(email, password)

print("Robots:")
for robot in account.robots:
    print(robot)
    print(robot.get_robot_state().json())
