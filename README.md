# support-ticket-system# Support Ticketing App

This repository contains a **Support Ticketing Backend** built with **FastAPI**, **PostgreSQL**, and **WebSockets** for real-time chat between users and Customer Support Representatives (CSRs). It provides RESTful and WebSocket endpoints, JWT-based authentication, role-based permissions, and database migrations via Alembic.

---

## 🎯 Project Overview

The Support Ticketing App enables:

* **User signup & login** with secure password hashing and JWT tokens.
* **Ticket creation** by end users with fields: title, description, category, and type.
* **Auto-assignment** of new tickets to CSRs via a round-robin or random strategy.
* **Ticket listing & detail views** for users (with pagination, filtering, sorting).
* **CSR endpoints** to list, assign, and update ticket status (open, in\_progress, resolved, closed).
* **Real-time chat** per ticket using WebSockets, allowing user–CSR messaging.
* **Token refresh & logout** flows with refresh token revocation via a blacklist.

---

## 🛠️ Tech Stack

* **Framework**: FastAPI (async-first web framework)
* **Database**: PostgreSQL (relational) via SQLModel/SQLAlchemy
* **Migrations**: Alembic for schema versioning and migrations
* **Auth**: JWT (access + refresh) with bcrypt password hashing
* **WebSockets**: FastAPI WebSocket endpoints with a custom connection manager
* **Testing**: pytest, pytest-asyncio, httpx.AsyncClient, FastAPI TestClient

---

## 🚀 Getting Started

### Prerequisites

* Python 3.10+
* PostgreSQL database
* Docker & Docker Compose

### Installation

1. **Clone the repo**:

   ```bash
   git clone https://github.com/Korede01/support-ticket-system.git
   cd support-ticketing-system
   ```

2. **Create & activate a virtual environment**:

   ```bash
   python -m venv venv
   source venv/bin/activate
   ```

3. **Install dependencies**:

   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables** (copy `.env.example` to `.env`):

   ```ini
   DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/support_db
   JWT_SECRET_KEY=your_jwt_secret
   ALGORITHM=HS256
   ACCESS_TOKEN_EXPIRE_MINUTES=15
   REFRESH_TOKEN_EXPIRE_DAYS=7
   ```

### Database Migrations (Alembic)

We use **Alembic** to manage PostgreSQL schema changes:

1. **Create migration**:

   ```bash
   alembic revision --autogenerate -m "Add tickets table"
   ```

2. **Apply migrations**:

   ```bash
   alembic upgrade head
   ```

All migration scripts live under the `alembic/versions/` directory.

---

## 🏃‍♂️ Running the App

#### Locally (with Uvicorn)

```bash
uvicorn app.main:app --reload
```

The API will be available at `http://localhost:8000`.

#### With Docker Compose

```bash
docker-compose up --build
```

This spins up services: API, PostgreSQL, Redis, Celery worker.

---

## 📚 API Documentation

FastAPI auto-generates interactive docs:

* **Swagger UI**: `http://localhost:8000/docs`
* **ReDoc**: `http://localhost:8000/redoc`

### Namespaced Endpoints (`/api/v1`)

#### Auth

* `POST /auth/signup`
* `POST /auth/login`
* `POST /auth/refresh`
* `POST /auth/logout`

#### User Ticket Routes (`/api/v1/users/tickets`)

* `POST /tickets` — Create ticket
* `GET /tickets` — List own tickets (pagination, filter by `status`, `category`)
* `GET /tickets/{ticket_id}` — View single ticket

#### CSR Ticket Routes (`/api/v1/csr/tickets`)

* `GET /tickets` — List all tickets (optional `unassigned`, `status` filters)
* `POST /tickets/{ticket_id}/assign` — Assign CSR + set priority
* `PATCH /tickets/{ticket_id}` — Update ticket status

#### WebSocket Chat

* **Endpoint**: `ws://localhost:8000/ws/tickets/{ticket_id}?token=<JWT>`
* Authenticated user or CSR can connect. Messages are broadcast to all participants.

---

## 🧪 Testing

Run the full test suite via pytest:

```bash
pytest
```

This includes:

* Auth flow tests (`tests/test_auth.py`)
* Ticket CRUD & CSR tests (`tests/test_tickets.py`)
* Real-time chat tests (`tests/test_chat.py`)

---

## 📂 Project Structure

```
├── app/
│   ├── api/v1/endpoints/      # User & CSR routers
│   ├── core/                  # Config, dependencies, security
│   ├── db/                    # Session & Base
│   ├── models/                # SQLAlchemy models (User, Ticket, Message)
│   ├── schemas/               # Pydantic schemas
│   ├── services/              # Business logic (ticket assignment)
├── alembic/                   # DB migrations
├── tests/                     # pytest test files
├── Dockerfile
├── requirements.txt
└── README.md
```

---

## 🤝 Contributions

Contributions, issues, and feature requests are welcome! Please open a GitHub issue or submit a pull request.


