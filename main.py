import os, json, time, threading, websocket, requests
from flask import Flask

# --- FLASK WEB SERVER (For Railway Persistence) ---
app = Flask('')
@app.route('/')
def home(): return "🛰️ Sentinel Dual-Lock: Active"

def run_web():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

# --- CONFIG ---
GUILD_ID = os.getenv("GUILD")
CHANNEL_ID = os.getenv("CHANNEL")
APP_ID = "1492480420955295784" 

# Token Dictionary
tokens = {
    "Sentinel 1": os.getenv("TOKEN_ONE"),
    "Sentinel 2": os.getenv("TOKEN_TWO")
}

# --- HOURLY MESSAGE FUNCTION ---
def send_hourly_msg():
    while True:
        token = os.getenv("TOKEN_ONE") 
        if token:
            url = f"https://discord.com/api/v9/channels/{CHANNEL_ID}/messages"
            headers = {"Authorization": token.strip(), "Content-Type": "application/json"}
            payload = {"content": "d"}
            try:
                res = requests.post(url, headers=headers, json=payload)
                if res.status_code == 200:
                    print("📅 Hourly message 'd' sent successfully.")
                else:
                    print(f"⚠️ Failed to send hourly message: {res.text}")
            except Exception as e:
                print(f"⚠️ Message error: {e}")
        
        # Wait 1 hour (3600 seconds)
        time.sleep(3600) 

def vc_locker(token, name):
    if not token:
        print(f"⚠️ {name} token missing in Railway Variables.")
        return

    while True:
        try:
            ws = websocket.WebSocket()
            ws.connect('wss://gateway.discord.gg/?v=9&encoding=json', timeout=15)
            
            # 1. IDENTIFY with Clean Status
            ws.send(json.dumps({
                "op": 2, 
                "d": {
                    "token": token.strip(), 
                    "properties": {"$os": "windows", "$browser": "Chrome", "$device": ""},
                    "presence": {
                        "status": "online", 
                        "afk": False,
                        "activities": [{
                            "name": "High School DXD",
                            "type": 0,
                            "application_id": APP_ID,
                            "assets": {
                                "large_image": "riasgrimoired"
                            }
                        }]
                    }
                }
            }))

            # JOIN PAYLOAD: Deafened, Unmuted, Camera On, and Streaming
            join_payload = {
                "op": 4, 
                "d": {
                    "guild_id": GUILD_ID, 
                    "channel_id": CHANNEL_ID,
                    "self_mute": False, 
                    "self_deaf": True,
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

                # Join VC immediately
                if op == 10:
                    ws.send(json.dumps(join_payload))

                if t == "READY":
                    user_id = d['user']['id']
                    print(f"✅ {name} connected as {d['user']['username']}")

                # --- INSTANT REJOIN LOGIC (1s delay) ---
                if t == "VOICE_STATE_UPDATE":
                    if d.get('user_id') == user_id:
                        if d.get('channel_id') != CHANNEL_ID:
                            print(f"🔄 {name} moved. Rejoining in 1s...")
                            time.sleep(1)
                            ws.send(json.dumps(join_payload))

                # --- HEARTBEAT & BADGE REFRESH ---
                if time.time() - last_heartbeat > 30:
                    ws.send(json.dumps({"op": 1, "d": data.get('s')}))
                    # Re-send join payload to refresh icons
                    ws.send(json.dumps(join_payload)) 
                    last_heartbeat = time.time()

        except Exception as e:
            print(f"⚠️ {name} connection error: {e}. Reconnecting...")
            time.sleep(10)

if __name__ == "__main__":
    # Start Flask Web Server
    threading.Thread(target=run_web, daemon=True).start()
    
    # Start the Hourly "d" Message
    threading.Thread(target=send_hourly_msg, daemon=True).start()
    
    print(f"🚀 Sentinel Multi-Lock active for Channel: {CHANNEL_ID}")
    
    threads = []
    for name, token in tokens.items():
        if token:
            t = threading.Thread(target=vc_locker, args=(token, name))
            t.start()
            threads.append(t)
            time.sleep(5) 

    for t in threads:
        t.join()
        
