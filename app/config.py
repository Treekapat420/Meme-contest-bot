import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Config:
    bot_token: str
    admin_ids: set[int]

    sol_rpc_url: str
    token_mint: str
    min_hold_usd: float

    contest_days_default: int
    sweep_every_seconds: int
    kick_on_fail: bool

    db_path: str

    # NEW: group where scoring happens
    contest_group_id: int


def load_config() -> Config:
    bot_token = os.getenv("BOT_TOKEN", "").strip()
    if not bot_token:
        raise RuntimeError("BOT_TOKEN is required")

    admin_ids_raw = os.getenv("ADMIN_IDS", "").strip()
    admin_ids = set()
    for x in admin_ids_raw.split(","):
        x = x.strip()
        if x:
            admin_ids.add(int(x))

    sol_rpc_url = os.getenv("SOL_RPC_URL", "").strip()
    if not sol_rpc_url:
        raise RuntimeError("SOL_RPC_URL is required")

    token_mint = os.getenv("TOKEN_MINT", "").strip()
    if not token_mint:
        raise RuntimeError("TOKEN_MINT is required")

    min_hold_usd = float(os.getenv("MIN_HOLD_USD", "5"))
    contest_days_default = int(os.getenv("CONTEST_DAYS_DEFAULT", "14"))
    sweep_every_seconds = int(os.getenv("SWEEP_EVERY_SECONDS", str(6 * 60 * 60)))
    kick_on_fail = os.getenv("KICK_ON_FAIL", "true").lower() == "true"

    db_path = os.getenv("DB_PATH", "contest.db").strip()

    contest_group_id = int(os.getenv("CONTEST_GROUP_ID", "0"))

    return Config(
        bot_token=bot_token,
        admin_ids=admin_ids,
        sol_rpc_url=sol_rpc_url,
        token_mint=token_mint,
        min_hold_usd=min_hold_usd,
        contest_days_default=contest_days_default,
        sweep_every_seconds=sweep_every_seconds,
        kick_on_fail=kick_on_fail,
        db_path=db_path,
        contest_group_id=contest_group_id,
    )
