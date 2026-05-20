from fastapi import FastAPI, Request
import httpx

app = FastAPI()

# ===== CONFIG — edit these =====
BROKER_URL  = "https://api.delta.exchange/your-webhook-endpoint"
STRATEGY_ID = "your_real_strategy_id"
SECRET      = "pick-a-long-random-string"   # shared password
SYMBOL_MAP  = {"XAUUSD": "XAUUSD"}      # chart symbol -> broker symbol

def reshape(p):
    # Predator Native JSON -> Delta Exchange schema
    return {
        "symbol":       SYMBOL_MAP.get(p["symbol"], p["symbol"]),
        "side":         "buy" if p["action"] == "buy" else "sell",
        "qty":          str(int(p["qty"])),        # whole-number string
        "trigger_time": p.get("timeframe", ""),
        "strategy_id":  STRATEGY_ID,
    }

@app.post("/relay")
async def relay(req: Request):
    p = await req.json()
    if p.get("secret") != SECRET:        # reject randoms
        return {"ok": False, "error": "bad secret"}
    if p.get("event") != "entry":      # only forward entries here
        return {"ok": True, "skipped": p.get("event")}

    payload = reshape(p)
    async with httpx.AsyncClient() as c:
        r = await c.post(BROKER_URL, json=payload, timeout=10)
    return {"ok": True, "broker_status": r.status_code}