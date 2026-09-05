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
        "password": "haslo_testowe123"
    }
    response = await client.post("/register", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "mechanik@warsztat.pl"
    assert data["role"] == "MECHANIC"
    assert "id" in data

@pytest.mark.asyncio
async def test_register_duplicate_email_fails(client):
    payload = {"email": "jan@warsztat.pl", "password": "haslo"}
    res1 = await client.post("/register", json=payload)
    assert res1.status_code == 201

    res2 = await client.post("/register", json=payload)
    assert res2.status_code == 400
    assert "już istnieje" in res2.json()["detail"]

@pytest.mark.asyncio
async def test_login_invalid_credentials(client):
    response = await client.post("/login", data={"username": "brak@test.pl", "password": "zle_haslo"})
    assert response.status_code == 401

@pytest.mark.asyncio
async def test_get_clients_unauthorized(client):
    response = await client.get("/clients")
    assert response.status_code == 401

@pytest.mark.asyncio
async def test_create_and_get_client_with_jwt(client):
    await client.post("/register", json={"email": "mechanic@warsztat.pl", "password": "haslo"})

    login_res = await client.post("/login", data={"username": "mechanic@warsztat.pl", "password": "haslo"})
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    client_payload = {
        "first_name": "Jan",
        "last_name": "Kowalski",
        "phone": "123456789",
        "email": "jan.kowalski@gmail.com"
    }
    create_res = await client.post("/clients", json=client_payload, headers=headers)
    assert create_res.status_code == 201
    assert create_res.json()["first_name"] == "Jan"

    get_res = await client.get("/clients", headers=headers)
    assert get_res.status_code == 200
    assert len(get_res.json()) == 1

@pytest.mark.asyncio
async def test_create_car_invalid_future_year_fails(client):
    await client.post("/register", json={"email": "mech@w.pl", "password": "pass"})
    login_res = await client.post("/login", data={"username": "mech@w.pl", "password": "pass"})
    headers = {"Authorization": f"Bearer {login_res.json()['access_token']}"}

    car_payload = {
        "brand": "BMW", "model": "M3", "registration_number": "WZ12345",
        "mileage": 100000, "body_type": "Sedan", "production_year": 2099, "owner_id": 1
    }
    res = await client.post("/cars", json=car_payload, headers=headers)
    assert res.status_code == 422

@pytest.mark.asyncio
async def test_create_order_negative_cost_fails(client):
    await client.post("/register", json={"email": "m2@w.pl", "password": "pass"})
    login_res = await client.post("/login", data={"username": "m2@w.pl", "password": "pass"})
    headers = {"Authorization": f"Bearer {login_res.json()['access_token']}"}

    order_payload = {
        "description": "Wymiana oleju", "status": "PENDING", "total_cost": -150.0, "car_id": 1
    }
    res = await client.post("/orders", json=order_payload, headers=headers)
    assert res.status_code == 422


@pytest.mark.asyncio
async def test_delete_car_permission_denied_for_mechanic(client):
    await client.post("/register", json={"email": "m3@w.pl", "password": "pass"})
    login_res = await client.post("/login", data={"username": "m3@w.pl", "password": "pass"})
    headers = {"Authorization": f"Bearer {login_res.json()['access_token']}"}

    response = await client.delete("/cars/1", headers=headers)
    assert response.status_code == 403

@pytest.mark.asyncio
async def test_delete_car_allowed_for_admin(client, admin_token):
    await client.post("/register", json={"email": "m4@w.pl", "password": "pass"})
    login_mech = await client.post("/login", data={"username": "m4@w.pl", "password": "pass"})
    mech_headers = {"Authorization": f"Bearer {login_mech.json()['access_token']}"}

    client_res = await client.post("/clients", json={"first_name": "A", "last_name": "B", "phone": "123", "email": "a@b.pl"}, headers=mech_headers)
    owner_id = client_res.json()["id"]

    car_res = await client.post("/cars", json={
        "brand": "Audi", "model": "A4", "registration_number": "NO12345",
        "mileage": 50000, "body_type": "Kombi", "production_year": 2018, "owner_id": owner_id
    }, headers=mech_headers)
    car_id = car_res.json()["id"]

    admin_headers = {"Authorization": f"Bearer {admin_token}"}

    delete_res = await client.delete(f"/cars/{car_id}", headers=admin_headers)
    assert delete_res.status_code == 204