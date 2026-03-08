import requests
import json

BASE_URL = "http://localhost:8000"

def test_api():
    # 1. Login
    login_data = {"username": "fabian", "password": "123456"}
    res = requests.post(f"{BASE_URL}/auth/login", json=login_data)
    if res.status_code != 200:
        print(f"Login failed: {res.status_code} {res.text}")
        return
    
    data = res.json()
    token = data["token"]
    player_id = data["player_id"]
    print(f"Logged in. Token: {token[:10]}..., Player ID: {player_id}")
    
    # 2. Test /provinzen
    url = f"{BASE_URL}/player/{player_id}/provinzen?token={token}"
    print(f"Testing URL: {url}")
    res = requests.get(url)
    print(f"Response /provinzen: {res.status_code}")
    if res.status_code == 200:
        print(json.dumps(res.json(), indent=2))
    else:
        print(res.text)

if __name__ == "__main__":
    test_api()
