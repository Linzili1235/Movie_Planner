from fastapi import FastAPI
from pydantic import BaseModel, Field
from typing import List, Optional

app = FastAPI(title="CineMatch API", version="0.1.0")


class Constraints(BaseModel):
    # Hard constraints (filters). These should be applied deterministically.
    max_runtime: Optional[int] = None
    min_year: Optional[int] = None
    genres: List[str] = Field(default_factory=list)


class RecommendRequest(BaseModel):
    # User intent in natural language (e.g., "lighthearted comedy for a group").
    mood: str
    constraints: Constraints = Field(default_factory=Constraints)


class Movie(BaseModel):
    title: str
    year: int
    genres: List[str]
    runtime: int
    explanation: str


@app.get("/health")
def health():
    return {"ok": True}


@app.post("/v1/recommendations/query", response_model=list[Movie])
def recommend(req: RecommendRequest):
    """
    MVP implementation:
    - Return a small mocked list so the frontend + BFF + backend chain works end-to-end.
    - Later, replace this with DB retrieval + vector search + reranking.
    """
    base = [
        Movie(
            title="The Grand Budapest Hotel",
            year=2014,
            genres=["Comedy"],
            runtime=99,
            explanation=f"Matches a '{req.mood}' vibe and is fast-paced and group-friendly.",
        ),
        Movie(
            title="Knives Out",
            year=2019,
            genres=["Mystery", "Comedy"],
            runtime=130,
            explanation=f"Fits '{req.mood}' with a mix of humor and a mystery you can discuss afterward.",
        ),
    ]

    # Example deterministic filter for the MVP
    if req.constraints.max_runtime:
        base = [m for m in base if m.runtime <= req.constraints.max_runtime]

    return base
