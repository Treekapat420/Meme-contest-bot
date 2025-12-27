import math
from aiogram import Bot, Dispatcher
from aiogram.filters import Command
from aiogram.types import Message

from .config import Config
from .db import DB
from .solana import SOL_ADDR_RE, get_token_balance_raw, get_token_decimals, get_price_usd_dexscreener

def is_admin(cfg: Config, user_id: int) -> bool:
    return user_id in cfg.admin_ids

def build_dispatcher(bot: Bot, cfg: Config, database: DB) -> Dispatcher:
    dp = Dispatcher()

    @dp.message(Command("start"))
    async def start(m: Message):
        database.ensure_user(m.from_user.id, m.from_user.username or "")
        active, start_ts, end_ts = database.contest_status()
        live = database.contest_is_live()

        status = "LIVE ✅" if live else ("Active (not in window) ⚠️" if active else "Not started ❌")

        text = (
            "🏁 *Memecoin Contest Bot*\n\n"
            f"Token mint (CA): `{cfg.token_mint}`\n"
            f"Min hold: **${cfg.min_hold_usd:.2f}**\n\n"
            "✅ To participate you must be a holder.\n"
            "1) Verify: `/verify YOUR_SOL_WALLET`\n"
            "2) Join: `/join`\n"
            "3) Check: `/leaderboard` or `/myrank`\n\n"
            f"Contest status: {status}\n"
        )
        if end_ts:
            text += f"Ends: <t:{end_ts}:F>\n"
        await m.answer(text, parse_mode="Markdown")

    @dp.message(Command("status"))
    async def status(m: Message):
        database.ensure_user(m.from_user.id, m.from_user.username or "")
        active, start_ts, end_ts = database.contest_status()
        live = database.contest_is_live()
        await m.answer(
            f"Active: {active}\nLive: {live}\nStart: {start_ts}\nEnd: {end_ts}"
        )

    @dp.message(Command("verify"))
    async def verify(m: Message):
        database.ensure_user(m.from_user.id, m.from_user.username or "")

        parts = m.text.split()
        if len(parts) != 2:
            return await m.answer("Usage: `/verify YOUR_SOL_WALLET`", parse_mode="Markdown")

        wallet = parts[1].strip()
        if not SOL_ADDR_RE.match(wallet):
            return await m.answer("That doesn’t look like a valid Solana wallet address.")

        # balance
        try:
            bal_raw = await get_token_balance_raw(cfg.sol_rpc_url, wallet, cfg.token_mint)
        except Exception as e:
            return await m.answer(f"RPC error verifying wallet. Try again later.\n\n`{e}`", parse_mode="Markdown")

        # decimals
        decimals = await get_token_decimals(cfg.sol_rpc_url, cfg.token_mint)
        if decimals is None:
            return await m.answer("Couldn’t fetch token decimals right now. Try again shortly.")

        # price
        price_usd = await get_price_usd_dexscreener(cfg.token_mint)
        if not price_usd or price_usd <= 0:
            return await m.answer("Couldn’t fetch token price right now (Dexscreener). Try again shortly.")

        # threshold
        min_tokens = cfg.min_hold_usd / price_usd
        min_raw = math.ceil(min_tokens * (10 ** decimals))

        if bal_raw < min_raw:
            ui_bal = bal_raw / (10 ** decimals)
            ui_min = min_raw / (10 ** decimals)
            database.set_verified(m.from_user.id, wallet, 0)
            return await m.answer(
                f"❌ Not enough holdings.\n\n"
                f"Minimum: **${cfg.min_hold_usd:.2f}** (≈ **{ui_min:.6f}** tokens)\n"
                f"You have: **{ui_bal:.6f}** tokens\n\n"
                f"Buy a little more and run `/verify {wallet}` again.",
                parse_mode="Markdown",
            )

        database.set_verified(m.from_user.id, wallet, 1)
        await m.answer("✅ Verified holder (≥ $5). Now use `/join` to enter the contest.", parse_mode="Markdown")

    @dp.message(Command("join"))
    async def join(m: Message):
        database.ensure_user(m.from_user.id, m.from_user.username or "")

        if not database.contest_is_live():
            return await m.answer("Contest isn’t live right now.")

        u = database.get_user(m.from_user.id)
        if not u or int(u["verified"]) != 1:
            return await m.answer("You must verify as a holder first: `/verify YOUR_SOL_WALLET`", parse_mode="Markdown")

        database.mark_joined(m.from_user.id)
        await m.answer("🏁 You’re in! Use `/leaderboard` to track the rankings.", parse_mode="Markdown")

    @dp.message(Command("leaderboard"))
    async def leaderboard(m: Message):
        rows = database.top_leaderboard(10)
        if not rows:
            return await m.answer("No entries yet. Be the first to `/join`.")

        lines = ["🏆 *Top 10 Leaderboard*"]
        for i, r in enumerate(rows, start=1):
            name = r["username"] or f"user_{r['tg_id']}"
            lines.append(f"{i}. @{name} — *{int(r['points'])}* pts")
        await m.answer("\n".join(lines), parse_mode="Markdown")

    @dp.message(Command("myrank"))
    async def myrank(m: Message):
        rank = database.get_rank(m.from_user.id)
        if not rank:
            return await m.answer("You’re not ranked yet. Verify + `/join` first.")
        pos, pts = rank
        await m.answer(f"📍 Your rank: *#{pos}* with *{pts}* points.", parse_mode="Markdown")

    # -------- Admin Commands --------

    @dp.message(Command("setcontest"))
    async def setcontest(m: Message):
        if not is_admin(cfg, m.from_user.id):
            return await m.answer("Admin only.")
        parts = m.text.split()
        if len(parts) != 2 or not parts[1].isdigit():
            return await m.answer("Usage: `/setcontest 14` (days)", parse_mode="Markdown")
        days = int(parts[1])
        database.set_contest_days(days)
        _, _, end_ts = database.contest_status()
        await m.answer(f"✅ Contest started for {days} days.\nEnds: <t:{end_ts}:F>")

    @dp.message(Command("endcontest"))
    async def endcontest(m: Message):
        if not is_admin(cfg, m.from_user.id):
            return await m.answer("Admin only.")
        database.end_contest()
        await m.answer("⛔ Contest ended.")

    @dp.message(Command("addpoints"))
    async def addpoints(m: Message):
        if not is_admin(cfg, m.from_user.id):
            return await m.answer("Admin only.")

        parts = m.text.split(maxsplit=3)
        if len(parts) < 3:
            return await m.answer("Usage: `/addpoints @username 10 optional_reason`", parse_mode="Markdown")

        username = parts[1].lstrip("@")
        delta = int(parts[2])

        tg_id = database.find_user_by_username(username)
        if not tg_id:
            return await m.answer("User not found (they must /start the bot first).")

        database.add_points(tg_id, delta)
        await m.answer(f"✅ Added {delta} points to @{username}.")

    @dp.message(Command("removepoints"))
    async def removepoints(m: Message):
        if not is_admin(cfg, m.from_user.id):
            return await m.answer("Admin only.")

        parts = m.text.split(maxsplit=3)
        if len(parts) < 3:
            return await m.answer("Usage: `/removepoints @username 5 optional_reason`", parse_mode="Markdown")

        username = parts[1].lstrip("@")
        delta = int(parts[2])

        tg_id = database.find_user_by_username(username)
        if not tg_id:
            return await m.answer("User not found (they must /start the bot first).")

        database.add_points(tg_id, -abs(delta))
        await m.answer(f"✅ Removed {abs(delta)} points from @{username}.")

    @dp.message(Command("winners"))
    async def winners(m: Message):
        rows = database.top_n(3)
        if not rows:
            return await m.answer("No entries yet.")
        prizes = ["🥇", "🥈", "🥉"]
        lines = ["🏆 *Winners (current)*"]
        for i, r in enumerate(rows):
            name = r["username"] or f"user_{r['tg_id']}"
            lines.append(f"{prizes[i]} @{name} — *{int(r['points'])}* pts")
        await m.answer("\n".join(lines), parse_mode="Markdown")

    return dp
