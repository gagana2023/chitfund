# Chitfund

*A digital chit fund : rotating savings, an honest auction, and a trust score that can explain itself.*

## Inspiration

My grandmother — Ajji — kept a small steel box on the shelf above the puja corner in our house in Chikmagalur, Karnataka. It never held jewelry. It held a notebook.

Every month, five or six women from the street would come by after the evening prayers and hand her folded notes — fifty rupees, a hundred, whatever the group had agreed on. She'd write the amount next to each name. This was the *chit*: a small, informal fund the women ran themselves, long before any of them had a bank account in their own name.

Once a month, one woman took the whole pot. If your daughter's wedding was three months out and you needed the money now instead of waiting your turn, you said so, and you said how much less you'd accept to get it early. Whoever asked for the least got paid, and the difference was split among everyone still waiting. 

Ajji was the one everyone trusted to hold the box.  She carried that ledger in her head as much as in pencil. When she passed, some of that memory went with her. The group dissolved within a year. No one else was trusted to hold it the way she had.

That's the problem I wanted to solve. Plenty of apps digitize payments. I wanted to digitize what Ajji actually did: hold the trust, not just the money. 

## What it does

Chitfund runs a full rotating savings circle (a ROSCA — chit fund, *kuri*, *committee*, depending on where you're from):

- **Pools**: a group agrees on a fixed contribution and a group size, and runs for exactly that many cycles.
- **Contributions**: every member pays the fixed amount every cycle — including members who've already won a payout, exactly as it works in a real chit fund.
- **A real auction, not a lottery**: each cycle, members who haven't won yet can bid the amount they're willing to accept early. The lowest bid wins the payout at that amount, and the gap between the full pool and the winning bid is split as a dividend among everyone else. If pool total is $P$ and the winning bid is $b$, the dividend each of the other $n-1$ members receives is:

$$
d = \frac{P - b}{n - 1}
$$

- **A trust score that explains itself**: rather than a black-box model, each member's score is a Laplace-smoothed on-time ratio —

$$
\text{trust} = \frac{(\text{on-time} + 1)}{(\text{total contributions} + 2)} \times 100
$$

  The $+1$ and $+2$ matter more than they look. Without smoothing, a member with one lucky on-time payment reads as a perfect 100 — exactly the kind of overconfident signal that got Ajji's successors in trouble when they trusted someone too early. The smoothing means trust has to be earned across a real history, the same way it was earned in that room with the steel box.
- **Discovery, requests, and a head**: pools are publicly browsable, anyone can request to join, and the pool's creator — its *head* — approves who gets in. That's Ajji's role, formalized: someone still has to decide who's trustworthy enough to hold a place in the circle.

## How I built it

**Backend**: Python, FastAPI, SQLAlchemy, SQLite. The bidding resolution and trust score are pure, dependency-free functions (`bidding_engine.py`, `trust_score.py`) so they could be unit-tested in isolation from the database and API layer — the part of the app where a silent bug would be the most damaging, since it's the part that decides who gets paid what.

**Frontend**: React, TypeScript, Vite, Tailwind. A dark, gold-accented interface — a deliberate choice, since a savings product built around trust and money shouldn't look like a generic dashboard template.

**Process**: I built this end to end with Claude Code, using the [ECC](https://github.com/affaan-m/ecc) agent harness for planning, TDD, and code review. 

## Challenges I faced

Two bugs, in particular, taught me more than anything that went smoothly.

**The phantom payout.** While testing, a member won a payout of ₹700 despite never having contributed a rupee to that cycle.The pool's head had contributed while she was still the *only* member, which was enough to satisfy "everyone has paid" and flip the cycle straight into bidding . The fix was recognizing that a chit fund's group has to be *fixed and full* before the fund starts, exactly like Ajji's five or six women agreeing on the circle before the first month's collection. I added a hard gate: no cycle can begin bidding until the pool has reached its full member count.

**The tab that lied about who it was.** A second, subtler bug: identity was stored in the browser's `localStorage`, which is shared across every tab in a browser. Testing with two tabs,the natural way to demo a multi-person app without spinning up incognito windows, meant logging in on tab two silently overwrote the identity tab one was using. An action in tab one could get attributed to whoever had most recently logged in *anywhere* in that browser. I moved identity to `sessionStorage`, scoped per tab, so each tab reliably stays whoever it says it is.
## What I learned

The hardest part of building a trust system  was deciding what trust should even *mean* — in a way a person could look at and believe, the way you'd believe Ajji's pencil marks in that notebook. So explainability became the actual design constraint.

## What's next

Real payment rail integration (the ledger is fully simulated today), proper session auth for real cross-device use, and a transfer-of-headship flow — so that when the person holding the circle together needs to step back, as Ajji eventually did, the group doesn't have to dissolve with her.
