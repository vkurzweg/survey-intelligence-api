import json
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from pymongo import MongoClient
from pymongo.errors import PyMongoError

from app.ask_layer.ask import INTENTS, MissingRequiredParamError, UnknownIntentError, ask


# ── Lifespan: open / close MongoDB connection ──────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    uri = os.environ["MONGODB_URI"]
    db_name = os.environ["MONGODB_DB"]
    client = MongoClient(uri)
    app.state.db = client[db_name]
    yield
    client.close()


# ── App ────────────────────────────────────────────────────────────────────────

app = FastAPI(
    title="Survey Intelligence API",
    description="Ask-layer API for survey intelligence data.",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Request / response models ──────────────────────────────────────────────────

class AskRequest(BaseModel):
    intent: str
    params: dict | None = None


# ── Routes ─────────────────────────────────────────────────────────────────────

@app.get("/")
def root():
    return {
        "service": "survey-intelligence-api",
        "version": "0.1.0",
        "intents": sorted(INTENTS.keys()),
        "docs": "/docs",
    }


@app.get("/health")
def health():
    try:
        app.state.db.command("ping")
        db_status = "ok"
    except PyMongoError:
        db_status = "unreachable"
    return {"status": "ok", "db": db_status}


@app.get("/intents")
def list_intents():
    return {
        intent_id: {
            "description": defn["description"],
            "required_params": defn.get("required_params", []),
            "default_params": defn["default_params"],
            "stakeholders": defn.get("stakeholders", []),
        }
        for intent_id, defn in INTENTS.items()
    }


@app.post("/ask")
def ask_post(body: AskRequest):
    return _run_ask(body.intent, body.params)


@app.get("/ask")
def ask_get(
    intent: str = Query(..., description="Intent ID"),
    params: str | None = Query(None, description="JSON-encoded params object"),
):
    try:
        parsed_params = json.loads(params) if params else None
    except json.JSONDecodeError:
        raise HTTPException(status_code=422, detail="params must be a valid JSON object")
    return _run_ask(intent, parsed_params)


# ── Shared handler ─────────────────────────────────────────────────────────────

def _run_ask(intent_id: str, params: dict | None) -> dict:
    try:
        return ask(intent_id, params, app.state.db)
    except UnknownIntentError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except MissingRequiredParamError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except PyMongoError as e:
        raise HTTPException(status_code=503, detail=f"Database error: {e}")
