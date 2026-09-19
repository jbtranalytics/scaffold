---
name: web-packages
description: Reference guide and architectural breakdown of frontend dependencies in apps/web.
---

# Frontend Package Catalog (`apps/web`)

This document serves as a reference guide for all dependencies in [`apps/web/package.json`](file:///home/josht/src/scaffold/apps/web/package.json).

Because `apps/web` is configured as a client-side Single Page Application (SPA) designed to compile to a static export (`output: 'export'`) and be hosted directly by the FastAPI backend, all dependencies operate cleanly in browser runtime environments.

---

## 1. AI, Chat & Agentic UI Components

| Package | Version | Purpose & Usage |
| :--- | :--- | :--- |
| **`@assistant-ui/react`** | `^0.15.21` | **Headless AI Chat Primitives**. Provides accessible React components for building chat interfaces (threads, message lists, user composer input, thread history, branch switching, and tool rendering). |
| **`@assistant-ui/react-ag-ui`** | `^0.0.60` | **Assistant UI + AG-UI Adapter**. Bridges assistant-ui runtime primitives to the Antigravity UI protocol stream. |
| **`@assistant-ui/react-markdown`** | `^0.14.16` | **Markdown Chat Renderer**. Specialized markdown parsing layer for `assistant-ui` that supports streaming tokens, syntax highlighting, and custom message components. |
| **`@ag-ui/client`** | `^1.0.0` | **AG-UI Frontend Transport Client**. Handles client-side bidirectional communication, token streaming, and tool call lifecycle events over HTTP/WebSocket. |
| **`@ag-ui/core`** | `^1.0.0` | **AG-UI Protocol Types & Core**. Formal wire schemas, interfaces, and serializers defining agentic UI message events and tool invocations. |

---

## 2. Markdown, Syntax Highlighting & Rich Content

| Package | Version | Purpose & Usage |
| :--- | :--- | :--- |
| **`react-markdown`** | `^10.1.0` | **React Markdown Component**. Converts raw Markdown strings from the LLM into native React DOM elements safely without `dangerouslySetInnerHTML`. |
| **`remark-gfm`** | `^4.0.1` | **GitHub Flavored Markdown Plugin**. Adds support for tables, task checklists, strikethrough, autolinks, and footnotes to `react-markdown`. |
| **`react-syntax-highlighter`** | `^15.6.6` | **React Code Highlighting Component**. Plugs directly into `react-markdown` code blocks to render syntax-highlighted Python, TypeScript, SQL, JSON, etc., with copy-to-clipboard support. |

---

## 3. UI Primitives, Styling & Micro-Interactions

| Package | Version | Purpose & Usage |
| :--- | :--- | :--- |
| **`@base-ui/react`** | `^1.8.0` | **Unstyled Accessible Primitives (MUI Base UI)**. Headless, accessible foundation components (dialogs, dropdowns, popovers, tooltips) that power UI design without prescribing CSS. |
| **`shadcn`** | `^4.21.0` | **Component Scaffolder & Registry CLI**. CLI tool used to add customizable accessible components (buttons, cards, inputs) into `apps/web/components/ui`. |
| **`lucide-react`** | `^1.47.0` | **Iconography System**. Clean, consistent SVG icon library for buttons, navigation tabs, chat actions (copy, thumbs up/down, retry), and status indicators. |
| **`react-textarea-autosize`** | `^8.5.9` | **Auto-Resizing Textarea Component**. Gold standard for chat composer inputs. Automatically grows and shrinks with user input without awkward scrollbars or layout shifts. |
| **`motion`** | `^12.38.1` | **React Animation Library**. Modern successor to Framer Motion with first-class React 19 support. Handles smooth chat bubbles, accordion reasoning toggles, and streaming text transitions. |
| **`sonner`** | `^2.0.7` | **React Toast Notification System**. Opinionated, beautiful toast notifications for user alerts ("Copied to clipboard", "Connection error", etc.). |
| **`class-variance-authority`** | `^0.7.1` | **Type-Safe Component Variants (`cva`)**. Enables defining style variants (e.g. `variant: "outline" | "ghost"`, `size: "sm" | "lg"`) with TypeScript autocomplete. |
| **`cn`** | `^0.3.0` | **Fast Classname Merging**. Compiled drop-in replacement for `clsx` + `tailwind-merge` used by shadcn. |
| **`clsx`** | `^2.1.1` | **Classname Utility**. Lightweight utility for conditionally constructing `className` strings. |
| **`tailwind-merge`** | `^3.7.0` | **Tailwind Conflict Resolver**. Merges conflicting Tailwind CSS utility classes without style collision. |
| **`tw-animate-css`** | `^1.4.0` | **Tailwind Animation Utilities**. Preconfigured CSS animation classes for smooth entry/exit, fades, and pulse effects. |
| **`tw-shimmer`** | `^0.4.13` | **Skeleton Shimmer Effects**. Adds glowing shimmer utility classes to render skeleton loading states while awaiting LLM responses. |

---

## 4. State Management & Architecture

| Package | Version | Purpose & Usage |
| :--- | :--- | :--- |
| **`zustand`** | `^5.0.15` | **Client-Side Reactive Store**. Lightweight, unopinionated state management without boilerplate. Used to manage active chat session IDs, sidebar toggle state, model selection, temperature settings, and global UI state. |

---

## 5. Core Framework & Runtime

| Package | Version | Purpose & Usage |
| :--- | :--- | :--- |
| **`next`** | `16.3.5` | **React Application Framework**. Compiles down to static HTML/JS/CSS assets (`output: 'export'`) served directly by FastAPI. |
| **`react`** | `19.2.8` | **Core UI Library**. Modern React 19 foundation providing hooks, concurrent rendering, and server/client component composition. |
| **`react-dom`** | `19.2.8` | **DOM Renderer for React**. Handles mounting and reconciliation of the React virtual DOM tree into the browser. |

---

## 6. Developer Tooling & Build Dependencies (`devDependencies`)

| Package | Version | Purpose & Usage |
| :--- | :--- | :--- |
| **`tailwindcss`** | `^4` | **Utility-First CSS Framework (v4)**. Modern, lightning-fast styling engine built on standard CSS variables without JavaScript config overhead. |
| **`@tailwindcss/postcss`** | `^4` | **PostCSS Tailwind Integration**. PostCSS plugin that allows Next.js to process and compile Tailwind CSS v4 syntax. |
| **`typescript`** | `^5` | **TypeScript Compiler & Language Engine**. Enforces strict static type checking across components, hooks, and API contracts. |
| **`@types/node`** | `^20` | **Node.js Type Definitions**. Provides TypeScript definitions for Node APIs used during development and build time. |
| **`@types/react`** | `^19` | **React Type Definitions**. Provides TypeScript types for React components, hooks, JSX elements, and synthetic events. |
| **`@types/react-dom`** | `^19` | **React DOM Type Definitions**. TypeScript types for browser DOM rendering APIs. |
| **`@types/react-syntax-highlighter`** | `^15.5.13` | **Syntax Highlighter Type Definitions**. TypeScript typings for `react-syntax-highlighter`. |
| **`eslint`** | `^9` | **JavaScript/TypeScript Linter**. Enforces code style, catches syntax errors, and prevents code smells. |
| **`eslint-config-next`** | `16.3.5` | **Next.js ESLint Configuration**. Official ESLint rules optimized for Next.js and React best practices. |
