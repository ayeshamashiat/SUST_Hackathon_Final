# Super Agent Console Frontend

Next.js App Router frontend for the SUST hackathon multi-provider liquidity and coordination prototype.

## Setup

```bash
cd frontend
npm install
npm run dev
```

Open `http://localhost:3000`.

By default the app calls the backend at `http://localhost:8000`. Override that with `frontend/.env.local`:

```bash
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
```

## Pages

- `/` shows the unified outlet dashboard: shared cash reserve, bKash/Nagad/Rocket balances, forecast confidence, feed health, and a polling transaction ticker.
- `/alerts` shows advisory alerts and their routed cases, including evidence, confidence notes, owner, next step, history, and allowed case transitions.

## Checks

```bash
npm run build
npm run lint
```

The UI is read-only against simulated data except for advisory case status updates. It does not move money or call any real MFS provider.
