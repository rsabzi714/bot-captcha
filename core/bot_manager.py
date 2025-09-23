# core/bot_manager.py
import time
import logging
import signal
import threading
from datetime import datetime, timedelta
from typing import Optional

from config import Config
from proxy_manager import ProxyManager
from captcha_solver import CaptchaSolver
from telegram_notifier import TelegramNotifier
from browser.browser_launcher import BrowserLauncher
from core.login_handler import LoginHandler
from core.session_manager import SessionManager
from utils.error_handler import ErrorHandler
from modules.monitoring import MonitoringService

class BotManager:
    """مدیر اصلی ربات MNE - مسئول هماهنگی بین ماژول‌ها"""
    
    def __init__(self):
        self.config = Config()
        self.logger = self._setup_logger()
        
        # اعتبارسنجی تنظیمات
        config_errors = self.config.validate_config()
        if config_errors:
            self.logger.error("❌ خطاهای تنظیمات:")
            for error in config_errors:
                self.logger.error(f"   - {error}")
            raise ValueError("تنظیمات ناقص یا نامعتبر")
        
        # راه‌اندازی اجزاء اصلی
        self.proxy_manager = ProxyManager(self.config.PROXY_CONFIG)
        self.captcha_solver = CaptchaSolver(self.config.CAPTCHA_API_KEY)
        self.error_handler = ErrorHandler(self.logger)
        
        # تلگرام (اختیاری)
        self.telegram = self._setup_telegram()
        
        # ماژول‌های اصلی
        self.browser_launcher = None
        self.login_handler = None
        self.session_manager = None
        self.monitoring = None
        
        # وضعیت ربات
        self.is_running = False
        self.is_logged_in = False
        self.login_attempts = 0
        self.max_login_attempts = 3
        
    def _setup_logger(self) -> logging.Logger:
        """تنظیم سیستم لاگ‌گیری بهینه‌شده"""
        logger = logging.getLogger('MNE_Bot')
        
        # تنظیم سطح لاگ از config
        log_level = getattr(logging, self.config.LOG_LEVEL.upper(), logging.INFO)
        logger.setLevel(log_level)
        
        # حذف handler های قبلی
        for handler in logger.handlers[:]:
            logger.removeHandler(handler)
        
        # فرمت لاگ از config
        formatter = logging.Formatter(
            self.config.LOG_FORMAT,
            datefmt=self.config.LOG_DATE_FORMAT
        )
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        console_handler.setLevel(log_level)
        logger.addHandler(console_handler)
        
        # File handler با rotation
        if self.config.LOG_TO_FILE:
            try:
                from logging.handlers import RotatingFileHandler
                file_handler = RotatingFileHandler(
                    self.config.LOG_FILE_PATH,
                    maxBytes=self.config.LOG_MAX_SIZE,
                    backupCount=self.config.LOG_BACKUP_COUNT,
                    encoding='utf-8'
                )
                file_handler.setFormatter(formatter)
                file_handler.setLevel(log_level)
                logger.addHandler(file_handler)
                logger.info(f"📝 سیستم لاگ‌گیری راه‌اندازی شد - سطح: {self.config.LOG_LEVEL}")
            except Exception as e:
                print(f"⚠️ خطا در ایجاد فایل لاگ: {e}")
        
        return logger
    
    def _setup_telegram(self) -> Optional[TelegramNotifier]:
        """راه‌اندازی تلگرام (اختیاری)"""
        if self.config.TELEGRAM_BOT_TOKEN and self.config.TELEGRAM_CHAT_ID:
            return TelegramNotifier(
                self.config.TELEGRAM_BOT_TOKEN,
                self.config.TELEGRAM_CHAT_ID
            )
        else:
            self.logger.warning("⚠️ تنظیمات تلگرام موجود نیست - اعلان‌ها غیرفعال است")
            return None
    
    def initialize(self) -> bool:
        """راه‌اندازی اولیه ربات"""
        try:
            self.logger.info("🚀 شروع راه‌اندازی ربات MNE")
            
            # راه‌اندازی مرورگر
            self.browser_launcher = BrowserLauncher(
                proxy_manager=self.proxy_manager,
                config=self.config,
                logger=self.logger
            )
            
            if not self.browser_launcher.launch():
                self.logger.error("❌ شکست در راه‌اندازی مرورگر")
                return False
            
            # راه‌اندازی ماژول‌های اصلی
            self.session_manager = SessionManager(
                browser=self.browser_launcher.get_browser(),
                config=self.config,
                logger=self.logger
            )
            
            self.login_handler = LoginHandler(
                browser=self.browser_launcher,
                page=self.browser_launcher.page,
                config=self.config,
                captcha_solver=self.captcha_solver,
                logger=self.logger
            )
            
            self.monitoring = MonitoringService(
                telegram=self.telegram,
                logger=self.logger
            )
            
            self.logger.info("✅ ربات با موفقیت راه‌اندازی شد")
            return True
            
        except Exception as e:
            self.error_handler.handle_error("initialization", e)
            return False
    
    def start(self):
        """شروع عملیات ربات"""
        if not self.initialize():
            return
        
        self.is_running = True
        self.logger.info("🔄 شروع چرخه نظارت")
        
        try:
            while self.is_running:
                self._main_loop()
                time.sleep(self.config.MONITORING_INTERVAL)
                
        except KeyboardInterrupt:
            self.logger.info("⏹️ توقف ربات توسط کاربر")
        except Exception as e:
            self.error_handler.handle_error("main_loop", e)
        finally:
            self.cleanup()
    
    def _main_loop(self):
        """حلقه اصلی ربات"""
        try:
            # بررسی عدم نشت IP در هر چرخه
            if not self._validate_proxy_security():
                self.logger.error("❌ مشکل امنیتی پروکسی تشخیص داده شد")
                return
            
            # بررسی وضعیت ورود
            if not self.is_logged_in:
                self._attempt_login()
            else:
                # بررسی مداوم وضعیت login
                if self._verify_current_login_status():
                    # ربات با موفقیت وارد شده است
                    self.logger.info("✅ ربات با موفقیت وارد شده و آماده است")
                    # انتظار قبل از چرخه بعدی
                    self._wait_before_next_cycle()
                else:
                    self.logger.warning("⚠️ وضعیت login از دست رفته - تلاش مجدد")
                    self.is_logged_in = False
                    self._attempt_login()
                
        except Exception as e:
            self.error_handler.handle_error("main_loop_iteration", e)
    
    def _validate_proxy_security(self) -> bool:
        """اعتبارسنجی امنیت پروکسی و عدم نشت IP"""
        try:
            # بررسی هر 5 چرخه (تقریباً هر 2.5 دقیقه)
            if not hasattr(self, '_proxy_check_counter'):
                self._proxy_check_counter = 0
            
            self._proxy_check_counter += 1
            
            if self._proxy_check_counter % 5 == 0:
                self.logger.info("🔍 بررسی امنیت پروکسی...")
                
                # بررسی وضعیت پروکسی
                if not self.proxy_manager.current_proxy:
                    self.logger.error("❌ هیچ پروکسی فعال نیست")
                    return False
                
                # اعتبارسنجی عدم نشت IP
                if not self.proxy_manager.validate_no_ip_leak():
                    self.logger.error("❌ نشت IP تشخیص داده شد - تلاش برای چرخش پروکسی")
                    
                    # تلاش برای چرخش پروکسی
                    if self.proxy_manager.force_rotation():
                        self.logger.info("✅ پروکسی با موفقیت چرخش یافت")
                        
                        # تست مجدد پس از چرخش
                        if not self.proxy_manager.validate_no_ip_leak():
                            self.logger.error("❌ نشت IP همچنان ادامه دارد")
                            return False
                    else:
                        self.logger.error("❌ شکست در چرخش پروکسی")
                        return False
                
                self.logger.info("✅ امنیت پروکسی تأیید شد")
            
            return True
            
        except Exception as e:
            self.logger.error(f"❌ خطا در اعتبارسنجی امنیت پروکسی: {e}")
            return False
    
    def _attempt_login(self):
        """تلاش برای ورود"""
        if self.login_attempts >= self.max_login_attempts:
            self.logger.error(f"❌ حداکثر تلاش ورود ({self.max_login_attempts}) به پایان رسید")
            self.is_running = False
            return
        
        self.login_attempts += 1
        self.logger.info(f"🔐 شروع تلاش ورود #{self.login_attempts}/{self.max_login_attempts}")
        
        try:
            # بررسی وضعیت مرورگر
            if not self.browser_launcher or not self.browser_launcher.is_browser_alive():
                self.logger.warning("⚠️ مرورگر در دسترس نیست - تلاش برای بازیابی...")
                
                # تلاش برای بازیابی مرورگر
                recovery_success = False
                if self.browser_launcher:
                    recovery_success = self.browser_launcher.recover_browser()
                    if recovery_success:
                        # بروزرسانی login_handler با page جدید
                        self.login_handler.page = self.browser_launcher.page
                        self.logger.info("✅ مرورگر بازیابی شد و login_handler بروزرسانی شد")
                
                if not recovery_success:
                    self.logger.warning("⚠️ شکست در بازیابی - راه‌اندازی کامل مجدد...")
                    if not self.initialize():
                        self.logger.error("❌ شکست در راه‌اندازی مجدد مرورگر")
                        return
            
            # تلاش ورود
            if self.login_handler.perform_login():
                self.is_logged_in = True
                self.login_attempts = 0  # ریست شمارنده
                self.logger.info("✅ ورود موفقیت‌آمیز")
                
                # ذخیره جلسه
                self.session_manager.save_session()
                
                # اطلاع‌رسانی تلگرام
                if self.telegram:
                    self.telegram.send_status_update(
                        "ورود موفق",
                        f"ربات با موفقیت وارد سیستم شد"
                    )
            else:
                self.logger.warning(f"⚠️ تلاش ورود #{self.login_attempts} ناموفق")
                
                # انتظار قبل از تلاش مجدد
                if self.login_attempts < self.max_login_attempts:
                    wait_time = 30  # 30 ثانیه انتظار
                    self.logger.info(f"⏳ انتظار {wait_time} ثانیه قبل از تلاش مجدد...")
                    time.sleep(wait_time)
                    
        except Exception as e:
            error_msg = str(e)
            
            # مدیریت خطاهای خاص
            if "Target page, context or browser has been closed" in error_msg:
                self.logger.warning("⚠️ Browser/context بسته شده - تلاش برای بازیابی...")
                if self.browser_launcher and self.browser_launcher.recover_browser():
                    # بروزرسانی login_handler با page جدید
                    self.login_handler.page = self.browser_launcher.page
                    self.logger.info("✅ مرورگر بازیابی شد")
                    # ریست وضعیت ورود برای تلاش مجدد
                    self.is_logged_in = False
                    return  # تلاش مجدد در چرخه بعدی
                else:
                    self.logger.error("❌ شکست در بازیابی مرورگر")
                    # ریست کامل
                    self.is_logged_in = False
            
            # مدیریت خطای ERR_CONNECTION_CLOSED (مسدود شدن IP)
            elif "ERR_CONNECTION_CLOSED" in error_msg or "connection was closed" in error_msg.lower() or "fechou a ligação" in error_msg:
                self.logger.warning("🚫 تشخیص مسدود شدن IP - تغییر فوری پروکسی")
                
                # تغییر فوری پروکسی
                if self.proxy_manager.force_proxy_rotation():
                    self.logger.info("✅ پروکسی تغییر کرد - راه‌اندازی مجدد مرورگر")
                    
                    # بستن مرورگر فعلی
                    if self.browser_launcher:
                        try:
                            self.browser_launcher.cleanup()
                        except:
                            pass
                    
                    # راه‌اندازی مجدد با پروکسی جدید
                    if self.initialize():
                        self.logger.info("✅ مرورگر با پروکسی جدید راه‌اندازی شد")
                        # کاهش شمارنده تلاش برای اینکه این تلاش محسوب نشود
                        self.login_attempts -= 1
                        return  # تلاش مجدد در چرخه بعدی
                    else:
                        self.logger.error("❌ شکست در راه‌اندازی مجدد با پروکسی جدید")
                else:
                    self.logger.error("❌ شکست در تغییر پروکسی")
            
            self.error_handler.handle_error("login_attempt", e)
            self.logger.warning(f"⚠️ تلاش ورود #{self.login_attempts} ناموفق")
            
            # انتظار قبل از تلاش مجدد
            if self.login_attempts < self.max_login_attempts:
                wait_time = 30
                self.logger.info(f"⏳ انتظار {wait_time} ثانیه قبل از تلاش مجدد...")
                time.sleep(wait_time)
    
    def _verify_current_login_status(self) -> bool:
        """بررسی وضعیت فعلی login"""
        try:
            if not self.browser_launcher or not self.browser_launcher.page:
                return False
            
            # استفاده از page_detector برای بررسی وضعیت
            from utils.page_detector import PageDetector
            page_detector = PageDetector(self.browser_launcher.page, self.logger)
            
            is_logged = page_detector.is_logged_in()
            
            if is_logged:
                self.logger.debug("✅ وضعیت login تأیید شد")
            else:
                self.logger.debug("❌ وضعیت login تأیید نشد")
            
            return is_logged
            
        except Exception as e:
            self.logger.error(f"❌ خطا در بررسی وضعیت login: {e}")
            return False
    
    def _wait_before_next_cycle(self):
        """انتظار هوشمند قبل از چرخه بعدی"""
        wait_time = self.config.MONITORING_INTERVAL
        self.logger.info(f"⏳ انتظار {wait_time} ثانیه تا چرخه بعدی...")
        time.sleep(wait_time)
    
    def stop(self):
        """توقف ربات"""
        self.logger.info("🛑 درخواست توقف ربات")
        self.is_running = False
    
    def cleanup(self):
        """تمیزکاری منابع"""
        try:
            if self.browser_launcher:
                self.browser_launcher.close()
            
            if self.session_manager:
                self.session_manager.save_current_session()
            
            self.logger.info("🧹 تمیزکاری منابع انجام شد")
            
        except Exception as e:
            self.logger.error(f"❌ خطا در تمیزکاری: {e}")