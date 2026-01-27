"""Debug roster test"""
import requests

BASE_URL = "http://127.0.0.1:8000/api/v1"
PROFESSIONAL_URL = f"{BASE_URL}/professional"
LEAGUES_URL = f"{BASE_URL}/leagues"
AUTH_URL = f"{BASE_URL}/auth"

# Login
login = requests.post(f"{AUTH_URL}/login", json={"email": "test@test.com", "password": "testpass123"})
token = login.json()["access_token"]
headers = {"Authorization": f"Bearer {token}"}

# Crear liga
league = requests.post(f"{LEAGUES_URL}/", json={"name": "Test Roster League", "max_teams": 10}, headers=headers)
league_id = league.json()["id"]
print(f"✅ Liga creada: {league_id}")

# Crear equipo profesional
print(f"\nCreando equipo profesional...")
team_response = requests.post(
    f"{PROFESSIONAL_URL}/teams",
    json={"name": "LOUD", "region": "Americas"}
)
print(f"Team Status: {team_response.status_code}")
print(f"Team Response: {team_response.json()}")

if team_response.status_code == 201:
    team_id = team_response.json()["id"]
    print(f"✅ Equipo creado: {team_id}")
    
    # Unirse a la liga
    print(f"\nUniéndose a la liga...")
    member_response = requests.post(
        f"{LEAGUES_URL}/{league_id}/join?team_name=Mi Equipo&selected_team_id={team_id}",
        headers=headers
    )
    print(f"Member Status: {member_response. status_code}")
    print(f"Member Response: {member_response.json()}")
    member_id = member_response.json()["id"]
    
    # Crear jugador
    print(f"\nCreando jugador...")
    player_response = requests.post(
        f"{PROFESSIONAL_URL}/players",
        json={
            "name": "aspas",
            "role": "Duelist",
            "region": "Americas",
            "current_price": 16.0,
            "base_price": 14.0,
            "points": 0.0
        }
    )
    print(f"Player Status: {player_response.status_code}")
    print(f"Player Response: {player_response.json()}")
    player_id = player_response.json()["id"]
    
    # Añadir al roster
    print(f"\nAñadiendo jugador al roster...")
    roster_response = requests.post(
        f"{LEAGUES_URL}/members/{member_id}/roster",
        json={
            "player_id": player_id,
            "is_starter": True,
            "is_bench": False,
            "role_position": "Duelist"
        }
    )
    print(f"Roster Status: {roster_response.status_code}")
    print(f"Roster Response: {roster_response.json()}")
