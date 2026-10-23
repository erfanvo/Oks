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
import io
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


class ProxyManager:
    def __init__(self):
        self.api_url = None
        self.static_proxies = []
        self.proxies = []
        self.last_fetch = 0
        self.lock = threading.Lock()

    def _parse_proxy_line(self, line):
        line = line.strip()
        if not line:
            return None
        if line.startswith(("http://", "https://", "socks5://")):
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

    def set_api_url(self, url):
        with self.lock:
            self.api_url = url
            self.static_proxies = []
            self.proxies = []
            self.last_fetch = 0
        return self.refresh_proxies()

    def set_proxy_list(self, raw_text):
        parsed = []
        for line in raw_text.strip().splitlines():
            p = self._parse_proxy_line(line)
            if p:
                parsed.append(p)
        with self.lock:
            if parsed:
                self.static_proxies = parsed
                self.api_url = None
                self.proxies = parsed
                return len(parsed)
        return 0

    def refresh_proxies(self):
        if not self.api_url:
            return False
        try:
            res = requests.get(self.api_url, timeout=20)
            if res.status_code == 200 and res.text.strip():
                parsed = [
                    self._parse_proxy_line(line)
                    for line in res.text.strip().splitlines()
                    if self._parse_proxy_line(line)
                ]
                if parsed:
                    self.proxies = parsed
                    self.last_fetch = time.time()
                    return True
        except Exception:
            pass
        return False

    def get_proxy(self):
        with self.lock:
            if self.static_proxies:
                selected = random.choice(self.static_proxies)
                return {"http": selected, "https": selected}

            if self.api_url:
                if not self.proxies or (time.time() - self.last_fetch > 60):
                    self.refresh_proxies()
                if self.proxies:
                    selected = random.choice(self.proxies)
                    return {"http": selected, "https": selected}

        return None

    def count(self):
        with self.lock:
            if self.static_proxies:
                return len(self.static_proxies)
            if self.proxies:
                return len(self.proxies)
        return 0


proxy_manager = ProxyManager()


class UniqueAddressGenerator:
    def __init__(self):
        self.used_coords = set()
        self.used_plaque_unit = set()
        self.lock = threading.Lock()

    def generate(self, base_lat, base_lng, base_address_text):
        with self.lock:
            while True:
                lat_offset = random.choice([-1, 1]) * random.uniform(0.00010, 0.00048)
                lng_offset = random.choice([-1, 1]) * random.uniform(0.00010, 0.00048)
                new_lat = round(float(base_lat) + lat_offset, 6)
                new_lng = round(float(base_lng) + lng_offset, 6)
                coord_key = (new_lat, new_lng)
                if coord_key not in self.used_coords:
                    self.used_coords.add(coord_key)
                    break

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
            res = requests.get(url, timeout=20)
            if res.status_code == 200:
                return res.json()
        except Exception:
            try:
                px = proxy_manager.get_proxy()
                res = requests.get(url, proxies=px, timeout=25)
                if res.status_code == 200:
                    return res.json()
            except Exception:
                pass
        time.sleep(2.0)
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

    def make_request(self, method, url, access_token=None, max_retries=5, **kwargs):
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
                    time.sleep(random.uniform(2.5, 4.5))
                    continue
            except Exception as e:
                self.log_request(method, url, f"EXCEPTION (Attempt {attempt+1})", str(e))
                time.sleep(random.uniform(2.5, 4.5))
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
    time.sleep(random.uniform(2.0, 4.0))

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
        status, _ = api.add_address(acc_token, uid, unique_addr)
        if status == 401 and ref_token:
            new_acc, new_ref = api.refresh_token(ref_token)
            if new_acc:
                data = update_tokens_in_data(data, acc_token, new_acc, ref_token, new_ref)
                acc_token, ref_token = new_acc, new_ref
                status, _ = api.add_address(acc_token, uid, unique_addr)

        if status == 200:
            address_added = True
            break
        time.sleep(random.uniform(2.5, 4.5))

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
                time.sleep(random.uniform(2.0, 3.5))
            time.sleep(random.uniform(1.5, 2.5))

    if added_count == 0 and len(template_data['items']) > 0:
        return target_url, "error_cart", data

    return target_url, "success", data


def process_all_links(session_dir, template_url, target_urls):
    if proxy_manager.api_url:
        proxy_manager.refresh_proxies()

    api = OkalaAPI()
    addr_generator = UniqueAddressGenerator()

    template_data_json = fetch_data(template_url)
    if not template_data_json:
        return None, None, "خطا در دریافت اکانت مرجع."

    t_acc, t_ref = get_tokens_from_data(template_data_json)
    t_uid = get_user_id_from_token(t_acc)

    if not t_uid or t_uid == 0:
        return None, None, "خطا در توکن اکانت مرجع."

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
        lat, lng = 36.2972, 59.6067
        addr_text = "آدرس ثبت شده"
        try:
            for origin in template_data_json.get('origins', []):
                for item in origin.get('localStorage', []):
                    if item.get('name') == 'mapInfo':
                        map_info = json.loads(item.get('value'))
                        if 'selectedCity' in map_info:
                            lat = map_info['selectedCity']['lat']
                            lng = map_info['selectedCity']['lng']
                            addr_text = map_info['selectedCity'].get('name', addr_text)
        except Exception:
            pass

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
        return None, api.request_logs, "فروشگاهی برای اکانت مرجع یافت نشد."

    store_ids = [s['storeId'] for s in stores_res['data']['stores']]

    status, cart_res = api.get_cart(t_acc, t_uid, store_ids)
    if status != 200 or not isinstance(cart_res, dict) or not cart_res.get('data', {}).get('result'):
        return None, api.request_logs, "خطا در دریافت سبد خرید مرجع."

    cart_data = cart_res['data']['result'][0]
    cart_items = cart_data.get('items', [])
    cart_store_id = cart_data.get('storeId')

    if not cart_items:
        return None, api.request_logs, "سبد خرید مرجع خالی است."

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
        "failed": 0
    }

    updated_dir = os.path.join(session_dir, "Updated_Accounts")
    os.makedirs(updated_dir, exist_ok=True)

    with open(os.path.join(updated_dir, "template_account.json"), "w", encoding="utf-8") as f:
        json.dump(template_data_json, f, ensure_ascii=False, indent=2)

    # سرعت پایین‌تر و ترافیک کنترل‌شده با ۲ ورکر همزمان
    with ThreadPoolExecutor(max_workers=2) as executor:
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
                else:
                    stats["failed"] += 1

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
                stats["failed"] += 1

    final_zip_base = os.path.join(session_dir, "Updated_Accounts_Data")
    final_zip_path = shutil.make_archive(final_zip_base, 'zip', updated_dir)

    return (final_zip_path, stats), api.request_logs, None


@router.message(Command("start"))
async def cmd_start(message: Message):
    await message.answer(
        "ارسال پروکسی: فایل txt، متن پروکسی‌ها یا لینک API پروکسی\n"
        "اجرای عملیات: ارسال لینک‌های اکانت‌ها (لینک اول: مرجع، سایر لینک‌ها: مقصد)"
    )


@router.message(Command("proxy"))
async def cmd_proxy(message: Message):
    text = message.text.replace("/proxy", "").strip()
    if not text:
        count = proxy_manager.count()
        await message.answer(f"پروکسی‌های فعال: {count}")
        return

    if text.startswith(("http://", "https://")):
        if proxy_manager.set_api_url(text):
            await message.answer(f"لینک پروکسی ثبت شد ({proxy_manager.count()} پروکسی).")
        else:
            await message.answer("خطا در دریافت پروکسی از لینک.")
    else:
        saved = proxy_manager.set_proxy_list(text)
        if saved > 0:
            await message.answer(f"{saved} پروکسی ذخیره شد.")
        else:
            await message.answer("پروکسی معتبری یافت نشد.")


@router.message(F.document)
async def handle_proxy_file(message: Message, bot: Bot):
    if not message.document.file_name.endswith(('.txt', '.csv')):
        await message.answer("لطفاً فایل txt ارسال کنید.")
        return

    file_io = io.BytesIO()
    await bot.download(message.document, destination=file_io)
    content = file_io.getvalue().decode('utf-8', errors='ignore').strip()

    if content.startswith(("http://", "https://")) and len(content.splitlines()) == 1:
        if proxy_manager.set_api_url(content):
            await message.answer(f"لینک پروکسی ثبت شد ({proxy_manager.count()} پروکسی).")
        else:
            await message.answer("خطا در دریافت پروکسی از لینک.")
    else:
        saved = proxy_manager.set_proxy_list(content)
        if saved > 0:
            await message.answer(f"{saved} پروکسی ذخیره شد.")
        else:
            await message.answer("پروکسی معتبری در فایل یافت نشد.")


@router.message(F.text)
async def handle_text_message(message: Message):
    text = message.text.strip()

    # بررسی اگر پیام ارسالی پروکسی باشد (متن چندخطی یا پورت)
    if ":" in text and not text.startswith("http") and ("." in text):
        saved = proxy_manager.set_proxy_list(text)
        if saved > 0:
            await message.answer(f"{saved} پروکسی ذخیره شد.")
            return

    # استخراج لینک‌ها
    urls = re.findall(r'(https?://\S+)', text)

    # اگر کاربر تنها یک لینک فرستاد و لینک مربوط به API پروکسی بود
    if len(urls) == 1 and ("proxy" in urls[0].lower() or "extract" in urls[0].lower()):
        if proxy_manager.set_api_url(urls[0]):
            await message.answer(f"لینک پروکسی ثبت شد ({proxy_manager.count()} پروکسی).")
        else:
            await message.answer("خطا در دریافت پروکسی از لینک.")
        return

    if len(urls) < 2:
        await message.answer("حداقل ۲ لینک ارسال کنید.")
        return

    template_url = urls[0]
    target_urls = urls[1:]

    msg = await message.answer(f"⏳ در حال پردازش {len(target_urls)} اکانت...")

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
            await message.answer_document(document=FSInputFile(log_file_path), caption="لاگ خطا")
        shutil.rmtree(session_dir, ignore_errors=True)
        return

    final_zip_path, stats = result_data
    await msg.delete()

    report_text = (
        f"پایان پردازش ({stats['total_targets']} اکانت):\n"
        f"موفق: {stats['success']}\n"
        f"ناموفق: {stats['failed']}"
    )

    await message.answer_document(document=FSInputFile(final_zip_path), caption=report_text)
    if os.path.exists(log_file_path):
        await message.answer_document(document=FSInputFile(log_file_path), caption="فایل لاگ")

    shutil.rmtree(session_dir, ignore_errors=True)


async def main():
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher()
    dp.include_router(router)
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
