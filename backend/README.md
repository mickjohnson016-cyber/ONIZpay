# OinzPay Backend Setup

This is the production-ready FastAPI backend for the OinzPay Secure Property Escrow Platform.

## Features
- JWT Authentication (Register/Login)
- Escrow Management (Create, Fund, Release)
- Dashboard Analytics
- PostgreSQL Database
- Dockerized Environment

## Prerequisites
- Python 3.11+
- Docker & Docker Compose (optional but recommended)
- PostgreSQL (if running locally)

## Getting Started (with Docker)

1. Navigate to the backend directory:
   ```bash
   cd backend
   ```

2. Start the services:
   ```bash
   docker-compose up --build
   ```

The API will be available at `http://localhost:8000`.
Documentation (Swagger UI) at `http://localhost:8000/docs`.

## Local Development (without Docker)

1. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Configure environment variables:
   Copy `.env` and adjust your database settings.

4. Start the server:
   ```bash
   uvicorn app.main:app --reload
   ```

## Test cURL Examples

### 1. Register a User
```bash
curl -X 'POST' \
  'http://localhost:8000/api/v1/auth/register' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{
  "email": "user@example.com",
  "password": "strongpassword",
  "full_name": "John Doe",
  "phone_number": "+2348000000000"
}'
```

### 2. Login
```bash
curl -X 'POST' \
  'http://localhost:8000/api/v1/auth/login' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/x-www-form-urlencoded' \
  -d 'username=user@example.com&password=strongpassword'
```

### 3. Fetch Dashboard (Requires Token)
```bash
curl -X 'GET' \
  'http://localhost:8000/api/v1/escrow/dashboard' \
  -H 'Authorization: Bearer YOUR_ACCESS_TOKEN'
```

### 4. Create Escrow
```bash
curl -X 'POST' \
  'http://localhost:8000/api/v1/escrow/create' \
  -H 'accept: application/json' \
  -H 'Authorization: Bearer YOUR_ACCESS_TOKEN' \
  -H 'Content-Type: application/json' \
  -d '{
  "title": "Property Purchase - Villa A",
  "description": "Purchase of semi-detached villa",
  "amount": 50000,
  "seller_email": "seller@example.com",
  "milestones": [
    {"title": "Deposit", "amount": 5000},
    {"title": "Final Payment", "amount": 45000}
  ]
}'
```
