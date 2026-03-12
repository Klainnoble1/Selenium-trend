import { promises as fs } from "node:fs";
import path from "node:path";
import { Pool } from "pg";

export type BlogPost = {
  id: string;
  title: string;
  slug: string;
  content: string;
  tags: string[];
  published: boolean;
  createdAt: string;
};

const postsFilePath = path.join(process.cwd(), "blog-posts.json");
const trendsFilePath = path.join(process.cwd(), "selenium-trends.json");
const tableName = "blog_posts";

declare global {
  var __bayBlogPool: Pool | undefined;
  var __bayBlogTableReady: Promise<void> | undefined;
}

async function ensureFile<T>(filePath: string, fallbackData: T): Promise<void> {
  try {
    await fs.access(filePath);
  } catch {
    await fs.writeFile(filePath, JSON.stringify(fallbackData, null, 2), "utf8");
  }
}

async function readJsonFile<T>(filePath: string, fallbackData: T): Promise<T> {
  await ensureFile(filePath, fallbackData);
  const raw = await fs.readFile(filePath, "utf8");
  try {
    return JSON.parse(raw) as T;
  } catch {
    return fallbackData;
  }
}

export async function getPosts(): Promise<BlogPost[]> {
  if (shouldUseDatabase()) {
    try {
      const pool = getPool();
      await ensureTable(pool);
      const result = await pool.query<{
        id: string;
        title: string;
        slug: string;
        content: string;
        tags: string[] | null;
        published: boolean;
        created_at: Date | string;
      }>(
        `SELECT id, title, slug, content, tags, published, created_at
         FROM ${tableName}
         ORDER BY created_at DESC`,
      );

      return result.rows.map((row) => ({
        id: row.id,
        title: row.title,
        slug: row.slug,
        content: row.content,
        tags: row.tags ?? [],
        published: row.published,
        createdAt: new Date(row.created_at).toISOString(),
      }));
    } catch (error) {
      console.error("Database connection failed, falling back to local storage:", error);
      // Fallback to local file storage if database fails
    }
  }

  const posts = await readJsonFile<BlogPost[]>(postsFilePath, []);
  return posts.sort((a, b) => (a.createdAt < b.createdAt ? 1 : -1));
}

export async function savePosts(posts: BlogPost[]): Promise<void> {
  await fs.writeFile(postsFilePath, JSON.stringify(posts, null, 2), "utf8");
}

export async function addPost(
  post: Omit<BlogPost, "id" | "createdAt" | "slug"> & { slug?: string },
): Promise<BlogPost> {
  if (shouldUseDatabase()) {
    const pool = getPool();
    await ensureTable(pool);

    const slugBase = slugify(post.slug?.trim() || post.title);
    const existingSlugsResult = await pool.query<{ slug: string }>(
      `SELECT slug FROM ${tableName} WHERE slug = $1 OR slug LIKE $2`,
      [slugBase, `${slugBase}-%`],
    );
    const slug = uniqueSlug(
      slugBase,
      existingSlugsResult.rows.map((entry) => entry.slug),
    );

    const newPost: BlogPost = {
      id: crypto.randomUUID(),
      title: post.title,
      slug,
      content: post.content,
      tags: post.tags,
      published: post.published,
      createdAt: new Date().toISOString(),
    };

    await pool.query(
      `INSERT INTO ${tableName} (id, title, slug, content, tags, published, created_at)
       VALUES ($1, $2, $3, $4, $5, $6, $7)`,
      [
        newPost.id,
        newPost.title,
        newPost.slug,
        newPost.content,
        newPost.tags,
        newPost.published,
        newPost.createdAt,
      ],
    );

    return newPost;
  }

  const posts = await getPosts();
  const slugBase = slugify(post.slug?.trim() || post.title);
  const slug = uniqueSlug(slugBase, posts.map((entry) => entry.slug));

  const newPost: BlogPost = {
    id: crypto.randomUUID(),
    title: post.title,
    slug,
    content: post.content,
    tags: post.tags,
    published: post.published,
    createdAt: new Date().toISOString(),
  };

  await savePosts([newPost, ...posts]);
  return newPost;
}

export function slugify(value: string): string {
  return value
    .toLowerCase()
    .trim()
    .replace(/[^\w\s-]/g, "")
    .replace(/\s+/g, "-")
    .replace(/-+/g, "-");
}

function uniqueSlug(base: string, existingSlugs: string[]): string {
  if (!existingSlugs.includes(base)) return base;

  let counter = 2;
  while (existingSlugs.includes(`${base}-${counter}`)) {
    counter += 1;
  }
  return `${base}-${counter}`;
}

export async function getSeleniumTrends(): Promise<string[]> {
  return readJsonFile<string[]>(trendsFilePath, [
    "Selenium 4 BiDi automation",
    "Cross-browser CI pipelines",
    "Web scraping ethics",
    "Flaky test stabilization",
    "Headless observability",
  ]);
}

function shouldUseDatabase(): boolean {
  return Boolean(process.env.DATABASE_URL);
}

function getPool(): Pool {
  if (!process.env.DATABASE_URL) {
    throw new Error("DATABASE_URL is required for database mode.");
  }

  if (!global.__bayBlogPool) {
    global.__bayBlogPool = new Pool({
      connectionString: process.env.DATABASE_URL,
      ssl: {
        rejectUnauthorized: false,
      },
    });
  }

  return global.__bayBlogPool;
}

async function ensureTable(pool: Pool): Promise<void> {
  if (!global.__bayBlogTableReady) {
    global.__bayBlogTableReady = pool
      .query(
        `CREATE TABLE IF NOT EXISTS ${tableName} (
          id TEXT PRIMARY KEY,
          title TEXT NOT NULL,
          slug TEXT NOT NULL UNIQUE,
          content TEXT NOT NULL,
          tags TEXT[] NOT NULL DEFAULT '{}',
          published BOOLEAN NOT NULL DEFAULT true,
          created_at TIMESTAMPTZ NOT NULL DEFAULT now()
        );`,
      )
      .then(() => undefined);
  }

  await global.__bayBlogTableReady;
}
