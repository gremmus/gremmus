from fastapi import FastAPI, Request
import httpx
import os

app = FastAPI()

# ===== CONFIG — read from environment =====
BROKER_URL = os.getenv("BROKER_URL")
STRATEGY_ID = os.getenv("STRATEGY_ID")
SECRET = os.getenv("SECRET")
SYMBOL_MAP = {"MNQ1!": "MNQM2026"} # chart symbol -> broker symbol


def reshape(p):
 # Predator Native JSON -> Delta Exchange schema
 return {
 "symbol": SYMBOL_MAP.get(p["symbol"], p["symbol"]),
 "side": "buy" if p["action"] == "buy" else "sell",
 "qty": str(int(p["qty"])), # whole-number string
 "trigger_time": p.get("timeframe", ""),
 "strategy_id": STRATEGY_ID,
 }

@app.post("/relay")
async def relay(req: Request):
 p = await req.json()
 if p.get("secret") != SECRET: # reject randoms
 return {"ok": False, "error": "bad secret"}
 if p.get("event") != "entry": # only forward entries here
 return {"ok": True, "skipped": p.get("event")}
 payload = reshape(p)
 async with httpx.AsyncClient() as c:
 r = await c.post(BROKER_URL, json=payload, timeout=10)
 return {"ok": True, "broker_status": r.status_code}
