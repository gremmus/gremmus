from fastapi import FastAPI, Request
import httpx
import json
import os

app = FastAPI()

# === KONFIGURASJON ===
TRADERSPPOST_URL = os.getenv("https://webhooks.traderspost.io/trading/webhook/a1a993ea-cec7-4187-8363-3a4f00f35744/8ae9e09726cbc198a6cda40c7fbc918b")  # Legg inn din TradersPost webhook her

@app.post("/webhook")
async def handle_webhook(request: Request):
    payload = await request.json()
    print("Received from TradingView:")
    print(json.dumps(payload, indent=2))

    transformed = {}

    symbol = payload.get("symbol", "").replace("1!", "")   # MNQ1! → MNQ

    # ENTRY
    if payload.get("event") == "entry":
        action = payload.get("action")  # "buy" eller "sell"
        transformed = {
            "ticker": symbol,
            "action": action,
            "orderType": "market",
            "quantity": payload.get("qty"),
            # "stopLoss": payload.get("sl"),
            # "takeProfit": payload.get("tp1"),   # du kan legge til flere hvis TradersPost støtter det
            "comment": f"Confluence: {payload.get('confluence')} | {payload.get('trigger')}"
        }

    # TP / SL / CLOSE ALL
    elif payload.get("action") == "close_all" or "tp" in str(payload.get("event", "")).lower() or "sl" in str(payload.get("event", "")).lower():
        transformed = {
            "ticker": symbol,
            "action": "close",
            "comment": payload.get("message", "TP/SL hit")
        }

    # Fallback
    else:
        transformed = {
            "ticker": symbol,
            "action": payload.get("action", "close")
        }

    print("Sending to TradersPost:")
    print(json.dumps(transformed, indent=2))

    # Send til TradersPost
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            resp = await client.post(TRADERSPPOST_URL, json=transformed)
            print(f"TradersPost responded with: {resp.status_code}")
            return {"status": "sent", "traderspost_code": resp.status_code}
        except Exception as e:
            print("Error sending to TradersPost:", str(e))
            return {"status": "error", "detail": str(e)}

@app.get("/")
async def root():
    return {"status": "Predator → TradersPost Relay is running"}
