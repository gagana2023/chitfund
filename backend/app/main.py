from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app import models  # noqa: F401 - ensures models are registered before create_all
from app.db import Base, engine
from app.routers import auth, cycles, pools

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Chitfund API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
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
