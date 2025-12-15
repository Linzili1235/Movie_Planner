from fastapi import FastAPI
from pydantic import BaseModel, Field
from typing import List, Optional

from app.db import search_movies

app = FastAPI(title="CineMatch API", version="0.1.0")


class Constraints(BaseModel):
    max_runtime: Optional[int] = None
    min_year: Optional[int] = None
    genres: List[str] = Field(default_factory=list)


class RecommendRequest(BaseModel):
    mood: str
    constraints: Constraints = Field(default_factory=Constraints)


class Movie(BaseModel):
    title: str
    year: Optional[int] = None
    genres: List[str]
    runtime: Optional[int] = None
    plot: Optional[str] = None
    explanation: str


@app.get("/health")
def health():
    return {"ok": True}


@app.post("/v1/recommendations/query", response_model=list[Movie])
def recommend(req: RecommendRequest):
    rows = search_movies(
        mood=req.mood,
        max_runtime=req.constraints.max_runtime,
        min_year=req.constraints.min_year,
        genres=req.constraints.genres,
        limit=10,
    )

    return [
        Movie(
            title=r["title"] or "Unknown",
            year=r.get("year"),
            genres=r.get("genres") or [],
            runtime=r.get("runtime"),
            plot=r.get("plot"),
            explanation="Matched your mood using plot-based text search and applied your filters.",
        )
        for r in rows
    ]
