import requests

class BetfairAuthService:
    def __init__(self, username, password, app_key):
        self.username = username
        self.password = password
        self.app_key = app_key
        self.certs_path = '../BetfairCerts'
        self.login_url = "https://identitysso-cert.betfair.com/api/certlogin"
    
    def get_session_token(self):
        cert = (f"{self.certs_path}/client-2048.crt", f"{self.certs_path}/client-2048.key")
        payload = {
            'username': self.username,
            'password': self.password
        }
        headers = {
            'X-Application': 'YourAppKeyGoesHere',
            'Content-Type': 'application/x-www-form-urlencoded'
        }

        try:
            response = requests.post(self.login_url, data=payload, cert=cert, headers=headers)
            json_response = response.json()

            if json_response.get('loginStatus') == 'SUCCESS':
                return json_response['sessionToken']
            else:
                raise Exception(f"Login failed: {json_response.get('error')}")
        except Exception as e:
            print(f"Login error: {e}")
            return None
