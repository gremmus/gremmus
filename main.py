from fastapi import FastAPI, Request
import httpx
import json
import os

app = FastAPI()

# Hent URL fra Environment Variable (sikker måte)
TRADERSPPOST_URL = os.getenv("TRADERSPPOST_URL")

if not TRADERSPPOST_URL:
    print("WARNING: TRADERSPPOST_URL environment variable is not set!")

@app.post("/webhook")
async def handle_webhook(request: Request):
    payload = await request.json()
    
    print("Received from TradingView:")
    print(json.dumps(payload, indent=2))

    symbol = payload.get("symbol", "").replace("1!", "").replace("!", "")

    # Transform logic
    if payload.get("event") == "entry":
        transformed = {
            "ticker": symbol,
            "action": payload.get("action"),
            "orderType": "market",
            "quantity": int(payload.get("qty", 1)),
            "comment": f"Predator | Conf:{payload.get('confluence')} | {payload.get('trigger')}"
        }
    else:
        # TP1, TP2, TP3, SL, close_all etc.
        transformed = {
            "ticker": symbol,
            "action": "close",
            "comment": payload.get("message", "Exit signal from Predator")
        }

    print("Sending to TradersPost:")
    print(json.dumps(transformed, indent=2))

    # Send videre
    if TRADERSPPOST_URL:
        async with httpx.AsyncClient(timeout=10.0) as client:
            try:
                resp = await client.post(TRADERSPPOST_URL, json=transformed)
                print(f"TradersPost status: {resp.status_code}")
            except Exception as e:
                print("Error to TradersPost:", e)

    return {"status": "ok"}