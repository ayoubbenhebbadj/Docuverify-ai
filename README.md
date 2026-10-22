# DocuVerify AI (frontend prototype)
React + TypeScript + Vite + Tailwind. Runs on mock data; no AI processing happens.

    npm install
    npm run dev        # http://localhost:5173
    npm run typecheck && npm run build

## Connecting FastAPI
All data access is in `src/services/api.ts`. Set `VITE_API_URL` (see `.env.example`) and replace each method body with `http<T>('/path')`. `src/services/mock.ts` can then be deleted. The backend owns all LLM-provider calls and credentials; the frontend never holds API keys.

## Structure
src/components (Layout, ui) | src/pages (7 pages) | src/services (api, mock) | src/types.ts | src/hooks.ts
