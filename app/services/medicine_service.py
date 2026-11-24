import json
from pathlib import Path

DATABASE_PATH = Path(__file__).resolve().parents[2] / "data" / "medicines.json"

def load_medicine_database():
    if not DATABASE_PATH.exists():
        return []
    with DATABASE_PATH.open("r", encoding="utf-8") as file:
        return json.load(file).get("medicines", [])

def search_medicines(disease: str):
    results = []
    for medicine in load_medicine_database():
        conditions = [x.lower() for x in medicine.get("conditions", [])]
        if disease.lower() in conditions and medicine.get("clinically_reviewed") is True and medicine.get("source_url"):
            results.append({
                "generic_name": medicine.get("generic_name"),
                "therapeutic_class": medicine.get("therapeutic_class"),
                "indication": medicine.get("indication"),
                "contraindications": medicine.get("contraindications", []),
                "side_effects": medicine.get("side_effects", []),
                "source_title": medicine.get("source_title"),
                "source_url": medicine.get("source_url"),
            })
    return results
