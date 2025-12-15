import argparse
import json
from pathlib import Path

import psycopg


def parse_genres(raw: str):
    """
    CMU genres are often stored as a JSON-like map of FreebaseId -> GenreName.
    Keep it as JSONB in Postgres. If parsing fails, store NULL.
    """
    raw = (raw or "").strip()
    if not raw:
        return None
    try:
        return json.loads(raw)
    except Exception:
        return None


def load_plots(plot_file: Path) -> dict[int, str]:
    plots: dict[int, str] = {}
    with plot_file.open("r", encoding="utf-8", errors="replace") as f:
        for line in f:
            line = line.rstrip("\n")
            if not line:
                continue
            # Format: <wiki_movie_id>\t<plot summary>
            parts = line.split("\t", 1)
            if len(parts) != 2:
                continue
            try:
                wiki_id = int(parts[0])
            except ValueError:
                continue
            plots[wiki_id] = parts[1]
    return plots


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--metadata", required=True, help="Path to movie.metadata.tsv")
    ap.add_argument("--plots", required=True, help="Path to plot_summaries.txt")
    ap.add_argument("--database-url", required=True, help="e.g. postgresql://user:pass@localhost:5432/db")
    ap.add_argument("--limit", type=int, default=0, help="0 = no limit (import all plots)")
    args = ap.parse_args()

    metadata_path = Path(args.metadata)
    plots_path = Path(args.plots)

    plots = load_plots(plots_path)

    with psycopg.connect(args.database_url) as conn:
        with conn.cursor() as cur:
            inserted = 0
            with metadata_path.open("r", encoding="utf-8", errors="replace") as f:
                for line in f:
                    if args.limit and inserted >= args.limit:
                        break

                    cols = line.rstrip("\n").split("\t")
                    # Expected at least 9 columns in metadata
                    if len(cols) < 9:
                        continue

                    try:
                        wiki_id = int(cols[0])
                    except ValueError:
                        continue

                    plot = plots.get(wiki_id)
                    # For RAG, only keep movies that have a plot summary
                    if not plot:
                        continue

                    freebase_id = cols[1] or None
                    title = cols[2] or None
                    release_date = cols[3] or None

                    def to_int(x):
                        x = (x or "").strip()
                        if not x:
                            return None
                        try:
                            return int(float(x))
                        except Exception:
                            return None

                    def to_float(x):
                        x = (x or "").strip()
                        if not x:
                            return None
                        try:
                            return float(x)
                        except Exception:
                            return None

                    revenue = to_int(cols[4])
                    runtime = to_float(cols[5])
                    languages = cols[6] or None
                    countries = cols[7] or None
                    genres = parse_genres(cols[8])

                    cur.execute(
                        """
                        INSERT INTO movies (
                          wiki_movie_id, freebase_movie_id, title, release_date,
                          box_office_revenue, runtime_minutes, languages, countries, genres, plot
                        )
                        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                        ON CONFLICT (wiki_movie_id) DO UPDATE SET
                          freebase_movie_id = EXCLUDED.freebase_movie_id,
                          title = EXCLUDED.title,
                          release_date = EXCLUDED.release_date,
                          box_office_revenue = EXCLUDED.box_office_revenue,
                          runtime_minutes = EXCLUDED.runtime_minutes,
                          languages = EXCLUDED.languages,
                          countries = EXCLUDED.countries,
                          genres = EXCLUDED.genres,
                          plot = EXCLUDED.plot
                        """,
                        (wiki_id, freebase_id, title, release_date, revenue, runtime, languages, countries, json.dumps(genres) if genres else None, plot),
                    )
                    inserted += 1

            conn.commit()
            print(f"Imported {inserted} movies with plots.")


if __name__ == "__main__":
    main()
