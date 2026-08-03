import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app import models  # noqa: F401 - ensures models are registered before create_all
from app.db import Base, engine
from app.routers import auth, cycles, pools

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Chitfund API")

# ALLOWED_ORIGINS: comma-separated list of frontend origins, e.g.
# "https://chitfund.vercel.app,http://localhost:5173". Falls back to the
# local dev origin so `uvicorn app.main:app` keeps working out of the box.
allowed_origins = os.environ.get("ALLOWED_ORIGINS", "http://localhost:5173").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(pools.router)
app.include_router(cycles.router)


@app.get("/health")
def health():
    return {"status": "ok"}
