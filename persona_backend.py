from __future__ import annotations

import os
import json
import asyncio
from datetime import datetime
from typing import List, Dict, Any, Optional

import httpx
from fastapi import FastAPI, HTTPException, Depends, UploadFile, File
from pydantic import BaseModel, Field as PydanticField
from sqlmodel import SQLModel, Field, create_engine, Session, select

from fastapi.middleware.cors import CORSMiddleware


OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434/api/generate")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "mistral:latest")
DATABASE_URL = "sqlite:///personas.db"

engine = create_engine(DATABASE_URL, echo=False)
app = FastAPI(title="Persona JSON Generator API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -------------------------------
# Database models
# -------------------------------
class Persona(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    samples: str = Field(default="[]", description="List[ str ] JSON-encoded writing samples")
    metadata_list: str = Field(default="[]", description="List[ dict ] JSON-encoded style metadata")
    persona_json: str = Field(default="{}", description="Final persona JSON (string)")
    updated_at: datetime = Field(default_factory=datetime.utcnow)


# -------------------------------
# Pydantic schemas
# -------------------------------
class SampleIn(BaseModel):
    text: str


class PersonaOut(BaseModel):
    id: int
    name: str
    persona: Dict[str, Any]
    samples: List[str]
    updated_at: datetime


# -------------------------------
# Helper functions
# -------------------------------
async def call_ollama(prompt: str) -> str:
    """Call local Ollama model and stream final response text"""
    payload = {
        "model": OLLAMA_MODEL,
        "prompt": prompt,
        "stream": False,
    }
    async with httpx.AsyncClient(timeout=120.0) as client:
        r = await client.post(OLLAMA_URL, json=payload)
        r.raise_for_status()
        data = r.json()
        return data.get("response", "")


def create_db_and_tables() -> None:
    SQLModel.metadata.create_all(engine)


@app.on_event("startup")
async def startup() -> None:
    create_db_and_tables()


# -------------------------------
# Prompt templates
# -------------------------------
STYLE_PROMPT_TEMPLATE = """
Analyze the following writing sample and return a JSON object with detailed style metadata. Use keys such as: sentence_length_avg, syntax_depth, vocabulary_diversity, pacing, tone, use_of_metaphor, use_of_sarcasm, emotional_tone, formality, humor_type, repetition_patterns, typical_sentence_structure, devices, dominant_POV, register, paragraph_structure, quirks, overall_impression.

Respond ONLY with valid JSON.

Writing sample:
"""

PERSONA_PROMPT_TEMPLATE = """
You are a persona architect creating style personas for LLM prompts.
Using the metadata below, generate a JSON object with 15-20 key traits.
Each trait should have the structure: "trait_name": {"value": <number|string>, "description": <string>}.
Respond ONLY with valid JSON.

Metadata:
"""


# -------------------------------
# Core logic
# -------------------------------
async def extract_metadata(sample: str) -> Dict[str, Any]:
    prompt = f"{STYLE_PROMPT_TEMPLATE}\n'''\n{sample}\n'''"
    response = await call_ollama(prompt)
    try:
        metadata = json.loads(response)
    except json.JSONDecodeError as e:
        raise ValueError(f"Failed to parse metadata JSON: {e} – Response was: {response[:200]}")
    return metadata


async def metadata_to_persona(metadata: Dict[str, Any]) -> Dict[str, Any]:
    prompt = f"{PERSONA_PROMPT_TEMPLATE}\n```json\n{json.dumps(metadata, indent=2)}\n```"
    response = await call_ollama(prompt)
    try:
        persona = json.loads(response)
    except json.JSONDecodeError as e:
        raise ValueError(f"Failed to parse persona JSON: {e} – Response was: {response[:200]}")
    return persona


def merge_metadata(existing: List[Dict[str, Any]], new: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Append new metadata; future: implement smarter merging."""
    return existing + [new]


# -------------------------------
# API endpoints
# -------------------------------
@app.post("/persona/", response_model=PersonaOut, status_code=201)
async def create_persona(name: str, sample: SampleIn):
    metadata = await extract_metadata(sample.text)
    persona_json = await metadata_to_persona(metadata)

    persona = Persona(
        name=name,
        samples=json.dumps([sample.text]),
        metadata_list=json.dumps([metadata]),
        persona_json=json.dumps(persona_json),
    )
    with Session(engine) as session:
        session.add(persona)
        session.commit()
        session.refresh(persona)
    return PersonaOut(
        id=persona.id,
        name=persona.name,
        persona=persona_json,
        samples=[sample.text],
        updated_at=persona.updated_at,
    )


@app.post("/persona/{persona_id}/add_sample", response_model=PersonaOut)
async def add_sample(persona_id: int, sample: SampleIn):
    with Session(engine) as session:
        persona = session.get(Persona, persona_id)
        if not persona:
            raise HTTPException(404, "Persona not found")
        samples = json.loads(persona.samples)
        metadata_list = json.loads(persona.metadata_list)

    # Process new sample
    new_metadata = await extract_metadata(sample.text)
    metadata_list = merge_metadata(metadata_list, new_metadata)

    # For simplicity, regenerate persona from latest metadata
    latest_persona_json = await metadata_to_persona(new_metadata)

    # Update record
    persona.samples = json.dumps(samples + [sample.text])
    persona.metadata_list = json.dumps(metadata_list)
    persona.persona_json = json.dumps(latest_persona_json)
    persona.updated_at = datetime.utcnow()

    with Session(engine) as session:
        session.add(persona)
        session.commit()
        session.refresh(persona)

    return PersonaOut(
        id=persona.id,
        name=persona.name,
        persona=latest_persona_json,
        samples=samples + [sample.text],
        updated_at=persona.updated_at,
    )


@app.get("/persona/{persona_id}", response_model=PersonaOut)
async def get_persona(persona_id: int):
    with Session(engine) as session:
        persona = session.get(Persona, persona_id)
        if not persona:
            raise HTTPException(404, "Persona not found")
        return PersonaOut(
            id=persona.id,
            name=persona.name,
            persona=json.loads(persona.persona_json),
            samples=json.loads(persona.samples),
            updated_at=persona.updated_at,
        )


@app.get("/persona/{persona_id}/export", response_model=dict)
async def export_persona_json(persona_id: int):
    with Session(engine) as session:
        persona = session.get(Persona, persona_id)
        if not persona:
            raise HTTPException(404, "Persona not found")
        return json.loads(persona.persona_json)


# -------------------------------
# Simple health check
# -------------------------------
@app.get("/")
async def root():
    return {"msg": "Persona JSON Generator API is running"}
