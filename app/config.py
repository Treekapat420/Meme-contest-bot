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
    contest_group_id: int

def load_config() -> Config:
    bot_token = os.getenv("BOT_TOKEN", "").strip()
    if not bot_token:
        raise RuntimeError("BOT_TOKEN is required")

    admin_ids = set(int(x) for x in os.getenv("ADMIN_IDS", "").split(",") if x.strip())
    sol_rpc_url = os.getenv("SOL_RPC_URL", "").strip()
    token_mint = os.getenv("TOKEN_MINT", "").strip()
    contest_group_id = int(os.getenv("CONTEST_GROUP_ID", "0"))

    if not sol_rpc_url or not token_mint:
        raise RuntimeError("SOL_RPC_URL and TOKEN_MINT are required")

    return Config(
        bot_token=bot_token,
        admin_ids=admin_ids,
        sol_rpc_url=sol_rpc_url,
        token_mint=token_mint,
        min_hold_usd=float(os.getenv("MIN_HOLD_USD", "5")),
        contest_days_default=int(os.getenv("CONTEST_DAYS_DEFAULT", "14")),
        sweep_every_seconds=int(os.getenv("SWEEP_EVERY_SECONDS", "21600")),
        kick_on_fail=os.getenv("KICK_ON_FAIL", "true").lower() == "true",
        db_path=os.getenv("DB_PATH", "contest.db"),
    )
        contest_group_id=contest_group_id,
