## Agentic AI Pharmacy Assistant System

This is a production-grade prototype for an **Agentic AI Pharmacy Assistant System**.  
It is designed to turn a traditional pharmacy into an AI-powered, autonomous ecosystem capable of understanding natural language orders, validating them safely, interacting with inventory and historical data, and executing backend actions.

**Phase 1** only sets up the project foundation: structure, configuration, and a minimal working backend.

---

## Project Structure

- **backend/**: FastAPI application, database connection, and data files.
- **agent/**: Agent orchestration and tools (placeholders for now).
- **frontend/**: Future chat UI and admin views (placeholders for now).
- **database/**: SQLite database file (`pharmacy.db`).

---

## Backend Setup

From the project root:

```bash
cd backend
python -m venv venv

# On Linux / macOS
source venv/bin/activate

# On Windows
venv\Scripts\activate

pip install -r requirements.txt
```

---

## Running the Backend Server

From the `backend` directory with your virtual environment activated:

```bash
uvicorn app.main:app --reload
```

Then open `http://localhost:8000` in a browser.

You should see a JSON response:

```json
{
  "status": "ok",
  "message": "Agentic Pharmacy Backend Running"
}
```

---

## Environment Variables

Environment variables are loaded from the root `.env` file. A template is provided:

```bash
OPENAI_API_KEY=
LANGFUSE_PUBLIC_KEY=
LANGFUSE_SECRET_KEY=
DATABASE_URL=sqlite:///../database/pharmacy.db
```

These values will be used in later phases for:

- OpenAI API access
- Langfuse observability
- Database connection configuration

---

## Next Phases

- **Phase 2**: Backend API endpoints and database models.
- **Phase 3**: Agent logic, tools, AI integration, and Langfuse wiring.
- **Phase 4**: Frontend chat UI and admin monitoring views.

