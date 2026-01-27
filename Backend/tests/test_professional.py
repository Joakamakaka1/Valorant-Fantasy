"""
Tests de integración para endpoints de Professional (Teams/Players)

Estos tests verifican que los endpoints funcionen correctamente
con datos reales en la base de datos.
"""

import requests

BASE_URL = "http://127.0.0.1:8000/api/v1/professional"

def test_create_team():
    """Test: Crear un equipo profesional"""
    print("\n🧪 Test: Crear equipo...")
    
    payload = {
        "name": "Fnatic",
        "region": "EMEA",
        "logo_url": "https://example.com/fnatic.png"
    }
    
    response = requests.post(f"{BASE_URL}/teams", json=payload)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    
    assert response.status_code == 201, f"Expected 201, got {response.status_code}"
    data = response.json()
    assert data["name"] == "Fnatic"
    assert data["region"] == "EMEA"
    assert "id" in data
    
    print("✅ Test pasado: Equipo creado correctamente")
    return data["id"]


def test_get_all_teams():
    """Test: Obtener todos los equipos"""
    print("\n🧪 Test: Obtener todos los equipos...")
    
    response = requests.get(f"{BASE_URL}/teams")
    print(f"Status: {response.status_code}")
    
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list), "Response should be a list"
    
    print(f"✅ Test pasado: Se encontraron {len(data)} equipos")


def test_create_player():
    """Test: Crear un jugador"""
    print("\n🧪 Test: Crear jugador...")
    
    # Primero crear un equipo
    team_payload = {
        "name": "Sentinels",
        "region": "Americas",
        "logo_url": None
    }
    team_response = requests.post(f"{BASE_URL}/teams", json=team_payload)
    team_id = team_response.json()["id"]
    
    # Crear jugador
    player_payload = {
        "name": "TenZ",
        "role": "Duelist",
        "region": "Americas",
        "team_id": team_id,
        "current_price": 15.0,
        "base_price": 12.0,
        "points": 0.0
    }
    
    response = requests.post(f"{BASE_URL}/players", json=player_payload)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "TenZ"
    assert data["role"] == "Duelist"
    assert data["current_price"] == 15.0
    
    print("✅ Test pasado: Jugador creado correctamente")
    return data["id"]


def test_get_players_by_role():
    """Test: Filtrar jugadores por rol"""
    print("\n🧪 Test: Filtrar jugadores por rol...")
    
    response = requests.get(f"{BASE_URL}/players?role=Duelist")
    print(f"Status: {response.status_code}")
    
    assert response.status_code == 200
    data = response.json()
    
    # Verificar que todos sean Duelist
    for player in data:
        assert player["role"] == "Duelist", f"Expected Duelist, got {player['role']}"
    
    print(f"✅ Test pasado: Se encontraron {len(data)} Duelists")


def test_update_player_price():
    """Test: Actualizar precio de jugador"""
    print("\n🧪 Test: Actualizar precio de jugador...")
    
    # Crear jugador primero
    player_id = test_create_player()
    
    # Actualizar precio
    update_payload = {
        "current_price": 18.0
    }
    
    response = requests.put(f"{BASE_URL}/players/{player_id}", json=update_payload)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    
    assert response.status_code == 200
    data = response.json()
    assert data["current_price"] == 18.0
    
    print("✅ Test pasado: Precio actualizado correctamente")


def test_get_price_history():
    """Test: Obtener historial de precios"""
    print("\n🧪 Test: Obtener historial de precios...")
    
    # Crear jugador
    player_id = test_create_player()
    
    # Actualizar precio para generar historial
    requests.put(f"{BASE_URL}/players/{player_id}", json={"current_price": 20.0})
    
    # Obtener historial
    response = requests.get(f"{BASE_URL}/players/{player_id}/price-history")
    print(f"Status: {response.status_code}")
    
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 2, "Should have at least 2 price entries (initial + update)"
    
    print(f"✅ Test pasado: Historial tiene {len(data)} entradas")


def run_all_tests():
    """Ejecutar todos los tests de professional"""
    print("\n" + "="*60)
    print("🚀 Ejecutando tests de PROFESSIONAL endpoints")
    print("="*60)
    
    try:
        test_create_team()
        test_get_all_teams()
        test_create_player()
        test_get_players_by_role()
        test_update_player_price()
        test_get_price_history()
        
        print("\n" + "="*60)
        print("✅ TODOS LOS TESTS PASARON")
        print("="*60)
        
    except AssertionError as e:
        print(f"\n❌ TEST FALLIDO: {str(e)}")
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")


if __name__ == "__main__":
    run_all_tests()
