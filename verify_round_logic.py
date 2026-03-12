import requests
import json

BASE_URL = "http://localhost:8000"

def verify_round_logic():
    # 1. Login
    login_data = {"username": "fabian", "password": "123456"}
    res = requests.post(f"{BASE_URL}/auth/login", json=login_data)
    if res.status_code != 200:
        print(f"Login failed: {res.status_code} {res.text}")
        return
    
    data = res.json()
    token = data["access_token"]
    player_id = data["player_id"]
    print(f"Logged in. Player ID: {player_id}")

    # 2. Get Provinces
    res = requests.get(f"{BASE_URL}/player/{player_id}/provinzen?token={token}")
    print(f"Response /provinzen: {res.status_code}")
    provinces_data = res.json()
    provinces = provinces_data.get("provinzen", [])
    
    if res.status_code != 200 or not provinces:
        print("No provinces found for this player. Please create one manually or via admin.")
        return
    
    province_id = provinces[0]["id"]
    print(f"Testing with Province ID: {province_id}")

    # 3. Test Preview (24h)
    print("\n--- Testing Preview (24h) ---")
    res = requests.get(f"{BASE_URL}/province/{province_id}/preview?hours=24&token={token}")
    if res.status_code == 200:
        print("Preview Success:")
        print(json.dumps(res.json(), indent=2))
    else:
        print(f"Preview Failed: {res.status_code} {res.text}")

    # 4. Test Spool (24h)
    print("\n--- Testing Spool (24h) ---")
    spool_data = {"hours": 24.0}
    res = requests.post(f"{BASE_URL}/province/{province_id}/spool?token={token}", json=spool_data)
    if res.status_code == 200:
        print("Spool Success:")
        print(json.dumps(res.json(), indent=2))
    else:
        print(f"Spool Failed: {res.status_code} {res.text}")

if __name__ == "__main__":
    verify_round_logic()
