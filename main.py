import os
import shutil
import asyncio
import json
import base64
import math
import requests
import time
import uuid
import random
import re
import threading
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from aiogram import Bot, Dispatcher, F, Router
from aiogram.types import Message, FSInputFile
from aiogram.filters import Command

BOT_TOKEN = os.getenv("BOT_TOKEN")

router = Router()

SESSION_BASE_DIR = "basket_sessions"
if os.path.exists(SESSION_BASE_DIR):
    shutil.rmtree(SESSION_BASE_DIR, ignore_errors=True)
os.makedirs(SESSION_BASE_DIR, exist_ok=True)

CUSTOM_PROXIES_FILE = "custom_proxies.json"

DEFAULT_PROXY_LIST = [
    "http://Eyi7eecyfihd:pe1rm71fd72ka0k@209.50.177.175:3129",
    "http://eyi7eecyfihd:pe1rm71fd72ka0k@65.111.6.98:3129",
    "http://eyi7eecyfihd:pe1rm71fd72ka0k@65.111.15.99:3129",
    "http://eyi7eecyfihd:pe1rm71fd72ka0k@45.3.47.48:3129",
    "http://eyi7eecyfihd:pe1rm71fd72ka0k@45.3.35.213:3129",
    "http://eyi7eecyfihd:pe1rm71fd72ka0k@209.50.160.216:3129",
    "http://eyi7eecyfihd:pe1rm71fd72ka0k@45.3.51.133:3129",
    "http://eyi7eecyfihd:pe1rm71fd72ka0k@209.50.180.169:3129",
    "http://eyi7eecyfihd:pe1rm71fd72ka0k@216.26.232.240:3129",
    "http://eyi7eecyfihd:pe1rm71fd72ka0k@45.3.52.87:3129",
    "http://eyi7eecyfihd:pe1rm71fd72ka0k@216.26.251.136:3129",
    "http://eyi7eecyfihd:pe1rm71fd72ka0k@209.50.191.84:3129",
    "http://eyi7eecyfihd:pe1rm71fd72ka0k@65.111.28.133:3129",
    "http://eyi7eecyfihd:pe1rm71fd72ka0k@45.3.37.181:3129",
    "http://eyi7eecyfihd:pe1rm71fd72ka0k@216.26.224.92:3129",
    "http://eyi7eecyfihd:pe1rm71fd72ka0k@216.26.255.106:3129",
    "http://eyi7eecyfihd:pe1rm71fd72ka0k@45.3.47.128:3129",
    "http://eyi7eecyfihd:pe1rm71fd72ka0k@45.3.38.17:3129",
    "http://eyi7eecyfihd:pe1rm71fd72ka0k@209.50.170.180:3129",
    "http://eyi7eecyfihd:pe1rm71fd72ka0k@209.50.172.165:3129",
    "http://eyi7eecyfihd:pe1rm71fd72ka0k@45.3.37.53:3129",
    "http://eyi7eecyfihd:pe1rm71fd72ka0k@209.50.169.0:3129",
    "http://eyi7eecyfihd:pe1rm71fd72ka0k@216.26.227.194:3129",
    "http://eyi7eecyfihd:pe1rm71fd72ka0k@45.3.53.50:3129",
    "http://eyi7eecyfihd:pe1rm71fd72ka0k@209.50.180.78:3129",
    "http://eyi7eecyfihd:pe1rm71fd72ka0k@209.50.188.218:3129",
    "http://eyi7eecyfihd:pe1rm71fd72ka0k@216.26.249.209:3129",
    "http://eyi7eecyfihd:pe1rm71fd72ka0k@45.3.33.21:3129",
    "http://eyi7eecyfihd:pe1rm71fd72ka0k@45.3.39.129:3129",
    "http://eyi7eecyfihd:pe1rm71fd72ka0k@209.50.191.208:3129",
    "http://eyi7eecyfihd:pe1rm71fd72ka0k@209.50.186.116:3129",
    "http://eyi7eecyfihd:pe1rm71fd72ka0k@104.167.19.176:3129",
    "http://eyi7eecyfihd:pe1rm71fd72ka0k@104.207.58.95:3129",
    "http://eyi7eecyfihd:pe1rm71fd72ka0k@65.111.13.165:3129",
    "http://eyi7eecyfihd:pe1rm71fd72ka0k@45.3.32.145:3129",
    "http://eyi7eecyfihd:pe1rm71fd72ka0k@104.207.33.227:3129",
    "http://eyi7eecyfihd:pe1rm71fd72ka0k@45.3.45.178:3129",
    "http://eyi7eecyfihd:pe1rm71fd72ka0k@45.3.38.33:3129",
    "http://eyi7eecyfihd:pe1rm71fd72ka0k@45.3.47.195:3129",
    "http://eyi7eecyfihd:pe1rm71fd72ka0k@217.181.91.121:3129",
    "http://eyi7eecyfihd:pe1rm71fd72ka0k@104.207.44.69:3129",
    "http://eyi7eecyfihd:pe1rm71fd72ka0k@216.26.230.228:3129",
    "http://eyi7eecyfihd:pe1rm71fd72ka0k@45.3.53.28:3129",
    "http://eyi7eecyfihd:pe1rm71fd72ka0k@209.50.187.186:3129",
    "http://eyi7eecyfihd:pe1rm71fd72ka0k@216.26.235.149:3129",
    "http://eyi7eecyfihd:pe1rm71fd72ka0k@209.50.174.138:3129",
    "http://eyi7eecyfihd:pe1rm71fd72ka0k@104.207.37.105:3129",
    "http://eyi7eecyfihd:pe1rm71fd72ka0k@45.3.37.240:3129",
    "http://eyi7eecyfihd:pe1rm71fd72ka0k@45.3.40.40:3129",
    "http://eyi7eecyfihd:pe1rm71fd72ka0k@104.207.56.236:3129",
    "http://eyi7eecyfihd:pe1rm71fd72ka0k@216.26.242.198:3129",
    "http://eyi7eecyfihd:pe1rm71fd72ka0k@45.3.34.203:3129",
    "http://eyi7eecyfihd:pe1rm71fd72ka0k@209.50.171.62:3129",
    "http://eyi7eecyfihd:pe1rm71fd72ka0k@216.26.239.126:3129",
    "http://eyi7eecyfihd:pe1rm71fd72ka0k@209.50.169.3:3129",
    "http://eyi7eecyfihd:pe1rm71fd72ka0k@216.26.244.93:3129",
    "http://eyi7eecyfihd:pe1rm71fd72ka0k@104.207.53.140:3129",
    "http://eyi7eecyfihd:pe1rm71fd72ka0k@217.181.91.129:3129",
    "http://eyi7eecyfihd:pe1rm71fd72ka0k@104.207.44.251:3129",
    "http://eyi7eecyfihd:pe1rm71fd72ka0k@209.50.173.23:3129",
    "http://eyi7eecyfihd:pe1rm71fd72ka0k@104.207.46.156:3129",
    "http://eyi7eecyfihd:pe1rm71fd72ka0k@216.26.245.137:3129",
    "http://eyi7eecyfihd:pe1rm71fd72ka0k@65.111.8.250:3129",
    "http://eyi7eecyfihd:pe1rm71fd72ka0k@209.50.162.29:3129",
    "http://eyi7eecyfihd:pe1rm71fd72ka0k@216.26.243.249:3129",
    "http://eyi7eecyfihd:pe1rm71fd72ka0k@216.26.232.50:3129",
    "http://eyi7eecyfihd:pe1rm71fd72ka0k@193.56.28.28:3129",
    "http://eyi7eecyfihd:pe1rm71fd72ka0k@65.111.13.253:3129",
    "http://eyi7eecyfihd:pe1rm71fd72ka0k@216.26.242.2:3129",
    "http://eyi7eecyfihd:pe1rm71fd72ka0k@104.207.34.129:3129",
    "http://eyi7eecyfihd:pe1rm71fd72ka0k@65.111.29.199:3129",
    "http://eyi7eecyfihd:pe1rm71fd72ka0k@45.3.42.143:3129",
    "http://eyi7eecyfihd:pe1rm71fd72ka0k@65.111.29.224:3129",
    "http://eyi7eecyfihd:pe1rm71fd72ka0k@45.3.36.239:3129",
    "http://eyi7eecyfihd:pe1rm71fd72ka0k@65.111.4.143:3129",
    "http://eyi7eecyfihd:pe1rm71fd72ka0k@65.111.14.79:3129",
    "http://eyi7eecyfihd:pe1rm71fd72ka0k@65.111.1.18:3129",
    "http://eyi7eecyfihd:pe1rm71fd72ka0k@104.207.54.229:3129",
    "http://eyi7eecyfihd:pe1rm71fd72ka0k@45.3.42.147:3129",
    "http://eyi7eecyfihd:pe1rm71fd72ka0k@216.26.227.153:3129",
    "http://eyi7eecyfihd:pe1rm71fd72ka0k@45.3.55.53:3129",
    "http://eyi7eecyfihd:pe1rm71fd72ka0k@65.111.7.244:3129",
    "http://eyi7eecyfihd:pe1rm71fd72ka0k@209.50.182.193:3129",
    "http://eyi7eecyfihd:pe1rm71fd72ka0k@104.207.36.52:3129",
    "http://eyi7eecyfihd:pe1rm71fd72ka0k@216.26.225.85:3129",
    "http://eyi7eecyfihd:pe1rm71fd72ka0k@209.50.181.217:3129",
    "http://eyi7eecyfihd:pe1rm71fd72ka0k@104.207.62.25:3129",
    "http://eyi7eecyfihd:pe1rm71fd72ka0k@104.207.58.236:3129",
    "http://eyi7eecyfihd:pe1rm71fd72ka0k@216.26.244.191:3129",
    "http://eyi7eecyfihd:pe1rm71fd72ka0k@65.111.25.234:3129",
    "http://eyi7eecyfihd:pe1rm71fd72ka0k@104.207.39.139:3129",
    "http://eyi7eecyfihd:pe1rm71fd72ka0k@45.3.38.200:3129",
    "http://eyi7eecyfihd:pe1rm71fd72ka0k@65.111.21.224:3129",
    "http://eyi7eecyfihd:pe1rm71fd72ka0k@104.207.40.150:3129",
    "http://eyi7eecyfihd:pe1rm71fd72ka0k@209.50.191.58:3129",
    "http://eyi7eecyfihd:pe1rm71fd72ka0k@104.207.58.48:3129",
    "http://eyi7eecyfihd:pe1rm71fd72ka0k@209.50.180.171:3129",
    "http://eyi7eecyfihd:pe1rm71fd72ka0k@65.111.4.154:3129",
    "http://eyi7eecyfihd:pe1rm71fd72ka0k@209.50.189.21:3129",
    "http://eyi7eecyfihd:pe1rm71fd72ka0k@45.3.40.101:3129"
]

PROXY_LIST = list(DEFAULT_PROXY_LIST)
PROXY_LOCK = threading.Lock()

# وضعیت انتظار برای دریافت پروکسی از سمت کاربر
WAITING_FOR_PROXY_USERS = set()

# حداکثر تعداد تردهای همزمان برای پردازش پایدار ۱۵۰+ اکانت
MAX_WORKERS = 8

# شعاع جابجایی مجاز روی نقشه بر حسب متر (بین ۸ تا ۴۵ متر؛ در همان کوچه/خیابان تا فروشگاه خارج نشود)
MIN_OFFSET_METERS = 8.0
MAX_OFFSET_METERS = 45.0

# بافر جمع‌آوری لینک‌ها برای مواقعی که تلگرام ۱۵۰ لینک را به چند پیام تقسیم می‌کند
USER_BATCH_BUFFERS = {}


# ==================== بخش مدیریت و پارس هوشمند پروکسی ====================

def _is_valid_port(val: str) -> bool:
    return val.isdigit() and 1 <= int(val) <= 65535


def _looks_like_host(val: str) -> bool:
    if not val or " " in val:
        return False
    # IPv4
    if re.match(r"^\d{1,3}(\.\d{1,3}){3}$", val):
        return True
    # دامنه معتبر (مانند gate.joyproxy.com)
    if "." in val and re.match(r"^[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$", val):
        return True
    return False


def normalize_single_proxy(raw_line: str) -> str | None:
    """
    تبدیل هوشمند انواع فرمت‌های پروکسی به فرمت استاندارد:
    http://user:pass@host:port یا http://host:port
    """
    s = raw_line.strip()
    if not s or s.startswith("#"):
        return None

    scheme = "http"
    if "://" in s:
        sp = s.split("://", 1)
        if sp[0].lower() in ("http", "https", "socks5", "socks5h", "socks4"):
            scheme = sp[0].lower()
            s = sp[1].strip()
        else:
            # اگر لینک معمولی وب است و پروکسی نیست
            return None

    # نادیده گرفتن مسیرهای اضافه در صورتی که لینک API یا وب باشد
    if "/" in s:
        return None

    # حالت ۱: حاوی @ (فرمت‌های user:pass@host:port یا برعکس host:port@user:pass)
    if "@" in s:
        left, right = s.rsplit("@", 1)
        if ":" in left and ":" in right:
            l1, l2 = left.rsplit(":", 1)
            r1, r2 = right.rsplit(":", 1)
            # استاندارد: user:pass@host:port
            if _looks_like_host(r1) and _is_valid_port(r2):
                return f"{scheme}://{left}@{r1}:{r2}"
            # برعکس: host:port@user:pass
            if _looks_like_host(l1) and _is_valid_port(l2):
                return f"{scheme}://{right}@{l1}:{l2}"
        return None

    parts = s.split(":")
    # حالت ۲: بدون احراز هویت (host:port)
    if len(parts) == 2:
        h, p = parts[0], parts[1]
        if _looks_like_host(h) and _is_valid_port(p):
            return f"{scheme}://{h}:{p}"
        return None

    # حالت ۳: ۴ بخشی (host:port:user:pass یا user:pass:host:port)
    if len(parts) >= 4:
        # بررسی host:port:user:pass
        if _looks_like_host(parts[0]) and _is_valid_port(parts[1]):
            host, port = parts[0], parts[1]
            user = parts[2]
            pw = ":".join(parts[3:])
            return f"{scheme}://{user}:{pw}@{host}:{port}"
        # بررسی user:pass:host:port
        if _looks_like_host(parts[-2]) and _is_valid_port(parts[-1]):
            host, port = parts[-2], parts[-1]
            user = parts[0]
            pw = ":".join(parts[1:-2])
            return f"{scheme}://{user}:{pw}@{host}:{port}"

    return None


def extract_proxies_from_text_or_url(content: str) -> list[str]:
    """
    پارس کردن متن ارسالی کاربر؛ اگر داخل متن لینک API دریافت پروکسی (مثل JoyProxy)
    وجود داشته باشد، ابتدا محتوای لینک را دانلود کرده و سپس پروکسی‌ها را استخراج می‌کند.
    """
    raw_lines = []
    for line in content.splitlines():
        line_str = line.strip()
        if not line_str:
            continue

        # بررسی اینکه آیا این خط یک لینک وب/API برای استخراج لیست پروکسی است
        if (line_str.startswith("http://") or line_str.startswith("https://")) and (
            "/" in line_str.split("://", 1)[1] or "?" in line_str
        ):
            try:
                res = requests.get(line_str, timeout=20)
                if res.status_code == 200 and res.text:
                    raw_lines.extend(res.text.splitlines())
                    continue
            except Exception:
                pass

        raw_lines.append(line_str)

    parsed_proxies = []
    seen = set()
    for item in raw_lines:
        # پشتیبانی از جداشدن با فاصله یا کاما در یک خط
        for token in re.split(r"[\s,;]+", item.strip()):
            if not token:
                continue
            norm = normalize_single_proxy(token)
            if norm and norm not in seen:
                seen.add(norm)
                parsed_proxies.append(norm)

    return parsed_proxies


def load_saved_proxies():
    global PROXY_LIST
    if os.path.exists(CUSTOM_PROXIES_FILE):
        try:
            with open(CUSTOM_PROXIES_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, list) and len(data) > 0:
                with PROXY_LOCK:
                    PROXY_LIST = data
        except Exception:
            pass


def save_custom_proxies(new_proxies: list[str]):
    global PROXY_LIST
    with PROXY_LOCK:
        PROXY_LIST = list(new_proxies)
    try:
        with open(CUSTOM_PROXIES_FILE, "w", encoding="utf-8") as f:
            json.dump(PROXY_LIST, f, ensure_ascii=False, indent=2)
    except Exception:
        pass


def reset_to_default_proxies():
    global PROXY_LIST
    with PROXY_LOCK:
        PROXY_LIST = list(DEFAULT_PROXY_LIST)
    if os.path.exists(CUSTOM_PROXIES_FILE):
        try:
            os.remove(CUSTOM_PROXIES_FILE)
        except Exception:
            pass


def get_random_proxy():
    with PROXY_LOCK:
        if not PROXY_LIST:
            return None
        selected = random.choice(PROXY_LIST)
    return {"http": selected, "https": selected}


# بارگذاری پروکسی‌های ذخیره‌شده هنگام روشن شدن ربات
load_saved_proxies()


# ==================== توابع اصلی عملیات اکانت و اوکالا ====================

def fetch_data(url):
    for attempt in range(3):
        try:
            res = requests.get(url, timeout=20)
            if res.status_code == 200:
                return res.json()
        except Exception:
            pass
        try:
            res = requests.get(url, proxies=get_random_proxy(), timeout=20)
            if res.status_code == 200:
                return res.json()
        except Exception:
            pass
        time.sleep(1.0 + attempt * 0.5)
    return None


def get_tokens_from_data(data):
    access_token, refresh_token = None, None
    try:
        for cookie in data.get('cookies', []):
            if cookie.get('name') == 'tokenMS':
                access_token = cookie.get('value')
            elif cookie.get('name') == 'refresh_token':
                refresh_token = cookie.get('value')
        if not access_token or not refresh_token:
            for origin in data.get('origins', []):
                for item in origin.get('localStorage', []):
                    if item.get('name') == 'tokenMS':
                        access_token = item.get('value')
                    elif item.get('name') == 'refresh_token':
                        refresh_token = item.get('value')
    except Exception:
        pass
    return access_token, refresh_token


def update_tokens_in_data(data, old_acc, new_acc, old_ref, new_ref):
    try:
        content = json.dumps(data, ensure_ascii=False)
        if old_acc and new_acc:
            content = content.replace(old_acc, new_acc)
        if old_ref and new_ref:
            content = content.replace(old_ref, new_ref)
        return json.loads(content)
    except Exception:
        return data


def update_map_info_in_data(data, new_lat, new_lng, new_address_text):
    """همگام‌سازی مختصات جدید در localStorage اکانت هدف (در صورت وجود)"""
    try:
        for origin in data.get('origins', []):
            for item in origin.get('localStorage', []):
                if item.get('name') == 'mapInfo' and item.get('value'):
                    map_info = json.loads(item['value'])
                    if isinstance(map_info, dict):
                        if 'selectedCity' in map_info and isinstance(map_info['selectedCity'], dict):
                            map_info['selectedCity']['lat'] = new_lat
                            map_info['selectedCity']['lng'] = new_lng
                        if 'lat' in map_info:
                            map_info['lat'] = new_lat
                        if 'lng' in map_info:
                            map_info['lng'] = new_lng
                        if 'address' in map_info and new_address_text:
                            map_info['address'] = new_address_text
                        item['value'] = json.dumps(map_info, ensure_ascii=False)
    except Exception:
        pass
    return data


def get_user_id_from_token(token):
    try:
        payload = token.split('.')[1]
        payload += '=' * (-len(payload) % 4)
        decoded_bytes = base64.urlsafe_b64decode(payload)
        data = json.loads(decoded_bytes)
        
        uid = data.get('userId') or data.get('alternativeCustomerId')
        if uid:
            return int(uid) 
        return 0
    except Exception:
        return 0


def generate_unique_addresses(base_addr, count, min_meters=MIN_OFFSET_METERS, max_meters=MAX_OFFSET_METERS):
    """
    تولید مختصات، پلاک و واحد کاملاً غیرتکراری برای تمام اکانت‌ها (مثلاً ۱۵۰ اکانت)
    با حرکت چرخشی (بالا، پایین، راست، چپ و قطرها) در شعاع بسیار نزدیک (۸ تا ۴۵ متر)
    تا فروشگاه به هیچ عنوان از محدوده خارج نشود.
    """
    base_lat = float(base_addr['lat'])
    base_lng = float(base_addr['lng'])
    base_text = base_addr.get('address', 'آدرس ثبت شده از نقشه')
    base_plaque = str(base_addr.get('plaque', '0'))
    base_unit = str(base_addr.get('unit', '1'))

    meters_to_lat = 1.0 / 111111.0
    cos_lat = math.cos(math.radians(base_lat))
    meters_to_lng = 1.0 / (111111.0 * max(cos_lat, 0.2))

    directions = [
        (1.0, 0.0, "بالا (شمال)"),
        (-1.0, 0.0, "پایین (جنوب)"),
        (0.0, 1.0, "راست (شرق)"),
        (0.0, -1.0, "چپ (غرب)"),
        (0.7071, 0.7071, "بالا-راست"),
        (-0.7071, -0.7071, "پایین-چپ"),
        (0.7071, -0.7071, "بالا-چپ"),
        (-0.7071, 0.7071, "پایین-راست"),
    ]

    plaque_unit_pool = [
        (str(p), str(u))
        for p in range(1, 160)
        for u in range(1, 11)
        if not (str(p) == base_plaque and str(u) == base_unit)
    ]
    random.shuffle(plaque_unit_pool)

    total_rings = max(1, math.ceil(count / len(directions)))
    used_coords = {(round(base_lat, 6), round(base_lng, 6))}
    address_list = []

    for idx in range(count):
        dir_idx = idx % len(directions)
        ring_idx = idx // len(directions)
        d_lat_sign, d_lng_sign, dir_label = directions[dir_idx]

        if total_rings <= 1:
            base_dist = (min_meters + max_meters) / 2.0
        else:
            base_dist = min_meters + (max_meters - min_meters) * (ring_idx / (total_rings - 1))

        for _ in range(20):
            jitter_dist = base_dist + random.uniform(-1.5, 1.5)
            jitter_dist = max(min_meters * 0.8, min(max_meters, jitter_dist))

            perp_lat = -d_lng_sign * random.uniform(-2.0, 2.0)
            perp_lng = d_lat_sign * random.uniform(-2.0, 2.0)

            offset_north_m = d_lat_sign * jitter_dist + perp_lat
            offset_east_m = d_lng_sign * jitter_dist + perp_lng

            new_lat = round(base_lat + offset_north_m * meters_to_lat, 6)
            new_lng = round(base_lng + offset_east_m * meters_to_lng, 6)

            if (new_lat, new_lng) not in used_coords:
                used_coords.add((new_lat, new_lng))
                break

        plaque_val, unit_val = plaque_unit_pool[idx % len(plaque_unit_pool)]

        address_list.append({
            'lat': new_lat,
            'lng': new_lng,
            'address': base_text,
            'plaque': plaque_val,
            'unit': unit_val,
            'direction': dir_label,
            'distance_m': round(math.hypot(
                (new_lat - base_lat) / meters_to_lat,
                (new_lng - base_lng) / meters_to_lng
            ), 1)
        })

    return address_list


class OkalaAPI:
    def __init__(self):
        self.request_logs = []
        self.log_lock = threading.Lock()
        self.base_headers = {
            'accept': 'application/json, text/plain, */*',
            'source': 'okala',
            'ui-version': '2.0',
            'origin': 'https://www.okala.com',
            'sec-ch-ua': '"Chromium";v="137", "Not/A)Brand";v="24"',
            'sec-ch-ua-mobile': '?1',
            'sec-ch-ua-platform': '"Android"',
            'User-Agent': 'Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 Chrome/137.0.0.0 Mobile'
        }

    def log_request(self, method, url, status_code, response_text):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        short_resp = str(response_text)
        if len(short_resp) > 600:
            short_resp = short_resp[:600] + "... [TRUNCATED]"
        log_entry = f"[{timestamp}] {method} {url}\nStatus: {status_code}\nResponse: {short_resp}\n{'-'*50}\n"
        with self.log_lock:
            self.request_logs.append(log_entry)

    def make_request(self, method, url, access_token=None, **kwargs):
        headers = self.base_headers.copy()
        headers['X-Correlation-Id'] = str(uuid.uuid4())
        headers['X-User-Unique-Id'] = str(uuid.uuid4())
        headers['session-id'] = str(uuid.uuid4())

        if access_token:
            headers['Authorization'] = f'Bearer {access_token}'

        if 'headers' in kwargs:
            headers.update(kwargs.pop('headers'))

        last_status, last_resp = 0, "Network Error"
        for attempt in range(4):
            current_proxy = get_random_proxy()
            try:
                res = requests.request(method, url, headers=headers, proxies=current_proxy, timeout=35, **kwargs)
                self.log_request(method, url, res.status_code, res.text)
                
                if res.status_code == 200:
                    try:
                        return 200, res.json()
                    except Exception:
                        return 200, {}
                elif res.status_code == 401:
                    return 401, {}
                elif res.status_code in (429, 500, 502, 503, 504):
                    last_status, last_resp = res.status_code, res.text
                    time.sleep(1.2 + attempt * 0.8)
                    continue
                else:
                    return res.status_code, res.text 
            except Exception as e:
                self.log_request(method, url, "EXCEPTION", str(e))
                time.sleep(1.2 + attempt * 0.5)
                continue
                
        return last_status, last_resp

    def refresh_token(self, refresh_token):
        url = "https://apigateway.okala.com/api/v1/accounts/tokens"
        data = {
            "grant_type": "refresh_token",
            "client_id": "customer_client_id",
            "client_secret": "u_M{'57j!%LI21#",
            "scope": "offline_access",
            "refresh_token": refresh_token
        }
        headers = {"content-type": "application/x-www-form-urlencoded"}
        status, response_data = self.make_request('POST', url, headers=headers, data=data)
        if status == 200 and isinstance(response_data, dict):
            return response_data.get('access_token'), response_data.get('refresh_token')
        return None, None

    def get_address(self, token, uid):
        url = 'https://apigateway.okala.com/api/voyager/CustomerAddress/CustomerAddressForReact'
        return self.make_request('GET', url, token, params={'customerId': uid})

    def add_address(self, token, uid, addr_data):
        url = 'https://apigateway.okala.com/api/voyager/C/CustomerAccount/AddAddress/'
        
        plaque_val = addr_data.get('plaque', '1')
        unit_val = addr_data.get('unit', '1')
        address_text = addr_data.get('address', 'آدرس ثبت شده از نقشه')

        payload = {
            'id': 0, 
            'customerId': uid, 
            'mobilePhone': '', 
            'ShoppingSectorPartId': '0',
            'shoppingSectorId': '0', 
            'plaque': str(plaque_val), 
            'unit': str(unit_val), 
            'lat': float(addr_data['lat']),
            'lng': float(addr_data['lng']), 
            'title': None, 
            'addressTypeId': 3, 
            'oprationDuration': random.randint(10000, 20000), 
            'address': address_text,
            'mapPlatform': 'ParsiMap'
        }
        return self.make_request('POST', url, token, json=payload)

    def get_stores(self, token, lat, lng, uid):
        url = 'https://apigateway.okala.com/api/opex/v4/stores/nearby'
        params = {'latitude': lat, 'longitude': lng}
        return self.make_request('GET', url, token, params=params)

    def get_cart(self, token, uid, store_ids):
        url = 'https://apigateway.okala.com/api/Basket/v4/ShoppingCart/GetCustomerShoppingCartItems'
        params = {'CustomerId': uid, 'StoreIds': store_ids, 'isFromCartPage': 'false'}
        return self.make_request('GET', url, token, params=params)

    def add_to_cart(self, token, uid, store_id, product_id):
        url = 'https://apigateway.okala.com/api/Basket/v2/ShoppingCart/AddToShoppingCart'
        payload = {
            'storeId': store_id, 'customerId': uid, 'productId': product_id, 'quantity': 1,
            'isSupplier': False, 'replaceItemMethodCode': -1, 'sectorId': '0', 'sectorPartId': '0',
            'productStoreId': '0', 'queryId': None
        }
        return self.make_request('POST', url, token, json=payload)


def verify_and_calibrate_radius(api, token, uid, base_addr, target_store_id):
    base_lat = float(base_addr['lat'])
    base_lng = float(base_addr['lng'])
    meters_to_lat = 1.0 / 111111.0
    cos_lat = math.cos(math.radians(base_lat))
    meters_to_lng = 1.0 / (111111.0 * max(cos_lat, 0.2))

    safe_max_radius = MAX_OFFSET_METERS
    for test_radius in (MAX_OFFSET_METERS, 25.0, 12.0):
        all_ok = True
        for d_lat, d_lng in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
            t_lat = round(base_lat + d_lat * test_radius * meters_to_lat, 6)
            t_lng = round(base_lng + d_lng * test_radius * meters_to_lng, 6)
            st_code, stores_res = api.get_stores(token, t_lat, t_lng, uid)
            if st_code == 200 and isinstance(stores_res, dict):
                stores = stores_res.get('data', {}).get('stores', [])
                store_ids = [s.get('storeId') for s in stores]
                if target_store_id not in store_ids:
                    all_ok = False
                    break
        if all_ok:
            safe_max_radius = test_radius
            break

    return min(MIN_OFFSET_METERS, safe_max_radius * 0.4), safe_max_radius


def worker_copy_basket(index, target_url, api, template_data, assigned_addr):
    time.sleep(random.uniform(0.1, 0.8))
    
    data = fetch_data(target_url)
    if not data:
        return index, target_url, "error_fetch", None, assigned_addr
    
    acc_token, ref_token = get_tokens_from_data(data)
    if not acc_token:
        return index, target_url, "error_token", data, assigned_addr

    uid = get_user_id_from_token(acc_token)
    if not uid or uid == 0:
        return index, target_url, "error_uuid", data, assigned_addr

    status, response_data = api.add_address(acc_token, uid, assigned_addr)
    
    if status == 401 and ref_token:
        new_acc, new_ref = api.refresh_token(ref_token)
        if new_acc:
            data = update_tokens_in_data(data, acc_token, new_acc, ref_token, new_ref)
            acc_token = new_acc
            ref_token = new_ref or ref_token
            status, response_data = api.add_address(acc_token, uid, assigned_addr)

    if status != 200:
        return index, target_url, "error_address", data, assigned_addr

    data = update_map_info_in_data(
        data,
        assigned_addr['lat'],
        assigned_addr['lng'],
        assigned_addr['address']
    )

    added_count = 0
    for item in template_data['items']:
        for _ in range(item['quantity']):
            c_status, _ = api.add_to_cart(acc_token, uid, template_data['store_id'], item['productId'])
            if c_status == 401 and ref_token:
                new_acc, new_ref = api.refresh_token(ref_token)
                if new_acc:
                    data = update_tokens_in_data(data, acc_token, new_acc, ref_token, new_ref)
                    acc_token = new_acc
                    ref_token = new_ref or ref_token
                    c_status, _ = api.add_to_cart(acc_token, uid, template_data['store_id'], item['productId'])
            if c_status == 200:
                added_count += 1
            time.sleep(random.uniform(0.25, 0.65))

    if added_count == 0 and len(template_data['items']) > 0:
        return index, target_url, "error_cart", data, assigned_addr

    return index, target_url, "success", data, assigned_addr


def process_all_links(session_dir, template_url, target_urls, progress_state=None):
    api = OkalaAPI()

    template_data_json = fetch_data(template_url)
    if not template_data_json:
        return None, None, "خطا: امکان دریافت اطلاعات اکانت مرجع (اولین لینک) وجود ندارد."

    t_acc, t_ref = get_tokens_from_data(template_data_json)
    t_uid = get_user_id_from_token(t_acc)

    if not t_uid or t_uid == 0:
        return None, None, "خطا: ساختار توکن اکانت مرجع معتبر نمی‌باشد."

    status, addr_res = api.get_address(t_acc, t_uid)
    if status == 401 and t_ref:
        new_t_acc, new_t_ref = api.refresh_token(t_ref)
        if new_t_acc:
            template_data_json = update_tokens_in_data(template_data_json, t_acc, new_t_acc, t_ref, new_t_ref)
            t_acc = new_t_acc
            t_ref = new_t_ref or t_ref
            status, addr_res = api.get_address(t_acc, t_uid)

    template_addr = None
    if status == 200 and isinstance(addr_res, dict) and addr_res.get('data'):
        template_addr = addr_res['data'][0]
    else:
        api.log_request("INFO", "TemplateAddressFallback", 200, "No saved address found for template account. Using mapInfo as fallback.")
        lat, lng = 35.69975, 51.33551
        addr_text = "آدرس استخراج شده از نقشه"
        try:
            for origin in template_data_json.get('origins', []):
                for item in origin.get('localStorage', []):
                    if item.get('name') == 'mapInfo':
                        map_info = json.loads(item.get('value'))
                        if 'selectedCity' in map_info:
                            lat = map_info['selectedCity']['lat']
                            lng = map_info['selectedCity']['lng']
                            addr_text = map_info['selectedCity'].get('name', addr_text)
        except Exception as e:
            api.log_request("ERROR", "ParseMapInfo", 0, str(e))
            
        template_addr = {
            'lat': lat,
            'lng': lng,
            'address': addr_text,
            'plaque': '1',
            'unit': '1'
        }

    status, stores_res = api.get_stores(t_acc, template_addr['lat'], template_addr['lng'], t_uid)
    if status != 200 or not isinstance(stores_res, dict) or not stores_res.get('data', {}).get('stores'):
        return None, api.request_logs, "خطا: هیچ فروشگاهی برای مختصات اکانت مرجع یافت نشد."

    store_ids = [s['storeId'] for s in stores_res['data']['stores']]

    status, cart_res = api.get_cart(t_acc, t_uid, store_ids)
    if status != 200 or not isinstance(cart_res, dict) or not cart_res.get('data', {}).get('result'):
        return None, api.request_logs, "خطا: امکان بازیابی سبد خرید اکانت مرجع وجود ندارد."

    cart_data = cart_res['data']['result'][0]
    cart_items = cart_data.get('items', [])
    cart_store_id = cart_data.get('storeId')
    cart_store_name = cart_data.get('storeName', str(cart_store_id))

    if not cart_items:
        return None, api.request_logs, "خطا: سبد خرید اکانت مرجع خالی است."

    base_addr_info = {
        'lat': template_addr['lat'],
        'lng': template_addr['lng'],
        'address': template_addr.get('address', 'آدرس ثبت شده'),
        'plaque': template_addr.get('plaque', '1'),
        'unit': template_addr.get('unit', '1')
    }

    safe_min_m, safe_max_m = verify_and_calibrate_radius(
        api, t_acc, t_uid, base_addr_info, cart_store_id
    )

    unique_addresses = generate_unique_addresses(
        base_addr_info,
        len(target_urls),
        min_meters=safe_min_m,
        max_meters=safe_max_m
    )

    template_data = {
        'address': base_addr_info,
        'store_id': cart_store_id,
        'store_name': cart_store_name,
        'safe_max_m': safe_max_m,
        'items': cart_items
    }

    stats = {
        "total_targets": len(target_urls), 
        "completed": 0,
        "success": 0, 
        "error_fetch": 0, 
        "error_address": 0, 
        "error_cart": 0, 
        "error_token": 0
    }
    if progress_state is not None:
        progress_state.update(stats)
        progress_state["store_name"] = cart_store_name
    
    updated_dir = os.path.join(session_dir, "Updated_Accounts")
    os.makedirs(updated_dir, exist_ok=True)

    with open(os.path.join(updated_dir, "000_template_account.json"), "w", encoding="utf-8") as f:
        json.dump(template_data_json, f, ensure_ascii=False, indent=2)

    address_report_lines = [
        f"فروشگاه مرجع: {cart_store_name} (ID: {cart_store_id})",
        f"مختصات پایه: {base_addr_info['lat']}, {base_addr_info['lng']}",
        f"شعاع ایمن جابجایی: {safe_min_m:.1f} تا {safe_max_m:.1f} متر",
        "=" * 70
    ]

    used_filenames = set()
    results_by_index = {}

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {
            executor.submit(
                worker_copy_basket,
                idx,
                url,
                api,
                template_data,
                unique_addresses[idx]
            ): (idx, url)
            for idx, url in enumerate(target_urls)
        }
        
        for future in as_completed(futures):
            idx, url = futures[future]
            try:
                _, _, result, updated_json, addr_used = future.result()
                if result == "success":
                    stats["success"] += 1
                elif result == "error_fetch":
                    stats["error_fetch"] += 1
                elif result in ["error_token", "error_uuid"]:
                    stats["error_token"] += 1
                elif result == "error_address":
                    stats["error_address"] += 1
                elif result == "error_cart":
                    stats["error_cart"] += 1
                
                if updated_json:
                    raw_name = url.strip('/').split('/')[-1]
                    raw_name = re.sub(r'[^a-zA-Z0-9_\-]', '_', raw_name)
                    if not raw_name or len(raw_name) < 3:
                        raw_name = f"target_{idx + 1:03d}"
                    file_name = raw_name
                    if file_name in used_filenames:
                        file_name = f"{idx + 1:03d}_{raw_name}"
                    used_filenames.add(file_name)

                    with open(os.path.join(updated_dir, f"{file_name}.json"), "w", encoding="utf-8") as f:
                        json.dump(updated_json, f, ensure_ascii=False, indent=2)

                results_by_index[idx] = (
                    f"[{idx + 1:03d}] وضعیت: {result} | جهت: {addr_used['direction']} ({addr_used['distance_m']}m) | "
                    f"مختصات: ({addr_used['lat']}, {addr_used['lng']}) | "
                    f"پلاک: {addr_used['plaque']} - واحد: {addr_used['unit']} | لینک: {url}"
                )
            except Exception as e:
                stats["error_fetch"] += 1
                results_by_index[idx] = f"[{idx + 1:03d}] وضعیت: exception ({e}) | لینک: {url}"

            stats["completed"] += 1
            if progress_state is not None:
                progress_state.update(stats)

    for idx in sorted(results_by_index.keys()):
        address_report_lines.append(results_by_index[idx])

    with open(os.path.join(updated_dir, "_addresses_report.txt"), "w", encoding="utf-8") as f:
        f.write("\n".join(address_report_lines))

    final_zip_base = os.path.join(session_dir, "Updated_Accounts_Data")
    final_zip_path = shutil.make_archive(final_zip_base, 'zip', updated_dir)

    return (final_zip_path, template_data, stats), api.request_logs, None


async def execute_batch_session(message: Message, urls: list[str]):
    unique_urls = list(dict.fromkeys(urls))

    if len(unique_urls) < 2:
        await message.answer("خطا: لطفاً حداقل ۲ لینک (یک الگو و حداقل یک هدف) ارسال کنید.")
        return

    template_url = unique_urls[0]
    target_urls = unique_urls[1:]

    msg = await message.answer(
        f"⏳ در حال پردازش...\n"
        f"اکانت مرجع دریافت شد.\n"
        f"تعداد کل اکانت‌های هدف: {len(target_urls)}\n"
        f"🌐 پروکسی‌های فعال: {len(PROXY_LIST)} عدد"
    )

    session_id = str(uuid.uuid4())
    session_dir = os.path.join(SESSION_BASE_DIR, session_id)
    os.makedirs(session_dir, exist_ok=True)

    progress_state = {
        "total_targets": len(target_urls),
        "completed": 0,
        "success": 0,
        "error_fetch": 0,
        "error_address": 0,
        "error_cart": 0,
        "error_token": 0,
        "store_name": "..."
    }

    task = asyncio.create_task(
        asyncio.to_thread(process_all_links, session_dir, template_url, target_urls, progress_state)
    )

    last_reported_completed = -1
    while not task.done():
        await asyncio.sleep(5.0)
        if task.done():
            break
        comp = progress_state.get("completed", 0)
        total = progress_state.get("total_targets", len(target_urls))
        if comp != last_reported_completed and comp > 0:
            last_reported_completed = comp
            try:
                await msg.edit_text(
                    f"⏳ در حال مدیریت و ثبت آدرس اکانت‌ها...\n\n"
                    f"🏪 فروشگاه: {progress_state.get('store_name', '...')}\n"
                    f"📊 پیشرفت: {comp} از {total}\n"
                    f"🟢 موفق: {progress_state.get('success', 0)} | "
                    f"🔴 خطا: {comp - progress_state.get('success', 0)}"
                )
            except Exception:
                pass

    result_data, logs, error_msg = await task

    log_file_path = os.path.join(session_dir, "debug_report.txt")
    if logs:
        with open(log_file_path, "w", encoding="utf-8") as f:
            f.write("\n".join(logs))

    if error_msg:
        try:
            await msg.edit_text(error_msg)
        except Exception:
            await message.answer(error_msg)
        if os.path.exists(log_file_path):
            await message.answer_document(document=FSInputFile(log_file_path), caption="فایل گزارش خطاها (Debug Log)")
        shutil.rmtree(session_dir, ignore_errors=True)
        return

    final_zip_path, template_data, stats = result_data
    try:
        await msg.delete()
    except Exception:
        pass

    total_qty = sum(item['quantity'] for item in template_data['items'])

    report_text = (
        "✅ گزارش عملکرد همگام‌سازی و مدیریت آدرس‌ها:\n\n"
        f"🏪 فروشگاه: {template_data.get('store_name', template_data['store_id'])}\n"
        f"📍 شعاع جابجایی ایمن: حداکثر {template_data.get('safe_max_m', MAX_OFFSET_METERS):.0f} متر (پلاک و واحد متغیر)\n"
        f"🛒 اقلام مرجع: {len(template_data['items'])} مدل (مجموع: {total_qty} عدد)\n\n"
        f"👥 تعداد کل اهداف: {stats['total_targets']}\n"
        f"🟢 موفق: {stats['success']}\n"
        f"🔴 خطای دریافت از لینک: {stats['error_fetch']}\n"
        f"🔴 خطای ثبت آدرس: {stats['error_address']}\n"
        f"🔴 خطای افزودن کالا: {stats['error_cart']}\n"
        f"🔴 خطای احراز هویت / توکن: {stats['error_token']}\n\n"
        "فایل ZIP اکانت‌ها (همراه با گزارش مختصات و پلاک هر اکانت) و فایل Debug پیوست شدند."
    )

    await message.answer_document(document=FSInputFile(final_zip_path), caption=report_text)
    if os.path.exists(log_file_path):
        await message.answer_document(document=FSInputFile(log_file_path), caption="گزارش کامل درخواست‌ها و پاسخ‌های سرور (Debug Log)")
    
    shutil.rmtree(session_dir, ignore_errors=True)


# ==================== هندلرهای تلگرام ====================

@router.message(Command("start"))
async def cmd_start(message: Message):
    user_id = message.from_user.id if message.from_user else message.chat.id
    WAITING_FOR_PROXY_USERS.discard(user_id)
    await message.answer(
        "سیستم همگام‌سازی سبد خرید و مدیریت هوشمند آدرس‌ها فعال است.\n\n"
        "📥 **ارسال اکانت‌ها:**\n"
        "لیست لینک‌های خود (مثلاً ۱۵۰ اکانت) را در یک یا چند پیام پیاپی و یا در قالب فایل `.txt` بفرستید (اولین لینک = اکانت مرجع).\n\n"
        "🌐 **مدیریت پروکسی‌ها:**\n"
        "• `/proxy` : ثبت یا جایگزینی پروکسی‌های جدید (با متن، فایل `.txt` یا لینک API)\n"
        "• `/proxies` : مشاهده وضعیت و تعداد پروکسی‌های فعال\n"
        "• `/reset_proxy` : بازگشت به پروکسی‌های پیش‌فرض"
    )


@router.message(Command("proxy", "setproxy"))
async def cmd_set_proxy(message: Message):
    user_id = message.from_user.id if message.from_user else message.chat.id

    # اگر کاربر در همان دستور /proxy، متن یا لینک پروکسی را هم جلوی دستور نوشته باشد
    parts = (message.text or "").split(maxsplit=1)
    if len(parts) > 1 and parts[1].strip():
        wait_msg = await message.answer("⏳ در حال بررسی و استخراج پروکسی‌ها...")
        extracted = await asyncio.to_thread(extract_proxies_from_text_or_url, parts[1])
        if extracted:
            save_custom_proxies(extracted)
            WAITING_FOR_PROXY_USERS.discard(user_id)
            await wait_msg.edit_text(
                f"✅ تعداد **{len(extracted)}** پروکسی با موفقیت استخراج و جایگزین شد.\n"
                f"نمونه: `{extracted[0]}`",
                parse_mode="Markdown"
            )
        else:
            await wait_msg.edit_text("❌ هیچ پروکسی معتبری در ورودی شما یافت نشد.")
        return

    WAITING_FOR_PROXY_USERS.add(user_id)
    await message.answer(
        "🌐 لطفاً لیست پروکسی‌های جدید را ارسال کنید:\n\n"
        "می‌توانید به یکی از ۳ روش زیر بفرستید:\n"
        "1️⃣ **لینک API پروکسی** (مثل لینک استخراج JoyProxy)\n"
        "2️⃣ **فایل `.txt`** حاوی پروکسی‌ها\n"
        "3️⃣ **متن مستقیم** پروکسی‌ها در پیام\n\n"
        "📌 تمام فرمت‌ها (`ip:port:user:pass`، `user:pass@host:port`، `http://...`) به صورت خودکار پشتیبانی می‌شوند.\n"
        "برای انصراف `/cancel` بزنید."
    )


@router.message(Command("cancel"))
async def cmd_cancel(message: Message):
    user_id = message.from_user.id if message.from_user else message.chat.id
    if user_id in WAITING_FOR_PROXY_USERS:
        WAITING_FOR_PROXY_USERS.discard(user_id)
        await message.answer("✅ عملیات ثبت پروکسی لغو شد.")
    else:
        await message.answer("عملیات فعالی برای لغو وجود ندارد.")


@router.message(Command("proxies"))
async def cmd_show_proxies(message: Message):
    with PROXY_LOCK:
        count = len(PROXY_LIST)
        sample = PROXY_LIST[:3]
    is_custom = os.path.exists(CUSTOM_PROXIES_FILE)
    mode_str = "سفارشی (ارسال‌شده توسط کاربر)" if is_custom else "پیش‌فرض سیستم"
    sample_text = "\n".join(f"• `{p}`" for p in sample)
    await message.answer(
        f"🌐 **وضعیت پروکسی‌های فعال:**\n\n"
        f"• نوع لیست: {mode_str}\n"
        f"• تعداد کل: **{count}** پروکسی\n\n"
        f"نمونه:\n{sample_text}",
        parse_mode="Markdown"
    )


@router.message(Command("reset_proxy"))
async def cmd_reset_proxy(message: Message):
    user_id = message.from_user.id if message.from_user else message.chat.id
    WAITING_FOR_PROXY_USERS.discard(user_id)
    reset_to_default_proxies()
    await message.answer(f"🔄 لیست پروکسی‌ها به حالت پیش‌فرض ({len(PROXY_LIST)} عدد) بازنشانی شد.")


@router.message(F.document)
async def handle_document_links(message: Message, bot: Bot):
    if not message.document or not message.document.file_name.lower().endswith(".txt"):
        return

    user_id = message.from_user.id if message.from_user else message.chat.id
    file_info = await bot.get_file(message.document.file_id)
    temp_path = os.path.join(SESSION_BASE_DIR, f"upload_{uuid.uuid4()}.txt")
    await bot.download_file(file_info.file_path, destination=temp_path)
    try:
        with open(temp_path, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)

    caption_text = (message.caption or "").strip().lower()
    is_proxy_mode = (
        user_id in WAITING_FOR_PROXY_USERS
        or "proxy" in message.document.file_name.lower()
        or "پروکسی" in caption_text
        or "proxy" in caption_text
    )

    if is_proxy_mode:
        wait_msg = await message.answer("⏳ در حال استخراج پروکسی‌ها از فایل...")
        extracted = await asyncio.to_thread(extract_proxies_from_text_or_url, content)
        if extracted:
            save_custom_proxies(extracted)
            WAITING_FOR_PROXY_USERS.discard(user_id)
            await wait_msg.edit_text(
                f"✅ تعداد **{len(extracted)}** پروکسی از فایل استخراج و جایگزین شد.\n"
                f"نمونه: `{extracted[0]}`",
                parse_mode="Markdown"
            )
            return
        elif user_id in WAITING_FOR_PROXY_USERS:
            await wait_msg.edit_text("❌ هیچ پروکسی معتبری در این فایل یافت نشد. دوباره تلاش کنید یا `/cancel` بزنید.")
            return
        else:
            await wait_msg.delete()

    urls = re.findall(r'(https?://\S+)', content)
    await execute_batch_session(message, urls)


@router.message(F.text)
async def handle_links_message(message: Message):
    user_id = message.from_user.id if message.from_user else message.chat.id
    text = (message.text or "").strip()

    if text in ("پروکسی", "ثبت پروکسی", "تغییر پروکسی"):
        await cmd_set_proxy(message)
        return

    # اگر کاربر در حالت انتظار برای ثبت پروکسی است
    if user_id in WAITING_FOR_PROXY_USERS:
        wait_msg = await message.answer("⏳ در حال بررسی و استخراج پروکسی‌ها...")
        extracted = await asyncio.to_thread(extract_proxies_from_text_or_url, text)
        if extracted:
            save_custom_proxies(extracted)
            WAITING_FOR_PROXY_USERS.discard(user_id)
            await wait_msg.edit_text(
                f"✅ تعداد **{len(extracted)}** پروکسی با موفقیت استخراج و فعال شد.\n"
                f"نمونه: `{extracted[0]}`",
                parse_mode="Markdown"
            )
        else:
            await wait_msg.edit_text(
                "❌ هیچ پروکسی معتبری در پیام شما پیدا نشد.\n"
                "لطفاً پروکسی‌ها، فایل `.txt` یا لینک API پروکسی را بفرستید و یا برای خروج `/cancel` بزنید."
            )
        return

    urls = re.findall(r'(https?://\S+)', text)
    if not urls:
        # اگر پیام شامل لینک عادی نیست، بررسی می‌کنیم آیا کاربر مستقیم لیست پروکسی فرستاده است
        possible_proxies = extract_proxies_from_text_or_url(text)
        if possible_proxies:
            save_custom_proxies(possible_proxies)
            await message.answer(
                f"✅ تعداد **{len(possible_proxies)}** پروکسی به صورت خودکار شناسایی و جایگزین شد.\n"
                f"نمونه: `{possible_proxies[0]}`",
                parse_mode="Markdown"
            )
        return

    # اگر تلگرام به خاطر محدودیت ۴۰۹۶ کاراکتر، ۱۵۰ لینک را به چند پیام پیاپی شکسته باشد،
    # پیام‌های ارسالی در بازه ۲.۵ ثانیه را با هم ادغام می‌کنیم تا همه با اولین لینک (مرجع) پردازش شوند.
    if user_id not in USER_BATCH_BUFFERS:
        USER_BATCH_BUFFERS[user_id] = {
            "urls": [],
            "message": message,
            "task": None
        }

    USER_BATCH_BUFFERS[user_id]["urls"].extend(urls)
    USER_BATCH_BUFFERS[user_id]["message"] = message

    existing_task = USER_BATCH_BUFFERS[user_id].get("task")
    if existing_task and not existing_task.done():
        existing_task.cancel()

    async def _delayed_run():
        await asyncio.sleep(2.5)
        batch = USER_BATCH_BUFFERS.pop(user_id, None)
        if batch and batch["urls"]:
            await execute_batch_session(batch["message"], batch["urls"])

    USER_BATCH_BUFFERS[user_id]["task"] = asyncio.create_task(_delayed_run())


async def main():
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher()
    dp.include_router(router)
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
