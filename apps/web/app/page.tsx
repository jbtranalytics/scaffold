import { Button } from "@/components/ui/button";
import { AgUiDemo } from "@/components/ag-ui-demo";
import { ArrowRight, Bot, Cpu, Layers, Sparkles, Terminal } from "lucide-react";

export default function Home() {
  return (
    <div className="flex min-h-screen flex-col items-center justify-center bg-background px-6 py-16 text-foreground">
      <main className="flex w-full max-w-3xl flex-col items-start gap-8 rounded-2xl border border-border/40 bg-card p-10 shadow-sm">
        <div className="flex items-center gap-2 rounded-full border border-border/60 bg-muted/60 px-3 py-1 text-xs font-medium text-muted-foreground">
          <Sparkles className="size-3.5 text-primary" />
          <span>Python 3.14 & Node 26 Monorepo</span>
        </div>

        <div className="flex flex-col gap-3">
          <h1 className="text-4xl font-bold tracking-tight sm:text-5xl">
            Scaffold Workspace
          </h1>
          <p className="max-w-xl text-lg text-muted-foreground">
            FastAPI backend, Next.js 16 frontend with Tailwind CSS v4, shadcn UI, Lucide icons, React Markdown, and AG-UI protocol integration.
          </p>
        </div>

        <div className="grid w-full grid-cols-1 gap-4 sm:grid-cols-3">
          <div className="flex flex-col gap-2 rounded-xl border border-border/40 p-4 bg-background/50">
            <div className="flex items-center gap-2 font-medium">
              <Cpu className="size-4 text-primary" />
              <span>Python 3.14 API</span>
            </div>
            <p className="text-sm text-muted-foreground">
              FastAPI service with RPC contract protocols and uv dependency resolution.
            </p>
          </div>

          <div className="flex flex-col gap-2 rounded-xl border border-border/40 p-4 bg-background/50">
            <div className="flex items-center gap-2 font-medium">
              <Layers className="size-4 text-primary" />
              <span>Next.js 16 + shadcn</span>
            </div>
            <p className="text-sm text-muted-foreground">
              Tailwind CSS v4 with Base UI primitives and Lucide icons.
            </p>
          </div>

          <div className="flex flex-col gap-2 rounded-xl border border-border/40 p-4 bg-background/50">
            <div className="flex items-center gap-2 font-medium">
              <Bot className="size-4 text-primary" />
              <span>AG-UI + Markdown</span>
            </div>
            <p className="text-sm text-muted-foreground">
              Agent-User Interaction protocol and React Markdown with GFM.
            </p>
          </div>
        </div>

        <AgUiDemo />

        <div className="flex flex-wrap items-center gap-3 pt-2">
          <Button className="gap-2">
            Get Started
            <ArrowRight className="size-4" />
          </Button>
          <Button variant="outline" className="gap-2">
            <Terminal className="size-4" />
            just web-dev
          </Button>
        </div>
      </main>
    </div>
  );
}
