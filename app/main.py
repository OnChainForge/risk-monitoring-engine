from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database import Base, engine
from app.logging_config import setup_logging
from app.routers import rules, events, alerts, analyze

setup_logging()

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Risk Monitoring Engine",
    description="Configurable rule engine for real-time on-chain risk monitoring and alerting.",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # dev only — restrict this to your real domain before deploying
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(rules.router)
app.include_router(events.router)
app.include_router(alerts.router)
app.include_router(analyze.router)


@app.get("/health")
def health_check():
    return {"status": "ok"}
