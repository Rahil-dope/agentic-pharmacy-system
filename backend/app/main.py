from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.database import init_db
from app.routes import customer_router, medicine_router, order_router, refill_router
from app.routes.agent_routes import router as agent_router
from app.utils.load_excel_data import load_initial_data


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Run startup tasks when the app starts."""
    init_db()
    load_initial_data()
    yield


app = FastAPI(title="Agentic Pharmacy Backend", lifespan=lifespan)


@app.get("/")
async def read_root():
    return {
        "status": "ok",
        "message": "Agentic Pharmacy Backend Running",
    }


app.include_router(medicine_router, prefix="/api")
app.include_router(order_router, prefix="/api")
app.include_router(customer_router, prefix="/api")
app.include_router(refill_router, prefix="/api")
app.include_router(agent_router, prefix="/api/agent")
