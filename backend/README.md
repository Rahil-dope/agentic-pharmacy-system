# Backend - Agentic Pharmacy System

This directory contains the FastAPI backend for the **Agentic AI Pharmacy Assistant System**.

At this stage (Phase 1), only the foundational structure, configuration, and database connection are in place. No business logic, models, or advanced routes are implemented yet.

## Requirements

- Python 3.11+

## Setup

From the `backend` directory:

```bash
python -m venv venv

# On Linux / macOS
source venv/bin/activate

# On Windows
venv\Scripts\activate

pip install -r requirements.txt
```

## Running the server

From the `backend` directory with your virtual environment activated:

```bash
uvicorn app.main:app --reload
```

Then open `http://localhost:8000` in a browser.  
You should see a JSON response indicating:

```json
{
  "status": "ok",
  "message": "Agentic Pharmacy Backend Running"
}
```

