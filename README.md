# Kalyan Simulator Admin Panel

This repository houses the complete **Admin Operations Console** for the Kalyan Simulator platform. It is a monorepo consisting of a Next.js web frontend and a FastAPI backend. 

> **Note**: The learner-facing Student Application (Flutter) is maintained in a separate repository and workstream. This repository focuses solely on the admin control plane.

## Repository Structure

- [`admin-backend/`](./admin-backend/): Python 3.12+ FastAPI backend powering the admin panel, game resolution logic, and public mobile APIs.
- [`admin-frontend/`](./admin-frontend/): Node.js 20+ Next.js 14 frontend providing the web-based operations dashboard.

## Quick Start

### 1. Backend (FastAPI)
Open a terminal and start the backend:
```bash
cd admin-backend
cp .env.example .env
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
alembic upgrade head
python -m app.seed
uvicorn app.main:app --reload --port 8000
```
The Backend API and its Swagger documentation will be available at [http://localhost:8000/docs](http://localhost:8000/docs).

### 2. Frontend (Next.js)
Open a **new terminal window** and start the frontend:
```bash
cd admin-frontend
npm install
npm run dev
```
The Admin Panel will be accessible at [http://localhost:3000](http://localhost:3000).

*The seed script prints a generated demo admin password (or uses `ADMIN_INITIAL_PASSWORD` from your `.env`, min 12 chars) for `admin@kalyan.com`. `python -m app.seed` wipes the database and refuses to run against anything but SQLite.*

---

## Detailed Documentation
For more detailed information, see the component-specific READMEs:
- [Backend Documentation](./admin-backend/README.md)
- [Backend Capabilities Matrix](./admin-backend/CAPABILITIES.md)
- [Frontend Documentation](./admin-frontend/README.md)
