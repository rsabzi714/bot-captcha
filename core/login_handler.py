# core/login_handler.py
import time
from datetime import datetime
from typing import Optional

from utils.element_finder import ElementFinder
from utils.page_detector import PageDetector
from modules.form_automation import FormAutomation
from modules.captcha_handler import CaptchaHandler
from human_behavior import HumanBehavior

class LoginHandler:
    """مدیریت فرآیند ورود به سیستم MNE"""
    
    def __init__(self, browser, page, config, captcha_solver, logger):
        self.browser = browser
        self.page = page 
        self.config = config
        self.captcha_solver = captcha_solver
        self.logger = logger
        
        # ابزارهای کمکی - فقط اگر browser و page موجود باشند
        if browser and browser.page:
            self.element_finder = ElementFinder(browser.page, logger)
            self.page_detector = PageDetector(browser.page, logger)
            self.form_automation = FormAutomation(browser.page, logger)
            self.captcha_handler = CaptchaHandler(browser.page, captcha_solver, logger)
            self.human_behavior = HumanBehavior(browser.page)
        else:
            self.element_finder = None
            self.page_detector = None
            self.form_automation = None
            self.captcha_handler = None
            self.human_behavior = None
        
        # تنظیمات ورود بهبود یافته
        self.max_retries = 5  # افزایش تعداد تلاش‌ها
        self.retry_delay = 5
        self.captcha_max_retries = 3  # تلاش‌های مخصوص کپچا
        self.adaptive_delay = True  # تأخیر تطبیقی
        self.retry_strategies = ['standard', 'aggressive', 'conservative']  # استراتژی‌های مختلف
    
    def _calculate_retry_delay(self, attempt: int, strategy: str = 'standard') -> int:
        """محاسبه تأخیر تطبیقی بر اساس استراتژی"""
        base_delay = self.retry_delay
        
        if strategy == 'standard':
            # تأخیر خطی: 5, 10, 15, 20, 25
            return base_delay * (attempt + 1)
        elif strategy == 'aggressive':
            # تأخیر کم برای تلاش سریع: 3, 6, 9, 12, 15
            return max(3, base_delay * attempt * 0.6)
        elif strategy == 'conservative':
            # تأخیر نمایی برای حفظ منابع: 5, 10, 20, 40, 80
            return base_delay * (2 ** attempt)
        else:
            return base_delay
    
    def _retry_with_strategy(self, operation_func, operation_name: str, max_attempts: int = None, strategy: str = 'standard') -> bool:
        """اجرای عملیات با استراتژی retry پیشرفته"""
        if max_attempts is None:
            max_attempts = self.max_retries
        
        last_error = None
        
        for attempt in range(max_attempts):
            try:
                self.logger.info(f"🔄 {operation_name} - تلاش {attempt + 1}/{max_attempts} (استراتژی: {strategy})")
                
                result = operation_func()
                if result:
                    self.logger.info(f"✅ {operation_name} موفق در تلاش {attempt + 1}")
                    return True
                
                # اگر نتیجه False بود اما خطایی نداشت
                self.logger.warning(f"⚠️ {operation_name} ناموفق در تلاش {attempt + 1}")
                
            except Exception as e:
                last_error = e
                self.logger.warning(f"⚠️ خطا در {operation_name} تلاش {attempt + 1}: {str(e)[:100]}...")
            
            # محاسبه تأخیر برای تلاش بعدی
            if attempt < max_attempts - 1:
                if self.adaptive_delay:
                    delay = self._calculate_retry_delay(attempt, strategy)
                else:
                    delay = self.retry_delay
                
                self.logger.info(f"⏳ انتظار {delay} ثانیه قبل از تلاش مجدد...")
                time.sleep(delay)
        
        # اگر همه تلاش‌ها ناموفق بودند
        if last_error:
            self.logger.error(f"❌ {operation_name} پس از {max_attempts} تلاش ناموفق - آخرین خطا: {last_error}")
        else:
            self.logger.error(f"❌ {operation_name} پس از {max_attempts} تلاش ناموفق")
        
        return False
    
    def _handle_captcha_with_retry(self) -> bool:
        """حل کپچا با سیستم retry پیشرفته"""
        def captcha_operation():
            if not self.captcha_handler:
                self.logger.warning("⚠️ captcha_handler موجود نیست")
                return False
            return self.captcha_handler.solve_captcha()
        
        # تلاش با استراتژی‌های مختلف
        for strategy in self.retry_strategies:
            self.logger.info(f"🎯 تلاش حل کپچا با استراتژی {strategy}")
            
            success = self._retry_with_strategy(
                captcha_operation,
                f"حل کپچا ({strategy})",
                self.captcha_max_retries,
                strategy
            )
            
            if success:
                return True
            
            # انتظار بین استراتژی‌ها
            if strategy != self.retry_strategies[-1]:
                self.logger.info("⏳ انتظار قبل از تغییر استراتژی...")
                time.sleep(10)
        
        return False

    # In core/login_handler.py

    def perform_login(self) -> bool:
        """انجام فرآیند کامل ورود با ترتیب صحیح و بی‌نقص"""
        start_time = datetime.now()
        self.logger.info("🆕 شروع فرآیند ورود جدید")
        
        try:
            # در ابتدای هر تلاش، وضعیت کپچا را ریست می‌کنیم
            if hasattr(self, 'captcha_handler') and self.captcha_handler:
                self.captcha_handler.reset_captcha_state()
            
            # --- مرحله 1: پیمایش به صفحه و تعاملات اولیه ---
            if not self._navigate_to_login_page(): return False
            self._handle_cookies()
            self._select_authentication_method()
            
            # --- مرحله 2: پر کردن اطلاعات کاربری ---
            if not self._fill_login_form(): return False
            
            # --- مرحله 3: حل کپچا (مرحله حیاتی قبل از ارسال) ---
            if not self._handle_captcha_if_required():
                self.logger.error("❌ حل کپچا ناموفق بود. امکان ادامه ورود وجود ندارد.")
                return False

            # --- مرحله 4: ارسال فرم نهایی (حالا که کپچا حل شده) ---
            if not self._click_submit_button_forcefully():
                return False
                
            # --- مرحله 5: تأیید نهایی موفقیت ورود ---
            if self._verify_login_success():
                login_duration = (datetime.now() - start_time).total_seconds()
                self.logger.info(f"🎉 ورود موفقیت‌آمیز در {login_duration:.1f} ثانیه")
                return True
            else:
                self.logger.error("❌ ورود تأیید نشد. بررسی مجدد اطلاعات ورود توصیه می‌شود.")
                return False
                
        except Exception as e:
            self.logger.error(f"❌ خطای مرگبار در فرآیند ورود: {e}")
            import traceback
            traceback.print_exc()
            return False    

    def _navigate_to_login_page(self) -> bool:
        """رفتن به صفحه ورود با مقاومت بالا در برابر مشکلات شبکه"""
        self.logger.info("📍 مرحله 1: اتصال به صفحه ورود")
        
        # URLs مختلف برای تلاش
        urls_to_try = [
            self.config.MNE_LOGIN_URL,
            'https://agendamentos.mne.gov.pt/',
            'https://agendamentos.mne.gov.pt/pt'
        ]
        
        # استراتژی‌های مختلف wait_until
        wait_strategies = ['domcontentloaded', 'load', 'networkidle']
        
        for url in urls_to_try:
            self.logger.info(f"🔗 تلاش اتصال به: {url}")
            
            for attempt in range(self.max_retries):
                try:
                    # بررسی وضعیت مرورگر قبل از تلاش
                    if not self.browser.is_browser_alive():
                        self.logger.warning("⚠️ مرورگر بسته شده - تلاش برای بازیابی...")
                        if not self.browser.recover_browser():
                            self.logger.error("❌ شکست در بازیابی مرورگر")
                            return False
                        self._update_helper_tools()
                    
                    self.logger.info(f"   📡 تلاش {attempt + 1}/{self.max_retries}")
                    
                    # تلاش با timeout های مختلف
                    timeouts = [60000, 45000, 30000]  # 60, 45, 30 ثانیه
                    
                    for timeout_ms in timeouts:
                        try:
                            # تلاش با wait_until مختلف
                            for strategy in wait_strategies:
                                try:
                                    self.logger.info(f"      🔄 استراتژی: {strategy}, timeout: {timeout_ms/1000}s")
                                    self.browser.page.goto(url, wait_until=strategy, timeout=timeout_ms)
                                    
                                    # صبر اضافی برای بارگذاری کامل
                                    time.sleep(5)
                                    
                                    # بررسی موفقیت
                                    current_url = self.browser.page.url
                                    if any(keyword in current_url.lower() for keyword in ['agendamentos', 'mne']):
                                        self.logger.info(f"✅ اتصال موفق: {current_url}")
                                        
                                        # اگر در صفحه login نیستیم، تلاش برای رفتن به آن
                                        if 'login' not in current_url.lower():
                                            try:
                                                self.logger.info("🔄 تلاش برای رفتن به صفحه login...")
                                                self.browser.page.goto(self.config.MNE_LOGIN_URL, timeout=30000)
                                                time.sleep(3)
                                            except:
                                                self.logger.warning("⚠️ نتوانست به صفحه login برود، ادامه با صفحه فعلی")
                                        
                                        # تنظیم تشخیص refresh
                                        self.browser.page.evaluate("""
                                            window.pageRefreshed = false;
                                            window.addEventListener('beforeunload', () => {
                                                window.pageRefreshed = true;
                                            });
                                        """)
                                        
                                        self.logger.info("✅ مرحله 1 موفق: صفحه ورود بارگذاری شد")
                                        return True
                                        
                                except Exception as e:
                                    self.logger.debug(f"         ❌ شکست با {strategy}: {str(e)[:50]}")
                                    continue
                            
                            # تلاش نهایی بدون wait_until
                            try:
                                self.logger.info(f"      🔄 تلاش نهایی بدون wait_until, timeout: {timeout_ms/1000}s")
                                self.browser.page.goto(url, timeout=timeout_ms)
                                time.sleep(10)
                                
                                current_url = self.browser.page.url
                                if 'agendamentos' in current_url.lower():
                                    self.logger.info("✅ اتصال نهایی موفق")
                                    
                                    # تنظیم تشخیص refresh
                                    self.browser.page.evaluate("""
                                        window.pageRefreshed = false;
                                        window.addEventListener('beforeunload', () => {
                                            window.pageRefreshed = true;
                                        });
                                    """)
                                    
                                    return True
                                    
                            except Exception as e:
                                self.logger.debug(f"         ❌ تلاش نهایی ناموفق: {str(e)[:50]}")
                                continue
                                
                        except Exception as e:
                            self.logger.debug(f"      ❌ شکست با timeout {timeout_ms/1000}s: {str(e)[:50]}")
                            continue
                    
                    # اگر همه timeout ها شکست خوردند
                    raise Exception(f"همه timeout ها برای تلاش {attempt + 1} شکست خوردند")
                    
                except Exception as e:
                    error_msg = str(e)
                    
                    if "Target page, context or browser has been closed" in error_msg:
                        self.logger.warning("⚠️ Browser/context بسته شده - تلاش برای بازیابی...")
                        if not self.browser.recover_browser():
                            self.logger.error("❌ شکست در بازیابی مرورگر")
                            return False
                        self._update_helper_tools()
                        continue
                        
                    elif any(error in error_msg for error in ["NS_ERROR_PROXY_FORBIDDEN", "ERR_TUNNEL_CONNECTION_FAILED", "ERR_PROXY_CONNECTION_FAILED", "net::ERR_PROXY_CONNECTION_FAILED", "ERR_NAME_NOT_RESOLVED", "net::ERR_NAME_NOT_RESOLVED"]):
                        if "ERR_NAME_NOT_RESOLVED" in error_msg or "net::ERR_NAME_NOT_RESOLVED" in error_msg:
                            self.logger.warning(f"⚠️ تلاش {attempt + 1} - خطای DNS: {error_msg[:100]}...")
                        else:
                            self.logger.warning(f"⚠️ تلاش {attempt + 1} - خطای پروکسی: {error_msg[:100]}...")
                        
                        # تلاش برای چرخش پروکسی
                        if hasattr(self, 'browser') and hasattr(self.browser, 'proxy_manager'):
                            self.logger.info("🔄 تلاش برای چرخش پروکسی...")
                            self.browser.proxy_manager.force_rotation()
                        
                        if attempt < self.max_retries - 1:
                            self.logger.info("⏳ انتظار قبل از تلاش مجدد...")
                            time.sleep(self.retry_delay * 2)  # انتظار بیشتر برای خطاهای شبکه
                            continue
                            
                    elif "ERR_TIMED_OUT" in error_msg or "TimeoutError" in error_msg:
                        self.logger.warning(f"⚠️ تلاش {attempt + 1} - timeout: {error_msg[:100]}...")
                        
                        if attempt < self.max_retries - 1:
                            self.logger.info("⏳ انتظار قبل از تلاش مجدد...")
                            time.sleep(self.retry_delay * 3)  # انتظار بیشتر برای timeout
                            continue
                    
                    else:
                        self.logger.warning(f"⚠️ تلاش {attempt + 1} - خطای عمومی: {error_msg[:100]}...")
                        if attempt < self.max_retries - 1:
                            time.sleep(self.retry_delay)
                            continue
            
            self.logger.warning(f"❌ شکست در اتصال به {url} - تلاش URL بعدی")
        
        self.logger.error("❌ شکست در اتصال به صفحه ورود - همه URL ها و تلاش‌ها ناموفق")
        return False
    
    def _update_helper_tools(self):
        """به‌روزرسانی ابزارهای کمکی پس از بازیابی مرورگر"""
        try:
            self.element_finder = ElementFinder(self.browser.page, self.logger)
            self.page_detector = PageDetector(self.browser.page, self.logger)
            self.form_automation = FormAutomation(self.browser.page, self.logger)
            self.captcha_handler = CaptchaHandler(self.browser.page, self.captcha_solver, self.logger)
            self.human_behavior = HumanBehavior(self.browser.page)
            
            # ثبت مجدد listener برای تشخیص refresh
            self.browser.page.evaluate("""
                window.pageRefreshed = false;
                window.addEventListener('beforeunload', () => {
                    window.pageRefreshed = true;
                });
            """)
            self.logger.debug("✅ listener تشخیص refresh مجدداً ثبت شد")
            
        except Exception as e:
            self.logger.error(f"❌ خطا در به‌روزرسانی ابزارهای کمکی: {e}")
    
    def _handle_cookies(self):
        """مدیریت کوکی‌ها"""
        self.logger.info("📍 مرحله 2: مدیریت کوکی‌ها")
        
        if self.config.COOKIE_CONSENT_REQUIRED:
            cookie_selectors = [
                'button:has-text("Accept")',
                'button:has-text("Aceitar")',
                'button:has-text("OK")',
                '.cookie-accept',
                '#cookie-accept'
            ]
            
            for selector in cookie_selectors:
                if self.element_finder.click_if_exists(selector):
                    self.logger.info("✅ کوکی‌ها پذیرفته شدند")
                    self.human_behavior.human_delay(1, 3)
                    break
        
        self.logger.info("✅ مرحله 2 تکمیل شد")
    
    def _select_authentication_method(self):
        """انتخاب روش احراز هویت"""
        self.logger.info("📍 مرحله 3: انتخاب روش احراز هویت")
        
        if self.config.AUTHENTICATION_METHOD == 'credentials':
            auth_selectors = [
                'button:has-text("credenciais")',
                'button:has-text("credentials")',
                'a:has-text("credenciais")',
                '.auth-credentials',
                '#auth-credentials'
            ]
            
            for selector in auth_selectors:
                if self.element_finder.click_if_exists(selector):
                    self.logger.info("✅ روش احراز هویت انتخاب شد")
                    self.human_behavior.human_delay(3, 6)
                    break
        
        self.logger.info("✅ مرحله 3 تکمیل شد")
    
    def _fill_login_form(self) -> bool:
        """پر کردن فرم ورود"""
        self.logger.info("📍 مرحله 4: پر کردن فرم ورود")
        
        # دریافت اطلاعات کاربری
        current_account = self.config.get_current_account()
        if not current_account:
            self.logger.error("❌ اطلاعات کاربری یافت نشد")
            return False
        
        username = current_account['username']
        password = current_account['password']
        
        # validation اطلاعات کاربری
        if not username or not password:
            self.logger.error("❌ نام کاربری یا رمز عبور خالی است")
            return False
        
        if len(username) < 3 or len(password) < 3:
            self.logger.error("❌ نام کاربری یا رمز عبور خیلی کوتاه است")
            return False
        
        self.logger.info(f"🔑 استفاده از اکانت: {username}")
        self.logger.debug(f"🔐 طول رمز عبور: {len(password)} کاراکتر")
        
        # انتظار برای تثبیت صفحه
        self.browser.page.wait_for_load_state('networkidle', timeout=10000)
        self.human_behavior.human_delay(2, 4)
        
        # بررسی عدم refresh صفحه
        if self._check_page_refresh():
            self.logger.error("❌ صفحه refresh شده است")
            return False
        
        # جستجو برای دکمه نمایش فرم (در صورت پنهان بودن)
        self._reveal_login_form()
        
        # شبیه‌سازی رفتار انسانی قبل از پر کردن فرم
        self.human_behavior.simulate_human_form_interaction()
        
        # پر کردن فیلدها با fallback
        if not self.form_automation.fill_username_field(username):
            # fallback: تلاش دستی برای یافتن فیلد username
            self.logger.warning("⚠️ form_automation برای username شکست خورد - تلاش fallback")
            username_filled = False
            username_selectors = [
                'input[name="username"]',
                'input[name="email"]', 
                'input[type="email"]',
                'input[id*="user"]',
                'input[id*="email"]',
                'input[placeholder*="email"]',
                'input[placeholder*="utilizador"]'
            ]
            
            for selector in username_selectors:
                try:
                    elements = self.browser.page.locator(selector)
                    if elements.count() > 0:
                        element = elements.first
                        if element.is_visible():
                            element.fill(username)
                            self.logger.info(f"✅ username با fallback پر شد: {selector}")
                            username_filled = True
                            break
                except Exception as e:
                    self.logger.debug(f"خطا در fallback username {selector}: {e}")
                    continue
            
            if not username_filled:
                self.logger.error("❌ نتوانستیم فیلد username را پیدا کنیم")
                return False
        
        # تاخیر انسانی بین فیلدها
        self.human_behavior.human_delay(1, 3, "thinking")
        
        if not self.form_automation.fill_password_field(password):
            # fallback: تلاش دستی برای یافتن فیلد password
            self.logger.warning("⚠️ form_automation برای password شکست خورد - تلاش fallback")
            password_filled = False
            password_selectors = [
                'input[name="password"]',
                'input[type="password"]',
                'input[id*="pass"]',
                'input[placeholder*="password"]',
                'input[placeholder*="senha"]'
            ]
            
            for selector in password_selectors:
                try:
                    elements = self.browser.page.locator(selector)
                    if elements.count() > 0:
                        element = elements.first
                        if element.is_visible():
                            element.fill(password)
                            self.logger.info(f"✅ password با fallback پر شد: {selector}")
                            password_filled = True
                            break
                except Exception as e:
                    self.logger.debug(f"خطا در fallback password {selector}: {e}")
                    continue
            
            if not password_filled:
                self.logger.error("❌ نتوانستیم فیلد password را پیدا کنیم")
                return False
        
        self.logger.info("✅ مرحله 4 تکمیل شد")
        return True
    
    def _reveal_login_form(self):
        """نمایش فرم ورود در صورت پنهان بودن"""
        self.logger.info("🔍 جستجو برای دکمه نمایش فرم")
        
        trigger_selectors = [
            'div[aria-label="Autenticação via credenciais"]',
            'div[title*="autenticação"]',
            'button:has-text("Entrar")',
            'button[aria-label*="autenticação"]',
            'button[title*="autenticação"]',
            'button[name="Entrar"]',
            '[role="button"]:has-text("credenciais")',
            '.cursor-pointer:has-text("Autenticação via credenciais")'
        ]
        
        for selector in trigger_selectors:
            if self.element_finder.click_if_exists(selector):
                self.logger.info(f"🎯 دکمه نمایش فرم یافت شد: {selector}")
                self.human_behavior.human_delay(2, 4)
                break
    
    def _handle_captcha_if_required(self) -> bool:
        """بررسی و حل کپچا در صورت نیاز"""
        self.logger.info("📍 مرحله 6: بررسی نیاز به کپچا")
        
        # انتظار برای بارگذاری کامل پاسخ سرور
        self.human_behavior.human_delay(3, 5)
        
        # بررسی وجود کپچا قبل از ارسال فرم
        self.logger.info("🔍 بررسی وجود کپچا در صفحه...")
        captcha_info = self.captcha_handler.detect_captcha()
        
        if captcha_info['detected']:
            self.logger.info(f"🎯 کپچای {captcha_info['type']} تشخیص داده شد - شروع حل")
            return self._solve_captcha()
        
        # بررسی خطاهای کپچا پس از ارسال فرم
        captcha_error_selectors = [
            ':has-text("Recaptcha é obrigatório")',
            ':has-text("reCAPTCHA")',
            ':has-text("captcha")',
            ':has-text("Captcha")',
            '.error:has-text("obrigatório")',
            '.alert:has-text("Recaptcha")',
            '.error-message:has-text("captcha")',
            '[class*="error"]:has-text("captcha")',
            '[id*="error"]:has-text("captcha")'
        ]
        
        captcha_error_found = False
        for selector in captcha_error_selectors:
            try:
                elements = self.browser.page.locator(selector)
                if elements.count() > 0:
                    for i in range(elements.count()):
                        element = elements.nth(i)
                        if element.is_visible():
                            error_text = element.text_content()
                            self.logger.info(f"🔍 خطای کپچا یافت شد: {error_text}")
                            captcha_error_found = True
                            break
                if captcha_error_found:
                    break
            except Exception as e:
                self.logger.debug(f"خطا در بررسی selector {selector}: {e}")
                continue
        
        if captcha_error_found:
            self.logger.info("🎯 خطای کپچا تشخیص داده شد - بررسی مجدد کپچا")
            # بررسی مجدد وجود کپچا
            captcha_info = self.captcha_handler.detect_captcha()
            if captcha_info['detected']:
                return self._solve_captcha()
            else:
                # fallback: جستجوی دستی برای iframe کپچا
                self.logger.warning("⚠️ detect_captcha شکست خورد - تلاش fallback")
                try:
                    iframe_exists = self.browser.page.locator('iframe[src*="recaptcha"]').count() > 0
                    if iframe_exists:
                        self.logger.info("🔍 iframe کپچا با fallback یافت شد")
                        return self._solve_captcha()
                except Exception as e:
                    self.logger.debug(f"خطا در fallback detection: {e}")
                
                self.logger.error("❌ خطای کپچا وجود دارد اما کپچا در صفحه یافت نشد")
                return False
        
        self.logger.info("✅ نیازی به کپچا نیست")
        return True
    
    def _solve_captcha(self) -> bool:
        """حل کپچا با سیستم بهینه‌شده و اعتبارسنجی دقیق"""
        self.logger.info("🔧 شروع حل کپچا")
        
        # لاگ وضعیت قبل از شروع
        if hasattr(self.captcha_handler, 'log_captcha_status'):
            self.captcha_handler.log_captcha_status()
        
        # شبیه‌سازی رفتار انسانی قبل از کپچا (کاهش زمان)
        self.human_behavior.simulate_captcha_thinking()
        
        # استفاده از متد بهینه‌شده captcha_handler
        success = self.captcha_handler.solve_captcha()
        
        if success:
            # تاخیر کوتاه بعد از حل کپچا
            self.human_behavior.human_delay(0.5, 1, "thinking")
            
            # لاگ وضعیت بعد از تلاش حل
            if hasattr(self.captcha_handler, 'log_captcha_status'):
                self.captcha_handler.log_captcha_status()
            
            # اعتبارسنجی اضافی: بررسی وضعیت captcha_handler
            if hasattr(self.captcha_handler, 'captcha_solved') and self.captcha_handler.captcha_solved:
                self.logger.info("✅ کپچا با موفقیت حل و تأیید شد")
                return True
            else:
                self.logger.warning("⚠️ captcha_handler موفقیت گزارش کرد اما وضعیت داخلی تأیید نمی‌کند")
                
                # تلاش برای اعتبارسنجی مستقل
                independent_verification = self._independent_captcha_verification()
                if independent_verification:
                    self.logger.info("✅ اعتبارسنجی مستقل کپچا موفق")
                    # به‌روزرسانی وضعیت handler
                    if hasattr(self.captcha_handler, 'captcha_solved'):
                        self.captcha_handler.captcha_solved = True
                    return True
                else:
                    self.logger.error("❌ اعتبارسنجی مستقل کپچا ناموفق")
                    return False
        else:
            self.logger.error("❌ حل کپچا ناموفق بود")
            # لاگ جزئیات اضافی برای دیباگ
            if hasattr(self.captcha_handler, 'get_captcha_status'):
                status = self.captcha_handler.get_captcha_status()
                self.logger.debug(f"🔍 جزئیات شکست: {status}")
            return False
    
    def _click_submit_button_forcefully(self) -> bool:
        """
        با استفاده از جاوا اسکریپت، کلیک را روی دکمه ورود شبیه‌سازی می‌کند
        تا از مشکل لایه‌های نامرئی عبور کند.
        """
        self.logger.info("🚀 ارسال فرم با کلیک شبیه‌سازی‌شده (JavaScript)...")
        try:
            # انتظار کوتاه برای تأیید کپچا (کاهش از 5 ثانیه به 2 ثانیه)
            self.logger.info("⏳ انتظار برای تأیید کپچا (2 ثانیه)...")
            self.page.wait_for_timeout(2000)

            submit_button_selector = "button[type='submit']"
            
            # بررسی اینکه آیا دکمه قابل کلیک است
            try:
                is_disabled = self.page.locator(submit_button_selector).is_disabled(timeout=3000)
                if is_disabled:
                    self.logger.error("❌ دکمه ورود غیرفعال است. احتمالاً کپچا پذیرفته نشده.")
                    return False
            except:
                self.logger.warning("⚠️ نتوانست وضعیت دکمه را بررسی کند، ادامه می‌دهد...")

            self.logger.info("🎯 دکمه ورود فعال است. تلاش برای کلیک با جاوا اسکریپت...")
            
            # کلیک با جاوا اسکریپت
            click_result = self.page.evaluate(f'''
                () => {{
                    const button = document.querySelector("{submit_button_selector}");
                    if (button) {{
                        button.click();
                        return true;
                    }}
                    return false;
                }}
            ''')
            
            if click_result:
                self.logger.info("✅ کلیک با جاوا اسکریپت با موفقیت انجام شد.")
                self.page.wait_for_load_state('networkidle', timeout=15000)
                return True
            else:
                self.logger.error("❌ دکمه submit یافت نشد")
                return False
                
        except Exception as e:
            self.logger.error(f"❌ خطا در کلیک اجباری روی دکمه submit: {e}")
            return False 

    def _verify_login_success(self) -> bool:
        """تأیید موفقیت ورود"""
        self.logger.info("📍 مرحله 8: تأیید ورود")
        
        # انتظار برای بارگذاری صفحه جدید
        self.human_behavior.human_delay(5, 8)
        
        # بررسی URL فعلی
        current_url = self.browser.page.url
        self.logger.info(f"🔍 URL فعلی: {current_url}")
        
        # بررسی title صفحه
        try:
            page_title = self.browser.page.title()
            self.logger.info(f"🔍 عنوان صفحه: {page_title}")
        except:
            page_title = "نامشخص"
        
        # بررسی وجود المان‌های مشخص کننده ورود موفق
        success_indicators = [
            'a[href*="logout"]',
            'button:has-text("Sair")',
            'button:has-text("Logout")',
            '.user-menu',
            '.profile-menu',
            '.dashboard'
        ]
        
        for indicator in success_indicators:
            try:
                if self.browser.page.locator(indicator).count() > 0:
                    self.logger.info(f"✅ ورود موفق تأیید شد - المان یافت شد: {indicator}")
                    return True
            except:
                continue
        
        # بررسی عدم وجود فرم ورود (نشانه ورود موفق)
        login_form_exists = False
        try:
            login_form_exists = self.browser.page.locator('input[type="password"]').count() > 0
        except:
            pass
        
        # بررسی URL های مشخص کننده ورود موفق
        success_urls = ['/dashboard', '/home', '/main']
        for url_indicator in success_urls:
            if url_indicator in current_url.lower():
                self.logger.info(f"✅ ورود موفق تأیید شد - URL موفقیت: {current_url}")
                return True
    
    def _independent_captcha_verification(self) -> bool:
        """اعتبارسنجی مستقل کپچا - بررسی مستقل از captcha_handler"""
        try:
            self.logger.info("🔍 شروع اعتبارسنجی مستقل کپچا...")
            
            # بررسی وجود توکن در صفحه
            token_verification = self.browser.page.evaluate("""
                () => {
                    // بررسی فیلدهای response
                    const responseSelectors = [
                        'textarea[name="g-recaptcha-response"]',
                        'input[name="g-recaptcha-response"]',
                        '#g-recaptcha-response'
                    ];
                    
                    for (let selector of responseSelectors) {
                        const field = document.querySelector(selector);
                        if (field && field.value && field.value.length > 20) {
                            return {
                                hasToken: true,
                                tokenLength: field.value.length,
                                source: selector
                            };
                        }
                    }
                    
                    // بررسی grecaptcha
                    if (typeof grecaptcha !== 'undefined') {
                        try {
                            const response = grecaptcha.getResponse();
                            if (response && response.length > 20) {
                                return {
                                    hasToken: true,
                                    tokenLength: response.length,
                                    source: 'grecaptcha.getResponse()'
                                };
                            }
                        } catch (e) {}
                    }
                    
                    return {hasToken: false};
                }
            """)
            
            if token_verification.get('hasToken'):
                self.logger.info(f"✅ توکن معتبر یافت شد - طول: {token_verification.get('tokenLength')} - منبع: {token_verification.get('source')}")
                
                # بررسی اضافی: آیا کپچا هنوز نمایش داده می‌شود؟
                captcha_visible = self._check_captcha_visibility()
                if not captcha_visible:
                    self.logger.info("✅ کپچا دیگر نمایش داده نمی‌شود")
                    return True
                else:
                    self.logger.warning("⚠️ توکن یافت شد اما کپچا هنوز نمایش داده می‌شود")
                    return False
            else:
                self.logger.error("❌ هیچ توکن معتبری یافت نشد")
                return False
                
        except Exception as e:
            self.logger.error(f"❌ خطا در اعتبارسنجی مستقل کپچا: {e}")
            return False
    
    def _check_captcha_visibility(self) -> bool:
        """بررسی نمایش کپچا در صفحه"""
        try:
            captcha_visible = self.browser.page.evaluate("""
                () => {
                    // بررسی iframe های کپچا
                    const captchaFrames = document.querySelectorAll('iframe[src*="recaptcha"], iframe[src*="hcaptcha"]');
                    for (let frame of captchaFrames) {
                        const rect = frame.getBoundingClientRect();
                        const style = window.getComputedStyle(frame);
                        if (style.display !== 'none' && 
                            style.visibility !== 'hidden' && 
                            rect.width > 0 && 
                            rect.height > 0) {
                            return true;
                        }
                    }
                    
                    // بررسی چالش‌های تصویری
                    const challengeFrames = document.querySelectorAll('iframe[src*="bframe"]');
                    for (let frame of challengeFrames) {
                        const rect = frame.getBoundingClientRect();
                        const style = window.getComputedStyle(frame);
                        if (style.display !== 'none' && 
                            style.visibility !== 'hidden' && 
                            rect.width > 0 && 
                            rect.height > 0) {
                            return true;
                        }
                    }
                    
                    return false;
                }
            """)
            
            return captcha_visible
            
        except Exception as e:
            self.logger.error(f"❌ خطا در بررسی نمایش کپچا: {e}")
            return True  # در صورت خطا، فرض می‌کنیم کپچا هنوز نمایش داده می‌شود
    
    def reset_captcha_state(self):
        """ریست کامل وضعیت کپچا"""
        if hasattr(self.captcha_handler, 'reset_captcha_state'):
            self.captcha_handler.reset_captcha_state()
            self.logger.info("🔄 وضعیت کپچا در handler ریست شد")
        else:
            self.logger.warning("⚠️ captcha_handler متد reset_captcha_state ندارد")
        
        if not login_form_exists and 'login' not in current_url.lower():
            self.logger.info("✅ ورود موفق تأیید شد - فرم ورود وجود ندارد و URL تغییر کرده")
            return True
        
        # اگر هنوز در صفحه login هستیم، ورود ناموفق بوده
        if 'login' in current_url.lower():
            self.logger.warning("⚠️ ورود ناموفق - هنوز در صفحه login هستیم")
            return False
        
        # استفاده از page_detector به عنوان آخرین گزینه
        result = self.page_detector.is_logged_in()
        self.logger.info(f"🔍 نتیجه page_detector: {result}")
        return result
    
    def _check_page_refresh(self) -> bool:
        """بررسی refresh شدن صفحه"""
        try:
            page_refreshed = self.browser.page.evaluate("window.pageRefreshed || false")
            if page_refreshed:
                return True
            
            current_url = self.browser.page.url
            if not current_url or 'login' not in current_url:
                return True
            
            return False
            
        except Exception:
            return False