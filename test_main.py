import pytest

@pytest.mark.asyncio
async def test_health_check(client):
    response = await client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json() == {"database": "ok", "server": "ok"}

@pytest.mark.asyncio
async def test_register_user_success(client):
    payload = {
        "email": "mechanik@warsztat.pl",
        "password": "haslo_testowe123",
        "role": "MECHANIC"
    }
    response = await client.post("/register", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "mechanik@warsztat.pl"
    assert data["role"] == "MECHANIC"
    assert "id" in data

@pytest.mark.asyncio
async def test_get_clients_unauthorized(client):
    response = await client.get("clients")
    assert response.status_code == 401