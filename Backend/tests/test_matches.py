"""
Tests de integración para endpoints de Matches

Estos tests verifican que los endpoints de partidos y estadísticas
funcionen correctamente.
"""

import requests
from datetime import datetime

BASE_URL = "http://127.0.0.1:8000/api/v1"
MATCHES_URL = f"{BASE_URL}/matches"
PROFESSIONAL_URL = f"{BASE_URL}/professional"

def test_create_match():
    """Test: Crear un partido"""
    print("\n🧪 Test: Crear partido...")
    
    # Crear equipos primero
    team_a = requests.post(
        f"{PROFESSIONAL_URL}/teams",
        json={"name": "Paper Rex", "region": "Pacific"}
    ).json()
    
    team_b = requests.post(
        f"{PROFESSIONAL_URL}/teams",
        json={"name": "DRX", "region": "Pacific"}
    ).json()
    
    # Crear partido
    payload = {
        "vlr_match_id": "12345",
        "date": datetime.utcnow().isoformat(),
        "status": "upcoming",
        "tournament_name": "VCT Pacific",
        "stage": "Regular Season",
        "vlr_url": "https://vlr.gg/12345",
        "format": "Bo3",
        "team_a_id": team_a["id"],
        "team_b_id": team_b["id"],
        "score_team_a": 0,
        "score_team_b": 0
    }
    
    response = requests.post(f"{MATCHES_URL}/", json=payload)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    
    assert response.status_code == 201
    data = response.json()
    assert data["vlr_match_id"] == "12345"
    assert data["status"] == "upcoming"
    
    print("✅ Test pasado: Partido creado correctamente")
    return data["id"]


def test_update_match_score():
    """Test: Actualizar resultado de partido"""
    print("\n🧪 Test: Actualizar resultado de partido...")
    
    # Crear partido
    match_id = test_create_match()
    
    # Actualizar resultado
    update_payload = {
        "status": "completed",
        "score_team_a": 2,
        "score_team_b": 1
    }
    
    response = requests.put(f"{MATCHES_URL}/{match_id}", json=update_payload)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "completed"
    assert data["score_team_a"] == 2
    assert data["score_team_b"] == 1
    
    print("✅ Test pasado: Resultado actualizado")


def test_create_player_stats():
    """Test: Crear estadísticas de jugador en partido"""
    print("\n🧪 Test: Crear estadísticas de jugador...")
    
    # Crear partido
    match_id = test_create_match()
    
    # Crear jugador
    player = requests.post(
        f"{PROFESSIONAL_URL}/players",
        json={
            "name": "Jinggg",
            "role": "Duelist",
            "region": "Pacific",
            "current_price": 14.0,
            "base_price": 14.0,
            "points": 0.0
        }
    ).json()
    
    # Crear stats
    payload = {
        "match_id": match_id,
        "player_id": player["id"],
        "agent": "Jett",
        "kills": 25,
        "death": 18,
        "assists": 5,
        "acs": 275.5,
        "adr": 165.3,
        "kast": 75.0,
        "hs_percent": 28.5,
        "rating": 1.35,
        "first_kills": 5,
        "first_deaths": 2,
        "clutches_won": 2
    }
    
    response = requests.post(f"{MATCHES_URL}/stats", json=payload)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    
    assert response.status_code == 201
    data = response.json()
    assert data["kills"] == 25
    assert data["death"] == 18
    assert data["fantasy_points_earned"] > 0, "Fantasy points should be calculated"
    
    print(f"✅ Test pasado: Stats creadas con {data['fantasy_points_earned']} fantasy points")


def test_get_match_stats():
    """Test: Obtener estadísticas de un partido"""
    print("\n🧪 Test: Obtener estadísticas de partido...")
    
    # Crear stats primero
    test_create_player_stats()
    
    # Obtener match_id del último partido creado
    match_id = test_create_match()
    
    response = requests.get(f"{MATCHES_URL}/{match_id}/stats")
    print(f"Status: {response.status_code}")
    
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    
    print(f"✅ Test pasado: {len(data)} estadísticas encontradas")


def test_filter_matches_by_status():
    """Test: Filtrar partidos por estado"""
    print("\n🧪 Test: Filtrar partidos por estado...")
    
    response = requests.get(f"{MATCHES_URL}/?status_filter=upcoming")
    print(f"Status: {response.status_code}")
    
    assert response.status_code == 200
    data = response.json()
    
    # Verificar que todos sean upcoming
    for match in data:
        assert match["status"] == "upcoming"
    
    print(f"✅ Test pasado: {len(data)} partidos upcoming")


def test_mark_match_as_processed():
    """Test: Marcar partido como procesado"""
    print("\n🧪 Test: Marcar partido como procesado...")
    
    # Crear partido
    match_id = test_create_match()
    
    # Marcar como procesado
    response = requests.post(f"{MATCHES_URL}/{match_id}/mark-processed")
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    
    assert response.status_code == 200
    data = response.json()
    assert data["is_processed"] == True
    
    print("✅ Test pasado: Partido marcado como procesado")


def run_all_tests():
    """Ejecutar todos los tests de matches"""
    print("\n" + "="*60)
    print("🚀 Ejecutando tests de MATCHES endpoints")
    print("="*60)
    
    try:
        test_create_match()
        test_update_match_score()
        test_create_player_stats()
        test_get_match_stats()
        test_filter_matches_by_status()
        test_mark_match_as_processed()
        
        print("\n" + "="*60)
        print("✅ TODOS LOS TESTS PASARON")
        print("="*60)
        
    except AssertionError as e:
        print(f"\n❌ TEST FALLIDO: {str(e)}")
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")


if __name__ == "__main__":
    run_all_tests()
