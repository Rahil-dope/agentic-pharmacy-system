# Agentic AI Pharmacy Assistant System — Setup Guide

## 1. Project Overview

The **Agentic AI Pharmacy Assistant System** is a fully autonomous, AI-powered pharmacy management system built for HackFusion 2026. It enables patients to place medicine orders via a conversational interface, enforces prescription rules automatically, and predicts when refills are needed — all with end-to-end observability.

### Key Features

- 🤖 **Conversational AI Pharmacist** — Natural language interface powered by OpenAI tool calling
- 📦 **Inventory-Aware Ordering** — Real-time stock checks before every order
- 🔁 **Predictive Refill Detection** — Automatically identifies patients due for refills
- 🏭 **Warehouse Webhook Automation** — Triggers downstream systems on order creation
- 🔍 **Langfuse Observability** — Full trace logging of agent decisions and tool calls
- 💬 **Chat UI + Admin Dashboard** — Browser-based interface for patients and administrators
- 🎙️ **Voice Input** — Speak your request using the browser microphone

---

## 2. Project Structure

```
agentic-pharmacy-system/
│
├── backend/                  # FastAPI server (API, database, routes)
│   ├── app/
│   │   ├── main.py           # Application entrypoint
│   │   ├── routes/           # API route handlers
│   │   ├── models/           # SQLAlchemy database models
│   │   ├── schemas/          # Pydantic request/response schemas
│   │   ├── services/         # Business logic (refill engine, etc.)
│   │   └── utils/            # Excel ingestion, helpers
│   └── requirements.txt
│
├── agent/                    # AI agent system
│   ├── agent.py              # Core agent loop and tool dispatch
│   ├── tools.py              # Tool implementations (backend integration)
│   ├── observability.py      # Langfuse trace/span helpers
│   └── config.py             # Agent configuration
│
├── frontend/                 # Browser-based UI (pure HTML/CSS/JS)
│   ├── index.html            # Main page (Chat + Admin views)
│   ├── styles.css            # Styling
│   └── app.js                # Frontend logic and API calls
│
├── database/                 # SQLite database files
│   └── pharmacy.db           # Auto-created on first run
│
├── .env                      # Environment variables (secrets)
├── SETUP.md                  # This file
└── README.md
```

---

## 3. System Requirements

| Requirement | Details |
|---|---|
| **Python** | 3.10 or higher |
| **Operating System** | Windows, Linux, or macOS |
| **Browser** | Google Chrome (recommended, required for voice input) |
| **OpenAI API Key** | Required for agent functionality |
| **Langfuse Account** | Optional but recommended for trace visibility |

---

## 4. Clone or Download the Project

**Option A — Git Clone:**
```bash
git clone <repository_url>
cd agentic-pharmacy-system
```

**Option B — ZIP Download:**
1. Download the ZIP from the repository
2. Extract the archive
3. Navigate into the `agentic-pharmacy-system` folder

---

## 5. Environment Setup

### Step 1 — Navigate to the backend directory

```bash
cd backend
```

### Step 2 — Create a Python virtual environment

```bash
python -m venv venv
```

### Step 3 — Activate the virtual environment

**Windows:**
```bash
venv\Scripts\activate
```

**Linux / macOS:**
```bash
source venv/bin/activate
```

### Step 4 — Install dependencies

```bash
pip install -r requirements.txt
```

---

## 6. Configure Environment Variables

Create a `.env` file in the **project root** (next to `SETUP.md`) with the following content:

```env
# OpenAI — Required for agent to function
OPENAI_API_KEY=your_openai_api_key

# Langfuse Observability — Optional but recommended
LANGFUSE_PUBLIC_KEY=your_langfuse_public_key
LANGFUSE_SECRET_KEY=your_langfuse_secret_key
LANGFUSE_HOST=https://cloud.langfuse.com

# Webhook — Use https://webhook.site to get a free test URL
WAREHOUSE_WEBHOOK_URL=https://webhook.site/your_webhook_url

# Database path (relative to backend/ folder)
DATABASE_URL=sqlite:///../database/pharmacy.db
```

### Where to obtain keys

| Key | Source |
|---|---|
| `OPENAI_API_KEY` | [platform.openai.com/api-keys](https://platform.openai.com/api-keys) |
| `LANGFUSE_PUBLIC_KEY` / `LANGFUSE_SECRET_KEY` | [cloud.langfuse.com](https://cloud.langfuse.com) → Project Settings |
| `WAREHOUSE_WEBHOOK_URL` | [webhook.site](https://webhook.site) — free, no signup needed |

---

## 7. Run the Backend Server

Ensure the virtual environment is active and you are in the `backend/` directory.

```bash
uvicorn app.main:app --reload
```

**Expected output:**
```
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
INFO:     Started reloader process
INFO:     Application startup complete.
```

**Test the API is running:**

Open your browser and visit: [http://localhost:8000/docs](http://localhost:8000/docs)

You should see the interactive FastAPI Swagger documentation.

---

## 8. Run the Frontend

1. Navigate to the `frontend/` folder in your file explorer
2. Open `index.html` in Google Chrome:
   - **Double-click** `index.html`, or
   - **Right-click** → *Open with* → *Google Chrome*

The frontend automatically connects to the backend at `http://localhost:8000`.

> **Note:** The backend must be running before you open the frontend.

---

## 9. Test the Chat System

1. The Chat View opens by default
2. Type a message in the input field:
   ```
   I need 5 paracetamol tablets
   ```
3. Click **Send** or press **Enter**

**Expected result:**
- Agent checks stock availability
- Order is created if stock is available
- Agent response appears in the chat window
- A **🔍 View Trace in Langfuse** link appears below the response

Click the trace link to view the full agent decision tree in your Langfuse dashboard.

---

## 10. Test the Admin Dashboard

1. Click the **Admin View** button at the top right
2. The dashboard loads automatically and shows:
   - **Refill Alerts table** — Customers overdue for a refill
   - **Inventory table** — All medicines, stock levels, and prescription requirements

---

## 11. Test Voice Input

1. Click the **🎤 microphone button** in the chat input area
2. The button glows red — speak your request clearly, e.g.:
   ```
   I need my blood pressure medication refilled
   ```
3. Your speech is transcribed into the input field
4. Review the text, then click **Send**

> **Important:** Voice input requires Google Chrome. Other browsers may not support the Web Speech API.

---

## 12. Database Behavior

- The SQLite database is **automatically created** on first startup at `database/pharmacy.db`
- Medicine inventory and customer order history are **loaded from Excel files** automatically
- All orders, customers, and medicines are persisted across server restarts

---

## 13. Observability Verification

After placing an order via the chat UI:

1. Click the **🔍 View Trace in Langfuse** link displayed below the agent response
2. This opens your Langfuse dashboard showing:
   - The full agent execution trace
   - Individual tool calls (`check_medicine_availability`, `create_order`, etc.)
   - LLM input/output tokens
   - Final agent response
   - Warehouse webhook trigger

If `LANGFUSE_PUBLIC_KEY` / `LANGFUSE_SECRET_KEY` are not set, tracing is skipped gracefully and the trace link will not be shown.

---

## 14. Webhook Testing

1. Visit [https://webhook.site](https://webhook.site) and copy your unique URL
2. Add it to `.env`:
   ```env
   WAREHOUSE_WEBHOOK_URL=https://webhook.site/your-unique-id
   ```
3. Restart the backend server
4. Place an order via the chat UI
5. Go to webhook.site — you will see the incoming webhook payload with order details

---

## 15. Troubleshooting

| Problem | Solution |
|---|---|
| `ModuleNotFoundError` on startup | Ensure virtual environment is activated and `pip install -r requirements.txt` was run |
| Backend won't start | Check that port 8000 is not already in use |
| `OPENAI_API_KEY` error | Ensure `.env` is in the project root and the key is valid |
| Frontend shows "backend offline" | Ensure `uvicorn` is running before opening the frontend |
| Langfuse traces not visible | Check `LANGFUSE_PUBLIC_KEY` and `LANGFUSE_SECRET_KEY` in `.env` |
| Voice input not working | Switch to Google Chrome; other browsers are not supported |
| Database errors | Delete `database/pharmacy.db` and restart backend to rebuild from scratch |
| Agent gives unhelpful response | Check that `OPENAI_API_KEY` is valid and has available credits |

---

## 16. Stop the Server

Press **CTRL+C** in the terminal where `uvicorn` is running.

To deactivate the virtual environment:
```bash
deactivate
```

---

## 17. Summary

The **Agentic AI Pharmacy Assistant System** is fully operational and ready for demonstration.

The complete system flow is:

```
User (Frontend) → Chat API → AI Agent → Tool Calls → Backend DB
                                                            ↓
                                                    Webhook Triggered
                                                            ↓
                                                  Langfuse Trace Created
                                                            ↓
                        Structured Response ← Agent ← Tool Results
                                ↓
                    Response + Trace Link displayed in UI
```

The system is designed to showcase autonomous AI decision-making with full observability, prescription safety enforcement, and predictive analytics — all in a clean, functional UI.
