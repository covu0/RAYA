"""RAYA backend — FastAPI + SQLite. Run with: uvicorn main:app --reload"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import sqlite3
from contextlib import contextmanager

from interactions import resolve_drug, check_interactions, list_known_drugs

DB_PATH = "raya.db"

app = FastAPI(title="RAYA API", version="0.1.0")

# CORS — open for local dev; tighten for production
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@contextmanager
def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db():
    with get_db() as db:
        db.executescript("""
        CREATE TABLE IF NOT EXISTS caregivers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            phone TEXT
        );
        CREATE TABLE IF NOT EXISTS patients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            caregiver_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            age INTEGER,
            FOREIGN KEY (caregiver_id) REFERENCES caregivers(id)
        );
        CREATE TABLE IF NOT EXISTS medications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_id INTEGER NOT NULL,
            name_input TEXT NOT NULL,
            active_ingredient TEXT NOT NULL,
            dose TEXT,
            frequency TEXT,
            FOREIGN KEY (patient_id) REFERENCES patients(id)
        );
        """)


init_db()


# ----- Pydantic models -----
class CaregiverIn(BaseModel):
    name: str
    phone: Optional[str] = None


class PatientIn(BaseModel):
    caregiver_id: int
    name: str
    age: Optional[int] = None


class MedicationIn(BaseModel):
    name: str
    dose: Optional[str] = None
    frequency: Optional[str] = None


# ----- Endpoints -----
@app.get("/")
def root():
    return {"app": "RAYA", "status": "ok"}


@app.get("/drugs")
def known_drugs():
    """Returns ingredient → [aliases] for the frontend autocomplete."""
    return list_known_drugs()


@app.post("/caregivers")
def create_caregiver(c: CaregiverIn):
    with get_db() as db:
        cur = db.execute(
            "INSERT INTO caregivers (name, phone) VALUES (?, ?)",
            (c.name, c.phone),
        )
        return {"id": cur.lastrowid, "name": c.name, "phone": c.phone}


@app.post("/patients")
def create_patient(p: PatientIn):
    with get_db() as db:
        cur = db.execute(
            "INSERT INTO patients (caregiver_id, name, age) VALUES (?, ?, ?)",
            (p.caregiver_id, p.name, p.age),
        )
        return {"id": cur.lastrowid, **p.model_dump()}


@app.get("/patients/{patient_id}")
def get_patient(patient_id: int):
    with get_db() as db:
        row = db.execute(
            "SELECT * FROM patients WHERE id = ?", (patient_id,)
        ).fetchone()
        if not row:
            raise HTTPException(404, "Patient not found")
        return dict(row)


@app.get("/patients/{patient_id}/medications")
def list_medications(patient_id: int):
    with get_db() as db:
        rows = db.execute(
            "SELECT * FROM medications WHERE patient_id = ? ORDER BY id DESC",
            (patient_id,),
        ).fetchall()
        return [dict(r) for r in rows]


@app.post("/patients/{patient_id}/medications")
def add_medication(patient_id: int, med: MedicationIn):
    resolved = resolve_drug(med.name)
    if not resolved:
        raise HTTPException(
            400,
            {
                "error": "drug_not_recognized",
                "message": f"Could not recognize drug '{med.name}'.",
            },
        )
    with get_db() as db:
        existing = db.execute(
            "SELECT active_ingredient FROM medications WHERE patient_id = ?",
            (patient_id,),
        ).fetchall()
        existing_ingredients = [r["active_ingredient"] for r in existing]
        warnings = check_interactions(resolved, existing_ingredients)

        cur = db.execute(
            """INSERT INTO medications
               (patient_id, name_input, active_ingredient, dose, frequency)
               VALUES (?, ?, ?, ?, ?)""",
            (patient_id, med.name, resolved, med.dose, med.frequency),
        )
        return {
            "id": cur.lastrowid,
            "patient_id": patient_id,
            "name_input": med.name,
            "active_ingredient": resolved,
            "dose": med.dose,
            "frequency": med.frequency,
            "warnings": warnings,
        }


@app.delete("/medications/{medication_id}")
def delete_medication(medication_id: int):
    with get_db() as db:
        db.execute("DELETE FROM medications WHERE id = ?", (medication_id,))
        return {"deleted": medication_id}


@app.get("/patients/{patient_id}/check")
def full_check(patient_id: int):
    """Run a full interaction scan across all current medications."""
    with get_db() as db:
        rows = db.execute(
            "SELECT active_ingredient FROM medications WHERE patient_id = ?",
            (patient_id,),
        ).fetchall()
    ingredients = [r["active_ingredient"] for r in rows]
    all_warnings = []
    seen_pairs = set()
    for i in range(len(ingredients)):
        warnings = check_interactions(ingredients[i], ingredients[:i])
        for w in warnings:
            pair = frozenset({w["drug_a"], w["drug_b"]})
            if pair in seen_pairs:
                continue
            seen_pairs.add(pair)
            all_warnings.append(w)
    return {"medication_count": len(ingredients), "warnings": all_warnings}
