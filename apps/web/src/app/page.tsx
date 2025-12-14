"use client";

import { useState } from "react";

type Movie = {
  title: string;
  year: number;
  genres: string[];
  runtime: number;
  explanation: string;
};

export default function Page() {
  const [mood, setMood] = useState("lighthearted comedy for a group");
  const [maxRuntime, setMaxRuntime] = useState<number | "">(110);
  const [movies, setMovies] = useState<Movie[]>([]);
  const [err, setErr] = useState("");

  async function onSubmit() {
    setErr("");

    const resp = await fetch("/api/recommendations", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        mood,
        constraints: {
          max_runtime: maxRuntime === "" ? undefined : Number(maxRuntime),
          genres: [],
        },
      }),
    });

    if (!resp.ok) {
      setErr("Request failed.");
      return;
    }

    setMovies(await resp.json());
  }

  return (
    <main style={{ maxWidth: 800, margin: "40px auto", padding: 16 }}>
      <h1>CineMatch AI (Local MVP)</h1>

      <div style={{ display: "flex", gap: 12, marginTop: 16 }}>
        <input
          value={mood}
          onChange={(e) => setMood(e.target.value)}
          placeholder='Mood (e.g., "cozy, low-stress, feel-good")'
          style={{ flex: 1, padding: 10 }}
        />
        <input
          value={maxRuntime}
          onChange={(e) =>
            setMaxRuntime(e.target.value === "" ? "" : Number(e.target.value))
          }
          placeholder="Max minutes"
          style={{ width: 160, padding: 10 }}
        />
        <button onClick={onSubmit} style={{ padding: "10px 14px" }}>
          Recommend
        </button>
      </div>

      {err && <p style={{ color: "red" }}>{err}</p>}

      <ul style={{ marginTop: 20 }}>
        {movies.map((m) => (
          <li key={`${m.title}-${m.year}`} style={{ marginBottom: 14 }}>
            <div>
              <strong>{m.title}</strong> ({m.year}) · {m.runtime} min ·{" "}
              {m.genres.join(", ")}
            </div>
            <div>{m.explanation}</div>
          </li>
        ))}
      </ul>
    </main>
  );
}
