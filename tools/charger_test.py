import pyemvue
import json
import getpass
import os

# Create PyEmVue object
vue = pyemvue.PyEmVue()

# Check if keys.json exists
if not os.path.exists('keys.json'):
    # Get email and password
    email = input("Enter your email: ")
    password = getpass.getpass("Enter your password: ")

    # Log in to PyEmVue
    logged_in = vue.login(username=email, password=password, token_storage_file='keys.json')
else:
    # If keys.json exists, log in using the keys in the file
    logged_in = vue.login(token_storage_file='keys.json')

print("Logged in?", logged_in)
if not logged_in:
    raise Exception("Login failed")

# Get the list of chargers
chargers = vue.get_chargers()

# Print charger data to the screen
print("Charger data:")
print(json.dumps([charger.__dict__ for charger in chargers], indent=4))

# Wait for user to press enter
input("Press enter to turn off the charger and print the charger data again...")

# Turn off charger and print the charger data again
for charger in chargers:
    vue.update_charger(charger, on=False)
    print("Updated charger data:")
    print(json.dumps(charger.__dict__, indent=4))