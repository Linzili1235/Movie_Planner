import { z } from "zod";

const Schema = z.object({
  mood: z.string().min(1),
  constraints: z
    .object({
      max_runtime: z.number().int().positive().optional(),
      min_year: z.number().int().optional(),
      genres: z.array(z.string()).default([]),
    })
    .default({ genres: [] }),
});

export async function POST(req: Request) {
  // Validate input at the BFF layer to keep the backend contract clean and stable.
  const body = await req.json();
  const parsed = Schema.safeParse(body);

  if (!parsed.success) {
    return Response.json(
      { error: "Invalid request", detail: parsed.error.flatten() },
      { status: 400 }
    );
  }

  // Use the internal service URL in Docker, fall back to localhost for local dev.
  const apiBase = process.env.API_BASE_URL ?? "http://movieplanner-api:8000";

  const resp = await fetch(`${apiBase}/v1/recommendations/query`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(parsed.data),
    cache: "no-store",
  });

  if (!resp.ok) {
    return Response.json({ error: "Backend request failed" }, { status: 502 });
  }

  return Response.json(await resp.json());
}
