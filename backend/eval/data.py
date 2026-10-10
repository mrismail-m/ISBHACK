"""Load the evaluation dataset from fixtures/eval/ and the A1 assessment. Task: M4.1."""

import csv
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from app.config import FIXTURES_DIR
from app.schemas.grading import Rubric

EVAL_DIR = FIXTURES_DIR / "eval"
ANSWERS_FILE = EVAL_DIR / "answers_a1.json"
AUTHOR_FILE = EVAL_DIR / "author_levels_a1.json"
HUMAN_FILE = EVAL_DIR / "human_scores_a1.csv"
ASSESSMENT_ID = "a_1"


@dataclass(frozen=True)
class Answer:
    answer_id: str
    text: str


@dataclass(frozen=True)
class Assessment:
    title: str
    instructions_md: str
    max_marks: float
    rubric: Rubric


def load_answers(path: Path = ANSWERS_FILE) -> list[Answer]:
    rows = json.loads(path.read_text(encoding="utf-8"))
    return [Answer(r["answer_id"], r["text"]) for r in rows]


def load_assessment() -> Assessment:
    raw: list[dict[str, Any]] = json.loads(
        (FIXTURES_DIR / "api" / "assessments.json").read_text(encoding="utf-8")
    )
    a = next(x for x in raw if x["id"] == ASSESSMENT_ID)
    return Assessment(
        title=a["title"],
        instructions_md=a["instructions_md"],
        max_marks=float(a["max_marks"]),
        rubric=Rubric.model_validate(a["rubric"]),
    )


def load_author_levels(path: Path = AUTHOR_FILE) -> dict[str, list[int]]:
    return json.loads(path.read_text(encoding="utf-8"))["levels"]


def load_human_scores(
    criteria: list[str], path: Path = HUMAN_FILE
) -> dict[str, dict[str, list[int]]]:
    """Return {rater: {answer_id: [level per criterion, in rubric order]}}.

    Only answers where the rater filled in every criterion are kept. A missing file or a
    blank template gives an empty dict, so the report says "pending" instead of inventing data.
    """
    if not path.exists():
        return {}
    cells: dict[str, dict[str, dict[str, int]]] = {}
    with path.open(encoding="utf-8", newline="") as fh:
        for row in csv.DictReader(fh):
            level = (row.get("level") or "").strip()
            if not level:
                continue
            value = int(level)
            if not 0 <= value <= 4:
                raise ValueError(f"level out of range in {path.name}: {row}")
            cells.setdefault(row["rater"], {}).setdefault(row["answer_id"], {})[
                row["criterion_id"]
            ] = value
    out: dict[str, dict[str, list[int]]] = {}
    for rater, answers in cells.items():
        for answer_id, by_criterion in answers.items():
            if all(c in by_criterion for c in criteria):
                out.setdefault(rater, {})[answer_id] = [by_criterion[c] for c in criteria]
    return out
