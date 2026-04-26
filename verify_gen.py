import requests

token = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJhZG1pbiIsImV4cCI6MTc3NDY1NDI2OSwidHlwZSI6ImFjY2VzcyJ9.QsrVFGxCc7Mxc42Z4sYtWr_pvCzlwgn5MNBAz6ksy1Y'
url = 'http://localhost:8000/api/admin/world/generate'

# Test with exclusion of Sanddünen (13)
payload = {
    'width': 50,
    'height': 50,
    'seed': 42,
    'excluded_terrain_ids': [13]
}

r = requests.post(f"{url}?token={token}", json=payload)
print(f"Status: {r.status_code}")

r_data = requests.get(f"http://localhost:8000/api/admin/world/map_data?token={token}")
data = r_data.json()
cells = data.get('cells', [])
terrains = set(c['terrain'] for c in cells)
print(f"Terrains: {terrains}")
print(f"Sanddünen present? {'Sanddünen' in terrains}")

oases = [c for c in cells if c['terrain'] in ['Wald', 'Grasland', 'Grünland']]
print(f"Oasis cells: {len(oases)}")

# Grouped check: Ocean Borders
borders = [c for c in cells if c['x'] == 0 or c['x'] == 49 or c['y'] == 0 or c['y'] == 49]
all_ocean = all(c['terrain'] == 'Ozean' for c in borders)
print(f"Borders are Ocean: {all_ocean}")
