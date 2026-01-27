"""Debug auth test"""
import requests

AUTH_URL = "http://127.0.0.1:8000/api/v1/auth"

# Intentar registrar
register_payload = {
    "email": "test@test.com",
    "username": "testuser",
    "password": "test123"
}

print("Registrando usuario...")
register_response = requests.post(f"{AUTH_URL}/register", json=register_payload)
print(f"Register Status: {register_response.status_code}")
print(f"Register Response: {register_response.json()}")

# Intentar login
login_payload = {
    "email": "test@test.com",
    "password": "test123"
}

print("\nHaciendo login...")
login_response = requests.post(f"{AUTH_URL}/login", json=login_payload)
print(f"Login Status: {login_response.status_code}")
print(f"Login Response: {login_response.json()}")

if login_response.status_code == 200:
    print(f"\n✅ Token obtenido: {login_response.json()['access_token'][:50]}...")
