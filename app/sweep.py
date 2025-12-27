import asyncio
import math
from aiogram import Bot

from .db import DB
from .config import Config
from .solana import SOL_ADDR_RE, get_token_balance_raw, get_token_decimals, get_price_usd_dexscreener

async def sweep_task(bot: Bot, cfg: Config, database: DB):
    """
    Periodic enforcement (C):
    - fetch decimals + price once per cycle
    - check verified+joined users
    - if wallet < $MIN_HOLD_USD worth of token => unverify + (optional) kick from contest
    """
    await asyncio.sleep(10)

    while True:
        try:
            decimals = await get_token_decimals(cfg.sol_rpc_url, cfg.token_mint)
            price_usd = await get_price_usd_dexscreener(cfg.token_mint)

            if decimals is None or not price_usd or price_usd <= 0:
                # skip this cycle if we can’t determine threshold
                print("[SWEEP] Skipping: missing decimals or price")
                await asyncio.sleep(cfg.sweep_every_seconds)
                continue

            min_tokens = cfg.min_hold_usd / price_usd
            min_raw = math.ceil(min_tokens * (10 ** decimals))

            users = database.list_verified_users(only_joined=True)
            print(f"[SWEEP] Checking {len(users)} users. min_raw={min_raw}")

            for u in users:
                tg_id = int(u["tg_id"])
                wallet = u["wallet"]

                if not wallet or not SOL_ADDR_RE.match(wallet):
                    database.unverify_and_optionally_kick(tg_id, cfg.kick_on_fail)
                    continue

                try:
                    bal_raw = await get_token_balance_raw(cfg.sol_rpc_url, wallet, cfg.token_mint)
                except Exception as e:
                    # don’t punish user for RPC issues
                    print(f"[SWEEP] RPC error tg_id={tg_id}: {e}")
                    await asyncio.sleep(0.25)
                    continue

                if bal_raw < min_raw:
                    database.unverify_and_optionally_kick(tg_id, cfg.kick_on_fail)

                    # DM notice (optional; will fail if user blocked bot)
                    try:
                        ui_bal = bal_raw / (10 ** decimals)
                        ui_min = min_raw / (10 ** decimals)
                        await bot.send_message(
                            tg_id,
                            (
                                "⚠️ Contest verification removed.\n\n"
                                f"Minimum: **${cfg.min_hold_usd:.2f}** (≈ **{ui_min:.6f}** tokens)\n"
                                f"Your balance: ≈ **{ui_bal:.6f}** tokens\n\n"
                                "Buy/hold above the minimum and re-verify:\n"
                                f"`/verify {wallet}`"
                            ),
                            parse_mode="Markdown",
                        )
                    except Exception as dm_err:
                        print(f"[SWEEP] DM failed tg_id={tg_id}: {dm_err}")

                await asyncio.sleep(0.25)  # throttle per-wallet

        except Exception as e:
            print(f"[SWEEP] Fatal sweep error: {e}")

        await asyncio.sleep(cfg.sweep_every_seconds)
