import { NextResponse } from "next/server";
import { addPost, getPosts, slugify } from "@/lib/blog-store";

type IncomingPayload = {
  title?: unknown;
  slug?: unknown;
  content?: unknown;
  tags?: unknown;
  published?: unknown;
};

const DEFAULT_TOKEN = "786273jiahgsdiuhjsda8721y378213nbsadjhgsdajhgsajdg982738972931";

function normalizeTags(rawTags: unknown): string[] {
  if (Array.isArray(rawTags)) {
    return rawTags.map((tag) => String(tag).trim()).filter(Boolean);
  }

  if (typeof rawTags === "string") {
    const normalized = rawTags.trim();
    if (!normalized) return [];

    // Supports either comma-separated tags or JSON array strings.
    if (normalized.startsWith("[") && normalized.endsWith("]")) {
      try {
        const parsed = JSON.parse(normalized) as unknown;
        if (Array.isArray(parsed)) {
          return parsed.map((tag) => String(tag).trim()).filter(Boolean);
        }
      } catch {
        // Falls through to comma-split.
      }
    }

    return normalized
      .split(",")
      .map((tag) => tag.trim())
      .filter(Boolean);
  }

  return [];
}

function toBoolean(value: unknown, fallback = true): boolean {
  if (typeof value === "boolean") return value;
  if (typeof value === "string") {
    if (value.toLowerCase() === "true") return true;
    if (value.toLowerCase() === "false") return false;
  }
  return fallback;
}

export async function POST(request: Request) {
  const authHeader = request.headers.get("authorization") ?? "";
  const acceptHeader = request.headers.get("accept") ?? "";
  const expectedToken = process.env.BLOG_API_TOKEN || DEFAULT_TOKEN;
  const expectedHeader = `Bearer ${expectedToken}`;

  // Log incoming request for debugging
  console.log(`[API] POST /api/blog/create | Accept: ${acceptHeader}`);

  if (authHeader !== expectedHeader) {
    console.error("[API] Unauthorized access attempt.");
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  }

  let body: any;
  try {
    body = await request.json();
  } catch (err) {
    console.error("[API] Failed to parse JSON body:", err);
    return NextResponse.json(
      { error: "Invalid JSON body. Ensure Content-Type is application/json." },
      { status: 400 },
    );
  }

  // Support both single object and array of objects (common in n8n)
  const payload: IncomingPayload = Array.isArray(body) ? body[0] : body;

  if (!payload) {
    return NextResponse.json({ error: "Empty payload received." }, { status: 400 });
  }

  // Robustly extract title and content, supporting common n8n field names
  const title = String(payload.title || "").trim();
  
  // Support 'content', 'blog_content' (from n8n template), or 'body'
  const rawContent = (payload.content || (payload as any).blog_content || (payload as any).body || "");
  const content = String(rawContent).trim();

  if (!title || !content) {
    const missing = [];
    if (!title) missing.push("title");
    if (!content) missing.push("content");
    
    console.warn(`[API] Missing required fields: ${missing.join(", ")}`);
    return NextResponse.json(
      { 
        error: `Missing required fields: ${missing.join(", ")}`,
        receivedFields: Object.keys(payload),
        tip: "Ensure your n8n node is sending 'title' and 'content' (or 'blog_content')."
      }, 
      { status: 400 }
    );
  }

  try {
    const slugCandidate = String(payload.slug || "").trim();
    const post = await addPost({
      title,
      slug: slugify(slugCandidate || title),
      content,
      tags: normalizeTags(payload.tags),
      published: toBoolean(payload.published, true),
    });

    console.log(`[API] Successfully published: ${title}`);
    return NextResponse.json(
      {
        ok: true,
        post,
        note: "Published successfully.",
      },
      { status: 201 },
    );
  } catch (error) {
    console.error("[API] Error adding post:", error);
    return NextResponse.json(
      { error: "Internal server error while saving the post." },
      { status: 500 }
    );
  }
}

export async function GET() {
  const posts = await getPosts();
  return NextResponse.json({ posts }, { status: 200 });
}
