import { getPosts, getSeleniumTrends } from "@/lib/blog-store";

function previewText(content: string): string {
  const plain = content.replace(/[#*_`>\-\n]/g, " ").replace(/\s+/g, " ").trim();
  return plain.length > 200 ? `${plain.slice(0, 200)}...` : plain;
}

export default async function Home() {
  const [posts, trends] = await Promise.all([getPosts(), getSeleniumTrends()]);
  const publishedPosts = posts.filter((post) => post.published);

  return (
    <div className="min-h-screen bg-background transition-colors duration-300">
      {/* Navigation / Header */}
      <header className="sticky top-0 z-50 w-full border-b border-border glass px-6 py-4">
        <div className="mx-auto flex max-w-5xl items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="h-8 w-8 rounded-lg bg-accent flex items-center justify-center text-accent-foreground font-bold shadow-sm">
              B
            </div>
            <span className="text-xl font-bold tracking-tight">Bay Blog</span>
          </div>
          <nav className="hidden md:flex items-center gap-6 text-sm font-medium text-muted-foreground">
            <a href="#" className="hover:text-foreground transition-colors">Reflections</a>
            <a href="#" className="hover:text-foreground transition-colors">Trends</a>
            <a href="#" className="hover:text-foreground transition-colors">About</a>
          </nav>
          <button className="rounded-full bg-foreground text-background px-4 py-2 text-sm font-medium hover:opacity-90 transition-opacity">
            Subscribe
          </button>
        </div>
      </header>

      <main className="mx-auto max-w-5xl px-6 py-12 md:py-20 flex flex-col gap-16">
        {/* Hero Section */}
        <section className="animate-fade-in">
          <div className="max-w-3xl">
            <h1 className="text-4xl font-extrabold tracking-tight md:text-6xl lg:text-7xl">
              Capturing thoughts, <br /> 
              <span className="text-accent underline decoration-accent/30 decoration-8 underline-offset-4">one byte</span> at a time.
            </h1>
            <p className="mt-6 text-lg text-muted-foreground md:text-xl leading-relaxed">
              A minimalist space for deep dives into automation, development, and the 
              ever-changing landscape of technology. Driven by n8n.
            </p>
            
            <div className="mt-8 flex flex-wrap gap-3">
              <span className="text-xs font-semibold uppercase tracking-widest text-accent mb-1 w-full">Current Trends</span>
              {trends.map((trend) => (
                <span 
                  key={trend} 
                  className="rounded-full bg-muted border border-border px-4 py-1.5 text-sm font-medium transition-transform hover:scale-105"
                >
                  {trend}
                </span>
              ))}
            </div>
          </div>
        </section>

        {/* Blog Posts Section */}
        <section className="animate-fade-in stagger-2">
          <div className="flex items-end justify-between mb-10">
            <div>
              <h2 className="text-2xl font-bold">Latest reflections</h2>
              <div className="h-1 w-12 bg-accent mt-2 rounded-full"></div>
            </div>
            <p className="text-sm text-muted-foreground">{publishedPosts.length} updates</p>
          </div>

          {publishedPosts.length === 0 ? (
            <div className="rounded-3xl border-2 border-dashed border-border p-12 text-center">
              <p className="text-muted-foreground">The ink is still drying. Check back soon for new insights.</p>
              <code className="mt-4 block text-xs opacity-50 text-foreground">PUSH via /api/blog/create</code>
            </div>
          ) : (
            <div className="grid gap-8 md:grid-cols-2 lg:grid-cols-2">
              {publishedPosts.map((post, idx) => (
                <article 
                  key={post.id} 
                  className={`group relative flex flex-col overflow-hidden rounded-3xl border border-border bg-card p-8 shadow-sm transition-all hover:shadow-xl hover:-translate-y-1 animate-fade-in stagger-${(idx % 3) + 1}`}
                >
                  <div className="absolute top-0 right-0 p-4 opacity-0 transition-opacity group-hover:opacity-100">
                    <svg className="h-6 w-6 text-accent" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14 5l7 7m0 0l-7 7m7-7H3" />
                    </svg>
                  </div>
                  
                  <time className="text-xs font-medium text-accent uppercase tracking-wider">
                    {new Date(post.createdAt).toLocaleDateString(undefined, { month: 'long', day: 'numeric', year: 'numeric' })}
                  </time>
                  
                  <h3 className="mt-4 text-2xl font-bold leading-tight group-hover:text-accent transition-colors">
                    {post.title}
                  </h3>
                  
                  <p className="mt-4 flex-grow text-muted-foreground line-clamp-3 leading-relaxed">
                    {previewText(post.content)}
                  </p>
                  
                  <div className="mt-8 flex flex-wrap gap-2">
                    {post.tags.map((tag) => (
                      <span 
                        key={`${post.id}-${tag}`} 
                        className="rounded-lg bg-muted px-3 py-1 text-xs font-semibold text-foreground"
                      >
                        #{tag}
                      </span>
                    ))}
                  </div>
                </article>
              ))}
            </div>
          )}
        </section>
      </main>

      {/* Dynamic Footer */}
      <footer className="mt-20 border-t border-border bg-muted/30 px-6 py-12">
        <div className="mx-auto max-w-5xl flex flex-col md:flex-row justify-between items-center gap-8">
          <div className="flex items-center gap-2">
            <div className="h-6 w-6 rounded bg-foreground flex items-center justify-center text-background text-[10px] font-bold">
              B
            </div>
            <span className="font-bold tracking-tight">Bay Blog</span>
          </div>
          <p className="text-sm text-muted-foreground">
            © {new Date().getFullYear()} Bay Blog. Powered by Next.js & n8n.
          </p>
          <div className="flex gap-6">
            <a href="#" className="text-muted-foreground hover:text-foreground transition-colors">Twitter</a>
            <a href="#" className="text-muted-foreground hover:text-foreground transition-colors">GitHub</a>
          </div>
        </div>
      </footer>
    </div>
  );
}
