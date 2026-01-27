"""Test individual para debug"""
import requests

BASE_URL = "http://127.0.0.1:8000/api/v1/professional"

# Crear equipo
team_payload = {"name": "Test Team", "region": "EMEA"}
team_response = requests.post(f"{BASE_URL}/teams", json=team_payload)
print(f"Team response: {team_response.status_code} - {team_response.json()}")
team_id = team_response.json()["id"]

# Crear jugador  
player_payload = {
    "name": "Test Player",
    "role": "Duelist",
    "region": "EMEA",
    "team_id": team_id,
    "current_price": 15.0,
    "base_price": 12.0,
    "points": 0.0
}

player_response = requests.post(f"{BASE_URL}/players", json=player_payload)
print(f"Player response: {player_response.status_code} - {player_response.json()}")
player_id = player_response.json()["id"]

# Actualizar precio
update_payload = {"current_price": 18.0}
update_response = requests.put(f"{BASE_URL}/players/{player_id}", json=update_payload)
print(f"Update response: {update_response.status_code} - {update_response.json()}")

# Obtener historial
history_response = requests.get(f"{BASE_URL}/players/{player_id}/price-history")
print(f"History response: {history_response.status_code} - {history_response.json()}")
