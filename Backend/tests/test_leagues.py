"""
Tests de integración para endpoints de Leagues

Estos tests verifican que los endpoints de ligas, miembros y rosters
funcionen correctamente.
"""

import requests

BASE_URL = "http://127.0.0.1:8000/api/v1"
PROFESSIONAL_URL = f"{BASE_URL}/professional"
LEAGUES_URL = f"{BASE_URL}/leagues"
AUTH_URL = f"{BASE_URL}/auth"

# Variable global para almacenar el token de autenticación
AUTH_TOKEN = None

def get_auth_token():
    """Obtener token de autenticación (necesario para crear ligas)"""
    global AUTH_TOKEN
    
    if AUTH_TOKEN:
        return AUTH_TOKEN
    
    print("\n🔐 Autenticando usuario...")
    
    # Intentar login
    login_payload = {
        "email": "test@test.com",
        "password": "testpass123"
    }
    
    response = requests.post(f"{AUTH_URL}/login", json=login_payload)
    
    if response.status_code == 200:
        AUTH_TOKEN = response.json()["access_token"]
        print("✅ Autenticación exitosa")
        return AUTH_TOKEN
    
    # Si no existe, registrar usuario
    print("Usuario no existe, registrando...")
    register_payload = {
        "email": "test@test.com",
        "username": "testuser",
        "password": "testpass123"
    }
    
    requests.post(f"{AUTH_URL}/register", json=register_payload)
    
    # Intentar login de nuevo
    response = requests.post(f"{AUTH_URL}/login", json=login_payload)
    AUTH_TOKEN = response.json()["access_token"]
    print("✅ Usuario registrado y autenticado")
    
    return AUTH_TOKEN


def test_create_league():
    """Test: Crear una liga"""
    print("\n🧪 Test: Crear liga...")
    
    token = get_auth_token()
    headers = {"Authorization": f"Bearer {token}"}
    
    payload = {
        "name": "Champions League 2024",
        "max_teams": 10
    }
    
    response = requests.post(f"{LEAGUES_URL}/", json=payload, headers=headers)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Champions League 2024"
    assert data["max_teams"] == 10
    assert "invite_code" in data
    assert len(data["invite_code"]) == 8  # Código de 8 caracteres
    
    print(f"✅ Test pasado: Liga creada con código {data['invite_code']}")
    return data["id"], data["invite_code"]


def test_get_all_leagues():
    """Test: Obtener todas las ligas"""
    print("\n🧪 Test: Obtener todas las ligas...")
    
    response = requests.get(f"{LEAGUES_URL}/")
    print(f"Status: {response.status_code}")
    
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    
    print(f"✅ Test pasado: Se encontraron {len(data)} ligas")


def test_join_league():
    """Test: Unirse a una liga"""
    print("\n🧪 Test: Unirse a una liga...")
    
    # Crear liga primero
    league_id, invite_code = test_create_league()
    
    token = get_auth_token()
    headers = {"Authorization": f"Bearer {token}"}
    
    # Crear equipo para unirse
    team_response = requests.post(
        f"{PROFESSIONAL_URL}/teams",
        json={"name": "Team Liquid", "region": "Americas"}
    )
    team_id = team_response.json()["id"]
    
    # Unirse a la liga
    response = requests.post(
        f"{LEAGUES_URL}/{league_id}/join?team_name=Mi Equipo Fantasy&selected_team_id={team_id}",
        headers=headers
    )
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    
    assert response.status_code == 201
    data = response.json()
    assert data["team_name"] == "Mi Equipo Fantasy"
    assert data["selected_team_id"] == team_id
    assert data["budget"] == 100.0  # Presupuesto inicial
    
    print("✅ Test pasado: Usuario unido a la liga")
    return data["id"]


def test_add_player_to_roster():
    """Test: Añadir jugador al roster"""
    print("\n🧪 Test: Añadir jugador al roster...")
    
    # Crear jugador
    player_response = requests.post(
        f"{PROFESSIONAL_URL}/players",
        json={
            "name": "Boaster",
            "role": "Controller",
            "region": "EMEA",
            "current_price": 10.0,
            "base_price": 10.0,
            "points": 0.0
        }
    )
    player_id = player_response.json()["id"]
    
    # Unirse a liga
    member_id = test_join_league()
    
    # Añadir jugador al roster
    payload = {
        "player_id": player_id,
        "is_starter": True,
        "is_bench": False,
        "role_position": "Controller"
    }
    
    response = requests.post(
        f"{LEAGUES_URL}/members/{member_id}/roster",
        json=payload
    )
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    
    assert response.status_code == 201
    data = response.json()
    assert data["player_id"] == player_id
    assert data["is_starter"] == True
    
    print("✅ Test pasado: Jugador añadido al roster")


def test_get_roster_starters():
    """Test: Obtener titulares del roster"""
    print("\n🧪 Test: Obtener titulares del roster...")
    
    # Añadir jugador primero
    test_add_player_to_roster()
    
    # Obtener member_id (del último test)
    member_id = test_join_league()
    
    response = requests.get(f"{LEAGUES_URL}/members/{member_id}/roster/starters")
    print(f"Status: {response.status_code}")
    
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    
    # Verificar que todos son starters
    for entry in data:
        assert entry["is_starter"] == True
    
    print(f"✅ Test pasado: {len(data)} titulares en roster")


def test_league_rankings():
    """Test: Obtener rankings de liga"""
    print("\n🧪 Test: Obtener rankings de liga...")
    
    league_id, _ = test_create_league()
    
    response = requests.get(f"{LEAGUES_URL}/{league_id}/rankings")
    print(f"Status: {response.status_code}")
    
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    
    print(f"✅ Test pasado: Rankings obtenidos ({len(data)} equipos)")


def run_all_tests():
    """Ejecutar todos los tests de leagues"""
    print("\n" + "="*60)
    print("🚀 Ejecutando tests de LEAGUES endpoints")
    print("="*60)
    
    try:
        test_create_league()
        test_get_all_leagues()
        test_join_league()
        test_add_player_to_roster()
        test_get_roster_starters()
        test_league_rankings()
        
        print("\n" + "="*60)
        print("✅ TODOS LOS TESTS PASARON")
        print("="*60)
        
    except AssertionError as e:
        print(f"\n❌ TEST FALLIDO: {str(e)}")
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")


if __name__ == "__main__":
    run_all_tests()
