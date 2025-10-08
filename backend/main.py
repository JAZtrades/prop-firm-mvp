"""Main FastAPI application for the prop firm MVP.

This file creates the FastAPI instance, configures CORS, imports the
API routers and ensures the database schema is created on start‑up.  The
application is mounted at root (``/``) and exposes Swagger docs at
``/docs``.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .db.session import Base, engine
from .api import auth, accounts, trades, metrics, payouts, admin

# Create database tables on start up.  In a production setting you would
# manage schema migrations via Alembic instead of calling ``create_all``.
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Prop Firm MVP", version="0.1.0")

# Allow the front end to call the API locally.
origins = [
    "http://localhost",
    "http://localhost:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routers
app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(accounts.router, prefix="/accounts", tags=["accounts"])
app.include_router(trades.router, prefix="/trades", tags=["trades"])
app.include_router(metrics.router, prefix="/metrics", tags=["metrics"])
app.include_router(payouts.router, prefix="/payouts", tags=["payouts"])
app.include_router(admin.router, prefix="/admin", tags=["admin"])


@app.get("/")
def read_root():
    return {"message": "Welcome to the Prop Firm MVP API"}
