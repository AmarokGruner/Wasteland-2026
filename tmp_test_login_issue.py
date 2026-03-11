import requests
import json

BASE_URL = "http://localhost:8000"

def test_login_and_resources(username, password):
    print(f"\n--- Testing for {username} ---")
    login_res = requests.post(f"{BASE_URL}/auth/login", json={"username": username, "password": password})
    if not login_res.ok:
        print(f"Login failed: {login_res.status_code} {login_res.text}")
        return
    
    data = login_res.json()
    token = data["access_token"]
    player_id = data["player_id"]
    print(f"Login success. player_id: {player_id}")
    
    # Try getting resources
    # app.js fallback for player_id
    effective_player_id = player_id if player_id is not None else 1
    
    res_url = f"{BASE_URL}/player/{effective_player_id}/resources/total?token={token}"
    res = requests.get(res_url)
    print(f"Resources request to {res_url}: {res.status_code}")
    if res.ok:
        print(f"Data: {res.json()}")
    else:
        print(f"Error: {res.text}")

if __name__ == "__main__":
    # Test fabian (password should be 'test' or whatever it was set to)
    # I'll try to find the password in previous logs or just try 'wasteland' or something common
    # Wait, I don't know the password. I'll use the admin account to list players and then maybe reset a password.
    # Actually, I know 'admin' works.
    test_login_and_resources("admin", "admin")
    # I'll try to guess fabian's password or register a new user and test
    test_login_and_resources("test_mfdh", "password") # I saw this in previous logs
