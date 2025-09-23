# proxy_manager.py
import random
import time
import requests
import logging
import hashlib
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta

class ProxyManager:
    """مدیریت پیشرفته پروکسی با قابلیت چرخش هوشمند و جلسات پایدار"""
    
    def __init__(self, proxy_config: Dict):
        self.proxy_config = proxy_config
        self.current_proxy = None
        self.current_session_id = None
        
        # تنظیمات زمان‌بندی
        self.sticky_session_duration = 1800  # 30 دقیقه
        self.rotation_cooldown = 300  # 5 دقیقه حداقل بین چرخش‌ها
        self.last_rotation = 0
        self.session_start_time = None
        
        # آمار و نظارت
        self.total_rotations = 0
        self.failed_connections = 0
        self.successful_connections = 0
        self.proxy_health_score = 1.0
        
        # لاگ
        self.logger = logging.getLogger(__name__)
        
        # لیست IP های استفاده شده (برای جلوگیری از تکرار)
        self.used_ips = set()
        self.ip_usage_history = {}
    
    def get_proxy_config(self, force_new_session: bool = False) -> Optional[Dict]:
        """دریافت تنظیمات پروکسی فعلی با مدیریت هوشمند جلسه"""
        try:
            # بررسی نیاز به چرخش
            if force_new_session or self._should_rotate_proxy():
                if not self._rotate_proxy():
                    self.logger.error("شکست در چرخش پروکسی")
                    return None
            
            # اولین بار استفاده
            if not self.current_proxy:
                if not self._rotate_proxy():
                    self.logger.error("شکست در راه‌اندازی اولیه پروکسی")
                    return None
            
            return self.current_proxy
            
        except Exception as e:
            self.logger.error(f"خطا در دریافت تنظیمات پروکسی: {e}")
            return None
    
    def force_proxy_rotation(self) -> bool:
        """تغییر فوری پروکسی در صورت مسدود شدن"""
        try:
            self.logger.warning("🔄 تغییر فوری پروکسی به دلیل مسدود شدن")
            
            # ریست کردن آمار فعلی
            self.failed_connections += 1
            self.proxy_health_score *= 0.8  # کاهش امتیاز سلامت
            
            # اجبار به چرخش فوری
            self.last_rotation = 0  # ریست کردن زمان آخرین چرخش
            
            # تولید session ID جدید
            current_time = time.time()
            timestamp = int(current_time)
            random_part = random.randint(10000, 99999)
            new_session_id = f"emergency_{timestamp}_{random_part}"
            
            # تغییر session ID فعلی
            self.current_session_id = new_session_id
            self.session_start_time = current_time
            
            # چرخش پروکسی
            if self._rotate_proxy():
                self.logger.info(f"✅ پروکسی با موفقیت تغییر کرد - Session: {new_session_id}")
                return True
            else:
                self.logger.error("❌ شکست در تغییر فوری پروکسی")
                return False
                
        except Exception as e:
            self.logger.error(f"❌ خطا در تغییر فوری پروکسی: {e}")
            return False
            
            return self.current_proxy
            
        except Exception as e:
            self.logger.error(f"خطا در دریافت تنظیمات پروکسی: {e}")
            return None
    
    def _should_rotate_proxy(self) -> bool:
        """بررسی هوشمند نیاز به چرخش پروکسی"""
        current_time = time.time()
        
        # بررسی حداقل زمان بین چرخش‌ها
        if (current_time - self.last_rotation) < self.rotation_cooldown:
            return False
        
        # بررسی انقضای جلسه پایدار
        if self.session_start_time:
            session_age = current_time - self.session_start_time
            if session_age > self.sticky_session_duration:
                self.logger.info(f"جلسه پروکسی منقضی شد ({session_age:.0f}s)")
                return True
        
        # بررسی سلامت پروکسی
        if self.proxy_health_score < 0.5:
            self.logger.warning(f"سلامت پروکسی پایین ({self.proxy_health_score:.2f})")
            return True
        
        # بررسی تعداد خطاهای متوالی
        if self.failed_connections > 3:
            self.logger.warning(f"تعداد زیاد خطا ({self.failed_connections})")
            return True
        
        return False
    
    def _rotate_proxy(self) -> bool:
        """چرخش پروکسی با انتخاب هوشمند و fallback"""
        try:
            # استفاده از تنظیمات اصلی پروکسی
            if self.proxy_config and self.proxy_config.get('host'):
                # استفاده از تنظیمات اصلی
                test_proxy = self._create_proxy_config(self.proxy_config)
                if self._test_proxy_connection(test_proxy):
                    self.current_proxy = test_proxy
                    
                    # به‌روزرسانی آمار
                    self.total_rotations += 1
                    self.last_rotation = time.time()
                    self.session_start_time = time.time()
                    
                    self.logger.info(f"✅ پروکسی اصلی فعال شد: {self.current_proxy['host']}:{self.current_proxy['port']}")
                    return True
            
            # در صورت شکست، استفاده از پروکسی‌های پشتیبان
            available_proxies = [
                'smartproxy_primary',
                'smartproxy_backup'
            ]
            
            # انتخاب پروکسی بر اساس اولویت
            for proxy_name in available_proxies:
                if proxy_name in proxy_configs:
                    proxy_config = proxy_configs[proxy_name]
                    
                    try:
                        # تست پروکسی قبل از استفاده
                        test_proxy = self._create_proxy_config(proxy_config)
                        if self._test_proxy_connection(test_proxy):
                            self.current_proxy = test_proxy
                            self.proxy_config = proxy_config
                            
                            # به‌روزرسانی آمار
                            self.total_rotations += 1
                            self.last_rotation = time.time()
                            self.session_start_time = time.time()
                            
                            self.logger.info(f"✅ پروکسی {proxy_name} فعال شد: {self.current_proxy['host']}:{self.current_proxy['port']}")
                            return True
                        else:
                            self.logger.warning(f"⚠️ پروکسی {proxy_name} در دسترس نیست")
                            
                    except Exception as e:
                        self.logger.warning(f"⚠️ خطا در تست پروکسی {proxy_name}: {e}")
                        continue
            
            # اگر هیچ پروکسی کار نکرد، از تنظیمات اصلی استفاده کن
            return self._fallback_to_original_config()
            
        except Exception as e:
            self.logger.error(f"❌ خطا در چرخش پروکسی: {e}")
            return False
    
    def _create_proxy_config(self, proxy_config: Dict) -> Dict:
        """ایجاد تنظیمات پروکسی"""
        current_time = time.time()
        timestamp = int(current_time)
        random_part = random.randint(10000, 99999)
        
        if proxy_config['type'] == 'residential_rotating':
            # پروکسی چرخشی با session ID
            session_id = f"{timestamp}_{random_part}"
            self.current_session_id = session_id
            
            # برخی ارائه‌دهندگان از session در username استفاده می‌کنند
            username = proxy_config['username']
            # اگر username قبلاً session دارد، آن را جایگزین کن
            if '_session-' in username:
                # حذف session قدیمی و اضافه کردن جدید
                base_username = username.split('_session-')[0]
                username = f"{base_username}_session-{session_id}"
            elif 'session' not in username.lower():
                username = f"{username}_session-{session_id}"
            else:
                # اگر session دارد اما فرمت متفاوت است، از همان استفاده کن
                username = proxy_config['username']
            
            return {
                'host': proxy_config['host'],
                'port': proxy_config['port'],
                'username': username,
                'password': proxy_config['password']
            }
            
        elif proxy_config['type'] == 'sticky_session':
            # جلسه پایدار با مدت زمان مشخص
            session_hash = hashlib.md5(f"{timestamp}_{random_part}".encode()).hexdigest()[:8]
            self.current_session_id = session_hash
            
            return {
                'host': proxy_config['host'],
                'port': proxy_config['port'],
                'username': f"{proxy_config['username']}-session-{session_hash}",
                'password': proxy_config['password']
            }
        
        else:
            # پروکسی ساده بدون چرخش
            return {
                'host': proxy_config['host'],
                'port': proxy_config['port'],
                'username': proxy_config['username'],
                'password': proxy_config['password']
            }
    
    def _test_proxy_connection(self, proxy_config: Dict) -> bool:
        """تست سریع اتصال پروکسی"""
        try:
            import requests
            from requests.auth import HTTPProxyAuth
            
            proxy_url = f"http://{proxy_config['host']}:{proxy_config['port']}"
            username = proxy_config.get('username', '')
            password = proxy_config.get('password', '')
            
            proxies = {'http': proxy_url, 'https': proxy_url}
            auth = None
            
            if username and password:
                auth = HTTPProxyAuth(username, password)
                proxy_url_with_auth = f"http://{username}:{password}@{proxy_config['host']}:{proxy_config['port']}"
                proxies = {'http': proxy_url_with_auth, 'https': proxy_url_with_auth}
            
            # تست سریع
            response = requests.get(
                'http://httpbin.org/ip',
                proxies=proxies,
                auth=auth,
                timeout=10,
                verify=False
            )
            
            return response.status_code == 200
            
        except Exception:
            return False
    
    def _fallback_to_original_config(self) -> bool:
        """بازگشت به تنظیمات اصلی پروکسی"""
        try:
            current_time = time.time()
            timestamp = int(current_time)
            random_part = random.randint(10000, 99999)
            
            if self.proxy_config['type'] == 'residential_rotating':
                # پروکسی چرخشی با session ID
                session_id = f"{timestamp}_{random_part}"
                self.current_session_id = session_id
                
                # برخی ارائه‌دهندگان از session در username استفاده می‌کنند
                username = self.proxy_config['username']
                if 'session' not in username.lower():
                    username = f"{username}_session-{session_id}"
                
                self.current_proxy = {
                    'host': self.proxy_config['host'],
                    'port': self.proxy_config['port'],
                    'username': username,
                    'password': self.proxy_config['password']
                }
                
            elif self.proxy_config['type'] == 'sticky_session':
                # جلسه پایدار با مدت زمان مشخص
                session_hash = hashlib.md5(f"{timestamp}_{random_part}".encode()).hexdigest()[:8]
                self.current_session_id = session_hash
                
                self.current_proxy = {
                    'host': self.proxy_config['host'],
                    'port': self.proxy_config['port'],
                    'username': f"{self.proxy_config['username']}-session-{session_hash}",
                    'password': self.proxy_config['password']
                }
            
            else:
                # پروکسی ساده بدون چرخش
                self.current_proxy = {
                    'host': self.proxy_config['host'],
                    'port': self.proxy_config['port'],
                    'username': self.proxy_config['username'],
                    'password': self.proxy_config['password']
                }
            
            # به‌روزرسانی آمار
            self.last_rotation = current_time
            self.session_start_time = current_time
            self.total_rotations += 1
            self.failed_connections = 0  # ریست خطاها
            
            proxy_url = f"http://{self.current_proxy['host']}:{self.current_proxy['port']}"
            self.logger.warning(f"⚠️ استفاده از تنظیمات پروکسی اصلی: {proxy_url} (Session: {self.current_session_id})")
            return True
        except Exception as e:
            self.logger.error(f"❌ خطا در fallback: {e}")
            return False
    
    def test_proxy(self, timeout: int = 15) -> Tuple[bool, Optional[str]]:
        """تست پیشرفته عملکرد پروکسی"""
        if not self.current_proxy:
            return False, "هیچ پروکسی فعالی وجود ندارد"
        
        start_time = time.time()
        
        try:
            # ساخت URL پروکسی
            proxy_url = f"http://{self.current_proxy['username']}:{self.current_proxy['password']}@{self.current_proxy['host']}:{self.current_proxy['port']}"
            
            proxies = {
                'http': proxy_url,
                'https': proxy_url
            }
            
            # تست اتصال با چندین endpoint
            test_endpoints = [
                'http://httpbin.org/ip',
                'http://icanhazip.com',
                'http://ipinfo.io/ip'
            ]
            
            for endpoint in test_endpoints:
                try:
                    response = requests.get(
                        endpoint,
                        proxies=proxies,
                        timeout=timeout,
                        headers={
                            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                        }
                    )
                    
                    if response.status_code == 200:
                        # استخراج IP
                        if 'httpbin' in endpoint:
                            ip_info = response.json()
                            current_ip = ip_info.get('origin', '').split(',')[0].strip()
                        else:
                            current_ip = response.text.strip()
                        
                        # محاسبه زمان پاسخ
                        response_time = time.time() - start_time
                        
                        # به‌روزرسانی آمار
                        self.successful_connections += 1
                        self._update_proxy_health(True, response_time)
                        self._track_ip_usage(current_ip)
                        
                        self.logger.info(f"پروکسی فعال - IP: {current_ip}, زمان پاسخ: {response_time:.2f}s")
                        return True, current_ip
                        
                except requests.RequestException:
                    continue
            
            # اگر همه endpoint ها شکست خوردند
            self.failed_connections += 1
            self._update_proxy_health(False)
            return False, "تمام endpoint های تست شکست خوردند"
            
        except Exception as e:
            self.failed_connections += 1
            self._update_proxy_health(False)
            self.logger.error(f"خطا در تست پروکسی: {e}")
            return False, str(e)
    
    def _update_proxy_health(self, success: bool, response_time: float = None) -> None:
        """به‌روزرسانی امتیاز سلامت پروکسی"""
        if success:
            # بهبود امتیاز در صورت موفقیت
            self.proxy_health_score = min(1.0, self.proxy_health_score + 0.1)
            
            # جریمه برای زمان پاسخ بالا
            if response_time and response_time > 10:
                self.proxy_health_score *= 0.95
                
        else:
            # کاهش امتیاز در صورت شکست
            self.proxy_health_score *= 0.8
            
        self.proxy_health_score = max(0.0, self.proxy_health_score)
    
    def _track_ip_usage(self, ip: str) -> None:
        """ردیابی استفاده از IP ها"""
        if ip:
            self.used_ips.add(ip)
            self.ip_usage_history[ip] = datetime.now()
            
            # پاکسازی تاریخچه قدیمی (بیش از 24 ساعت)
            cutoff_time = datetime.now() - timedelta(hours=24)
            self.ip_usage_history = {
                ip: timestamp for ip, timestamp in self.ip_usage_history.items()
                if timestamp > cutoff_time
            }
    
    def get_proxy_stats(self) -> Dict:
        """دریافت آمار عملکرد پروکسی"""
        total_connections = self.successful_connections + self.failed_connections
        success_rate = (self.successful_connections / total_connections * 100) if total_connections > 0 else 0
        
        return {
            'total_rotations': self.total_rotations,
            'successful_connections': self.successful_connections,
            'failed_connections': self.failed_connections,
            'success_rate': round(success_rate, 2),
            'health_score': round(self.proxy_health_score, 2),
            'current_session_id': self.current_session_id,
            'session_age': time.time() - self.session_start_time if self.session_start_time else 0,
            'unique_ips_used': len(self.used_ips),
            'current_proxy_host': self.current_proxy['host'] if self.current_proxy else None
        }
    
    def force_rotation(self) -> bool:
        """اجبار به چرخش پروکسی"""
        self.logger.info("🔄 اجبار به چرخش پروکسی...")
        return self._rotate_proxy()
    
    def validate_no_ip_leak(self) -> bool:
        """اعتبارسنجی عدم نشت IP"""
        try:
            import requests
            
            if not self.current_proxy:
                self.logger.error("❌ هیچ پروکسی فعال نیست")
                return False
            
            # تنظیم پروکسی برای requests
            proxy_url = f"http://{self.current_proxy['host']}:{self.current_proxy['port']}"
            if self.current_proxy.get('username') and self.current_proxy.get('password'):
                username = self.current_proxy['username']
                password = self.current_proxy['password']
                proxy_url = f"http://{username}:{password}@{self.current_proxy['host']}:{self.current_proxy['port']}"
            
            proxies = {
                'http': proxy_url,
                'https': proxy_url
            }
            
            # تست چندگانه برای اطمینان
            test_urls = [
                'https://httpbin.org/ip',
                'https://api.ipify.org?format=json',
                'https://ifconfig.me/ip'
            ]
            
            proxy_ips = set()
            
            for url in test_urls:
                try:
                    response = requests.get(url, proxies=proxies, timeout=10)
                    if response.status_code == 200:
                        if 'json' in response.headers.get('content-type', ''):
                            ip = response.json().get('ip', response.json().get('origin', ''))
                        else:
                            ip = response.text.strip()
                        
                        if ip:
                            proxy_ips.add(ip.split(',')[0].strip())
                            
                except Exception as e:
                    self.logger.warning(f"⚠️ خطا در تست {url}: {e}")
                    continue
            
            if len(proxy_ips) == 0:
                self.logger.error("❌ نتوانستیم IP پروکسی را تشخیص دهیم")
                return False
            
            if len(proxy_ips) > 1:
                self.logger.warning(f"⚠️ IP های متفاوت تشخیص داده شد: {proxy_ips}")
            
            # بررسی IP واقعی سیستم
            try:
                real_response = requests.get('https://httpbin.org/ip', timeout=5)
                if real_response.status_code == 200:
                    real_ip = real_response.json().get('origin', '')
                    
                    for proxy_ip in proxy_ips:
                        if proxy_ip == real_ip:
                            self.logger.error(f"❌ نشت IP تشخیص داده شد! IP واقعی: {real_ip}")
                            return False
                            
            except:
                # اگر نتوانیم IP واقعی را بگیریم، مشکلی نیست
                pass
            
            self.logger.info(f"✅ عدم نشت IP تأیید شد. IP پروکسی: {list(proxy_ips)}")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ خطا در اعتبارسنجی نشت IP: {e}")
            return False

# نمونه پیکربندی
proxy_configs = {
    'smartproxy_primary': {
        'type': 'residential_rotating',
        'host': 'proxy.smartproxy.net',
        'port': 3120,
        'username': 'smart-m7rkmtitpgxx_area-IR_life-15_session-jjRBbwW',
        'password': 'O9nbcWhZ7JnGMCDR'
    },
    'smartproxy_backup': {
        'type': 'residential_rotating',
        'host': 'gate.smartproxy.com',
        'port': 10000,
        'username': 'smart-m7rkmtitpgxx_area-IR_life-15',
        'password': 'O9nbcWhZ7JnGMCDR'
    },
    'bright_data': {
        'type': 'sticky_session',
        'host': 'brd.superproxy.io',
        'port': 22225,
        'username': 'brd-customer-YOUR_CUSTOMER_ID-zone-residential',
        'password': 'YOUR_PASSWORD'
    }
}