# Warsztat API

REST API do zarządzania warsztatem samochodowym — klientami, pojazdami i zleceniami serwisowymi. Zbudowane w FastAPI z asynchroniczną obsługą PostgreSQL, uwierzytelnianiem JWT i systemem ról.

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
- Zarządzanie klientami warsztatu (CRUD)
- Zarządzanie pojazdami, z filtrowaniem po marce, modelu i właścicielu
- Zarządzanie zleceniami serwisowymi, z filtrowaniem po statusie i koszcie
- Health check sprawdzający realny stan połączenia z bazą danych

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
   venv\Scripts\activate      # Windows
   source venv/bin/activate   # Linux/macOS

   pip install -r requirements.txt
   ```

3. Skopiuj plik z przykładową konfiguracją i uzupełnij własnymi wartościami:
   ```bash
   cp .env.example .env
   ```

   Wymagane zmienne środowiskowe:

   | Zmienna | Opis |
   |---|---|
   | `SECRET_KEY` | Tajny klucz do podpisywania tokenów JWT |
   | `ALGORITHM` | Algorytm JWT (domyślnie `HS256`) |
   | `ACCESS_TOKEN_EXPIRE_MINUTES` | Czas ważności tokenu w minutach |
   | `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT`, `DB_NAME` | Dane połączenia z PostgreSQL |
   | `DATABASE_URL` | Pełny adres połączenia SQLAlchemy |
   | `DEBUG` | `true`/`false` — włącza logowanie zapytań SQL |

4. Uruchom bazę danych:
   ```bash
   docker-compose up -d
   ```

5. Uruchom serwer:
   ```bash
   uvicorn main:app --reload
   ```

API będzie dostępne pod `http://127.0.0.1:8000`, a interaktywna dokumentacja (Swagger UI) pod `http://127.0.0.1:8000/docs`.

## Tworzenie pierwszego konta administratora

Ze względów bezpieczeństwa rola `ADMIN` nie może zostać ustawiona przez publiczny endpoint rejestracji. Aby utworzyć pierwsze konto admina, uruchom skrypt:

```bash
python create_admin.py
```

Skrypt zapyta o email i hasło, a następnie utworzy użytkownika z rolą `ADMIN` (lub podniesie rolę istniejącego użytkownika).

## Endpointy

### Autoryzacja

| Metoda | Endpoint | Opis | Wymagana rola |
|---|---|---|---|
| POST | `/register` | Rejestracja nowego użytkownika (rola `MECHANIC`) | — |
| POST | `/login` | Logowanie, zwraca token JWT | — |
| GET | `/users/me` | Dane zalogowanego użytkownika | zalogowany |
| PATCH | `/users/{user_id}/role` | Zmiana roli użytkownika | `ADMIN` |

### Klienci

| Metoda | Endpoint | Opis | Wymagana rola |
|---|---|---|---|
| POST | `/clients` | Dodanie klienta | `MECHANIC` |
| GET | `/clients` | Lista klientów | zalogowany |
| GET | `/clients/{client_id}` | Szczegóły klienta | `MECHANIC` |

### Pojazdy

| Metoda | Endpoint | Opis | Wymagana rola |
|---|---|---|---|
| POST | `/cars` | Dodanie pojazdu | `MECHANIC` |
| GET | `/cars` | Lista pojazdów (filtry: marka, model, właściciel) | zalogowany |
| GET | `/cars/{car_id}` | Szczegóły pojazdu | zalogowany |
| DELETE | `/cars/{car_id}` | Usunięcie pojazdu | `ADMIN` |

### Zlecenia serwisowe

| Metoda | Endpoint | Opis | Wymagana rola |
|---|---|---|---|
| POST | `/orders` | Utworzenie zlecenia | `MECHANIC` |
| GET | `/orders` | Lista zleceń (filtry: status, pojazd, koszt) | zalogowany |
| GET | `/orders/{order_id}` | Szczegóły zlecenia | zalogowany |
| PATCH | `/orders/{order_id}` | Aktualizacja zlecenia | `MECHANIC` |

### Pozostałe

| Metoda | Endpoint | Opis |
|---|---|---|
| GET | `/` | Status API |
| GET | `/api/v1/health` | Health check (sprawdza połączenie z bazą) |

## Testy

Testy działają na osobnej bazie SQLite w pamięci, niezależnej od bazy produkcyjnej.

```bash
pytest -v
```

## Struktura projektu

```
warsztat-api/
├── main.py            # Endpointy API
├── models.py           # Modele SQLAlchemy
├── schemas.py          # Schematy Pydantic
├── database.py         # Konfiguracja połączenia z bazą
├── auth.py             # Logika JWT i autoryzacji
├── create_admin.py     # Skrypt do tworzenia konta administratora
├── test_main.py         # Testy
├── conftest.py          # Konfiguracja testów (fixtures)
├── docker-compose.yml   # Konfiguracja bazy danych
├── requirements.txt
└── .env.example
```