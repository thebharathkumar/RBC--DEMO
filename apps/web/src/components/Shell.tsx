import type { ReactElement } from "react";

/**
 * Application shell. Milestone 1 ships the layout primitives only; the live
 * trace and note views are wired in milestone 7.
 */
export function Shell(): ReactElement {
  return (
    <div className="flex min-h-full flex-col">
      <header className="border-b border-ink-200 bg-white">
        <div className="mx-auto flex max-w-7xl items-center justify-between px-6 py-4">
          <div className="flex items-baseline gap-3">
            <h1 className="font-serif text-2xl tracking-editorial text-ink-900">
              rbc research agent platform
            </h1>
            <span className="font-mono text-xs uppercase tracking-widest text-ink-400">
              v0.1.0
            </span>
          </div>
          <nav className="flex gap-6 text-sm text-ink-600">
            <a href="#runs" className="hover:text-ink-900">
              Runs
            </a>
            <a href="#watchlist" className="hover:text-ink-900">
              Watchlist
            </a>
            <a href="#docs" className="hover:text-ink-900">
              Docs
            </a>
          </nav>
        </div>
      </header>
      <main className="mx-auto w-full max-w-7xl flex-1 px-6 py-10">
        <section className="border border-ink-200 bg-white p-8">
          <p className="font-mono text-xs uppercase tracking-widest text-gold-600">
            Status
          </p>
          <h2 className="mt-2 font-serif text-3xl tracking-editorial text-ink-900">
            Scaffold ready. Agent runtime ships in milestone 3.
          </h2>
          <p className="mt-3 max-w-2xl text-ink-600">
            This deployment is the repository skeleton for the hierarchical
            multi-agent research platform. The supervisor, workers, eval
            harness, and PDF renderer come online in subsequent milestones.
          </p>
        </section>
      </main>
      <footer className="border-t border-ink-200 bg-white">
        <div className="mx-auto max-w-7xl px-6 py-4 text-xs text-ink-500">
          Built by Bharath Kumar Rajesh.
        </div>
      </footer>
    </div>
  );
}
