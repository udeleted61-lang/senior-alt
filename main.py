import os, json, time, threading, websocket, requests, random
from flask import Flask

# --- FLASK WEB SERVER ---
app = Flask('')
@app.route('/')
def home(): return "🛰️ Sentinel Remote-Control: Active"

def run_web():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

# --- CONFIGURATION ---
GUILD_ID = os.getenv("GUILD")
CHANNEL_ID = os.getenv("CHANNEL")

# YOUR DISCORD USER ID (Only requests from this ID will trigger commands)
MY_USER_ID = "1404189983807639672" 

tokens = {
    "Sentinel 1": os.getenv("TOKEN_ONE"),
    "Sentinel 2": os.getenv("TOKEN_TWO"),
    "Sentinel XP": os.getenv("TOKEN_XP") 
}

# --- 2-HOUR MESSAGE FUNCTION ---
def send_periodic_msg(token, name):
    while True:
        if token:
            url = f"https://discord.com/api/v9/channels/{CHANNEL_ID}/messages"
            headers = {"Authorization": token.strip(), "Content-Type": "application/json"}
            try:
                requests.post(url, headers=headers, json={"content": ""})
            except: pass
        time.sleep(7200) # 2 Hours

# --- HELPER TO SEND TEXT RESPONSES ---
def send_chat_message(token, text_channel_id, content):
    url = f"https://discord.com/api/v9/channels/{text_channel_id}/messages"
    headers = {"Authorization": token.strip(), "Content-Type": "application/json"}
    try:
        requests.post(url, headers=headers, json={"content": content})
    except Exception as e:
        print(f"⚠️ Failed to send message response: {e}")

# --- HELPER TO INTERACT WITH BUTTONS (For Owner Confirmation) ---
def click_confirm_button(token, msg_data):
    try:
        components = msg_data.get('components', [])
        if not components: return
        
        # Look for the button inside the action row
        button = components[0].get('components', [{}])[0]
        custom_id = button.get('custom_id')
        if not custom_id: return
        
        payload = {
            "type": 3,
            "guild_id": GUILD_ID,
            "channel_id": msg_data['channel_id'],
            "message_id": msg_data['id'],
            "application_id": msg_data['author']['id'],
            "data": {
                "component_type": 2,
                "custom_id": custom_id
            }
        }
        url = "https://discord.com/api/v9/interactions"
        headers = {"Authorization": token.strip(), "Content-Type": "application/json"}
        requests.post(url, headers=headers, json=payload)
        print("🔘 Clicked confirmation button automatically.")
    except Exception as e:
        print(f"⚠️ Button click error: {e}")

# --- MAIN VC LOCKER & GATEWAY LISTENER ---
def vc_locker(token, name, is_xp_token=False):
    if not token: return

    while True:
        try:
            ws = websocket.WebSocket()
            ws.connect('wss://gateway.discord.gg/?v=9&encoding=json', timeout=15)
            
            ws.send(json.dumps({
                "op": 2, 
                "d": {
                    "token": token.strip(), 
                    "properties": {"$os": "windows", "$browser": "Chrome", "$device": ""},
                    "presence": {"status": "online", "afk": False}
                }
            }))

            join_payload = {
                "op": 4, 
                "d": {
                    "guild_id": GUILD_ID, "channel_id": CHANNEL_ID,
                    "self_mute": False, "self_deaf": False,
                    "self_video": False, "self_stream": True
                }
            }

            last_heartbeat = 0
            user_id = None
            last_dice_roll = time.time()

            while True:
                msg = ws.recv()
                if not msg: break
                data = json.loads(msg)
                
                op = data.get('op')
                t = data.get('t')
                d = data.get('d')

                if op == 10:
                    ws.send(json.dumps(join_payload))

                if t == "READY":
                    user_id = d['user']['id']
                    print(f"✅ {name} connected.")

                # --- REMOTE CONTROL DISPATCHER ---
                if t == "MESSAGE_CREATE":
                    author_id = d.get('author', {}).get('id')
                    content = d.get('content', '').strip()
                    text_channel = d.get('channel_id')
                    msg_guild_id = d.get('guild_id')

                    if msg_guild_id == GUILD_ID and author_id == MY_USER_ID:
                        
                        # Command: Permission mapping
                        if content == "perm":
                            send_chat_message(token, text_channel, f".v perm {MY_USER_ID}")
                        elif content.startswith("perm "):
                            target = content.replace("perm ", "", 1).strip()
                            send_chat_message(token, text_channel, f".v perm {target}")

                        # Command: Ownership Transfer mapping
                        elif content == "ara lya owner":
                            send_chat_message(token, text_channel, f".v transfer {MY_USER_ID}")

                        # Command: Co-owner mapping
                        elif content == "ara cowner":
                            send_chat_message(token, text_channel, f".v cowner add {MY_USER_ID}")
                        elif content.startswith("cowner l hada "):
                            target = content.replace("cowner l hada ", "", 1).strip()
                            send_chat_message(token, text_channel, f".v cowner add {target}")

                # --- AUTO-CONFIRMATION BUTTON CLICKER (CRASH FIXED) ---
                if t in ["MESSAGE_UPDATE", "MESSAGE_CREATE"]:
                    if d and d.get('guild_id') == GUILD_ID:
                        components = d.get('components')
                        # Safe check without using an illegal walrus assignment expression
                        if components:
                            click_confirm_button(token, d)

                # --- SMART REJOIN LOGIC ---
                if t == "VOICE_STATE_UPDATE":
                    if d.get('user_id') == user_id:
                        new_channel = d.get('channel_id')
                        if new_channel is None: # Kicked
                            time.sleep(1)
                            ws.send(json.dumps(join_payload))

                # --- WAVY XP LOGIC ---
                if is_xp_token and (time.time() - last_dice_roll > 60):
                    if random.randint(1, 400) == 77:
                        break 
                    last_dice_roll = time.time()

                if time.time() - last_heartbeat > 30:
                    ws.send(json.dumps({"op": 1, "d": data.get('s')}))
                    last_heartbeat = time.time()

            ws.close()
            if is_xp_token:
                time.sleep(random.randint(400, 450))

        except Exception:
            time.sleep(10)

if __name__ == "__main__":
    threading.Thread(target=run_web, daemon=True).start()
    
    threads = []
    for name, token in tokens.items():
        if token:
            is_xp = (name == "Sentinel XP")
            vt = threading.Thread(target=vc_locker, args=(token, name, is_xp))
            vt.start()
            threads.append(vt)
            
            mt = threading.Thread(target=send_periodic_msg, args=(token, name), daemon=True)
            mt.start()
            time.sleep(5) 

    for t in threads:
        t.join()
                    
