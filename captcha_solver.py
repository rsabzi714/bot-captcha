# captcha_solver.py
import requests
import time
import base64
import logging
import random
from typing import Optional, Dict, Tuple, List
from datetime import datetime, timedelta

class CaptchaSolver:
    """حل‌کننده پیشرفته کپچا با استراتژی اجتناب-محور"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = 'http://2captcha.com'
        self.logger = logging.getLogger(__name__)
        
        # آمار و نظارت
        self.total_attempts = 0
        self.successful_solves = 0
        self.failed_solves = 0
        self.last_solve_time = None
        
        # استراتژی اجتناب
        self.avoidance_strategies = {
            'trust_score_building': True,
            'behavioral_mimicking': True,
            'session_warming': True,
            'captcha_delay_tactics': True
        }
        
        # تاریخچه کپچاها
        self.captcha_history = []
        self.daily_captcha_count = 0
        self.last_reset_date = datetime.now().date()
    
    def should_attempt_solve(self) -> Tuple[bool, str]:
        """تصمیم‌گیری هوشمند برای تلاش حل کپچا"""
        # بررسی محدودیت روزانه
        if self._check_daily_limit():
            return False, "محدودیت روزانه کپچا رسیده"
        
        # بررسی فاصله زمانی از آخرین حل
        if self._check_solve_frequency():
            return False, "فاصله زمانی کافی نیست"
        
        # بررسی موجودی
        balance = self.get_balance()
        if balance < 0.01:  # حداقل برای یک کپچا
            return False, "موجودی ناکافی"
        
        return True, "آماده حل کپچا"
    
    def solve_captcha(self, site_key: str, page_url: str, captcha_type: str = 'reCAPTCHA v2') -> Optional[str]:
        """متد اصلی حل کپچا - سازگار با captcha_handler جدید"""
        try:
            self.logger.info(f"🧩 شروع حل کپچا نوع {captcha_type}")
            
            # تلاش اول با سرویس اصلی
            result = None
            if captcha_type in ['reCAPTCHA v2', 'reCAPTCHA Enterprise', 'recaptcha_v2']:
                result = self.solve_recaptcha_v2(site_key, page_url)
            elif captcha_type in ['reCAPTCHA v3', 'recaptcha_v3']:
                result = self.solve_recaptcha_v3(site_key, page_url)
            elif captcha_type in ['hCaptcha', 'hcaptcha']:
                result = self.solve_hcaptcha(site_key, page_url)
            else:
                self.logger.warning(f"⚠️ نوع کپچای {captcha_type} پشتیبانی نمی‌شود")
                return None
            
            # اگر نتیجه موفق بود، برگردان
            if result:
                return result
            
            # Fallback: تلاش با تنظیمات مختلف
            self.logger.warning("🔄 تلاش با fallback mechanism...")
            return self._fallback_solve(site_key, page_url, captcha_type)
                
        except Exception as e:
            self.logger.error(f"❌ خطا در حل کپچا: {e}")
            # تلاش fallback حتی در صورت خطا
            try:
                return self._fallback_solve(site_key, page_url, captcha_type)
            except:
                return None
    
    def _fallback_solve(self, site_key: str, page_url: str, captcha_type: str) -> Optional[str]:
        """مکانیزم fallback برای حل کپچا"""
        try:
            self.logger.info("🆘 شروع fallback mechanism...")
            
            if captcha_type in ['reCAPTCHA v2', 'reCAPTCHA Enterprise', 'recaptcha_v2']:
                # تلاش با تنظیمات مختلف برای reCAPTCHA
                fallback_configs = [
                    # تنظیمات ساده
                    {
                        'method': 'userrecaptcha',
                        'googlekey': site_key,
                        'pageurl': page_url,
                        'key': self.api_key,
                        'json': 1,
                        'soft': 1  # حالت آسان‌تر
                    },
                    # تنظیمات با proxy
                    {
                        'method': 'userrecaptcha',
                        'googlekey': site_key,
                        'pageurl': page_url,
                        'key': self.api_key,
                        'json': 1,
                        'proxy': 'http',  # استفاده از proxy
                        'proxytype': 'HTTP'
                    }
                ]
                
                for i, config in enumerate(fallback_configs, 1):
                    self.logger.info(f"🔄 Fallback تلاش {i}/{len(fallback_configs)}...")
                    
                    try:
                        response = requests.post(f"{self.base_url}/in.php", data=config, timeout=30)
                        result = response.json()
                        
                        if result.get('status') == 1:
                            task_id = result['request']
                            self.logger.info(f"✅ Fallback ارسال موفق! Task ID: {task_id}")
                            
                            # انتظار برای نتیجه
                            token = self._wait_for_result(task_id, max_wait=120)
                            if token:
                                self.logger.info(f"✅ Fallback موفق! (تلاش {i})")
                                return token
                        else:
                            error_msg = result.get('error_text', result.get('request', 'خطای نامشخص'))
                            self.logger.warning(f"⚠️ Fallback تلاش {i} ناموفق: {error_msg}")
                            
                    except Exception as e:
                        self.logger.warning(f"⚠️ خطا در fallback تلاش {i}: {e}")
                        continue
            
            self.logger.error("❌ همه تلاش‌های fallback ناموفق")
            return None
            
        except Exception as e:
            self.logger.error(f"❌ خطا در fallback mechanism: {e}")
            return None
    
    def solve_recaptcha_v2(self, site_key: str, page_url: str, page=None) -> Optional[str]:
        """حل reCAPTCHA v2/Enterprise با تنظیمات بهبود یافته"""
        try:
            self.logger.info(f"🔧 حل reCAPTCHA v2 - Site Key: {site_key[:20]}...")
            
            # بررسی شرایط حل
            can_solve, reason = self.should_attempt_solve()
            if not can_solve:
                self.logger.warning(f"⚠️ عدم امکان حل کپچا: {reason}")
                return None
            
            self.total_attempts += 1
            
            # تلاش با تنظیمات مختلف
            attempts = [
                # تلاش 1: بدون Enterprise
                {
                    'method': 'userrecaptcha',
                    'googlekey': site_key,
                    'pageurl': page_url,
                    'key': self.api_key,
                    'json': 1
                },
                # تلاش 2: با Enterprise
                {
                    'method': 'userrecaptcha',
                    'googlekey': site_key,
                    'pageurl': page_url,
                    'key': self.api_key,
                    'json': 1,
                    'enterprise': 1
                },
                # تلاش 3: با تنظیمات اضافی
                {
                    'method': 'userrecaptcha',
                    'googlekey': site_key,
                    'pageurl': page_url,
                    'key': self.api_key,
                    'json': 1,
                    'invisible': 1
                }
            ]
            
            for attempt_num, submit_data in enumerate(attempts, 1):
                self.logger.info(f"🔄 تلاش {attempt_num}/3 برای ارسال کپچا...")
                
                try:
                    response = requests.post(f"{self.base_url}/in.php", data=submit_data, timeout=30)
                    result = response.json()
                    
                    if result['status'] != 1:
                        error_msg = result.get('error_text', result.get('request', 'خطای نامشخص'))
                        self.logger.warning(f"⚠️ تلاش {attempt_num} ناموفق: {error_msg}")
                        
                        # اگر خطا مربوط به تنظیمات باشد، تلاش بعدی را امتحان کن
                        if any(err in error_msg.lower() for err in ['enterprise', 'invisible', 'method']):
                            continue
                        else:
                            # خطای جدی - توقف
                            self.logger.error(f"❌ خطای جدی در ارسال: {error_msg}")
                            self.failed_solves += 1
                            return None
                    
                    task_id = result['request']
                    self.logger.info(f"✅ کپچا با موفقیت ارسال شد (تلاش {attempt_num}). Task ID: {task_id}")
                    self.logger.info(f"⏳ شروع انتظار برای حل کپچا (حداکثر 180 ثانیه)...")
                    
                    # انتظار برای حل با timeout بهینه
                    token = self._wait_for_result(task_id, max_wait=180)
                    
                    if token:
                        self.successful_solves += 1
                        self.daily_captcha_count += 1
                        self.last_solve_time = datetime.now()
                        self._record_captcha_solve('recaptcha_v2', True)
                        self.logger.info(f"✅ reCAPTCHA v2 با موفقیت حل شد (تلاش {attempt_num})")
                        return token
                    else:
                        self.logger.warning(f"⚠️ تلاش {attempt_num} برای حل ناموفق بود")
                        # اگر تلاش آخر بود
                        if attempt_num == len(attempts):
                            self.failed_solves += 1
                            self._record_captcha_solve('recaptcha_v2', False)
                            self.logger.error("❌ همه تلاش‌ها برای حل reCAPTCHA v2 ناموفق")
                            return None
                        # در غیر این صورت تلاش بعدی
                        continue
                        
                except requests.exceptions.Timeout:
                    self.logger.warning(f"⚠️ Timeout در تلاش {attempt_num}")
                    if attempt_num == len(attempts):
                        self.logger.error("❌ همه تلاش‌ها به دلیل timeout ناموفق")
                        self.failed_solves += 1
                        return None
                    continue
                except Exception as e:
                    self.logger.warning(f"⚠️ خطا در تلاش {attempt_num}: {e}")
                    if attempt_num == len(attempts):
                        self.logger.error(f"❌ همه تلاش‌ها ناموفق: {e}")
                        self.failed_solves += 1
                        return None
                    continue
            
            return None
            
        except Exception as e:
            self.failed_solves += 1
            self.logger.error(f"❌ خطا در حل reCAPTCHA v2: {e}")
            return None
    
    def solve_recaptcha_v3(self, site_key: str, page_url: str, action: str = 'submit', page=None) -> Optional[str]:
        """حل reCAPTCHA v3"""
        try:
            self.logger.info(f"🔧 حل reCAPTCHA v3 - Site Key: {site_key[:20]}..., Action: {action}")
            
            # بررسی شرایط حل
            can_solve, reason = self.should_attempt_solve()
            if not can_solve:
                self.logger.warning(f"⚠️ عدم امکان حل کپچا: {reason}")
                return None
            
            self.total_attempts += 1
            
            # ارسال کپچا به سرویس 2captcha
            submit_data = {
                'method': 'userrecaptcha',
                'googlekey': site_key,
                'pageurl': page_url,
                'action': action,
                'version': 'v3',
                'min_score': 0.3,
                'key': self.api_key,
                'json': 1
            }
            
            try:
                response = requests.post(f"{self.base_url}/in.php", data=submit_data, timeout=30)
                result = response.json()
            except requests.exceptions.Timeout:
                self.logger.error("❌ timeout در ارسال کپچا v3")
                self.failed_solves += 1
                return None
            except Exception as e:
                self.logger.error(f"❌ خطای غیرمنتظره در ارسال v3: {e}")
                self.failed_solves += 1
                return None
            
            if result['status'] != 1:
                error_msg = result.get('error_text', 'خطای نامشخص')
                self.logger.error(f"خطا در ارسال کپچا v3: {error_msg}")
                self.failed_solves += 1
                return None
            
            task_id = result['request']
            self.logger.info(f"✅ کپچا v3 با موفقیت ارسال شد. Task ID: {task_id}")
            
            # انتظار برای حل
            token = self._wait_for_result(task_id, max_wait=180)
            
            if token:
                self.successful_solves += 1
                self.daily_captcha_count += 1
                self.last_solve_time = datetime.now()
                self._record_captcha_solve('recaptcha_v3', True)
                self.logger.info("✅ reCAPTCHA v3 با موفقیت حل شد")
            else:
                self.failed_solves += 1
                self._record_captcha_solve('recaptcha_v3', False)
                self.logger.error("❌ شکست در حل reCAPTCHA v3")
            
            return token
            
        except Exception as e:
            self.failed_solves += 1
            self.logger.error(f"❌ خطا در حل reCAPTCHA v3: {e}")
            return None
    
    def solve_hcaptcha(self, site_key: str, page_url: str, page=None) -> Optional[str]:
        """حل hCaptcha"""
        try:
            self.logger.info(f"🔧 حل hCaptcha - Site Key: {site_key[:20]}...")
            
            # بررسی شرایط حل
            can_solve, reason = self.should_attempt_solve()
            if not can_solve:
                self.logger.warning(f"⚠️ عدم امکان حل کپچا: {reason}")
                return None
            
            self.total_attempts += 1
            
            # ارسال کپچا به سرویس 2captcha
            submit_data = {
                'method': 'hcaptcha',
                'sitekey': site_key,
                'pageurl': page_url,
                'key': self.api_key,
                'json': 1
            }
            
            try:
                response = requests.post(f"{self.base_url}/in.php", data=submit_data, timeout=30)
                result = response.json()
            except requests.exceptions.Timeout:
                self.logger.error("❌ timeout در ارسال hCaptcha")
                self.failed_solves += 1
                return None
            except Exception as e:
                self.logger.error(f"❌ خطای غیرمنتظره در ارسال hCaptcha: {e}")
                self.failed_solves += 1
                return None
            
            if result['status'] != 1:
                error_msg = result.get('error_text', 'خطای نامشخص')
                self.logger.error(f"خطا در ارسال hCaptcha: {error_msg}")
                self.failed_solves += 1
                return None
            
            task_id = result['request']
            self.logger.info(f"✅ hCaptcha با موفقیت ارسال شد. Task ID: {task_id}")
            
            # انتظار برای حل
            token = self._wait_for_result(task_id, max_wait=180)
            
            if token:
                self.successful_solves += 1
                self.daily_captcha_count += 1
                self.last_solve_time = datetime.now()
                self._record_captcha_solve('hcaptcha', True)
                self.logger.info("✅ hCaptcha با موفقیت حل شد")
            else:
                self.failed_solves += 1
                self._record_captcha_solve('hcaptcha', False)
                self.logger.error("❌ شکست در حل hCaptcha")
            
            return token
            
        except Exception as e:
            self.failed_solves += 1
            self.logger.error(f"❌ خطا در حل hCaptcha: {e}")
            return None
    
    def _check_daily_limit(self) -> bool:
        """بررسی محدودیت روزانه کپچا"""
        today = datetime.now().date()
        
        # ریست شمارنده روزانه
        if today != self.last_reset_date:
            self.daily_captcha_count = 0
            self.last_reset_date = today
        
        # حداکثر 10 کپچا در روز (برای جلوگیری از مشکوک شدن)
        return self.daily_captcha_count >= 10
    
    def _check_solve_frequency(self) -> bool:
        """بررسی فرکانس حل کپچا"""
        if not self.last_solve_time:
            return False
        
        # حداقل 5 دقیقه فاصله بین حل کپچاها
        time_since_last = datetime.now() - self.last_solve_time
        return time_since_last < timedelta(minutes=5)
    
    def pre_solve_preparation(self, page) -> bool:
        """آماده‌سازی قبل از حل کپچا برای افزایش امتیاز اعتماد"""
        try:
            if not self.avoidance_strategies['trust_score_building']:
                return True
            
            self.logger.info("شروع آماده‌سازی قبل از حل کپچا...")
            
            # شبیه‌سازی رفتار انسانی
            self._simulate_human_behavior(page)
            
            # تاخیر تصادفی
            delay = random.uniform(3, 8)
            self.logger.info(f"تاخیر {delay:.1f} ثانیه قبل از حل کپچا")
            time.sleep(delay)
            
            return True
            
        except Exception as e:
            self.logger.error(f"خطا در آماده‌سازی: {e}")
            return False
    
    def _simulate_human_behavior(self, page) -> None:
        """شبیه‌سازی رفتار انسانی قبل از حل کپچا"""
        try:
            # حرکت ماوس تصادفی
            for _ in range(random.randint(2, 5)):
                x = random.randint(100, 800)
                y = random.randint(100, 600)
                page.mouse.move(x, y)
                time.sleep(random.uniform(0.5, 1.5))
            
            # اسکرول تصادفی
            if random.random() < 0.7:
                page.mouse.wheel(0, random.randint(-200, 200))
                time.sleep(random.uniform(1, 3))
            
            # کلیک در نقطه خالی (شبیه‌سازی بررسی صفحه)
            if random.random() < 0.5:
                page.click('body', position={'x': random.randint(100, 300), 'y': random.randint(100, 300)})
                time.sleep(random.uniform(0.5, 2))
                
        except Exception as e:
            self.logger.warning(f"خطا در شبیه‌سازی رفتار: {e}")
    
    def solve_recaptcha_v2(self, site_key: str, page_url: str, page=None, enterprise=False) -> Optional[str]:
        """حل پیشرفته reCAPTCHA v2 با استراتژی اجتناب"""
        try:
            self.total_attempts += 1
            
            # بررسی امکان حل
            can_solve, reason = self.should_attempt_solve()
            if not can_solve:
                self.logger.warning(f"عدم امکان حل کپچا: {reason}")
                return None
            
            # آماده‌سازی قبل از حل
            if page and not self.pre_solve_preparation(page):
                self.logger.error("شکست در آماده‌سازی")
                return None
            
            self.logger.info(f"شروع حل reCAPTCHA v2 - Site Key: {site_key}")
            self.logger.debug(f"🔑 Site Key کامل: {site_key} (طول: {len(site_key)})")
            self.logger.debug(f"🌐 Page URL: {page_url}")
            
            # ارسال وظیفه با پارامترهای بهینه
            submit_data = {
                'method': 'userrecaptcha',
                'googlekey': site_key,
                'pageurl': page_url,
                'key': self.api_key,
                'json': 1,
                'invisible': 0,  # مشخص کردن نوع reCAPTCHA
                'min_score': 0.3,  # حداقل امتیاز برای v3
                'action': 'submit'  # اکشن پیش‌فرض
            }
            
            # اضافه کردن پارامترهای Enterprise
            if enterprise:
                submit_data['enterprise'] = 1
                submit_data['action'] = 'LOGIN'  # اکشن مخصوص Enterprise
                self.logger.info("🏢 حالت Enterprise فعال شد")
            
            self.logger.info(f"📤 ارسال درخواست به 2captcha...")
            self.logger.debug(f"📤 داده‌های ارسالی: {submit_data}")
            
            try:
                response = requests.post(f"{self.base_url}/in.php", data=submit_data, timeout=30)
                
                self.logger.info(f"📥 پاسخ دریافت شد - HTTP Status: {response.status_code}")
                self.logger.debug(f"📥 Raw Response: {response.text}")
                
                if response.status_code != 200:
                    self.logger.error(f"❌ خطای HTTP: {response.status_code}")
                    self.failed_solves += 1
                    return None
                
                result = response.json()
                self.logger.debug(f"📥 Parsed JSON: {result}")
                
            except requests.exceptions.Timeout:
                self.logger.error("❌ Timeout در ارسال درخواست به 2captcha")
                self.failed_solves += 1
                return None
            except requests.exceptions.ConnectionError:
                self.logger.error("❌ خطای اتصال به 2captcha")
                self.failed_solves += 1
                return None
            except Exception as e:
                self.logger.error(f"❌ خطای غیرمنتظره در ارسال: {e}")
                self.failed_solves += 1
                return None
            
            if result['status'] != 1:
                error_msg = result.get('error_text', 'خطای نامشخص')
                self.logger.error(f"خطا در ارسال کپچا: {error_msg}")
                self.failed_solves += 1
                return None
            
            task_id = result['request']
            self.logger.info(f"✅ کپچا با موفقیت ارسال شد. Task ID: {task_id}")
            self.logger.info(f"⏳ شروع انتظار برای حل کپچا (حداکثر 180 ثانیه)...")
            
            # انتظار برای حل با timeout بهینه
            token = self._wait_for_result(task_id, max_wait=180)
            
            if token:
                self.successful_solves += 1
                self.daily_captcha_count += 1
                self.last_solve_time = datetime.now()
                self._record_captcha_solve('recaptcha_v2', True)
                self.logger.info("reCAPTCHA v2 با موفقیت حل شد")
            else:
                self.failed_solves += 1
                self._record_captcha_solve('recaptcha_v2', False)
                self.logger.error("شکست در حل reCAPTCHA v2")
            
            return token
            
        except Exception as e:
            self.failed_solves += 1
            self.logger.error(f"خطا در حل reCAPTCHA: {e}")
            return None
    
    def _record_captcha_solve(self, captcha_type: str, success: bool) -> None:
        """ثبت تاریخچه حل کپچا"""
        record = {
            'type': captcha_type,
            'success': success,
            'timestamp': datetime.now(),
            'daily_count': self.daily_captcha_count
        }
        
        self.captcha_history.append(record)
        
        # نگهداری فقط 100 رکورد آخر
        if len(self.captcha_history) > 100:
            self.captcha_history = self.captcha_history[-100:]
    
    def get_solve_statistics(self) -> Dict:
        """دریافت آمار حل کپچا"""
        success_rate = (self.successful_solves / self.total_attempts * 100) if self.total_attempts > 0 else 0
        
        return {
            'total_attempts': self.total_attempts,
            'successful_solves': self.successful_solves,
            'failed_solves': self.failed_solves,
            'success_rate': round(success_rate, 2),
            'daily_count': self.daily_captcha_count,
            'last_solve': self.last_solve_time.isoformat() if self.last_solve_time else None,
            'balance': self.get_balance()
        }
    
    def solve_image_captcha(self, image_path: str) -> Optional[str]:
        """حل کپچای تصویری"""
        try:
            # خواندن تصویر
            with open(image_path, 'rb') as f:
                image_data = base64.b64encode(f.read()).decode('utf-8')
            
            # ارسال وظیفه
            submit_data = {
                'method': 'base64',
                'body': image_data,
                'key': self.api_key,
                'json': 1
            }
            
            response = requests.post(f"{self.base_url}/in.php", data=submit_data)
            result = response.json()
            
            if result['status'] != 1:
                print(f"خطا در ارسال کپچای تصویری: {result.get('error_text')}")
                return None
            
            task_id = result['request']
            print(f"کپچای تصویری ارسال شد. Task ID: {task_id}")
            
            # انتظار برای حل
            return self._wait_for_result(task_id)
            
        except Exception as e:
            print(f"خطا در حل کپچای تصویری: {e}")
            return None
    
    def _wait_for_result(self, task_id: str, max_wait: int = 120) -> Optional[str]:
        """انتظار برای دریافت نتیجه با مدیریت خطای بهبود یافته"""
        start_time = time.time()
        retry_count = 0
        max_retries = 3
        
        self.logger.info(f"⏳ انتظار برای حل کپچا - Task ID: {task_id}")
        
        while time.time() - start_time < max_wait:
            elapsed = int(time.time() - start_time)
            time.sleep(5)  # انتظار 5 ثانیه
            
            try:
                self.logger.debug(f"🔍 بررسی وضعیت کپچا... ({elapsed}s)")
                response = requests.get(
                    f"{self.base_url}/res.php",
                    params={
                        'key': self.api_key,
                        'action': 'get',
                        'id': task_id,
                        'json': 1
                    },
                    timeout=30
                )
                
                # بررسی وضعیت HTTP
                if response.status_code != 200:
                    self.logger.warning(f"⚠️ HTTP خطا در بررسی وضعیت: {response.status_code}")
                    continue
                
                self.logger.debug(f"📥 پاسخ بررسی: {response.text}")
                
                # تلاش برای parse کردن JSON
                try:
                    result = response.json()
                except ValueError as e:
                    self.logger.error(f"❌ خطا در parse JSON: {e}")
                    self.logger.debug(f"Response text: {response.text[:200]}")
                    continue
                
                # بررسی نتیجه
                if 'status' in result:
                    if result['status'] == 1:
                        self.logger.info("✅ کپچا با موفقیت حل شد!")
                        return result['request']
                    elif result['status'] == 0:
                        # بررسی نوع خطا یا وضعیت
                        request_text = result.get('request', '')
                        error_text = result.get('error_text', request_text)
                        
                        if error_text == 'CAPCHA_NOT_READY' or request_text == 'CAPCHA_NOT_READY':
                            elapsed = int(time.time() - start_time)
                            self.logger.debug(f"⏳ در انتظار حل کپچا... ({elapsed}s)")
                            continue
                        else:
                            self.logger.error(f"❌ خطا در دریافت نتیجه: {error_text}")
                            
                            # خطاهای غیرقابل تکرار
                            if error_text in ['ERROR_WRONG_USER_KEY', 'ERROR_KEY_DOES_NOT_EXIST']:
                                self.logger.error("❌ مشکل در API Key - توقف")
                                return None
                            elif error_text == 'ERROR_ZERO_BALANCE':
                                self.logger.error("❌ موجودی ناکافی - توقف")
                                return None
                            elif error_text in ['ERROR_CAPTCHA_UNSOLVABLE', 'Workers could not solve the Captcha']:
                                self.logger.warning("⚠️ کپچا قابل حل نیست - ممکن است نیاز به تنظیمات مختلف باشد")
                                # بجای return None، اجازه retry بده
                                retry_count += 1
                                if retry_count >= max_retries:
                                    self.logger.error(f"❌ حداکثر تلاش مجدد رسید: {error_text}")
                                    return None
                                self.logger.warning(f"⚠️ تلاش مجدد {retry_count}/{max_retries} برای کپچای مشکل‌دار")
                                time.sleep(15)  # انتظار بیشتر برای کپچای مشکل‌دار
                                continue
                            else:
                                # سایر خطاها - تلاش مجدد
                                retry_count += 1
                                if retry_count >= max_retries:
                                    self.logger.error(f"❌ حداکثر تلاش مجدد رسید: {error_text}")
                                    return None
                                self.logger.warning(f"⚠️ تلاش مجدد {retry_count}/{max_retries}: {error_text}")
                                time.sleep(10)  # انتظار بیشتر قبل از تلاش مجدد
                                continue
                    else:
                        self.logger.warning(f"⚠️ وضعیت نامشخص: {result}")
                        continue
                else:
                    self.logger.error(f"❌ پاسخ نامعتبر: {result}")
                    continue
                    
            except requests.exceptions.Timeout:
                self.logger.warning(f"⚠️ Timeout در بررسی وضعیت ({elapsed}s)")
                time.sleep(5)
                continue
            except requests.exceptions.RequestException as e:
                self.logger.warning(f"⚠️ خطای اتصال در بررسی وضعیت: {e} ({elapsed}s)")
                time.sleep(5)
                continue
            except Exception as e:
                self.logger.warning(f"⚠️ خطا در بررسی وضعیت: {e} ({elapsed}s)")
                time.sleep(5)
                continue
        
        self.logger.warning("⏰ زمان انتظار تمام شد")
        return None
    
    def get_balance(self) -> float:
        """دریافت موجودی حساب"""
        try:
            response = requests.get(
                f"{self.base_url}/res.php",
                params={
                    'key': self.api_key,
                    'action': 'getbalance',
                    'json': 1
                }
            )
            
            result = response.json()
            if result['status'] == 1:
                return float(result['request'])
            else:
                print(f"خطا در دریافت موجودی: {result.get('error_text')}")
                return 0.0
                
        except Exception as e:
            print(f"خطا در دریافت موجودی: {e}")
            return 0.0

class CaptchaDetector:
    """تشخیص‌دهنده پیشرفته کپچا با قابلیت‌های اجتناب"""
    
    def __init__(self, page):
        self.page = page
        self.logger = logging.getLogger(__name__)
        
        # آمار تشخیص
        self.detection_count = 0
        self.false_positives = 0
        self.captcha_types_seen = set()
        
        # استراتژی‌های اجتناب
        self.avoidance_active = True
        self.trust_building_mode = True
    
    def detect_captcha_type(self) -> Dict:
        """تشخیص نوع کپچا در صفحه - مطابق با ساختار واقعی سایت MNE"""
        self.detection_count += 1
        
        captcha_info = {
            'type': None,
            'site_key': None,
            'image_element': None,
            'location': 'unknown'
        }
        
        try:
            self.logger.info("🔍 CaptchaDetector: شروع تشخیص کپچا...")
            
            # انتظار کوتاه برای بارگذاری
            import time
            time.sleep(1)
            
            # بررسی Google reCAPTCHA v2 (در صفحه ورود)
            recaptcha_selectors = [
                '.g-recaptcha',
                'div[data-sitekey]',
                'iframe[src*="recaptcha"]',
                'iframe[src*="google.com/recaptcha"]',
                '#recaptcha-container',
                'iframe[title*="reCAPTCHA"]',
                '[data-callback]',
                'iframe[name^="a-"]',  # reCAPTCHA iframe pattern
                '.recaptcha-checkbox'
            ]
            
            for selector in recaptcha_selectors:
                try:
                    elements = self.page.locator(selector)
                    if elements.count() > 0:
                        for i in range(elements.count()):
                            element = elements.nth(i)
                            try:
                                # بررسی visibility با timeout کوتاه
                                if element.is_visible(timeout=1000):
                                    site_key = element.get_attribute('data-sitekey')
                                    if site_key:
                                         captcha_info['type'] = 'recaptcha_v2'
                                         captcha_info['site_key'] = site_key
                                         captcha_info['location'] = 'login_page'
                                         captcha_info['element'] = element
                                         self.captcha_types_seen.add('recaptcha_v2')
                                         self.logger.info(f"✅ reCAPTCHA v2 تشخیص داده شد - Site Key: {site_key[:20]}...")
                                         return captcha_info
                                    else:
                                        # حتی بدون sitekey، اگر iframe reCAPTCHA است
                                        src = element.get_attribute('src')
                                        if src and ('recaptcha' in src.lower() or 'google.com/recaptcha' in src.lower()):
                                            # تلاش برای یافتن sitekey در صفحه
                                            page_sitekey = self._extract_sitekey_from_page()
                                            if page_sitekey:
                                                captcha_info['type'] = 'recaptcha_v2'
                                                captcha_info['site_key'] = page_sitekey
                                                captcha_info['location'] = 'login_page'
                                                captcha_info['element'] = element
                                                self.captcha_types_seen.add('recaptcha_v2')
                                                self.logger.info(f"✅ reCAPTCHA v2 تشخیص داده شد از iframe - Site Key: {page_sitekey[:20]}...")
                                                return captcha_info
                            except:
                                continue
                except Exception as e:
                    self.logger.debug(f"خطا در بررسی selector {selector}: {e}")
                    continue
            
            # بررسی کپچای تصویری (قبل از دسترسی به تقویم)
            image_captcha_selectors = [
                'img[src*="captcha"]',
                'img[alt*="captcha"]', 
                'img[id*="captcha"]',
                'img[src*="verification"]',
                'img[class*="captcha"]',
                '.captcha-image img',
                '#captcha-image',
                '.captcha img'
            ]
            
            for selector in image_captcha_selectors:
                try:
                    elements = self.page.locator(selector)
                    if elements.count() > 0:
                        for i in range(elements.count()):
                            element = elements.nth(i)
                            try:
                                if element.is_visible(timeout=1000):
                                    captcha_info['type'] = 'image_captcha'
                                    captcha_info['image_element'] = element
                                    captcha_info['location'] = 'calendar_access'
                                    captcha_info['element'] = element
                                    self.captcha_types_seen.add('image_captcha')
                                    self.logger.info("✅ کپچای تصویری تشخیص داده شد")
                                    return captcha_info
                            except:
                                continue
                except Exception as e:
                    self.logger.debug(f"خطا در بررسی تصویر {selector}: {e}")
                    continue
            
            # بررسی hCaptcha
            hcaptcha_selectors = [
                '.h-captcha',
                'div[data-hcaptcha-sitekey]',
                'iframe[src*="hcaptcha"]'
            ]
            
            for selector in hcaptcha_selectors:
                try:
                    elements = self.page.locator(selector)
                    if elements.count() > 0:
                        for i in range(elements.count()):
                            element = elements.nth(i)
                            try:
                                if element.is_visible(timeout=1000):
                                    site_key = element.get_attribute('data-hcaptcha-sitekey') or element.get_attribute('data-sitekey')
                                    captcha_info['type'] = 'hcaptcha'
                                    captcha_info['site_key'] = site_key
                                    captcha_info['location'] = 'login_page'
                                    captcha_info['element'] = element
                                    self.captcha_types_seen.add('hcaptcha')
                                    self.logger.info(f"✅ hCaptcha تشخیص داده شد - Site Key: {site_key[:20] if site_key else 'نامشخص'}...")
                                    return captcha_info
                            except:
                                continue
                except Exception as e:
                    self.logger.debug(f"خطا در بررسی hCaptcha {selector}: {e}")
                    continue
            
            # بررسی سایر انواع کپچا (احتیاطی)
            other_captcha_selectors = [
                '[class*="captcha"]',
                '[id*="captcha"]',
                '.verification-code',
                '#verification',
                'input[name*="captcha"]'
            ]
            
            for selector in other_captcha_selectors:
                try:
                    elements = self.page.locator(selector)
                    if elements.count() > 0:
                        for i in range(elements.count()):
                            element = elements.nth(i)
                            try:
                                if element.is_visible(timeout=1000):
                                    captcha_info['type'] = 'unknown_captcha'
                                    captcha_info['image_element'] = element
                                    captcha_info['location'] = 'unknown'
                                    captcha_info['element'] = element
                                    self.logger.warning(f"⚠️ نوع ناشناخته کپچا تشخیص داده شد: {selector}")
                                    return captcha_info
                            except:
                                continue
                except Exception as e:
                    self.logger.debug(f"خطا در بررسی {selector}: {e}")
                    continue
            
            # هیچ کپچایی یافت نشد
            self.logger.debug("ℹ️ هیچ کپچایی تشخیص داده نشد")
            return captcha_info
            
        except Exception as e:
            self.logger.error(f"❌ خطا در تشخیص کپچا: {e}")
            return captcha_info
    
    def _extract_sitekey_from_page(self) -> str:
        """استخراج sitekey از کد صفحه"""
        try:
            # جستجو در کد HTML
            page_content = self.page.content()
            
            import re
            # الگوهای مختلف sitekey
            patterns = [
                r'data-sitekey=["\']([^"\'\']+)["\']',
                r'sitekey["\']?\s*[:=]\s*["\']([^"\'\']+)["\']',
                r'grecaptcha\.render\([^,]+,\s*{[^}]*sitekey["\']?\s*:\s*["\']([^"\'\']+)["\']',
                r'"sitekey"\s*:\s*"([^"]+)"',
                r'\'sitekey\'\s*:\s*\'([^\']+)\''
            ]
            
            for pattern in patterns:
                matches = re.findall(pattern, page_content, re.IGNORECASE)
                if matches:
                    sitekey = matches[0]
                    if len(sitekey) > 20:  # sitekey معمولاً طولانی است
                        self.logger.info(f"🔑 sitekey از کد صفحه استخراج شد: {sitekey[:20]}...")
                        return sitekey
            
            # جستجو در JavaScript
            js_sitekey = self.page.evaluate("""
                () => {
                    // جستجو در تمام script ها
                    const scripts = document.querySelectorAll('script');
                    for (let script of scripts) {
                        const content = script.textContent || script.innerText;
                        const match = content.match(/sitekey["']?\\s*[:=]\\s*["']([^"']+)["']/i);
                        if (match && match[1].length > 20) {
                            return match[1];
                        }
                    }
                    
                    // جستجو در data attributes
                    const elements = document.querySelectorAll('[data-sitekey]');
                    for (let el of elements) {
                        const sitekey = el.getAttribute('data-sitekey');
                        if (sitekey && sitekey.length > 20) {
                            return sitekey;
                        }
                    }
                    
                    return null;
                }
            """)
            
            if js_sitekey:
                self.logger.info(f"🔑 sitekey از JavaScript استخراج شد: {js_sitekey[:20]}...")
                return js_sitekey
            
            return None
            
        except Exception as e:
            self.logger.debug(f"خطا در استخراج sitekey: {e}")
            return None
     
    def solve_detected_captcha(self, solver: CaptchaSolver) -> bool:
        """حل کپچای تشخیص‌داده‌شده"""
        captcha_info = self.detect_captcha_type()
        
        if captcha_info['type'] == 'recaptcha_v2':
            return self._solve_recaptcha_v2(solver, captcha_info['site_key'])
        elif captcha_info['type'] == 'image_captcha':
            return self._solve_image_captcha(solver, captcha_info['image_element'])
        
        return True  # اگر کپچایی نبود
    
    def _solve_recaptcha_v2(self, solver: CaptchaSolver, site_key: str) -> bool:
        """حل reCAPTCHA v2"""
        try:
            current_url = self.page.url
            token = solver.solve_recaptcha_v2(site_key, current_url)
            
            if token:
                # تزریق توکن
                self.page.evaluate(f"""
                    document.getElementById('g-recaptcha-response').innerHTML = '{token}';
                    if (typeof grecaptcha !== 'undefined') {{
                        grecaptcha.getResponse = function() {{ return '{token}'; }};
                    }}
                """)
                return True
            
        except Exception as e:
            print(f"خطا در حل reCAPTCHA: {e}")
        
        return False
    
    def _solve_image_captcha(self, solver: CaptchaSolver, image_element) -> bool:
        """حل کپچای تصویری"""
        try:
            # گرفتن اسکرین‌شات از تصویر کپچا
            image_path = 'temp_captcha.png'
            image_element.screenshot(path=image_path)
            
            # حل کپچا
            solution = solver.solve_image_captcha(image_path)
            
            if solution:
                # یافتن فیلد ورودی کپچا
                captcha_input = self.page.locator('input[name*="captcha"], input[id*="captcha"], input[placeholder*="captcha"]').first
                if captcha_input.count() > 0:
                    captcha_input.fill(solution)
                    return True
            
        except Exception as e:
            print(f"خطا در حل کپچای تصویری: {e}")
        
        return False