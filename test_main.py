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
    assert len(get_res.json()["items"]) == 1

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

@pytest.mark.asyncio
async def test_clients_search_and_pagination(client, admin_token):
    headers = {"Authorization": f"Bearer {admin_token}"}
    for i in range(3):
        await client.post("/clients", json={
            "first_name": f"Jan{i}", "last_name": "Kowalski",
            "phone": "123", "email": f"jan{i}@test.pl"
        }, headers=headers)
    await client.post("/clients", json={
        "first_name": "Anna", "last_name": "Nowak",
        "phone": "456", "email": "anna@test.pl"
    }, headers=headers)

    page = (await client.get("/clients?limit=2&offset=0", headers=headers)).json()
    assert page["total"] == 4
    assert len(page["items"]) == 2

    found = (await client.get("/clients?search=nowak", headers=headers)).json()
    assert found["total"] == 1
    assert found["items"][0]["first_name"] == "Anna"

@pytest.mark.asyncio
async def test_delete_client_rules(client, admin_token):  # NOWE
    admin_headers = {"Authorization": f"Bearer {admin_token}"}

    created = await client.post("/clients", json={
        "first_name": "Jan", "last_name": "Test", "phone": "123", "email": "del@test.pl"
    }, headers=admin_headers)
    client_id = created.json()["id"]

    await client.post("/register", json={"email": "mech-del@w.pl", "password": "pass"})
    login = await client.post("/login", data={"username": "mech-del@w.pl", "password": "pass"})
    mech_headers = {"Authorization": f"Bearer {login.json()['access_token']}"}
    assert (await client.delete(f"/clients/{client_id}", headers=mech_headers)).status_code == 403

    car = await client.post("/cars", json={
        "brand": "Audi", "model": "A4", "registration_number": "DEL1234",
        "mileage": 1000, "body_type": "Sedan", "production_year": 2018, "owner_id": client_id
    }, headers=admin_headers)
    assert (await client.delete(f"/clients/{client_id}", headers=admin_headers)).status_code == 400

    await client.delete(f"/cars/{car.json()['id']}", headers=admin_headers)
    assert (await client.delete(f"/clients/{client_id}", headers=admin_headers)).status_code == 204
    assert (await client.get(f"/clients/{client_id}", headers=admin_headers)).status_code == 404

@pytest.mark.asyncio
async def test_delete_car_with_orders_is_blocked(client, admin_token):
    headers = {"Authorization": f"Bearer {admin_token}"}

    owner = await client.post("/clients", json={
        "first_name": "Ola", "last_name": "Test", "phone": "123", "email": "ola@test.pl"
    }, headers=headers)
    car = await client.post("/cars", json={
        "brand": "Opel", "model": "Astra", "registration_number": "BLK1234",
        "mileage": 1000, "body_type": "Hatchback", "production_year": 2015,
        "owner_id": owner.json()["id"]
    }, headers=headers)
    car_id = car.json()["id"]

    order = await client.post("/orders", json={
        "description": "Wymiana oleju", "status": "PENDING", "total_cost": 100, "car_id": car_id
    }, headers=headers)
    assert order.status_code == 201

    assert (await client.delete(f"/cars/{car_id}", headers=headers)).status_code == 400

    car2 = await client.post("/cars", json={
        "brand": "Fiat", "model": "Panda", "registration_number": "FREE123",
        "mileage": 500, "body_type": "Hatchback", "production_year": 2019,
        "owner_id": owner.json()["id"]
    }, headers=headers)
    assert (await client.delete(f"/cars/{car2.json()['id']}", headers=headers)).status_code == 204

@pytest.mark.asyncio
async def test_update_order_changes_car(client, admin_token):
    headers = {"Authorization": f"Bearer {admin_token}"}

    owner = await client.post("/clients", json={
        "first_name": "Ewa", "last_name": "Test", "phone": "123", "email": "ewa@test.pl"
    }, headers=headers)
    owner_id = owner.json()["id"]

    car_ids = []
    for reg in ("UPD1111", "UPD2222"):
        car = await client.post("/cars", json={
            "brand": "Audi", "model": "A3", "registration_number": reg,
            "mileage": 1000, "body_type": "Sedan", "production_year": 2018, "owner_id": owner_id
        }, headers=headers)
        car_ids.append(car.json()["id"])

    order = await client.post("/orders", json={
        "description": "Przegląd", "status": "PENDING", "total_cost": 100, "car_id": car_ids[0]
    }, headers=headers)
    order_id = order.json()["id"]

    res = await client.patch(f"/orders/{order_id}", json={"car_id": car_ids[1]}, headers=headers)
    assert res.status_code == 200
    assert res.json()["car_id"] == car_ids[1]

    res = await client.patch(f"/orders/{order_id}", json={"car_id": 99999}, headers=headers)
    assert res.status_code == 404

@pytest.mark.asyncio
async def test_orders_search_and_pagination(client, admin_token):
    headers = {"Authorization": f"Bearer {admin_token}"}
    owner = await client.post("/clients", json={
        "first_name": "Adam", "last_name": "Test", "phone": "123", "email": "adam@test.pl"
    }, headers=headers)
    car = await client.post("/cars", json={
        "brand": "Kia", "model": "Ceed", "registration_number": "ORD1234",
        "mileage": 1000, "body_type": "Kombi", "production_year": 2017,
        "owner_id": owner.json()["id"]
    }, headers=headers)
    car_id = car.json()["id"]

    for desc in ("Wymiana oleju", "Wymiana klocków", "Przegląd"):
        await client.post("/orders", json={
            "description": desc, "status": "PENDING", "total_cost": 50, "car_id": car_id
        }, headers=headers)

    page = (await client.get("/orders?limit=2", headers=headers)).json()
    assert page["total"] == 3
    assert len(page["items"]) == 2

    found = (await client.get("/orders?search=klocków", headers=headers)).json()
    assert found["total"] == 1