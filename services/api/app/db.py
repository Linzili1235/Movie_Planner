import os
from typing import Any, Optional

import psycopg


def get_database_url() -> str:
    url = os.getenv("DATABASE_URL")
    if not url:
        raise RuntimeError("DATABASE_URL is not set")
    return url


def search_movies(
    mood: str,
    max_runtime: Optional[int],
    min_year: Optional[int],
    genres: list[str],
    limit: int = 10,
) -> list[dict[str, Any]]:
    """
    Baseline retrieval:
    - Full-text search over title + plot (English)
    - Filters: runtime, release_year, and (optional) genres in the JSONB map values
    """
    base_filters = ["search_tsv @@ websearch_to_tsquery('english', %(q)s)"]
    params: dict[str, Any] = {"q": mood, "limit": limit}

    if max_runtime is not None:
        base_filters.append("runtime_minutes <= %(max_runtime)s")
        params["max_runtime"] = max_runtime

    if min_year is not None:
        base_filters.append("release_year >= %(min_year)s")
        params["min_year"] = min_year

    if genres:
        base_filters.append(
            """
            EXISTS (
              SELECT 1
              FROM jsonb_each_text(movies.genres) AS g
              WHERE g.value = ANY(%(genres)s)
            )
            """
        )
        params["genres"] = genres

    where_clause = " AND ".join(base_filters)

    sql = f"""
    SELECT
      wiki_movie_id,
      title,
      release_year,
      runtime_minutes,
      (
        SELECT array_agg(DISTINCT g.value)
        FROM jsonb_each_text(movies.genres) AS g
      ) AS genre_names,
      plot,
      ts_rank_cd(search_tsv, websearch_to_tsquery('english', %(q)s)) AS rank
    FROM movies
    WHERE {where_clause}
    ORDER BY rank DESC
    LIMIT %(limit)s;
    """

    with psycopg.connect(get_database_url()) as conn:
        with conn.cursor() as cur:
            cur.execute(sql, params)
            rows = cur.fetchall()

    out = []
    for wiki_id, title, year, runtime, genre_names, plot, rank in rows:
        out.append(
            {
                "wiki_movie_id": wiki_id,
                "title": title,
                "year": year,
                "runtime": int(runtime) if runtime is not None else None,
                "genres": genre_names or [],
                "plot": plot,
                "rank": float(rank) if rank is not None else 0.0,
            }
        )
    return out
