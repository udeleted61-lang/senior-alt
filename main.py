import os, json, time, threading, websocket
from flask import Flask

# --- FLASK WEB SERVER (Persistence) ---
app = Flask('')
@app.route('/')
def home(): return "🛰️ Dual Sentinel Lock: Active"

def run_web():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

# --- CONFIG ---
GUILD_ID = "777271906486976512"
CHANNEL_ID = "1487672527370322132"

# Token Dictionary
tokens = {
    "Sentinel 1": os.getenv("TOKEN_ONE"),
    "Sentinel 2": os.getenv("TOKEN_TWO")
}

def vc_locker(token, name):
    if not token:
        print(f"⚠️ {name} token missing. Skipping...")
        return

    while True:
        try:
            ws = websocket.WebSocket()
            ws.connect('wss://gateway.discord.gg/?v=9&encoding=json')
            
            # 1. IDENTIFY
            ws.send(json.dumps({
                "op": 2, 
                "d": {
                    "token": token.strip(), 
                    "properties": {"$os": "linux", "$browser": "Chrome", "$device": "pc"},
                    "presence": {"status": "online", "afk": False}
                }
            }))

            # Join Payload
            join_payload = {
                "op": 4, 
                "d": {
                    "guild_id": GUILD_ID, 
                    "channel_id": CHANNEL_ID,
                    "self_mute": False, 
                    "self_deaf": False,
                    "self_video": True,
                    "self_live_screan": True
                }
            }

            last_heartbeat = 0
            user_id = None

            while True:
                msg = ws.recv()
                if not msg: break
                data = json.loads(msg)
                
                op = data.get('op')
                t = data.get('t')
                d = data.get('d')

                # Initial Join on Hello
                if op == 10:
                    ws.send(json.dumps(join_payload))

                # Capture ID to identify "Moves"
                if t == "READY":
                    user_id = d['user']['id']
                    print(f"✅ {name} Logged in as {d['user']['username']}")

                # --- INSTANT REJOIN LOGIC ---
                if t == "VOICE_STATE_UPDATE":
                    if d.get('user_id') == user_id:
                        if d.get('channel_id') != CHANNEL_ID:
                            print(f"🔄 {name} Move/Disconnect! Rejoining in 3s...")
                            time.sleep(3)
                            ws.send(json.dumps(join_payload))

                # Keep Connection Alive
                if time.time() - last_heartbeat > 30:
                    ws.send(json.dumps({"op": 1, "d": data.get('s')}))
                    last_heartbeat = time.time()

        except Exception as e:
            print(f"⚠️ {name} instability: {e}. Reconnecting in 5s...")
            time.sleep(5)

if __name__ == "__main__":
    # Start the "Keep Alive" server
    threading.Thread(target=run_web, daemon=True).start()
    
    print(f"🚀 Dual Lock active for Channel: {CHANNEL_ID}")
    
    threads = []
    for name, token in tokens.items():
        t = threading.Thread(target=vc_locker, args=(token, name))
        t.start()
        threads.append(t)
        time.sleep(5) # Staggered startup

    for t in threads:
        t.join()
