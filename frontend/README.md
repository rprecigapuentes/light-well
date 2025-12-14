This is a [Next.js](https://nextjs.org) project bootstrapped with [`create-next-app`](https://nextjs.org/docs/app/api-reference/cli/create-next-app).

## Getting Started

First, run the development server:

```bash
npm run dev
# or
yarn dev
# or
pnpm dev
# or
bun dev
```

Open [http://localhost:3000](http://localhost:3000) with your browser to see the result.

You can start editing the page by modifying `app/page.tsx`. The page auto-updates as you edit the file.

This project uses [`next/font`](https://nextjs.org/docs/app/building-your-application/optimizing/fonts) to automatically optimize and load [Geist](https://vercel.com/font), a new font family for Vercel.

## Learn More

To learn more about Next.js, take a look at the following resources:

- [Next.js Documentation](https://nextjs.org/docs) - learn about Next.js features and API.
- [Learn Next.js](https://nextjs.org/learn) - an interactive Next.js tutorial.

You can check out [the Next.js GitHub repository](https://github.com/vercel/next.js) - your feedback and contributions are welcome!

## Deploy on Vercel

The easiest way to deploy your Next.js app is to use the [Vercel Platform](https://vercel.com/new?utm_medium=default-template&filter=next.js&utm_source=create-next-app&utm_campaign=create-next-app-readme) from the creators of Next.js.

Check out our [Next.js deployment documentation](https://nextjs.org/docs/app/building-your-application/deploying) for more details.

## Step 0 — Frontend initialization (Next.js + TypeScript)

**Objective:** create and run locally the base frontend of the project using Next.js with TypeScript, without additional libraries or styling frameworks.

### Environment
- Node.js >= 20.9.0
- npm (included with Node.js)

### Project creation
The frontend is created inside the `frontend/` folder using the official Next.js generator.

Selected configuration:
- TypeScript: enabled
- App Router: enabled
- `src/` directory: enabled
- Tailwind CSS: disabled
- React Compiler: disabled

### Local execution
The development server is started with:
```

npm run dev

```

By default, the application is available at:
```

[http://localhost:3000](http://localhost:3000)

```

### Generated base structure
```

frontend/
├─ src/
│  └─ app/
│     ├─ layout.tsx
│     └─ page.tsx
├─ public/
├─ package.json
├─ next.config.ts
└─ tsconfig.json

```

This step leaves a minimal, functional frontend environment ready for development.

## Step 1 — Define backend contract (single-day mode)

**Operation mode:**  
The frontend operates in *single-day per request* mode. The user selects a calendar date, which is converted into a start/end datetime range for that day in the Bogotá timezone. All API calls are made using this daily range.

**Backend endpoints used:**
- `GET /data` — retrieve metrics for the selected day
- `GET /insight` — generate an LLM insight for the selected day
- `GET /ask` — answer a user question for the selected day

**Required query parameters:**
- `start` (ISO 8601 datetime)
- `end` (ISO 8601 datetime)
- `question` (string, only for `/ask`)

**Minimum data to display:**
- **Global metrics (day-wide):**
  - `features_global`
  - `l04_global`
- **By-day metrics:**
  - `features_by_day[date]`
  - `l04_by_day[date]`
- **Text outputs:**
  - LLM insight (`/insight`)
  - LLM answer to user question (`/ask`)

If no data is available for the selected day (`count == 0`), the UI displays a “no data” state and disables insight and question features.

## Step 2 — Bogotá day-range utilities

**Objective:** standardize how a calendar date is converted into a backend-ready time range.

A utility function was implemented in `src/lib/time` to:
- Accept a date in `YYYY-MM-DD` format.
- Convert it into the start and end of that day in the Bogotá timezone.
- Return ISO 8601 timestamps with an explicit UTC-05:00 offset.

**Result:**  
All frontend API requests use a consistent `{ startISO, endISO }` range, ensuring correct daily queries and avoiding timezone-related errors.

## Step 3–4 — API client integration and CORS configuration

**Objective:** connect the frontend to the backend API and enable browser access.

### Frontend API client
A centralized API client was implemented in `src/lib/api` to:
- Call backend endpoints (`/data`, `/insight`, `/ask`) for a single-day range.
- Use `NEXT_PUBLIC_API_BASE` as the only external dependency.
- Handle network and HTTP errors consistently.
- Prevent direct `fetch` usage inside UI components.

### Backend CORS configuration
CORS was enabled in the FastAPI application to allow requests from the frontend origin during local development.

- Browser requests originate from `http://localhost:3000`.
- The backend runs on `http://127.0.0.1:8000`.
- FastAPI was configured with `CORSMiddleware` to explicitly allow this cross-origin access.

### Result
The frontend can successfully request daily data from the backend, receive responses in the browser, and display validated results (e.g. row count), confirming end-to-end connectivity.

## Step 5 — UI orchestration and LLM normalization

**Objective:** connect UI components, time utilities, and API client into a working daily view, while keeping components stateless and simple.

### Page orchestration
The main page (`src/app/page.tsx`) acts as the orchestrator:
- Manages the selected date.
- Converts the date into a Bogotá day range using `lib/time`.
- Fetches daily data via `lib/api`.
- Coordinates loading, error, and empty-data states.
- Passes prepared data to presentational components.

### LLM response normalization
Backend LLM responses (`/insight`, `/ask`) may return structured objects rather than plain text.  
A single normalization helper is used at the page level to:
- Convert LLM outputs into displayable strings.
- Handle multiple response shapes (summary, recommendations, answer, notes).
- Ensure UI components only receive render-safe types.

### UI components usage
- **DaySelector:** controls date selection.
- **Card:** groups and displays content blocks.
- **InsightBox:** renders the normalized daily insight text.
- **AskBox:** handles user questions and displays normalized answers.

### Result
- End-to-end daily workflow is functional.
- Frontend successfully displays metrics, compliance analysis, insights, and Q&A.
- Components remain “dumb” and reusable.
- All business logic and data shaping live in the page layer.

This completes a fully integrated, single-day frontend view connected to the backend API.

## Step 6 — Fix LLM rendering after strict typing

**Problem**  
After typing the frontend strictly, the LLM outputs stopped rendering. The backend was already returning **JSON objects**, but the frontend assumed the `llm` field was a plain string, causing the UI to show “No insight available” and breaking the Ask flow.

**Root cause**  
`llm` is returned as structured JSON (e.g. `{ summary, recommendations }` or `{ answer, notes }`), not as a string.

**Solution**  
1. Update the frontend types so `llm` accepts structured JSON:
   - Define `LLMOutput` as `string | object`.
2. Restore a normalization helper (`llmToText`) that:
   - Extracts `summary`, `recommendations`, `answer`, and `notes` when present.
   - Falls back to `JSON.stringify` for unknown shapes.
3. Use this helper consistently for both **Insight** and **Ask** responses.
4. Keep the daily metrics and L04 typing unchanged.

**Result**  
The frontend renders LLM insights and answers correctly again, with strict TypeScript typing and no runtime validation or extra libraries.

## Step 7 — UI Design Update (Light Theme + Visual Consistency)

### Goal
Replace the dark background / white-card clash with a clean light palette and consistent component styling across the page.

### What changed
- Introduced a **light theme palette** using CSS variables (`:root`) for:
  - background/surfaces, borders, text colors
  - primary (blue) accents
  - status colors (success/danger) and notes (warning)
  - shared shadows

### Main layout
- Set `.main` to a **light background** (`--bg`) with full-height (`min-height: 100vh`) and standard readable text color.

### Inputs (date picker + ask textarea)
- Unified input styling (`.dateInput`, `.askInput`) to avoid “black box” fields:
  - light background, consistent border radius, subtle shadow
  - proper focus ring using `--primary-border` and a soft blue glow

### Cards and sections
- Updated `.statCard` and `.tierBox` to match the palette:
  - white surface, soft border, consistent shadows
  - hover elevation for tier cards (subtle lift + stronger shadow)

### Buttons
- Improved `.askButton` for a cohesive primary action:
  - primary blue background, hover state, disabled state
  - slight hover lift for better affordance

### Text blocks (LLM output)
- Styled `.answerArea` to look intentional:
  - light blue surface (`--primary-soft`)
  - left accent border and matching border color
  - preserves formatting via `white-space: pre-wrap`

### Result
A consistent **light UI** with coherent colors, readable contrast, and matching input/button/card styles (no dark mode).
