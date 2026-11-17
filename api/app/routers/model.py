import json
from pathlib import Path

from fastapi import APIRouter
from pydantic import BaseModel

from app.deps import CurrentUser
from app.services import categorizer

router = APIRouter(prefix="/model", tags=["Modèle"])

REPORT_PATH = Path(__file__).resolve().parents[2] / "ml" / "reports" / "metrics.json"


class ModelInfo(BaseModel):
    engine: str
    name: str | None = None
    trained_at: str | None = None
    training_examples: int | None = None
    accuracy_manual_test: float | None = None


@router.get("", response_model=ModelInfo)
def read_model_info(_user: CurrentUser):
    """Indique si la catégorisation repose sur le modèle entraîné ou sur les règles, avec ses mesures."""
    if not categorizer.model_loaded():
        return ModelInfo(engine="regles")
    try:
        report = json.loads(REPORT_PATH.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return ModelInfo(engine="modele")
    return ModelInfo(
        engine="modele",
        name=report.get("modele_retenu"),
        trained_at=report.get("date"),
        training_examples=report.get("donnees", {}).get("total"),
        accuracy_manual_test=report.get("test_manuel", {}).get("exactitude"),
    )
