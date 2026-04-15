import os, json, time, threading, websocket
from flask import Flask

# --- FLASK WEB SERVER (Railway Persistence) ---
app = Flask('')
@app.route('/')
def home(): return "🛰️ Sentinel Dual-Lock: Active"

def run_web():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

# --- CONFIG ---
GUILD_ID = "777271906486976512"
CHANNEL_ID = "1487672527370322132"

# Token Dictionary (Ensure TOKEN_ONE and TOKEN_TWO are in Railway)
tokens = {
    "Sentinel 1": os.getenv("TOKEN_ONE"),
    "Sentinel 2": os.getenv("TOKEN_TWO")
}

def vc_locker(token, name):
    if not token:
        print(f"⚠️ {name} token missing.")
        return

    while True:
        try:
            ws = websocket.WebSocket()
            ws.connect('wss://gateway.discord.gg/?v=9&encoding=json', timeout=15)
            
            # 1. IDENTIFY (Using Desktop properties for better Stream support)
            ws.send(json.dumps({
                "op": 2, 
                "d": {
                    "token": token.strip(), 
                    "properties": {"$os": "windows", "$browser": "Chrome", "$device": ""},
                    "presence": {"status": "online", "afk": False}
                }
            }))

            # JOIN PAYLOAD: Targeting Camera (self_video) and Live Badge (self_stream)
            join_payload = {
                "op": 4, 
                "d": {
                    "guild_id": GUILD_ID, 
                    "channel_id": CHANNEL_ID,
                    "self_mute": False, 
                    "self_deaf": False,
                    "self_video": True,
                    "self_stream": True
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

                # Join VC immediately upon connection
                if op == 10:
                    ws.send(json.dumps(join_payload))

                if t == "READY":
                    user_id = d['user']['id']
                    print(f"✅ {name} connected as {d['user']['username']}")

                # --- INSTANT REJOIN LOGIC (3s delay) ---
                if t == "VOICE_STATE_UPDATE":
                    if d.get('user_id') == user_id:
                        if d.get('channel_id') != CHANNEL_ID:
                            print(f"🔄 {name} was moved/disconnected. Rejoining in 3s...")
                            time.sleep(3)
                            ws.send(json.dumps(join_payload))

                # --- HEARTBEAT & BADGE REFRESH ---
                if time.time() - last_heartbeat > 30:
                    ws.send(json.dumps({"op": 1, "d": data.get('s')}))
                    # Re-send join payload to refresh the "Live" and "Camera" icons
                    ws.send(json.dumps(join_payload)) 
                    last_heartbeat = time.time()

        except Exception as e:
            print(f"⚠️ {name} connection error: {e}. Reconnecting in 10s...")
            time.sleep(10)

if __name__ == "__main__":
    # Start persistence server
    threading.Thread(target=run_web, daemon=True).start()
    
    print(f"🚀 Dual Lock active for Channel: {CHANNEL_ID}")
    
    threads = []
    for name, token in tokens.items():
        if token:
            t = threading.Thread(target=vc_locker, args=(token, name))
            t.start()
            threads.append(t)
            time.sleep(8) # Staggered join to stay safe

    for t in threads:
        t.join()
        
