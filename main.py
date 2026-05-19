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

# --- FIXED: ADVANCED AUTO-BUTTON CLICKER ---
def click_confirm_button(token, msg_data):
    try:
        components = msg_data.get('components', [])
        if not components: return
        
        custom_id = None
        # Deep loop to find any valid button custom_id in the message layout
        for row in components:
            if row.get('type') == 1: # Action Row
                for item in row.get('components', []):
                    if item.get('type') == 2: # Button
                        custom_id = item.get('custom_id')
                        break
            if custom_id: break
            
        if not custom_id: return
        
        # Build the exact integration transaction request payload
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
        
        # Fire the interaction post request
        url = "https://discord.com/api/v9/interactions"
        headers = {"Authorization": token.strip(), "Content-Type": "application/json"}
        res = requests.post(url, headers=headers, json=payload)
        
        if res.status_code in [200, 204]:
            print("🔘 Successfully executed automated button bypass confirmation.")
        else:
            print(f"⚠️ Button interaction failed: {res.status_code} - {res.text}")
    except Exception as e:
        print(f"⚠️ Button click processor error: {e}")

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
                        
                        # Command: Perm
                        if content == "perm":
                            send_chat_message(token, text_channel, f".v perm {MY_USER_ID}")
                        elif content.startswith("perm "):
                            target = content.replace("perm ", "", 1).strip()
                            send_chat_message(token, text_channel, f".v perm {target}")

                        # Command: Transfer Owner
                        elif content == "ara lya owner":
                            send_chat_message(token, text_channel, f".v transfer {MY_USER_ID}")

                        # Command: Co-Owner Add
                        elif content == "ara cowner":
                            send_chat_message(token, text_channel, f".v cowner add {MY_USER_ID}")
                        elif content.startswith("cowner l hada "):
                            target = content.replace("cowner l hada ", "", 1).strip()
                            send_chat_message(token, text_channel, f".v cowner add {target}")

                        # NEW Command: Co-Owner Remove (7yd cowner [username/ID])
                        elif content.startswith("7yd cowner "):
                            target = content.replace("7yd cowner ", "", 1).strip()
                            send_chat_message(token, text_channel, f".v cowner remove {target}")

                        # NEW Command: Reject User (rejecti had zmar [username/ID])
                        elif content == "rejecti had zmar":
                            send_chat_message(token, text_channel, f".v reject {MY_USER_ID}")
                        elif content.startswith("rejecti had zmar "):
                            target = content.replace("rejecti had zmar ", "", 1).strip()
                            send_chat_message(token, text_channel, f".v reject {target}")

                # --- AUTO-CONFIRMATION BUTTON CLICKER ---
                if t in ["MESSAGE_UPDATE", "MESSAGE_CREATE"]:
                    if d and d.get('guild_id') == GUILD_ID:
                        # Ensure the message is actually from a bot layout
                        author = d.get('author', {})
                        if author.get('bot') is True:
                            components = d.get('components')
                            if components:
                                # Small delay so Discord registers the bot message before the alt clicks it
                                time.sleep(0.5)
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
        
