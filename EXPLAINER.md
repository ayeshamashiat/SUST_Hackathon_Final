# The idea, explained simply

*A knowledge-transfer doc for anyone joining the project — teammates, judges, or future you. No prior context assumed.*

## The problem, as a story

Picture an agent's shop counter in a busy market, the afternoon before Eid. The shop serves customers of three mobile-money providers — bKash, Nagad, Rocket. The agent has:

- **One physical cash drawer** (real taka, shared across all three providers).
- **Three separate phone-wallet balances** — one e-money account per provider, kept completely apart (bKash's app can't see Nagad's numbers, and vice versa).

Money moves in two directions:

- **Cash-out** (a customer wants cash): the customer sends e-money to the agent, the agent hands over cash. Result: cash drawer goes **down**, that provider's e-money balance goes **up**.
- **Cash-in** (a customer wants to top up their wallet): the customer hands the agent cash, the agent sends e-money to the customer. Result: cash drawer goes **up**, that provider's e-money balance goes **down**.

Right before Eid, almost everyone wants cash-out (people cashing in remittances, salaries, bonuses). So the agent's cash drawer drains fast — even though, on paper, the agent looks "rich" if you add up cash + all three e-money balances. The three separate app screens don't help: nobody is doing that addition, and nobody is looking ahead to say "you'll run out of cash by 5pm" or "bKash specifically is about to stall, not Nagad or Rocket."

On top of that, a flood of similar-looking cash-out requests from a handful of accounts starts coming in. Is that just normal Eid demand? A glitch in the data feed? Or something that deserves a closer look? And once someone decides it deserves a closer look — who actually looks at it, and how do we know it got handled?

## What we're building

Three things, working together:

### 1. A unified dashboard
One screen that shows the cash drawer and all three provider balances side by side, plus a plain-language forecast: *"At the current pace, bKash cash-out may stall around 5:20 PM. Confidence: medium — based on the last 40 minutes of activity."* No merging of the actual wallets — we're just showing three separate numbers next to each other and doing the arithmetic a human would eventually do anyway, faster and continuously.

### 2. An alarm system (explainable, not a black box)
Small, well-understood statistics — rolling averages, "how many standard deviations from normal is this," simple thresholds — watch the transaction stream. When something crosses a threshold, it raises a flag:
- *Liquidity flag*: "cash (or one provider's balance) is trending toward zero, here's when and how sure we are."
- *Anomaly flag*: "an unusual burst of near-identical transactions from a small group of accounts — here are the actual transactions that triggered this."

Every flag always says **"unusual" / "requires review"** — never "this is fraud." The system hands over evidence; a human makes the call. This isn't a legal disclaimer bolted on afterward — it's a hard rule baked into every template and every code path.

### 3. A coordination checklist (turning a blinking light into a tracked case)
When something important is flagged, it becomes a **case**: who was notified, who owns it, what they should do next, and whether it's acknowledged / in progress / escalated / resolved. This is the difference between "the dashboard turned red" (and everyone assumes someone else saw it) and "Officer X acknowledged this at 4:47 PM and is checking with the agent now."

## Why the multi-provider view is more than a UI convenience

The genuinely new insight only shows up when you can see *across* providers at once. Example: a small group of accounts does near-identical cash-outs on bKash, and — within the same few minutes, at the same shop — a similar pattern shows up on Nagad. Individually, bKash's ops team and Nagad's ops team each see a normal-ish blip on their own side. Only a view that sits across both providers, at the same physical agent, can connect those two blips into one pattern worth a second look. That's the core argument for why a "super agent" needs a unified tool at all, not just three tabs open side by side.

## What the system deliberately never does

- Never merges the three providers' balances into one pot, or implies money can move between them.
- Never touches a real wallet, account, or transaction — everything is simulated/synthetic data.
- Never declares "this is fraud" — only "unusual, here's why, here's who should look at it."
- Never blocks a user, freezes funds, or takes an automatic financial action.
- Never asks for PINs, OTPs, passwords, or real customer identities.

## How it's built, in one paragraph

A FastAPI backend simulates the agent's transaction stream (cash drawer + 3 provider balances), runs the forecasting and anomaly-detection math, and turns important findings into alerts that automatically get routed to the right role and tracked as cases with an audit trail. A Next.js frontend shows all of this as a dashboard, an alert list with evidence, and a case-tracking view, with English/Bengali/Banglish explanations. No external AI API is called — the "AI/analytics" requirement is met by the statistical detectors themselves (EWMA forecasting, z-score anomaly detection), which keeps the whole thing explainable, testable, and safe to demo without an internet dependency.

## Where to look next

- [`initial_plan.md`](initial_plan.md) — the full 3-pass build plan (what ships in which pass, and why).
- [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) — the system diagram and component breakdown.
- [`docs/DATA_SIMULATION.md`](docs/DATA_SIMULATION.md) — how the fake data and scenarios are generated (once Pass 1 ships).
