import requests
import re
import urllib3
import time
import threading
import os
import sys
import json
import string
import hashlib
import socket
import random
from datetime import datetime
from urllib.parse import urlparse, parse_qs, urljoin
from concurrent.futures import ThreadPoolExecutor

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ==========================================
# 1. CONFIGURATION (GITHUB INTEGRATION)
# ==========================================
BOT_TOKEN = "8628520343:AAGaR2xOcKRzzDO7ozX3g3bWCbOzUWnTjR0"
ADMIN_CHAT_ID = "6840380489"

# မင်းရဲ့ GitHub Raw URL ကို ဒီမှာ အစားထိုးပါ
GITHUB_RAW_URL = "https://raw.githubusercontent.com/tmmt6132-coder/Rujie-/main/key.txt"
LOCAL_KEYS_FILE = os.path.expanduser("~/.ruijie_cache.txt")

RED, GREEN, YELLOW, BLUE, MAGENTA, CYAN, WHITE, RESET = "\033[91m", "\033[92m", "\033[93m", "\033[94m", "\033[95m", "\033[96m", "\033[97m", "\033[0m"
BOLD = "\033[1m"

stop_event = threading.Event()

# ==========================================
# 2. DATA & AUTHENTICATION SYSTEM
# ==========================================

def get_id():
    uid = os.getuid() if hasattr(os, 'getuid') else 1000
    user = os.environ.get('USER', 'Neko')
    return f"{uid}{user}"

def get_authorized_data():
    try:
        # Cache မငြိအောင် timestamp ထည့်ပြီး GitHub ကနေ ဖတ်ပါတယ်
        r = requests.get(f"{GITHUB_RAW_URL}?t={int(time.time())}", timeout=8)
        if r.status_code == 200:
            with open(LOCAL_KEYS_FILE, 'w', encoding='utf-8') as f:
                f.write(r.text)
            return r.text.strip().split('\n')
    except:
        pass
    if os.path.exists(LOCAL_KEYS_FILE):
        with open(LOCAL_KEYS_FILE, 'r', encoding='utf-8') as f:
            return f.read().strip().split('\n')
    return []

def get_online_time():
    try:
        r = requests.get("http://worldtimeapi.org/api/timezone/Asia/Yangon", timeout=5)
        if r.status_code == 200:
            return datetime.fromisoformat(r.json()['datetime'].split('.')[0])
    except: return None

def auto_kill_monitor(sys_key):
    while True:
        try:
            lines = get_authorized_data()
            active = False
            for line in lines:
                data = [d.strip() for d in line.split(',')]
                if data and data[0] == sys_key:
                    active = True
                    # Admin က Key ကို ဖြုတ်လိုက်ရင် ဒါမှမဟုတ် BLOCK လို့ ရေးလိုက်ရင် ပိတ်မယ်
                    if len(data) >= 4 and "BLOCK" in data[3].upper():
                        print(f"\n{RED}[!!!] ACCESS REVOKED BY ADMIN{RESET}")
                        os._exit(0)
                    
                    exp_val = data[2] if len(data) >= 3 else "UNLIMITED"
                    if exp_val != "UNLIMITED":
                        expiry_date = datetime.strptime(exp_val, "%Y-%m-%d")
                        now = get_online_time() or datetime.now()
                        if now > expiry_date:
                            print(f"\n{RED}[!!!] SESSION EXPIRED: {exp_val}{RESET}")
                            os._exit(0)
                    break
            if not active:
                print(f"\n{RED}[!!!] KEY REMOVED FROM SERVER{RESET}")
                os._exit(0)
            time.sleep(30)
        except: time.sleep(10)

# ==========================================
# 3. STEALTH & NETWORK LOGICS
# ==========================================

def get_stealth_headers():
    ua = "Mozilla/5.0 (Linux; Android 14; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Mobile Safari/537.36"
    return {
        "User-Agent": ua,
        "Accept": "application/json, text/plain, */*",
        "X-Ruijie-Client-ID": ''.join(random.choices(string.digits, k=13)),
        "Connection": "keep-alive"
    }

def identify_brand(url, text):
    url, text = url.lower(), text.lower()
    if any(x in url for x in ["wifidog", "2060", "eportal", "ruijie"]): return "RUIJIE"
    if "mikrotik" in url or "login?dst=" in url: return "MIKROTIK"
    return "GENERIC"

# ==========================================
# 4. UI & MAIN ENGINE
# ==========================================

def show_neko_banner():
    os.system('clear' if os.name == 'posix' else 'cls')
    print(f"""
{CYAN}        ╱|、
       (˚ˎ 。7  
        |、˜〵          
        じしˍ,)ノ {RESET}{GREEN}AIDEN TEAM WiFi Engine {RESET}{YELLOW}v10.0{RESET}
{CYAN}     「 GitHub Key System · Stealth Mode 」{RESET}
""")

def check_approval():
    show_neko_banner()
    sys_key = get_id()
    lines = get_authorized_data()
    
    is_approved = False
    display_expiry = "N/A"
    
    for line in lines:
        data = [d.strip() for d in line.split(',')]
        if data and data[0] == sys_key:
            is_approved = True
            display_expiry = data[2] if len(data) >= 3 else "UNLIMITED"
            break

    if not is_approved:
        print(f"{RED}[!] Key Not Found: {sys_key}{RESET}")
        print(f"{YELLOW}[*] GitHub ထဲမှာ Key ထည့်ပြီးမှ ပြန်ပွင့်ပါမည်။{RESET}")
        sys.exit()

    print(f"{GREEN}┌─────────────────────────────────────────┐")
    print(f"│ {WHITE}● KEY     {RESET}{GREEN}{sys_key}{' '*(33-len(sys_key))}{RESET}{GREEN}│")
    print(f"│ {WHITE}● EXPIRY  {RESET}{MAGENTA}{display_expiry}{' '*(33-len(display_expiry))}{RESET}{GREEN}│")
    print(f"└─────────────────────────────────────────┘")
    
    print(f"\n{CYAN}[1] Start Engine{RESET}    {YELLOW}[2] Exit{RESET}")
    if input(f"{GREEN}> {RESET}") == "1":
        threading.Thread(target=auto_kill_monitor, args=(sys_key,), daemon=True).start()
        return True
    sys.exit()

def start_bypass():
    session = requests.Session()
    print(f"\n{CYAN}[*] Searching for Portal...{RESET}")
    
    while True:
        try:
            # အင်တာနက်ရှိမရှိ အရင်စစ်မယ်
            if requests.get("http://connectivitycheck.gstatic.com/generate_204", timeout=2).status_code == 204:
                print(f"{GREEN}[✔] ONLINE! STANDBY...{RESET}             ", end="\r")
                time.sleep(10)
                continue

            # Captive Portal ကို ရှာမယ်
            r = session.get("http://1.1.1.1", allow_redirects=True, timeout=5)
            brand = identify_brand(r.url, r.text)
            
            # Logic များ (Ruijie/Mikrotik) ဒီမှာ ဆက်လုပ်ဆောင်ပါ...
            # (အရင် Code ထဲက Pulse Executor ကို ဒီမှာ ပြန်ထည့်နိုင်ပါတယ်)
            
            print(f"{BLUE}[BYPASS]{RESET} Target identified: {brand}          ", end="\r")
            time.sleep(5)
            
        except Exception as e:
            time.sleep(2)

if __name__ == "__main__":
    if check_approval():
        try:
            start_bypass()
        except KeyboardInterrupt:
            print(f"\n{RED}[!] Stopped.{RESET}")
            sys.exit()
