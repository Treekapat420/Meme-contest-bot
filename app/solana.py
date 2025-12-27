import aiohttp
import re
from typing import Any, Dict, Optional

SOL_ADDR_RE = re.compile(r"^[1-9A-HJ-NP-Za-km-z]{32,44}$")

async def sol_rpc(session: aiohttp.ClientSession, rpc_url: str, method: str, params: list) -> Dict[str, Any]:
    payload = {"jsonrpc": "2.0", "id": 1, "method": method, "params": params}
    async with session.post(rpc_url, json=payload, timeout=20) as resp:
        resp.raise_for_status()
        return await resp.json()

async def get_token_balance_raw(rpc_url: str, owner: str, mint: str) -> int:
    """
    Total token amount in raw units across token accounts for owner filtered by mint.
    """
    async with aiohttp.ClientSession() as session:
        res = await sol_rpc(session, rpc_url, "getTokenAccountsByOwner", [
            owner,
            {"mint": mint},
            {"encoding": "jsonParsed"}
        ])
        if "error" in res:
            raise RuntimeError(res["error"])

        value = res.get("result", {}).get("value", [])
        total = 0
        for acc in value:
            try:
                info = acc["account"]["data"]["parsed"]["info"]["tokenAmount"]
                amt = int(info["amount"])
                total += amt
            except Exception:
                continue
        return total

async def get_token_decimals(rpc_url: str, mint: str) -> Optional[int]:
    async with aiohttp.ClientSession() as session:
        res = await sol_rpc(session, rpc_url, "getTokenSupply", [mint])
    if "error" in res:
        return None
    try:
        return int(res["result"]["value"]["decimals"])
    except Exception:
        return None

async def get_price_usd_dexscreener(token_mint: str) -> Optional[float]:
    """
    Fetch USD price from Dexscreener. Chooses the highest-liquidity pair.
    """
    url = f"https://api.dexscreener.com/token-pairs/v1/solana/{token_mint}"
    async with aiohttp.ClientSession() as session:
        async with session.get(url, timeout=20) as resp:
            resp.raise_for_status()
            pairs = await resp.json()

    if not isinstance(pairs, list) or not pairs:
        return None

    def liq_usd(p):
        try:
            return float(p.get("liquidity", {}).get("usd") or 0)
        except Exception:
            return 0.0

    best = max(pairs, key=liq_usd)
    try:
        price = best.get("priceUsd")
        return float(price) if price is not None else None
    except Exception:
        return None
