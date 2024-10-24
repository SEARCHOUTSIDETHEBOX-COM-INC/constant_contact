from constant_contact.api.v3 import ConstantContact
import configparser

# Load your configuration from the .ini file
config = configparser.ConfigParser()
config.read("/Users/jeremywood/constant_contact-1/conf/constant_contact.ini")

# Extract necessary values from the configuration file
access_token = config['my_ctct_app']['access_token']
refresh_token = config['my_ctct_app']['refresh_token']
client_id = config['my_ctct_app']['api_key']
client_secret = config['my_ctct_app']['app_secret']

# Initialize the ConstantContact client with your tokens and credentials
cc = ConstantContact(
    access_token=access_token,
    refresh_token=refresh_token,
    client_id=client_id,
    client_secret=client_secret
)

# Fetch contacts
contacts = cc.get_contacts()
if contacts:
    print("Contacts fetched successfully:", contacts)
else:
    print("Failed to fetch contacts.")
