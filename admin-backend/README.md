# Admin Backend

The core API engine for the Kalyan Simulator, built with Python 3.12+, FastAPI, SQLAlchemy, and SQLite.

## Features
- **Data-Driven RBAC**: Custom roles and permissions for administrators.
- **Game Engine**: Dynamic resolution mechanics for Matka, Starline, and Gali-Disawar.
- **RESTful API**: Supports both the Next.js admin dashboard and the external mobile client (`/admin/*` and `/public/*` routers).
- **Error Handling**: Standardized machine-readable error codes (e.g. `CUTOFF_PASSED`).

## Setup Instructions

1. **Environment Config**:
   ```bash
   cp .env.example .env
   # Ensure JWT_SECRET is configured inside .env
   ```
2. **Dependencies**:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```
3. **Database Setup & Seeding**:
   ```bash
   alembic upgrade head
   python -m app.seed
   ```
   *Seeding creates the default Super Admin user (`admin@kalyan.com` / `admin123`).*

4. **Start Server**:
   ```bash
   uvicorn app.main:app --reload --port 8000
   ```

## API Documentation
Once the server is running, interactive API documentation is available at:
- **Swagger UI**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **ReDoc**: [http://localhost:8000/redoc](http://localhost:8000/redoc)

## Additional Reading
- [Capabilities Matrix](./CAPABILITIES.md): Details on supported game types and resolution mechanics.
- [Mobile API Integration](./MOBILE_API_INTEGRATION.md): Guide for connecting the external Flutter app.
