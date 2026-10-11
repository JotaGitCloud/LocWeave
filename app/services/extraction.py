import json
from pathlib import Path
from sqlalchemy.orm import Session
from app import models

def extract_from_json(file_path: str, project_id: int, db: Session) -> int:
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    count = 0
    if isinstance(data, dict):
        for key, value in data.items():
            if isinstance(value, str) and value.strip():
                entry = models.StringEntry(
                    project_id=project_id,
                    string_key=str(key),
                    source_text=value.strip(),
                    context="Imported from JSON"
                )
                db.add(entry)
                count += 1
    db.commit()
    return count

def extract_from_txt(file_path: str, project_id: int, db: Session) -> int:
    with open(file_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    count = 0
    for i, line in enumerate(lines, start=1):
        text = line.strip()
        if text:
            entry = models.StringEntry(
                project_id=project_id,
                string_key=f"line_{i:03d}",
                source_text=text,
                context="Imported from TXT"
            )
            db.add(entry)
            count += 1
    db.commit()
    return count

def extract_file(file_path: str, project_id: int, db: Session) -> int:
    path = Path(file_path)
    suffix = path.suffix.lower()

    if suffix == ".json":
        return extract_from_json(file_path, project_id, db)
    elif suffix == ".txt":
        return extract_from_txt(file_path, project_id, db)
    else:
        raise ValueError("Formato no soportado. Usa .json o .txt")