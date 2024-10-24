#!/usr/bin/env python

from constant_contact.config.find_dir import FindDir
import configparser, fcntl, requests, sys
import uuid  # Import uuid to generate the state parameter

# if you changed your app id in the configuration file, update here too
APP_ID = 'my_ctct_app'

# change this to point your ini file (absolute path required)
CONF_FILE = "/Users/jeremywood/constant_contact-1/sample_conf/constant_contact.ini"

# Generate a random state parameter to include in the request
state = str(uuid.uuid4())

# Update the CODE_REQUEST to include the state parameter
CODE_REQUEST = (
    "https://authz.constantcontact.com/oauth2/default/v1/authorize"
    "?response_type=code&client_id={}"
    "&scope=contact_data&redirect_uri=https%3A%2F%2Flocalhost"
    "&state={}"
)

TOKEN_REQUEST = (
    "https://authz.constantcontact.com/oauth2/default/v1/token"
)

# Use CONF_FILE directly as it's already an absolute path
conf_filename = CONF_FILE

parser = configparser.ConfigParser()
parser.read(conf_filename)

conf = dict(parser['my_ctct_app'])
if not parser.has_section(APP_ID):
    parser.add_section(APP_ID)

# Debugging: Print the sections found in the config file
print("Sections found:", parser.sections())

print("""
This script will generate new access / refresh tokens.

Assumptions:

1. You have already filled in {} with

  * api_key: XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX
  * app_secret: XXXXXXXXXXXXXXXXXXXXXX
""".format(conf_filename))

res = input("Have you filled these in? [Y/n] ")

if res.lower().startswith("n"):
    print("""
  You can obtain these from:

  https://app.constantcontact.com/pages/dma/portal/

  It's not obvious at the onset but the app_secret is generated
  after you select the app you're going to use. Find the button
  labeled "Generate Secret". A warning will pop up that you may
  be overwriting your current secret. After passing that you
  will get one shot to copy and paste it here or generate a new
  one and try again.

  When you are done, re-run this script.
    """)
    sys.exit()

print("""
2. You have access to a browser you can cut-n-paste into?

  I will be generating a URL from the entries provided in your
  conf/constant_contact.ini file. You will place this URL in a
  browser and it will redirect you to a local url. That URL will
  fail because you are not running a browser locally.

  What we need from that URL is the code it provides. It will
  look like:

  https://localhost/?code=XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX&state=XXXXXXXX

  You will need to cut~n~paste that code into here.
""")

res = input("Do you have access to a browser you can cut~n~paste into? [Y/n] ")

if res.lower().startswith("n"):
    print("You may need to run this at another time. The URL is too fraught\n"
          "with potential typos and it requires authentication through a\n"
          "browser to continue.\n")
    sys.exit()

# Add the state parameter to the request URL
url = CODE_REQUEST.format(conf['api_key'], state)

print("cut~n~paste the following url into your browser to retrieve the code.")
print("URL:\n  ", url + "\n")
print("just enter everything after the code= portion of the url")
print("https://localhost/?code=<code>&state={}".format(state))

code = input("Enter the code here: ")

# Verify that the state returned matches the one we sent
returned_state = input("Enter the state returned from the URL: ")

if returned_state != state:
    print("Error: The state returned by the server does not match the original state.")
    sys.exit()

# Now request the token
headers = {
    'Accept': 'application/json',
    'Content-Type': 'application/x-www-form-urlencoded'
}

data = {
    'code': code,
    'redirect_uri': 'https://localhost',
    'grant_type': 'authorization_code',
    'client_id': conf['api_key'],
    'client_secret': conf['app_secret']
}

req = requests.post(
    TOKEN_REQUEST, headers=headers, data=data
)

results = req.json()

import pprint
pprint.pprint(results)

# Check if access_token exists in the response
if 'access_token' in results:
    print("\n  access_token: ", results['access_token'])
    
    # Only print refresh_token if it exists in the response
    if 'refresh_token' in results:
        print("  refresh_token: ", results['refresh_token'])
    else:
        print("  refresh_token not returned in the response.")
else:
    print(f"Error in token request: {results}")

print("\nThese need to be updated in your configuration "
      "file: {}".format(conf_filename))

res = input("I can attempt to do that now if you'd like or you can\n"
            "stop and do it manually. Would you like me to update your\n"
            "configuration file? [Y/n]")

if res.lower().startswith("n"):
    print("\nYou can take it from here. Good Luck.\n")
    sys.exit()

# Update the config file with access_token and refresh_token if present
parser[APP_ID]['access_token'] = results['access_token']
if 'refresh_token' in results:
    parser[APP_ID]['refresh_token'] = results['refresh_token']

with open(conf_filename, 'w') as configfile:
    locked = False

    for x in range(30):
        try:
            fcntl.flock(configfile, fcntl.LOCK_EX | fcntl.LOCK_NB)
            locked = True
            break
        except OSError as e:
            if sys.stdout.isatty():  # interactive
                print("File Lock: {} - retrying...".format(e))

        time.sleep(1)

    if locked:
        parser.write(configfile)
        fcntl.flock(configfile, fcntl.LOCK_UN)
    else:
        raise OSError("Unable to establish lock on config file")

print("\nSuccess. Try running\n  bin/fetch_contacts.py\nto test your "
      "new configuration.")
