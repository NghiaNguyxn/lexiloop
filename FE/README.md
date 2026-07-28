# LexiLoop Web

The production frontend for LexiLoop, built as a React + TypeScript SPA.

## Local development

```bash
npm install
cp .env.example .env.local
npm run dev
```

The FastAPI backend defaults to `http://localhost:8000`. Open the frontend at
`http://localhost:5173` so the HttpOnly refresh cookie remains same-site in
local development.

## Quality checks

```bash
npm run lint
npm run test
npm run build
```

## Architecture

- React Router owns page navigation.
- TanStack Query owns server state.
- React Hook Form and Zod own form state and request validation.
- The access token stays in memory; the refresh token remains in the
  backend-managed HttpOnly cookie.
- Shared visual tokens live in `src/styles/globals.css` and mirror the Phase 1
  design system under `design-system/lexiloop`.
