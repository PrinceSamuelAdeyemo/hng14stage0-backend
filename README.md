# HNGx Stage 1 Backend API

This project is a Django RESTful API for creating and managing simple user profiles based on a name. It integrates with three public APIs (Genderize, Agify, Nationalize) to predict gender, age, and nationality, then classifies and stores the results. 

## Features
- **Create Profile**: Accepts a name, fetches predictions from external APIs, classifies the data, and stores it.
- **Idempotency**: If a profile for the same name exists, returns the existing record instead of creating a new one.
- **Get Single Profile**: Retrieve a profile by its unique ID.
- **List Profiles**: Retrieve all profiles, with optional filtering by gender, country, or age group.
- **Delete Profile**: Remove a profile by its ID.
- **CORS**: All endpoints include `Access-Control-Allow-Origin: *` for easy frontend integration.

## Endpoints

### 1. Create Profile
- **POST** `/api/profiles`
- **Body:** `{ "name": "ella" }`
- **Response:**
  - `201 Created` with profile data
  - If name exists: `200 OK` with message and profile data

### 2. Get Single Profile
- **GET** `/api/profiles/{id}`
- **Response:**
  - `200 OK` with profile data

### 3. List Profiles
- **GET** `/api/profiles`
- **Query params:** `gender`, `country_id`, `age_group` (all optional, case-insensitive)
- **Response:**
  - `200 OK` with count and list of profiles

### 4. Delete Profile
- **DELETE** `/api/profiles/{id}`
- **Response:**
  - `204 No Content` on success

## Classification Logic
- **Age group:**
  - 0–12 → child
  - 13–19 → teenager
  - 20–59 → adult
  - 60+ → senior
- **Nationality:**
  - Picks the country with the highest probability from Nationalize

## Error Handling
- All errors return `{ "status": "error", "message": "..." }`
- 400: Missing or empty name
- 422: Invalid type
- 404: Profile not found
- 502: Upstream API returned invalid response

## Tech Stack
- Python 3
- Django & Django REST Framework
- SQLite (default)
- `requests` for HTTP calls

## Setup
1. Clone the repo
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Run migrations:
   ```bash
   python manage.py migrate
   ```
4. Start the server:
   ```bash
   python manage.py runserver
   ```

## Notes
- All timestamps are UTC ISO 8601.
- All IDs are UUID (v4 for now; upgrade to v7 if supported).
- CORS is enabled for all endpoints.
- External API failures or missing data return 502 and do not store the profile.

---

### Example cURL
```bash
curl -X POST http://localhost:8000/api/profiles -H "Content-Type: application/json" -d '{"name": "ella"}'
```

---

Made for HNGx Stage 0. Built by [Your Name].
