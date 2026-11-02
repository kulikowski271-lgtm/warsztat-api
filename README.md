# Warsztat API

REST API do zarządzania warsztatem samochodowym — klientami, pojazdami i zleceniami serwisowymi.

Zbudowane w **FastAPI** z asynchroniczną obsługą **PostgreSQL**, uwierzytelnianiem **JWT** i systemem ról (**MECHANIC** / **ADMIN**).

## Tech stack

- **FastAPI** — framework API
- **PostgreSQL** — baza danych
- **SQLAlchemy 2.0** (async) — ORM
- **Pydantic v2** — walidacja danych
- **JWT (python-jose)** — uwierzytelnianie
- **passlib (bcrypt)** — hashowanie haseł
- **Docker Compose** — środowisko bazy danych
- **pytest + httpx** — testy (SQLite w pamięci)

## Funkcjonalności

- Rejestracja i logowanie użytkowników (JWT)
- System ról: `MECHANIC` i `ADMIN`, z kontrolą dostępu na poziomie endpointów
- Zarządzanie klientami (CRUD) z wyszukiwaniem i paginacją
- Zarządzanie pojazdami z filtrami, wyszukiwaniem i paginacją
- Zarządzanie zleceniami serwisowymi (statusy, koszty, filtry, paginacja)
- Dashboard ze statystykami (liczby, przychód, ostatnie aktywne zlecenia)
- Reguły biznesowe: nie można usunąć klienta z pojazdami ani pojazdu ze zleceniami
- Health check sprawdzający realne połączenie z bazą danych

## Wymagania

- Python 3.11+
- Docker i Docker Compose

## Instalacja

1. Sklonuj repozytorium:

```bash
git clone https://github.com/kulikowski271-lgtm/warsztat-api.git
cd warsztat-api
```

2. Utwórz środowisko wirtualne i zainstaluj zależności:

```bash
python -m venv venv
# Windows
venv\Scripts\activate
# Linux / macOS
source venv/bin/activate

pip install -r requirements.txt
```

> Do uruchomienia testów potrzebne są dodatkowo: `pytest`, `pytest-asyncio`, `httpx`  
> (np. `pip install pytest pytest-asyncio httpx`).

3. Skopiuj plik konfiguracyjny i uzupełnij wartości:

```bash
cp .env.example .env
```

| Zmienna | Opis |
|---|---|
| `SECRET_KEY` | Tajny klucz do podpisywania tokenów JWT |
| `ALGORITHM` | Algorytm JWT (domyślnie `HS256`) |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Czas ważności tokenu w minutach |
| `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT`, `DB_NAME` | Dane połączenia z PostgreSQL |
| `DATABASE_URL` | Pełny adres połączenia SQLAlchemy (np. `postgresql+psycopg://...`) |
| `DEBUG` | `true` / `false` — logowanie zapytań SQL (opcjonalnie) |

4. Uruchom bazę danych:

```bash
docker-compose up -d
```

5. Uruchom serwer:

```bash
uvicorn main:app --reload
```

API: `http://127.0.0.1:8000`  
Dokumentacja (Swagger UI): `http://127.0.0.1:8000/docs`

## Tworzenie konta administratora

Rola `ADMIN` **nie** może zostać ustawiona przez publiczny endpoint rejestracji.

```bash
python create_admin.py
```

Skrypt zapyta o email i hasło, a następnie utworzy użytkownika z rolą `ADMIN` (lub podniesie rolę istniejącego użytkownika).

## Endpointy

### Autoryzacja

| Metoda | Endpoint | Opis | Wymagana rola |
|---|---|---|---|
| POST | `/register` | Rejestracja (domyślnie `MECHANIC`) | — |
| POST | `/login` | Logowanie, zwraca token JWT | — |
| GET | `/users/me` | Dane zalogowanego użytkownika | zalogowany |
| PATCH | `/users/{user_id}/role` | Zmiana roli użytkownika | `ADMIN` |

### Dashboard

| Metoda | Endpoint | Opis | Wymagana rola |
|---|---|---|---|
| GET | `/api/v1/dashboard` | Statystyki: klienci, pojazdy, zlecenia, przychód, ostatnie aktywne zlecenia | `MECHANIC` |

### Klienci

| Metoda | Endpoint | Opis | Wymagana rola |
|---|---|---|---|
| POST | `/clients` | Dodanie klienta | `MECHANIC` |
| GET | `/clients` | Lista (search, limit, offset) | zalogowany |
| GET | `/clients/{client_id}` | Szczegóły klienta | `MECHANIC` |
| DELETE | `/clients/{client_id}` | Usunięcie (tylko bez pojazdów) | `ADMIN` |

**Query params (`GET /clients`):** `search`, `limit` (1–100), `offset`

### Pojazdy

| Metoda | Endpoint | Opis | Wymagana rola |
|---|---|---|---|
| POST | `/cars` | Dodanie pojazdu | `MECHANIC` |
| GET | `/cars` | Lista (search, filtry, paginacja) | zalogowany |
| GET | `/cars/{car_id}` | Szczegóły pojazdu | zalogowany |
| PUT | `/cars/{car_id}` | Aktualizacja danych pojazdu | `MECHANIC` |
| DELETE | `/cars/{car_id}` | Usunięcie (tylko bez zleceń) | `ADMIN` |

**Query params (`GET /cars`):** `search`, `brand`, `model`, `owner_id`, `limit`, `offset`

### Zlecenia serwisowe

| Metoda | Endpoint | Opis | Wymagana rola |
|---|---|---|---|
| POST | `/orders` | Utworzenie zlecenia | `MECHANIC` |
| GET | `/orders` | Lista (search, filtry, paginacja) | zalogowany |
| GET | `/orders/{order_id}` | Szczegóły zlecenia | zalogowany |
| PATCH | `/orders/{order_id}` | Częściowa aktualizacja (m.in. status, koszt, pojazd) | `MECHANIC` |

**Query params (`GET /orders`):** `search`, `status`, `car_id`, `min_cost`, `max_cost`, `limit`, `offset`

**Statusy zlecenia:** `PENDING`, `IN_PROGRESS`, `COMPLETED`, `CANCELLED`

### Pozostałe

| Metoda | Endpoint | Opis |
|---|---|---|
| GET | `/` | Status API |
| GET | `/api/v1/health` | Health check (serwer + baza) |

## Testy

Testy działają na osobnej bazie SQLite w pamięci (niezależnej od PostgreSQL).

```bash
pytest -v
```

## Struktura projektu

```
warsztat-api/
├── main.py              # Endpointy API
├── models.py            # Modele SQLAlchemy
├── schemas.py           # Schematy Pydantic
├── database.py          # Konfiguracja połączenia z bazą
├── auth.py              # JWT i autoryzacja (role)
├── create_admin.py      # Skrypt tworzenia konta ADMIN
├── test_main.py         # Testy integracyjne
├── conftest.py          # Fixtures pytest
├── docker-compose.yml   # PostgreSQL
├── requirements.txt
├── .env.example
└── README.md
```


