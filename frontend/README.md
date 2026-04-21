# LightWell — Frontend

Next.js 16 dashboard for the LightWell circadian lighting assessment system. Displays melanopic EDI statistics, WELL v2 L04 compliance results, AI-generated insights, and a Q&A interface for a user-selected day.

## Tech Stack

| | |
|---|---|
| Framework | Next.js 16, React 19 |
| Language | TypeScript 5 |
| Styling | CSS Modules + CSS variables (no UI framework) |
| Backend | FastAPI via REST — see `backend/myapp/README.md` |

## Setup

**Prerequisites:** Node.js >= 20.9.0

```bash
cd frontend
npm install
```

Create a `.env.local` file:

```
NEXT_PUBLIC_API_URL=http://127.0.0.1:8000
```

Start the development server:

```bash
npm run dev
# http://localhost:3000
```

## Environment Variables

| Variable | Description | Default |
|---|---|---|
| `NEXT_PUBLIC_API_URL` | Backend base URL | `http://127.0.0.1:8000` |

## Project Structure

```
src/
├── app/
│   ├── page.tsx           # Main daily view — orchestrates all data fetching and state
│   ├── layout.tsx         # Root layout and page metadata
│   └── page.module.css    # Light theme CSS variables and component styles
├── components/
│   ├── Card.tsx           # Reusable white card container
│   ├── InsightBox.tsx     # Renders LLM-generated daily insight (summary + recommendations)
│   ├── AskBox.tsx         # User Q&A input and answer display
│   └── DaySelector.tsx    # Date picker
└── lib/
    ├── time.ts            # bogotaDayRange() — converts YYYY-MM-DD to UTC ISO range (UTC-5)
    └── api/
        ├── index.ts       # Typed fetch wrappers for /data, /insight, /ask
        └── types.ts       # TypeScript types: TierResult, L04Result, Features, etc.
```

## How It Works

1. The user selects a date via `DaySelector`.
2. `bogotaDayRange()` converts the date to a UTC time range bracketing the full day in Bogotá time (UTC-5).
3. `page.tsx` fetches `/data`, then optionally `/insight` and `/ask`.
4. Fetched data is passed down to stateless presentational components — all data shaping and normalization live in the page layer.

LLM responses from the backend (`/insight`, `/ask`) may be plain strings or structured JSON objects. A normalization helper (`llmToText`) in `page.tsx` converts both shapes into displayable strings before passing them to `InsightBox` and `AskBox`.

## Backend Endpoints Used

| Endpoint | Description |
|---|---|
| `GET /data?start=&end=` | EDI statistics + WELL v2 L04 compliance |
| `GET /insight?start=&end=` | LLM daily summary + 3 recommendations |
| `GET /ask?start=&end=&question=` | LLM answer to a user question |

All timestamps use ISO 8601. The frontend sends UTC timestamps bracketing the selected day in Bogotá time (UTC-5).
