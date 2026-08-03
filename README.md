# Chitfund

A digital chit fund (rotating savings and credit association) built for **RLC Hacks 2026** — Open Track.

A chit fund is a group savings mechanism common across South Asia: a fixed group of members
contributes a fixed amount every cycle into a shared pool. Each cycle, exactly one member takes
the pooled payout via a competitive auction — the member willing to accept the *smallest* payout
wins it early, and the difference (the "discount") is split as a dividend among everyone else.
This repeats until every member has been paid out exactly once.

Chitfund digitizes this: pools, simulated contributions, a real bidding auction each cycle, and a
transparent, explainable **trust score** per member so organizers can see who's reliable before the
next cycle opens. Each pool has a **head** (the creator) who approves join requests from members
discovering the pool publicly, alongside the existing invite-code path for direct joins.

## Why a rule-based trust score, not a black-box model

The trust score is `(on-time contributions + 1) / (total contributions + 2) × 100` — Laplace-smoothed
so a member with only one or two contributions doesn't read as a perfect 100. It's deliberately not a
trained ML model: in a product about financial trust between real people, an organizer needs to be able
to explain *why* someone's score is what it is. Explainability was chosen over opacity as a design
decision, not a shortcut — see `backend/app/services/trust_score.py`.

## Stack

- **Backend**: Python, FastAPI, SQLAlchemy, SQLite
- **Frontend**: React, TypeScript, Vite, Tailwind CSS v4, React Router

## Architecture

```
backend/app/
  models.py              SQLAlchemy models: User, Pool, Membership, Cycle, Bid, LedgerEntry, JoinRequest
  security.py            PIN hashing (PBKDF2, salted) for lightweight auth
  services/
    bidding_engine.py     Pure, unit-tested auction resolution logic
    trust_score.py         Trust score formula
  routers/
    auth.py, pools.py, cycles.py

frontend/src/
  pages/                  LoginPage, DashboardPage, PoolDetailPage
  lib/                    api client, auth context, shared types
  components/             Layout, TrustBadge
```

## Running locally

Requires Python 3.11+ and Node 18+.

**Backend** (port 8000):
```bash
cd backend
python -m venv .venv
./.venv/Scripts/activate   # Windows; use `source .venv/bin/activate` on macOS/Linux
pip install -r requirements.txt
python -m uvicorn app.main:app --port 8000
```

**Frontend** (port 5173, proxies `/api` to the backend):
```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:5173, log in with a name + PIN (this is a hackathon demo, not a production auth
system; see "Known simplifications" below), create a pool, and in a second browser tab/profile either
join with the invite code directly, or use "Discover pools" to find it and request to join — the pool's
head (its creator) approves the request from the pool detail page.

## Running backend tests

```bash
cd backend
./.venv/Scripts/python.exe -m pytest -v
```

The bidding engine (`app/services/bidding_engine.py`) is covered by unit tests for: lowest-bid-wins,
tie-breaking by submission order, the no-bids fallback, out-of-range bid rejection, and ineligible
(already-won) members being excluded from a cycle's auction. `app/security.py` (PIN hashing) is
covered separately.

## Known simplifications (hackathon scope, 3-day → single-night build)

- **Auth**: name + PIN, no email/password, identity persisted in `sessionStorage` (scoped per browser
  tab, so you can demo multiple members side by side in one browser without incognito - a tab keeps
  whichever identity logged in on it, unaffected by logins in other tabs). Different people can share
  a display name — the (name, PIN) pair is the real identity, not the name alone. Real chit funds move
  real money, so production would need proper session auth (httpOnly cookies) — out of scope for a
  working-prototype demo.
- **Payments**: fully simulated ledger, no real payment provider integration.
- **Cycle/bid resolution**: manually triggered by any pool member for demo clarity, rather than
  automatic/time-boxed.
- **Head role**: only the original pool creator is head; no transfer-of-headship flow.

## AI tool usage disclosure

This project was built with assistance from Claude Code (Anthropic), using the
[ECC](https://github.com/affaan-m/ecc) agent harness for planning and workflow structure. Claude
generated the majority of the implementation (backend API, bidding engine, trust score logic,
frontend) under direct human direction on architecture, scope, and product decisions throughout a
single-night build session.
