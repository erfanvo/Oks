import os
import shutil
import asyncio
import json
import base64
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

# ----------------- تنظیمات ادمین -----------------
# آیدی عددی تلگرام خود را در لیست زیر قرار دهید (مثال: [123456789])
# همچنین می‌توانید در Environment Variables متغیر ADMIN_IDS را تعریف کنید (با کاما جدا شود)
ADMIN_IDS = [
    int(x.strip()) for x in os.getenv("ADMIN_IDS", "").split(",") if x.strip().isdigit()
]
# اگر می‌خواهید مستقیم در کد وارد کنید، عدد آیدی خود را در خط زیر داخل کروشه بگذارید:
# ADMIN_IDS.extend([123456789])


def is_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS
# -------------------------------------------------

# لینک API دریافت پروکسی‌های موبایل ایران (JoyProxy)
JOYPROXY_API_URL = (
    "https://api.joyproxy.com/v2/extract?"
    "token=1c3af1e9f3ad0078c9ba2e8890734471b4b20d13fcd1983676f58ea24d8a76bd"
    "&count=200&duration=1m&country_geoname_id=130758"
    "&network_type=cellular&format=crlf&output=auth"
)

router = Router()

SESSION_BASE_DIR = "basket_sessions"
if os.path.exists(SESSION_BASE_DIR):
    shutil.rmtree(SESSION_BASE_DIR, ignore_errors=True)
os.makedirs(SESSION_BASE_DIR, exist_ok=True)

# ----------------- بخش مدیریت آمار کاربران -----------------
STATS_FILE = "usage_stats.json"
stats_lock = threading.Lock()


def load_usage_stats():
    if os.path.exists(STATS_FILE):
        try:
            with open(STATS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {"users": {}, "total_requests": 0, "total_links": 0}


def record_user_link_submission(user, links_count):
    with stats_lock:
        data = load_usage_stats()
        uid = str(user.id)
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        if uid not in data["users"]:
            data["users"][uid] = {
                "name": user.full_name,
                "username": user.username or "ندارد",
                "submissions": 0,
                "links_count": 0,
                "first_seen": now_str,
                "last_seen": now_str
            }

        data["users"][uid]["name"] = user.full_name
        data["users"][uid]["username"] = user.username or "ندارد"
        data["users"][uid]["submissions"] += 1
        data["users"][uid]["links_count"] += links_count
        data["users"][uid]["last_seen"] = now_str

        data["total_requests"] = data.get("total_requests", 0) + 1
        data["total_links"] = data.get("total_links", 0) + links_count

        try:
            with open(STATS_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception:
            pass
# -----------------------------------------------------------


class ProxyManager:
    def __init__(self, api_url):
        self.api_url = api_url
        self.proxies = []
        self.last_fetch = 0
        self.lock = threading.Lock()

    def _parse_proxy_line(self, line):
        line = line.strip()
        if not line:
            return None
        if line.startswith("http://") or line.startswith("https://") or line.startswith("socks5://"):
            return line
        if "@" in line:
            return f"http://{line}"
        parts = line.split(":")
        if len(parts) == 4:
            host, port, user, password = parts[0], parts[1], parts[2], parts[3]
            return f"http://{user}:{password}@{host}:{port}"
        elif len(parts) == 2:
            return f"http://{line}"
        return None

    def refresh_proxies(self):
        try:
            res = requests.get(self.api_url, timeout=20)
            if res.status_code == 200 and res.text.strip():
                raw_lines = res.text.strip().splitlines()
                parsed = []
                for line in raw_lines:
                    p = self._parse_proxy_line(line)
                    if p:
                        parsed.append(p)
                if parsed:
                    self.proxies = parsed
                    self.last_fetch = time.time()
                    return True
        except Exception:
            pass
        return False

    def get_proxy(self):
        with self.lock:
            if not self.proxies or (time.time() - self.last_fetch > 50):
                self.refresh_proxies()
            
            if self.proxies:
                selected = random.choice(self.proxies)
                return {"http": selected, "https": selected}
        return None


proxy_manager = ProxyManager(JOYPROXY_API_URL)


class UniqueAddressGenerator:
    """
    تضمین عدم تکرار مختصات، پلاک و واحد برای بیش از ۱۵۰ اکانت (بدون دستکاری متن آدرس)
    """
    def __init__(self):
        self.used_coords = set()
        self.used_plaque_unit = set()
        self.lock = threading.Lock()

    def generate(self, base_lat, base_lng, base_address_text):
        with self.lock:
            # ۱. تولید مختصات کاملاً یکتا در شعاع ۱۵ تا ۵۵ متری (بدون خروج از محدوده فروشگاه)
            while True:
                lat_offset = random.choice([-1, 1]) * random.uniform(0.00010, 0.00048)
                lng_offset = random.choice([-1, 1]) * random.uniform(0.00010, 0.00048)
                new_lat = round(float(base_lat) + lat_offset, 6)
                new_lng = round(float(base_lng) + lng_offset, 6)
                coord_key = (new_lat, new_lng)
                if coord_key not in self.used_coords:
                    self.used_coords.add(coord_key)
                    break

            # ۲. تولید ترکیب (پلاک، واحد) کاملاً یکتا برای هر اکانت
            while True:
                plaque_val = random.randint(1, 250)
                unit_val = random.randint(1, 16)
                pu_key = (plaque_val, unit_val)
                if pu_key not in self.used_plaque_unit:
                    self.used_plaque_unit.add(pu_key)
                    break

            return {
                'lat': new_lat,
                'lng': new_lng,
                'plaque': str(plaque_val),
                'unit': str(unit_val),
                'address': base_address_text,
                'addressTypeId': random.choice([1, 2, 3])
            }


def fetch_data(url):
    for attempt in range(4):
        try:
            res = requests.get(url, timeout=15)
            if res.status_code == 200:
                return res.json()
        except Exception:
            try:
                px = proxy_manager.get_proxy()
                res = requests.get(url, proxies=px, timeout=20)
                if res.status_code == 200:
                    return res.json()
            except Exception:
                pass
        time.sleep(1)
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
        log_entry = f"[{timestamp}] {method} {url}\nStatus: {status_code}\nResponse: {str(response_text)[:300]}\n{'-'*50}\n"
        with self.log_lock:
            self.request_logs.append(log_entry)

    def make_request(self, method, url, access_token=None, max_retries=6, **kwargs):
        headers = self.base_headers.copy()
        headers['X-Correlation-Id'] = str(uuid.uuid4())
        headers['X-User-Unique-Id'] = str(uuid.uuid4())
        headers['session-id'] = str(uuid.uuid4())

        if access_token:
            headers['Authorization'] = f'Bearer {access_token}'

        if 'headers' in kwargs:
            headers.update(kwargs.pop('headers'))

        last_status = 0
        last_text = "Network Error"

        for attempt in range(max_retries):
            current_proxy = proxy_manager.get_proxy()
            try:
                res = requests.request(
                    method, url, headers=headers, proxies=current_proxy, timeout=30, **kwargs
                )
                self.log_request(method, url, res.status_code, res.text)
                
                if res.status_code == 200:
                    try:
                        return 200, res.json()
                    except Exception:
                        return 200, {}
                elif res.status_code == 401:
                    return 401, {}
                else:
                    last_status = res.status_code
                    last_text = res.text
                    time.sleep(random.uniform(1.0, 2.5))
                    continue
            except Exception as e:
                self.log_request(method, url, f"EXCEPTION (Attempt {attempt+1})", str(e))
                time.sleep(random.uniform(1.0, 2.5))
                continue
                
        return last_status, last_text

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

    def add_address(self, token, uid, unique_addr):
        url = 'https://apigateway.okala.com/api/voyager/C/CustomerAccount/AddAddress/'
        payload = {
            'id': 0, 
            'customerId': uid, 
            'mobilePhone': '', 
            'ShoppingSectorPartId': '0',
            'shoppingSectorId': '0', 
            'plaque': unique_addr['plaque'], 
            'unit': unique_addr['unit'], 
            'lat': unique_addr['lat'],
            'lng': unique_addr['lng'], 
            'title': None, 
            'addressTypeId': unique_addr['addressTypeId'], 
            'oprationDuration': random.randint(8500, 24000), 
            'address': unique_addr['address'],
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


def worker_copy_basket(target_url, api, template_data, addr_generator):
    time.sleep(random.uniform(0.1, 1.2))
    
    data = fetch_data(target_url)
    if not data:
        return target_url, "error_fetch", None
    
    acc_token, ref_token = get_tokens_from_data(data)
    if not acc_token:
        return target_url, "error_token", data

    uid = get_user_id_from_token(acc_token)
    if not uid or uid == 0:
        return target_url, "error_uuid", data

    base_addr = template_data['address']
    unique_addr = addr_generator.generate(base_addr['lat'], base_addr['lng'], base_addr['address'])

    address_added = False
    for attempt in range(4):
        status, response_data = api.add_address(acc_token, uid, unique_addr)
        if status == 401 and ref_token:
            new_acc, new_ref = api.refresh_token(ref_token)
            if new_acc:
                data = update_tokens_in_data(data, acc_token, new_acc, ref_token, new_ref)
                acc_token, ref_token = new_acc, new_ref
                status, response_data = api.add_address(acc_token, uid, unique_addr)
        
        if status == 200:
            address_added = True
            break
        time.sleep(random.uniform(1.0, 2.5))

    if not address_added:
        return target_url, "error_address", data

    added_count = 0
    for item in template_data['items']:
        for _ in range(item['quantity']):
            for item_attempt in range(4):
                c_status, _ = api.add_to_cart(acc_token, uid, template_data['store_id'], item['productId'])
                if c_status == 401 and ref_token:
                    new_acc, new_ref = api.refresh_token(ref_token)
                    if new_acc:
                        data = update_tokens_in_data(data, acc_token, new_acc, ref_token, new_ref)
                        acc_token, ref_token = new_acc, new_ref
                        c_status, _ = api.add_to_cart(acc_token, uid, template_data['store_id'], item['productId'])
                
                if c_status == 200:
                    added_count += 1
                    break
                time.sleep(random.uniform(0.8, 1.8))
            time.sleep(random.uniform(0.3, 0.7))

    if added_count == 0 and len(template_data['items']) > 0:
        return target_url, "error_cart", data

    return target_url, "success", data


def process_all_links(session_dir, template_url, target_urls):
    proxy_manager.refresh_proxies()
    
    api = OkalaAPI()
    addr_generator = UniqueAddressGenerator()

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
            t_acc, t_ref = new_t_acc, new_t_ref
            status, addr_res = api.get_address(t_acc, t_uid)

    template_addr = None
    if status == 200 and isinstance(addr_res, dict) and addr_res.get('data'):
        template_addr = addr_res['data'][0]
    else:
        api.log_request("INFO", "Template Address", 0, "No saved address found. Using mapInfo fallback.")
        lat, lng = 36.2972, 59.6067
        addr_text = "آدرس انتخاب شده از روی نقشه"
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
            api.log_request("ERROR", "mapInfo parse", 0, str(e))
            
        template_addr = {
            'lat': lat,
            'lng': lng,
            'address': addr_text,
            'plaque': '5',
            'unit': '5'
        }

    addr_generator.used_coords.add((round(float(template_addr['lat']), 6), round(float(template_addr['lng']), 6)))

    status, stores_res = api.get_stores(t_acc, template_addr['lat'], template_addr['lng'], t_uid)
    if status != 200 or not isinstance(stores_res, dict) or not stores_res.get('data', {}).get('stores'):
        return None, api.request_logs, "خطا: هیچ فروشگاهی برای مختصات اکانت مرجع یافت نشد (یا پروکسی‌ها پاسخ ندادند)."

    store_ids = [s['storeId'] for s in stores_res['data']['stores']]

    status, cart_res = api.get_cart(t_acc, t_uid, store_ids)
    if status != 200 or not isinstance(cart_res, dict) or not cart_res.get('data', {}).get('result'):
        return None, api.request_logs, "خطا: امکان بازیابی سبد خرید اکانت مرجع وجود ندارد."

    cart_data = cart_res['data']['result'][0]
    cart_items = cart_data.get('items', [])
    cart_store_id = cart_data.get('storeId')

    if not cart_items:
        return None, api.request_logs, "خطا: سبد خرید اکانت مرجع خالی است."

    template_data = {
        'address': {
            'lat': template_addr['lat'],
            'lng': template_addr['lng'],
            'address': template_addr.get('address', 'آدرس ثبت شده'),
            'plaque': template_addr.get('plaque', '5'),
            'unit': template_addr.get('unit', '5')
        },
        'store_id': cart_store_id,
        'items': cart_items
    }

    stats = {
        "total_targets": len(target_urls), 
        "success": 0, 
        "error_fetch": 0, 
        "error_address": 0, 
        "error_cart": 0, 
        "error_token": 0
    }
    
    updated_dir = os.path.join(session_dir, "Updated_Accounts")
    os.makedirs(updated_dir, exist_ok=True)

    with open(os.path.join(updated_dir, "template_account.json"), "w", encoding="utf-8") as f:
        json.dump(template_data_json, f, ensure_ascii=False, indent=2)

    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = {
            executor.submit(worker_copy_basket, url, api, template_data, addr_generator): url 
            for url in target_urls
        }
        
        counter = 1
        for future in as_completed(futures):
            url = futures[future]
            try:
                _, result, updated_json = future.result()
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
                    file_name = url.strip('/').split('/')[-1]
                    if not file_name or len(file_name) < 5:
                        file_name = f"target_account_{counter}"
                    if not file_name.endswith(".json"):
                        file_name += ".json"
                    with open(os.path.join(updated_dir, file_name), "w", encoding="utf-8") as f:
                        json.dump(updated_json, f, ensure_ascii=False, indent=2)
                counter += 1
            except Exception:
                stats["error_fetch"] += 1

    final_zip_base = os.path.join(session_dir, "Updated_Accounts_Data")
    final_zip_path = shutil.make_archive(final_zip_base, 'zip', updated_dir)

    return (final_zip_path, template_data, stats), api.request_logs, None


@router.message(Command("start"))
async def cmd_start(message: Message):
    base_text = (
        "سیستم همگام‌سازی سبد خرید (مجهز به پروکسی چرخشی ایران JoyProxy) فعال است.\n\n"
        "لطفاً لیست لینک‌های خود را ارسال کنید.\n\n"
        "🟢 **اولین لینک:** اکانت مرجع (الگو)\n"
        "📍 **ضد تکرار صددرصدی:** مختصات نقشه، پلاک و واحد برای هر ۱۵۰+ اکانت به صورت کاملاً یکتا ثبت می‌شود.\n"
        "🔄 **تلاش مجدد خودکار:** در صورت بروز هرگونه خطای پروکسی یا شبکه، سیستم به صورت خودکار پروکسی را عوض کرده و مجدداً تلاش می‌کند."
    )
    if message.from_user and is_admin(message.from_user.id):
        base_text += "\n\n👑 **پنل ادمین:** برای مشاهده آمار کاربران دستور /stats را ارسال کنید."

    await message.answer(base_text)


@router.message(Command("myid"))
async def cmd_myid(message: Message):
    if message.from_user:
        await message.answer(f"🆔 آیدی عددی تلگرام شما:\n`{message.from_user.id}`")


@router.message(Command("stats"))
async def cmd_stats(message: Message):
    # بررسی دسترسی ادمین
    if not message.from_user or not is_admin(message.from_user.id):
        return  # نادیده گرفتن دستور برای کاربران غیر ادمین

    data = load_usage_stats()
    users = data.get("users", {})
    total_unique_users = len(users)
    total_requests = data.get("total_requests", 0)
    total_links = data.get("total_links", 0)

    if total_unique_users == 0:
        await message.answer("📊 تاکنون هیچ کاربری لینکی وارد ربات نکرده است.")
        return

    text = (
        f"📊 **گزارش آمار کاربران ربات (مخصوص ادمین):**\n\n"
        f"👥 **تعداد کل افراد منحصربه‌فرد:** `{total_unique_users}` نفر\n"
        f"🔄 **مجموع دفعات ارسال لیست:** `{total_requests}` بار\n"
        f"🔗 **مجموع کل لینک‌های وارد شده:** `{total_links}` لینک\n"
        f"{'-'*30}\n"
        f"👤 **لیست آخرین کاربران فعال:**\n\n"
    )

    sorted_users = sorted(
        users.items(), 
        key=lambda x: x[1].get("last_seen", ""), 
        reverse=True
    )

    for idx, (uid, info) in enumerate(sorted_users[:20], 1):
        name = info.get("name", "نامشخص")
        username = f"@{info['username']}" if info.get("username") != "ندارد" else "بدون یوزرنیم"
        subs = info.get("submissions", 0)
        links = info.get("links_count", 0)
        last_seen = info.get("last_seen", "-")
        text += (
            f"{idx}. **{name}** ({username}) | ID: `{uid}`\n"
            f"   ├ دفعات ارسال: {subs} بار | مجموع لینک: {links}\n"
            f"   └ آخرین فعالیت: `{last_seen}`\n\n"
        )

    await message.answer(text)


@router.message(F.text)
async def handle_links_message(message: Message):
    urls = re.findall(r'(https?://\S+)', message.text)
    
    if len(urls) < 2:
        await message.answer("خطا: لطفاً حداقل ۲ لینک (یک الگو و حداقل یک هدف) ارسال کنید.")
        return

    # ثبت اطلاعات کاربر و تعداد لینک‌های ارسالی در آمار[span_0](start_span)[span_0](end_span)
    if message.from_user:
        record_user_link_submission(message.from_user, len(urls))

    template_url = urls[0]
    target_urls = urls[1:]

    msg = await message.answer(
        f"⏳ در حال دریافت پروکسی‌های ایران و پردازش اکانت‌ها...\n"
        f"تعداد اهداف: {len(target_urls)} اکانت\n"
        f"لطفاً تا اتمام عملیات صبر کنید."
    )

    session_id = str(uuid.uuid4())
    session_dir = os.path.join(SESSION_BASE_DIR, session_id)
    os.makedirs(session_dir, exist_ok=True)
    
    result_data, logs, error_msg = await asyncio.to_thread(process_all_links, session_dir, template_url, target_urls)

    log_file_path = os.path.join(session_dir, "debug_report.txt")
    if logs:
        with open(log_file_path, "w", encoding="utf-8") as f:
            f.write("\n".join(logs))

    if error_msg:
        await msg.edit_text(error_msg)
        if os.path.exists(log_file_path):
            await message.answer_document(document=FSInputFile(log_file_path), caption="فایل گزارش خطاها (Debug Log)")
        shutil.rmtree(session_dir, ignore_errors=True)
        return

    final_zip_path, template_data, stats = result_data
    await msg.delete()

    total_qty = sum(item['quantity'] for item in template_data['items'])

    # بخش آمار در کپشن فقط برای ادمین نمایش داده می‌شود
    admin_stats_line = ""
    if message.from_user and is_admin(message.from_user.id):
        current_stats = load_usage_stats()
        total_users_count = len(current_stats.get("users", {}))
        admin_stats_line = f"📊 کل کاربران استفاده کننده تاکنون: {total_users_count} نفر\n\n"

    report_text = (
        "✅ گزارش عملکرد همگام‌سازی:\n\n"
        f"📦 تعداد اقلام مرجع: {len(template_data['items'])} مدل (مجموع: {total_qty} عدد)\n"
        f"🏪 کد فروشگاه (Store ID): {template_data['store_id']}\n\n"
        f"👥 تعداد کل اهداف: {stats['total_targets']}\n"
        f"🟢 موفق (با لوکیشن ۱۰۰٪ یکتا): {stats['success']}\n"
        f"🔴 خطای دریافت لینک: {stats['error_fetch']}\n"
        f"🔴 خطای ثبت آدرس: {stats['error_address']}\n"
        f"🔴 خطای افزودن کالا: {stats['error_cart']}\n"
        f"🔴 خطای احراز هویت / توکن: {stats['error_token']}\n\n"
        f"{admin_stats_line}"
        "فایل ZIP اکانت‌های آپدیت‌شده و گزارش Debug پیوست شدند."
    )

    await message.answer_document(document=FSInputFile(final_zip_path), caption=report_text)
    if os.path.exists(log_file_path):
        await message.answer_document(document=FSInputFile(log_file_path), caption="گزارش کامل درخواست‌ها و پاسخ‌های سرور (Debug Log)")
    
    shutil.rmtree(session_dir, ignore_errors=True)


async def main():
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher()
    dp.include_router(router)
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())

