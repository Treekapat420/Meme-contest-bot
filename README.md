🏆 Meme Contest Bot (Telegram) — Holders Only

A Telegram contest bot for Solana memecoins that enforces wallet verification, a minimum USD hold, and automatically tracks meme engagement points in a contest group.

Built in Python, deployed on Railway, and designed for fair, holders-only meme competitions.

⸻

🚀 Features
	•	✅ Solana wallet verification
	•	💵 Minimum hold enforced ($5 USD)
	•	🧾 Tracks Telegram user ID + verified wallet together
	•	🖼️ Automatic meme scoring
	•	📈 Live leaderboard
	•	🧮 Admin overrides for points
	•	⏱️ Timed contest (default: 14 days)
	•	🔁 Automated holder sweeps (re-verifies wallets every 6 hours)
	•	🚫 Auto-removal if wallet drops below minimum
	•	☁️ Railway-ready deployment

⸻

🧠 How Points Are Earned (Current Rules)

Points are automatically tracked in the designated contest Telegram group.

✅ Meme Posting
	•	+1 point when a verified + joined user posts a meme
	•	Meme must be media:
	•	Photo
	•	Video
	•	GIF / animation
	•	Meme must be a new post, not a reply

⸻

💬 Replies on Your Meme
	•	+1 point to the meme owner for each reply on their meme
	•	Replies must be direct replies to the original meme post
	•	❌ Repliers do NOT receive points

⸻

👍 Likes on Your Meme (Reactions)
	•	+1 point to the meme owner for each unique user reaction
	•	Reactions counted as “likes” by default:
	•	👍
	•	❤️
	•	🔥
	•	Each user can only award 1 reaction point per meme
	•	❌ Likers do NOT receive points

⸻

🚫 Anti-Abuse Rules
	•	No double-counting of replies
	•	No reaction toggle farming
	•	Only verified + joined users can earn points
	•	Meme owner must still meet the $5 minimum hold to receive points

⸻

🧾 Contest Rules (Default)
	•	Chain: Solana
	•	Token Mint: 7VskDPVqgyf5VLtAVw23renwvepm4zScHeuHHw2dpump
		•	Minimum Hold: $5 USD
	•	Contest Length: 14 days
	•	Scoring: Fully automatic (meme engagement)
	•	Payouts: Handled manually (not by bot)
