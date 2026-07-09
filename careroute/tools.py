import json
from pathlib import Path

from pydantic import BaseModel, Field

SYMPTOMS_PATH = Path(__file__).resolve().parent.parent / "data" / "symptoms.json"


class LookupSymptomsInput(BaseModel):
    symptoms: list[str] = Field(description="Symptoms reported by the caller")


class ScoreUrgencyInput(BaseModel):
    red_flags: list[str] = Field(description="Red-flag indicators present, if any")
    duration_days: int = Field(ge=0, description="How many days symptoms have lasted")
    severity: int = Field(ge=1, le=10, description="Caller-reported severity from 1 to 10")


class SuggestAppointmentInput(BaseModel):
    urgency: str = Field(description="One of: emergency, urgent, routine, self_care")


def lookup_symptoms(**kwargs) -> dict:
    params = LookupSymptomsInput(**kwargs)
    knowledge = json.loads(SYMPTOMS_PATH.read_text())
    matches = {}
    unmatched = []
    for symptom in params.symptoms:
        key = symptom.strip().lower()
        if key in knowledge:
            matches[key] = knowledge[key]
        else:
            unmatched.append(symptom)
    return {"matches": matches, "unmatched": unmatched}


def score_urgency(**kwargs) -> dict:
    params = ScoreUrgencyInput(**kwargs)
    if params.red_flags:
        return {
            "urgency": "emergency",
            "rationale": "One or more red-flag indicators are present.",
        }
    if params.severity >= 7:
        return {
            "urgency": "urgent",
            "rationale": "High severity without red flags warrants same-day care.",
        }
    if params.severity >= 4 or params.duration_days >= 7:
        return {
            "urgency": "routine",
            "rationale": "Moderate or persistent symptoms warrant a scheduled visit.",
        }
    return {
        "urgency": "self_care",
        "rationale": "Mild, short-lived symptoms are suitable for self-care.",
    }


def suggest_appointment(**kwargs) -> dict:
    params = SuggestAppointmentInput(**kwargs)
    slots = {
        "emergency": "Go to the nearest emergency department now",
        "urgent": "Today 3:30 PM, CareRoute Urgent Care, 100 Demo St",
        "routine": "Thursday 10:00 AM, Dr. Example, CareRoute Clinic",
        "self_care": "No appointment needed; self-care guidance provided",
    }
    slot = slots.get(params.urgency, "Unknown urgency level; please re-score")
    return {"slot": slot, "note": "DEMO STUB: fake scheduling data, not a real appointment"}


TOOLS = [
    {
        "name": "lookup_symptoms",
        "description": (
            "Look up reported symptoms in the local knowledge base. Returns "
            "possible causes and red-flag indicators for each matched symptom. "
            "Call this first for any symptoms the caller reports."
        ),
        "input_schema": LookupSymptomsInput.model_json_schema(),
    },
    {
        "name": "score_urgency",
        "description": (
            "Score triage urgency from red flags, symptom duration, and severity. "
            "Returns emergency, urgent, routine, or self_care with a rationale. "
            "Call this after looking up symptoms."
        ),
        "input_schema": ScoreUrgencyInput.model_json_schema(),
    },
    {
        "name": "suggest_appointment",
        "description": (
            "Suggest an appointment slot for a scored urgency level. Call this "
            "after score_urgency to give the caller a concrete next step."
        ),
        "input_schema": SuggestAppointmentInput.model_json_schema(),
    },
]

HANDLERS = {
    "lookup_symptoms": lookup_symptoms,
    "score_urgency": score_urgency,
    "suggest_appointment": suggest_appointment,
}
