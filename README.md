How a chit fund works
     
  A chit fund is a rotating savings and credit association (ROSCA) — a traditional group savings and lending system, especially common in India,
  where a fixed group of people pool money together on a regular schedule, and one member gets access to a lump sum each cycle.

  The basic mechanics

  1. Form the group. Say 10 people agree to a chit fund: each contributes ₹1,000 every month, for 10 months. Total pool value = ₹10,000/month.
  2. Every cycle, everyone pays in. Every member pays their fixed ₹1,000 each month — no exceptions, whether or not they've already received a
  payout.
  3. One member gets the pot each cycle. Each month, exactly one member receives the pooled ₹10,000. Over the full 10 months, every member gets
  exactly one payout — that's what makes it "rotating."
  4. Who gets it, and how, varies by model:
    - Lottery/rotation: pure luck or a pre-agreed order.
    - Auction/bidding (the classic "chit fund" mechanism, and what we built): members who haven't won yet bid for how much less than the full pot
  they'd accept to take the payout now instead of waiting. Whoever bids lowest wins — e.g., if the pot is ₹10,000 and someone bids ₹9,000, they get
  ₹9,000 now. The ₹1,000 "discount" they gave up gets split as a dividend among the other members, effectively lowering their next contribution's
  real cost.
  5. Repeat until everyone's won once. After 10 cycles, everyone has contributed ₹10,000 total and received exactly one ₹10,000-ish payout — the fund
  closes.

  Why people use it

  - Early access to a lump sum without a bank loan — useful for a wedding, medical bill, or business need. Winning early is effectively borrowing at
  a "discount rate" you set yourself via your bid.
  - Forced savings for members who win later — the discipline of a recurring commitment.
  - Community trust-based credit — historically used where formal banking access is limited, since it runs on social trust rather than credit scores.

  The risk it carries — and why "trust" matters

  The entire system depends on every member continuing to pay in after they've already received their payout. Someone who wins early and then stops
  contributing (defaults) leaves a hole the rest of the group has to absorb. This is exactly the gap our app's trust score targets — it's a
  transparent, explainable measure of how reliably a member has paid on time, so an organizer can see risk before letting someone into a pool, not
  after a default has already happened. That's the product's real differentiator: digitizing a centuries-old trust-based system with a data-backed
  (but still human-readable) trust signal, rather than a black-box credit score.

  How this maps onto what we built

  ┌──────────────────────────────────────┬─────────────────────────────────────────────────┐
  │          Chit fund concept           │                   In the app                    │
  ├──────────────────────────────────────┼─────────────────────────────────────────────────┤
  │ Group + fixed contribution           │ Pool (name, contribution amount, member cap)    │
  ├──────────────────────────────────────┼─────────────────────────────────────────────────┤
  │ Monthly payment                      │ contribute endpoint → LedgerEntry               │
  ├──────────────────────────────────────┼─────────────────────────────────────────────────┤
  │ Auction round                        │ Cycle in bidding_open status + Bid records      │
  ├──────────────────────────────────────┼─────────────────────────────────────────────────┤
  │ Lowest bid wins, discount → dividend │ bidding_engine.resolve_cycle_bids()             │
  ├──────────────────────────────────────┼─────────────────────────────────────────────────┤
  │ "Already won, can't win again"       │ Membership.has_won                              │
  ├──────────────────────────────────────┼─────────────────────────────────────────────────┤
  │ Reliability reputation               │ trust_score.py — Laplace-smoothed on-time ratio │
  └──────────────────────────────────────┴─────────────────────────────────────────────────┘

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
