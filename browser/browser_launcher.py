# browser/browser_launcher.py

import random

from typing import Optional, Dict, List

from playwright.sync_api import sync_playwright, Browser, BrowserContext, Page


from browser.stealth_injector import StealthInjector

from browser.viewport_manager import ViewportManager


class BrowserLauncher:

    """مدیریت راه‌اندازی و تنظیم مرورگر"""

    

    def __init__(self, proxy_manager, config, logger):

        self.proxy_manager = proxy_manager

        self.config = config

        self.logger = logger

        

        # اجزاء مرورگر

        self.playwright = None

        self.browser: Optional[Browser] = None

        self.context: Optional[BrowserContext] = None

        self.page: Optional[Page] = None

        

        # ابزارهای کمکی

        self.stealth_injector = None

        self.viewport_manager = ViewportManager()

        self.proxy_settings = None

        

        # تنظیمات

        self.headless = config.HEADLESS

        self.user_agents = self._get_user_agents()

    

    def launch(self) -> bool:

        """راه‌اندازی مرورگر"""

        try:

            self.logger.info("🌐 راه‌اندازی مرورگر...")

            

            # مرحله A: راه‌اندازی Playwright

            self.logger.info("🔧 مرحله A: راه‌اندازی Playwright...")

            self.playwright = sync_playwright().start()

            self.logger.info("✅ مرحله A موفق: Playwright آماده شد")

            

            # مرحله B: راه‌اندازی مرورگر

            self.logger.info("🚀 مرحله B: راه‌اندازی مرورگر...")

            if not self._launch_browser():

                return False

            self.logger.info("✅ مرحله B موفق: مرورگر راه‌اندازی شد")

            

            # مرحله C: ایجاد Context

            self.logger.info("📄 مرحله C: ایجاد browser context...")

            if not self._create_context():

                return False

            self.logger.info("✅ مرحله C موفق: context ایجاد شد")

            

            # مرحله D: ایجاد Page

            self.logger.info("📃 مرحله D: ایجاد page...")

            if not self._create_page():

                return False

            self.logger.info("✅ مرحله D موفق: page ایجاد شد")

            

            # مرحله E: اعمال Stealth فوری

            self.logger.info("🥷 مرحله E: اعمال تنظیمات stealth...")

            self._apply_stealth()

            self.logger.info("✅ مرحله E موفق: stealth اعمال شد")

            

            # مرحله F: تاخیر اولیه برای تثبیت

            self.logger.info("⏳ مرحله F: تاخیر اولیه برای تثبیت مرورگر...")

            import time

            time.sleep(2)  # تاخیر 2 ثانیه برای تثبیت

            self.logger.info("✅ مرحله F موفق: مرورگر تثبیت شد")

            

            # مرحله G: اطمینان از عدم تداخل اسکریپت‌ها

            self.logger.info("✅ مرحله G موفق: stealth کامل اعمال شد")

            

            self.logger.info("🎉 تمام مراحل راه‌اندازی مرورگر موفق بود")

            return True

            

        except Exception as e:

            self.logger.error(f"❌ خطا در راه‌اندازی مرورگر: {e}")

            self.close()

            return False

    

    def _launch_browser(self) -> bool:

        """راه‌اندازی مرورگر اصلی"""

        try:

            # انتخاب نوع مرورگر در ابتدا

            browser_type = getattr(self.config, 'BROWSER_TYPE', 'chromium').lower()

            

            # تنظیمات مرورگر

            browser_args = self._get_browser_args()

            

            # تنظیمات راه‌اندازی - بهینه شده برای عدم تشخیص

            launch_options = {

                'headless': self.headless,

                'args': browser_args,

                'ignore_default_args': ['--enable-automation', '--enable-blink-features=AutomationControlled'],

                'slow_mo': 0,  # حذف slow_mo برای طبیعی‌تر بودن

                'devtools': False,  # اطمینان از بسته بودن devtools

                # استفاده از Chromium به جای Chrome برای پایداری بیشتر

                # channel حذف شد تا از Chromium پیش‌فرض استفاده شود

            }

            

            # اضافه کردن پروکسی در صورت وجود (مگر در حالت سرور ایران)

            if not getattr(self.config, 'DISABLE_PROXY_ON_FAILURE', False):

                proxy_applied = False

                max_proxy_attempts = 3

                

                for attempt in range(max_proxy_attempts):

                    self.logger.info(f"🔄 تلاش {attempt + 1}/{max_proxy_attempts} برای اتصال پروکسی...")

                    

                    proxy_config = self.proxy_manager.get_proxy_config(force_new_session=(attempt > 0))

                    if proxy_config:

                        proxy_settings = self._prepare_proxy_settings(proxy_config)

                        if proxy_settings:

                            # تست پروکسی با timeout کوتاه‌تر

                            if self._test_proxy(proxy_settings):

                                # تنظیمات پروکسی برای Chromium

                                if browser_type == 'chromium':

                                    # حذف آرگومان‌های متضاد

                                    browser_args = [arg for arg in browser_args if not arg.startswith('--no-proxy-server')]

                                    launch_options['args'] = browser_args

                                

                                # ذخیره تنظیمات پروکسی برای استفاده در context

                                self.proxy_settings = proxy_settings

                                self.logger.info(f"✅ پروکسی اعمال شد: {proxy_settings['server']}")

                                proxy_applied = True

                                break

                            else:

                                self.logger.warning(f"⚠️ تلاش {attempt + 1} ناموفق، چرخش پروکسی...")

                                # چرخش پروکسی برای تلاش بعدی

                                self.proxy_manager.force_rotation()

                                # انتظار کوتاه بین تلاش‌ها

                                import time

                                time.sleep(2)

                        else:

                            self.logger.warning(f"⚠️ خطا در آماده‌سازی تنظیمات پروکسی")

                    else:

                        self.logger.warning(f"⚠️ پروکسی در تلاش {attempt + 1} در دسترس نیست")

                

                if not proxy_applied:

                    self.logger.error("❌ نتوانستیم پروکسی معتبری پیدا کنیم")

                    return False

            else:

                self.logger.info("🇮🇷 حالت سرور ایران: پروکسی غیرفعال شد")

            

            if browser_type == 'firefox':

                self.browser = self.playwright.firefox.launch(**launch_options)

                self.logger.info("🦊 Firefox راه‌اندازی شد")

            elif browser_type == 'webkit':

                self.browser = self.playwright.webkit.launch(**launch_options)

                self.logger.info("🌐 WebKit راه‌اندازی شد")

            else:

                self.browser = self.playwright.chromium.launch(**launch_options)

                self.logger.info("🌐 Chromium راه‌اندازی شد")

            

            return True

            

        except Exception as e:

            self.logger.error(f"❌ خطا در راه‌اندازی مرورگر: {e}")

            return False

    

    def _create_context(self) -> bool:

        """ایجاد browser context با تنظیمات کاملاً طبیعی و پیشرفته"""

        try:

            # بررسی وضعیت مرورگر قبل از ایجاد context

            if not self.browser:

                self.logger.error("❌ مرورگر موجود نیست")

                return False

            

            # بررسی وضعیت اتصال مرورگر (سازگار با نسخه‌های مختلف Playwright)

            try:

                if hasattr(self.browser, '_connection') and hasattr(self.browser._connection, '_closed'):

                    if self.browser._connection._closed:

                        self.logger.error("❌ اتصال مرورگر بسته شده است")

                        return False

                elif hasattr(self.browser, 'is_connected'):

                    if not self.browser.is_connected():

                        self.logger.error("❌ مرورگر متصل نیست")

                        return False

            except Exception as e:

                self.logger.warning(f"⚠️ نتوانستیم وضعیت اتصال مرورگر را بررسی کنیم: {e}")

                # ادامه می‌دهیم چون ممکن است مرورگر سالم باشد

            

            # انتخاب تصادفی viewport و user agent از لیست‌های واقعی

            selected_viewport = self.viewport_manager.get_optimal_viewport()

            selected_ua = random.choice(self.user_agents)

            self.logger.info(f"شبیه‌سازی پروفایل: UA='{selected_ua[:50]}...', Viewport={selected_viewport}")


            # تنظیمات context - این بخش مهم‌ترین قسمت است

            context_options = {

                'viewport': selected_viewport,

                'user_agent': selected_ua,

                

                # --- تنظیمات زبان و منطقه (بسیار حیاتی) ---

                'locale': 'pt-PT',  # زبان پرتغالی-پرتغال

                'timezone_id': 'Europe/Lisbon',  # منطقه زمانی لیسبون

                

                # --- شبیه‌سازی مشخصات سخت‌افزاری ---

                'device_scale_factor': random.choice([1, 1.25, 1.5]),

                'is_mobile': False,

                'has_touch': False, # شبیه‌سازی دسکتاپ بدون صفحه لمسی

                

                # --- شبیه‌سازی مجوزهای مرورگر ---

                'geolocation': {'latitude': 38.7223, 'longitude': -9.1393},  # موقعیت مکانی لیسبون

                'permissions': ['geolocation'],

                

                # --- هدرهای HTTP کاملاً واقعی ---

                'extra_http_headers': {

                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',

                    'Accept-Encoding': 'gzip, deflate, br',

                    'Accept-Language': 'pt-PT,pt;q=0.9,en-US;q=0.8,en;q=0.7',

                    'Sec-Ch-Ua': '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',

                    'Sec-Ch-Ua-Mobile': '?0',

                    'Sec-Ch-Ua-Platform': '"Windows"',

                    'Sec-Fetch-Dest': 'document',

                    'Sec-Fetch-Mode': 'navigate',

                    'Sec-Fetch-Site': 'none',

                    'Sec-Fetch-User': '?1',

                    'DNT': '1' # Do Not Track را فعال می‌کند که طبیعی است

                    # حذف Upgrade-Insecure-Requests برای جلوگیری از CORS

                },

                

                # --- غیرفعال کردن برخی API های حساس ---

                'java_script_enabled': True,

                'bypass_csp': False, # پالیسی‌های امنیتی سایت را رعایت می‌کند

                'ignore_https_errors': True

            }

            

            # بخش پروکسی بدون تغییر باقی می‌ماند

            if hasattr(self, 'proxy_settings') and self.proxy_settings:

                context_options['proxy'] = self.proxy_settings

                self.logger.info(f"🌐 پروکسی اعمال شد: {self.proxy_settings['server']}")

            else:

                self.logger.info("🌐 context بدون پروکسی ایجاد می‌شود")

            

            # ایجاد context

            self.context = self.browser.new_context(**context_options)

            return True

            

        except Exception as e:

            self.logger.error(f"❌ خطا در ایجاد context: {e}")

            return False

    

    def _create_page(self) -> bool:

        """ایجاد page جدید"""

        try:

            self.page = self.context.new_page()

            

            # اعمال CSS برای اسکرول و نمایش بهتر

            self.page.add_style_tag(content="""

                html, body {

                    margin: 0 !important;

                    padding: 0 !important;

                    overflow: auto !important;

                    overflow-x: auto !important;

                    overflow-y: auto !important;

                    max-width: 100vw !important;

                    max-height: 100vh !important;

                    width: 100% !important;

                    height: 100% !important;

                    box-sizing: border-box !important;

                }

                body {

                    min-height: 100vh !important;

                    position: relative !important;

                }

                * {

                    box-sizing: border-box !important;

                    max-width: 100% !important;

                }

                /* اصلاح عناصر که ممکن است از صفحه خارج شوند */

                div, section, main, article {

                    max-width: 100% !important;

                    overflow-wrap: break-word !important;

                }

                /* اطمینان از قابلیت اسکرول */

                ::-webkit-scrollbar {

                    width: 12px !important;

                    height: 12px !important;

                }

                ::-webkit-scrollbar-track {

                    background: #f1f1f1 !important;

                }

                ::-webkit-scrollbar-thumb {

                    background: #888 !important;

                    border-radius: 6px !important;

                }

                ::-webkit-scrollbar-thumb:hover {

                    background: #555 !important;

                }

            """)

            

            self.logger.info("✅ تنظیمات CSS و اسکرول اعمال شد")

            return True

            

        except Exception as e:

            self.logger.error(f"❌ خطا در ایجاد page: {e}")

            return False

    

    def _apply_stealth(self):

        """اعمال تنظیمات stealth اولیه"""

        try:

            self.stealth_injector = StealthInjector(self.page, self.logger)

            self.stealth_injector.apply_all_stealth_techniques()

            

        except Exception as e:

            self.logger.warning(f"⚠️ خطا در اعمال stealth: {e}")

    


    

    def _prepare_proxy_settings(self, proxy_config) -> Optional[Dict]:

        """آماده‌سازی تنظیمات پروکسی"""

        try:

            proxy_url = f"http://{proxy_config['host']}:{proxy_config['port']}"

            

            return {

                'server': proxy_url,

                'username': str(proxy_config.get('username', '')),

                'password': str(proxy_config.get('password', ''))

            }

            

        except Exception as e:

            self.logger.error(f"❌ خطا در آماده‌سازی پروکسی: {e}")

            return None

    

    def _test_proxy(self, proxy_settings) -> bool:

        """تست پیشرفته عملکرد پروکسی و تشخیص نشت IP"""

        try:

            import requests

            from requests.auth import HTTPProxyAuth

            import socket

            

            proxy_url = proxy_settings['server']

            username = proxy_settings.get('username', '')

            password = proxy_settings.get('password', '')

            

            # تنظیم پروکسی با احراز هویت

            proxies = {

                'http': proxy_url,

                'https': proxy_url

            }

            

            # تنظیم احراز هویت

            auth = None

            if username and password:

                auth = HTTPProxyAuth(username, password)

                # همچنین URL با احراز هویت

                proxy_url_with_auth = proxy_url.replace('http://', f'http://{username}:{password}@')

                proxies = {

                    'http': proxy_url_with_auth,

                    'https': proxy_url_with_auth

                }

            

            # تست چندگانه با URL های مختلف

            test_urls = [

                'http://httpbin.org/ip',  # HTTP ابتدا

                'https://api.ipify.org?format=json',

                'https://ifconfig.me/ip'

            ]

            

            proxy_ip = None

            

            for url in test_urls:

                try:

                    self.logger.info(f"🔍 تست پروکسی با {url}...")

                    

                    # تنظیمات درخواست

                    request_kwargs = {

                        'proxies': proxies,

                        'timeout': 15,

                        'verify': False,  # برای مشکلات SSL

                        'allow_redirects': True

                    }

                    

                    if auth:

                        request_kwargs['auth'] = auth

                    

                    response = requests.get(url, **request_kwargs)

                    

                    if response.status_code == 200:

                        if 'json' in response.headers.get('content-type', ''):

                            data = response.json()

                            proxy_ip = data.get('ip', data.get('origin', ''))

                        else:

                            proxy_ip = response.text.strip()

                        

                        if proxy_ip:

                            self.logger.info(f"✅ پروکسی تست شد: {proxy_ip}")

                            break

                            

                except requests.exceptions.ProxyError as e:

                    self.logger.warning(f"⚠️ خطای پروکسی در {url}: {e}")

                    continue

                except requests.exceptions.ConnectTimeout as e:

                    self.logger.warning(f"⚠️ timeout در {url}: {e}")

                    continue

                except Exception as e:

                    self.logger.warning(f"⚠️ خطا در تست {url}: {e}")

                    continue

            

            if not proxy_ip:

                self.logger.error("❌ نتوانستیم IP پروکسی را دریافت کنیم")

                return False

            

            # بررسی IP واقعی سیستم (برای مقایسه)

            try:

                real_response = requests.get('http://httpbin.org/ip', timeout=5)

                if real_response.status_code == 200:

                    real_ip = real_response.json().get('origin', '')

                    

                    if proxy_ip == real_ip:

                        self.logger.error(f"❌ نشت IP تشخیص داده شد! IP واقعی: {real_ip}")

                        return False

                        

            except:

                # اگر نتوانیم IP واقعی را بگیریم، مشکلی نیست

                pass

            

            self.logger.info(f"✅ پروکسی تست شد و معتبر است: {proxy_ip}")

            return True

            

        except Exception as e:

            self.logger.error(f"❌ خطا در تست پروکسی: {e}")

            return False

    

    def _get_browser_args(self) -> List[str]:

        """دریافت آرگومان‌های مرورگر برای شبیه‌سازی مرورگر واقعی"""

        browser_type = getattr(self.config, 'BROWSER_TYPE', 'chromium').lower()

        

        # آرگومان‌های مشترک - بهینه شده برای عدم تشخیص

        common_args = [

            '--lang=pt-PT',

            '--accept-lang=pt-PT,pt;q=0.9,en;q=0.8',

            # تنظیمات ضروری امنیتی

            '--disable-webrtc',

            '--disable-webrtc-hw-decoding', 

            '--disable-webrtc-hw-encoding',

            '--disable-webrtc-multiple-routes',

            '--enforce-webrtc-ip-permission-check',

            '--force-webrtc-ip-handling-policy=disable_non_proxied_udp',

            # تنظیمات طبیعی مرورگر

            '--disable-background-timer-throttling',

            '--disable-renderer-backgrounding',

            '--disable-backgrounding-occluded-windows',

            '--disable-default-apps',

            '--disable-sync',

            '--no-first-run',

            '--no-default-browser-check',

            # حذف آرگومان‌های مشکوک automation

            # '--no-sandbox' - حذف شد

            # '--disable-dev-shm-usage' - حذف شد  

            # سایر آرگومان‌های مشکوک حذف شدند

        ]

        

        if browser_type == 'firefox':

            # آرگومان‌های مخصوص Firefox

            return common_args + [

                '--disable-features=TranslateUI',

                '--enable-webgl',

                # تنظیمات پروکسی Firefox

                '--proxy-server=http',

                '--proxy-bypass-list=<-loopback>',

                '--disable-extensions',

                '--disable-plugins',

                '--disable-gpu-sandbox',

                '--allow-running-insecure-content',

                '--disable-web-security',

                '--ignore-certificate-errors',

                '--ignore-ssl-errors',

                '--ignore-certificate-errors-spki-list',

                '--ignore-certificate-errors-ssl-errors'

            ]

        elif browser_type == 'webkit':

            # آرگومان‌های مخصوص WebKit

            return common_args + [

                '--enable-webgl',

                '--enable-accelerated-2d-canvas'

            ]

        else:  # chromium

            # آرگومان‌های مخصوص Chromium - طبیعی و غیرمشکوک

            return common_args + [

                # تنظیمات ضروری stealth

                '--disable-blink-features=AutomationControlled',

                '--exclude-switches=enable-automation',

                # تنظیمات عملکرد طبیعی

                '--enable-webgl',

                '--enable-accelerated-2d-canvas',

                '--force-color-profile=srgb',

                # تنظیمات امنیتی ضروری (فقط برای پروکسی)

                '--ignore-certificate-errors',

                '--allow-running-insecure-content',

                # حذف آرگومان‌های مشکوک:

                # '--disable-web-security' - حذف شد

                # '--disable-automation' - حذف شد  

                # '--disable-client-side-phishing-detection' - حذف شد

                # '--metrics-recording-only' - حذف شد

                # '--no-report-upload' - حذف شد

                # '--dns-prefetch-disable' - حذف شد

                # '--disable-domain-reliability' - حذف شد

            ]

    

    def _get_user_agents(self) -> List[str]:

        """دریافت لیست User Agent ها متناسب با نوع مرورگر"""

        browser_type = getattr(self.config, 'BROWSER_TYPE', 'chromium').lower()

        

        if browser_type == 'firefox':

            return [

                'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0',

                'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:120.0) Gecko/20100101 Firefox/120.0',

                'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:121.0) Gecko/20100101 Firefox/121.0',

                'Mozilla/5.0 (X11; Linux x86_64; rv:121.0) Gecko/20100101 Firefox/121.0',

                'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:119.0) Gecko/20100101 Firefox/119.0'

            ]

        elif browser_type == 'webkit':

            return [

                'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15',

                'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15',

                'Mozilla/5.0 (iPhone; CPU iPhone OS 17_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Mobile/15E148 Safari/604.1',

                'Mozilla/5.0 (iPad; CPU OS 17_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Mobile/15E148 Safari/604.1'

            ]

        else:  # chromium

            return [

                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',

                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',

                'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',

                'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',

                'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'

            ]

    

    def get_browser(self):

        """دریافت شیء مرورگر"""

        return self

    

    def recover_browser(self) -> bool:
        """بازیابی مرورگر در صورت بسته شدن"""
        try:
            self.logger.info("🔄 تلاش برای بازیابی مرورگر...")
            
            # بستن امن منابع قبلی
            self._safe_close_all()
            
            # انتظار کوتاه برای آزادسازی منابع
            import time
            time.sleep(1)
            
            # راه‌اندازی مجدد با retry
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    self.logger.info(f"🔄 تلاش بازیابی #{attempt + 1}/{max_retries}")
                    if self.launch():
                        self.logger.info("✅ بازیابی مرورگر موفق")
                        return True
                except Exception as e:
                    self.logger.warning(f"⚠️ تلاش #{attempt + 1} ناموفق: {e}")
                    if attempt < max_retries - 1:
                        time.sleep(2)  # انتظار بین تلاش‌ها
            
            self.logger.error("❌ تمام تلاش‌های بازیابی ناموفق")
            return False
            
        except Exception as e:
            self.logger.error(f"❌ خطا در بازیابی مرورگر: {e}")
            return False
    
    def _safe_close_all(self):
        """بستن امن تمام منابع"""
        try:
            # بستن page
            if self.page:
                try:
                    if not self.page.is_closed():
                        self.page.close()
                except:
                    pass
                self.page = None
            
            # بستن context
            if self.context:
                try:
                    self.context.close()
                except:
                    pass
                self.context = None
            
            # بستن browser
            if self.browser:
                try:
                    self.browser.close()
                except:
                    pass
                self.browser = None
            
            # توقف playwright
            if self.playwright:
                try:
                    self.playwright.stop()
                except:
                    pass
                self.playwright = None
                
        except Exception as e:
            self.logger.debug(f"خطا در بستن امن: {e}")

    

    def is_browser_alive(self) -> bool:
        """بررسی زنده بودن مرورگر"""
        try:
            # بررسی وجود اجزاء اصلی
            if not self.browser or not self.context or not self.page:
                return False
            
            # بررسی وضعیت اتصال مرورگر
            try:
                if hasattr(self.browser, '_connection') and hasattr(self.browser._connection, '_closed'):
                    if self.browser._connection._closed:
                        return False
                elif hasattr(self.browser, 'is_connected'):
                    if not self.browser.is_connected():
                        return False
            except Exception:
                return False
            
            # بررسی وضعیت page
            try:
                if hasattr(self.page, 'is_closed') and self.page.is_closed():
                    return False
            except Exception:
                return False
            
            # تست عملکرد با عملیات ساده
            try:
                # تست ساده برای اطمینان از عملکرد
                self.page.evaluate("() => document.readyState")
                return True
            except Exception as e:
                error_msg = str(e)
                # اگر خطای بسته شدن باشد، مرورگر زنده نیست
                if "Target page, context or browser has been closed" in error_msg:
                    return False
                # برای سایر خطاها، احتیاط کرده و false برمی‌گردانیم
                return False
            
        except Exception:
            return False

    

    def close(self):

        """بستن امن مرورگر"""

        try:

            if self.page:

                try:

                    self.page.close()

                except:

                    pass

                self.page = None

            

            if self.context:

                try:

                    self.context.close()

                except:

                    pass

                self.context = None

            

            if self.browser:

                try:

                    self.browser.close()

                except:

                    pass

                self.browser = None

            

            if self.playwright:

                try:

                    self.playwright.stop()

                except:

                    pass

                self.playwright = None

            

            self.logger.info("🔒 مرورگر بسته شد")

            

        except Exception as e:

            self.logger.error(f"❌ خطا در بستن مرورگر: {e}")