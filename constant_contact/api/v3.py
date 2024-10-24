import time
import requests

# Function to refresh the access token with retries and exponential backoff
def refresh_access_token_with_retry(refresh_token, client_id, client_secret, max_retries=5):
    headers = {
        'Accept': 'application/json',
        'Content-Type': 'application/x-www-form-urlencoded'
    }

    data = {
        'refresh_token': refresh_token,
        'grant_type': 'refresh_token',
        'client_id': client_id,
        'client_secret': client_secret
    }

    token_url = "https://authz.constantcontact.com/oauth2/default/v1/token"
    retries = 0

    while retries < max_retries:
        try:
            res = requests.post(token_url, headers=headers, data=data, timeout=30)  # Timeout added
            if res.status_code == 200:
                return res.json()  # Return the refreshed token
            else:
                print(f"Failed to refresh token: {res.status_code} {res.text}")
                return None
        except requests.exceptions.ConnectTimeout:
            retries += 1
            wait_time = 2 ** retries  # Exponential backoff
            print(f"Connection timeout. Retrying in {wait_time} seconds...")
            time.sleep(wait_time)

    print(f"Failed to refresh token after {max_retries} attempts.")
    return None


# Define the ConstantContact class
class ConstantContact:
    def __init__(self, access_token, refresh_token, client_id, client_secret):
        self.access_token = access_token
        self.refresh_token = refresh_token
        self.client_id = client_id
        self.client_secret = client_secret

    # Function to get contacts from Constant Contact API
    def get_contacts(self):
        url = "https://api.cc.email/v3/contacts"
        return self.request(url)

    # General function to make API requests
    def request(self, url, method="GET", data=None):
        headers = {"Authorization": f"Bearer {self.access_token}"}

        # Make the API request
        if method == "GET":
            response = requests.get(url, headers=headers)
        elif method == "POST":
            response = requests.post(url, headers=headers, data=data)

        # Check for 401 response (Unauthorized) and attempt token refresh
        if response.status_code == 401:  # Unauthorized, attempt to refresh the token
            print("401 response = refreshing token")
            new_tokens = refresh_access_token_with_retry(
                refresh_token=self.refresh_token,
                client_id=self.client_id,
                client_secret=self.client_secret
            )

            if new_tokens:
                # Update the access token and refresh token if available
                self.access_token = new_tokens['access_token']
                self.refresh_token = new_tokens.get('refresh_token', self.refresh_token)

                # Retry the original request with the new access token
                headers = {"Authorization": f"Bearer {self.access_token}"}
                if method == "GET":
                    response = requests.get(url, headers=headers)
                elif method == "POST":
                    response = requests.post(url, headers=headers, data=data)

        # Return the response or None if the status code is not 200
        return response.json() if response.status_code == 200 else None
