🏆 Meme Contest Bot (Telegram) — Holders Only

A Telegram contest bot for Solana memecoins that enforces wallet verification, a minimum USD hold, and runs a leaderboard-based contest with automatic compliance checks.

Built in Python, deployed on Railway, and designed for fair, holders-only competitions.

⸻

🚀 Features
	•	✅ Solana wallet verification
	•	💵 Minimum hold enforced ($5 USD)
	•	📈 Live leaderboard
	•	🧮 Admin-controlled scoring
	•	⏱️ Timed contest (default: 14 days)
	•	🔁 Automated holder sweeps (re-verifies wallets every 6 hours)
	•	🚫 Auto-removal if wallet drops below minimum
	•	☁️ Railway-ready deployment
	•	🧠 Clean, auditable logic (no referrals, no exploits)

⸻

🔐 Holder Verification Logic
	1.	User verifies wallet via /verify
	2.	Bot checks:
	•	Token balance (on-chain)
	•	Token decimals (RPC)
	•	USD price (Dexscreener)
	3.	Wallet must hold ≥ $5 USD worth of the token
	4.	Bot re-checks all participants every 6 hours
	5.	If balance falls below minimum:
	•	User is unverified
	•	User is removed from contest
	•	User can re-verify anytime

⸻

🧾 Contest Rules (Default)
	•	Chain: Solana
	•	Token Mint:
7VskDPVqgyf5VLtAVw23renwvepm4zScHeuHHw2dpump
	•	Minimum Hold: $5 USD
	•	Contest Length: 14 days
	•	Scoring: Admin-awarded points
	•	Prizes: External payout (not handled by bot)

⸻

🤖 Telegram Commands

👤 User Commands
Command                 Description
/start              View contest info
/verify <wallet>    Verify Solana wallet
/join             Join contest (holders only)
/leaderboard        View top 10
/myrank             View your rank

🛠️ Admin Commands
Command                 Description
/setcontest <days>      Start contest
/endcontest             End contest
/addpoints @user 10     Add points
/removepoints @user 5   Remove points
/winners                Show top 3
/status                 Contest status


