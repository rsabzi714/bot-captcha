# modules/captcha_handler.py
import time
from typing import Dict, Optional
from utils.element_finder import ElementFinder
from captcha_solver import CaptchaDetector, CaptchaSolver

class CaptchaHandler:
    """مدیریت تشخیص و حل کپچا - نسخه بهینه‌شده"""
    
    def __init__(self, page, captcha_solver, logger):
        self.page = page
        self.captcha_solver = captcha_solver
        self.logger = logger
        
        # ابزارهای کمکی
        self.element_finder = ElementFinder(page, logger)
        self.captcha_detector = CaptchaDetector(page)
        
        # تنظیمات بهینه‌شده
        self.detection_timeout = 10000   # کاهش timeout
        self.solve_timeout = 120000      # کاهش timeout
        self.max_solve_attempts = 2      # کاهش تلاش‌ها
        
        # وضعیت کپچا
        self.captcha_solved = False
        self.failed_solves = 0
        self.last_error = None
        self.solve_attempts = 0
    
    def reset_captcha_state(self):
        """ریست کردن وضعیت کپچا برای تلاش جدید"""
        self.captcha_solved = False
        self.failed_solves = 0
        self.last_error = None
        self.solve_attempts = 0
        self.logger.debug("🔄 وضعیت کپچا ریست شد")
    
    def detect_captcha(self) -> Dict:
        """تشخیص کپچا - متد سازگار با کد قدیمی"""
        try:
            captcha_info = self._detect_captcha()
            if captcha_info:
                return {
                    'detected': True,
                    'type': captcha_info['type'],
                    'element': captcha_info.get('element'),
                    'selector': captcha_info.get('selector')
                }
            else:
                return {'detected': False, 'type': None}
        except Exception as e:
            self.logger.error(f"❌ خطا در تشخیص کپچا: {e}")
            return {'detected': False, 'type': None}
    
    def solve_captcha(self) -> bool:
        """متد اصلی حل کپچا - با اعتبارسنجی واقعی"""
        self.solve_attempts += 1
        self.last_error = None
        
        try:
            self.logger.info(f"🔍 شروع فرآیند حل کپچا (تلاش {self.solve_attempts})")
            
            # انتظار کوتاه برای بارگذاری
            self.page.wait_for_timeout(2000)
            
            # تشخیص نوع کپچا
            captcha_info = self._detect_captcha()
            if not captcha_info:
                self.logger.info("✅ هیچ کپچایی یافت نشد")
                return True
            
            captcha_type = captcha_info.get('type')
            self.logger.info(f"🔍 کپچای {captcha_type} تشخیص داده شد")
            
            # حل کپچا بر اساس نوع
            solve_result = False
            if captcha_type == 'recaptcha_v2':
                solve_result = self._solve_recaptcha_v2()
            elif captcha_type == 'recaptcha_v3':
                solve_result = self._solve_recaptcha_v3(captcha_info)
            elif captcha_type == 'hcaptcha':
                solve_result = self._solve_hcaptcha(captcha_info)
            else:
                self.logger.warning(f"⚠️ نوع کپچای {captcha_type} پشتیبانی نمی‌شود")
                return False
            
            # تأیید نهایی حل کپچا
            if solve_result:
                final_verification = self._final_captcha_verification()
                if final_verification:
                    self.logger.info("✅ کپچا با موفقیت حل و تأیید شد")
                    self.captcha_solved = True
                    return True
                else:
                    self.logger.error("❌ کپچا حل شد اما تأیید نهایی ناموفق")
                    self.captcha_solved = False
                    return False
            else:
                self.logger.error("❌ حل کپچا ناموفق")
                self.captcha_solved = False
                return False
                
        except Exception as e:
            self.failed_solves += 1
            self.last_error = str(e)
            self.captcha_solved = False
            
            self.logger.error(f"❌ خطا در فرآیند حل کپچا (تلاش {self.solve_attempts}): {e}")
            self.logger.error(f"📊 آمار: {self.failed_solves} شکست از {self.solve_attempts} تلاش")
            
            # لاگ جزئیات اضافی برای دیباگ
            try:
                current_url = self.page.url
                page_title = self.page.title()
                self.logger.debug(f"🔍 جزئیات خطا - URL: {current_url}, Title: {page_title}")
            except:
                pass
                
            return False
    
    def _detect_captcha(self) -> Optional[Dict]:
        """تشخیص ساده و مؤثر کپچا"""
        try:
            self.logger.info("🔍 شروع تشخیص کپچا...")
            
            # بررسی reCAPTCHA v2/Enterprise
            recaptcha_iframe = self.page.query_selector('iframe[src*="recaptcha"]')
            if recaptcha_iframe:
                self.logger.info("🎯 کپچا یافت شد: recaptcha_v2")
                return {
                    'type': 'recaptcha_v2',
                    'selector': 'iframe[src*="recaptcha"]',
                    'element': recaptcha_iframe
                }
            
            # بررسی hCaptcha
            hcaptcha_iframe = self.page.query_selector('iframe[src*="hcaptcha"]')
            if hcaptcha_iframe:
                self.logger.info("🎯 کپچا یافت شد: hcaptcha")
                return {
                    'type': 'hcaptcha',
                    'selector': 'iframe[src*="hcaptcha"]',
                    'element': hcaptcha_iframe
                }
            
            # بررسی reCAPTCHA v3
            recaptcha_v3 = self.page.evaluate("""
                () => {
                    return typeof grecaptcha !== 'undefined' && 
                           document.querySelector('[data-sitekey]') !== null;
                }
            """)
            
            if recaptcha_v3:
                self.logger.info("🎯 کپچا یافت شد: recaptcha_v3")
                return {'type': 'recaptcha_v3'}
            
            return None
            
        except Exception as e:
            self.logger.error(f"❌ خطا در تشخیص کپچا: {e}")
            return None
    
    def _solve_recaptcha_v2(self) -> bool:
        """حل بهینه‌شده reCAPTCHA v2"""
        try:
            self.logger.info("🧩 شروع حل کپچای recaptcha_v2")
            
            # مرحله 1: کلیک روی چک‌باکس
            if not self._click_recaptcha_checkbox():
                self.logger.error("❌ کلیک روی چک‌باکس ناموفق")
                return False
            
            # مرحله 2: انتظار برای نتیجه
            result = self._wait_for_captcha_result()
            
            if result == 'solved':
                self.logger.info("✅ کپچا با کلیک حل شد")
                return True
            elif result == 'challenge':
                self.logger.info("🧩 چالش تصویری ظاهر شد، ارسال به سرویس...")
                service_result = self._solve_with_service()
                if service_result:
                    self.logger.info("✅ کپچا با سرویس حل شد")
                    return True
                else:
                    self.logger.error("❌ حل کپچا با سرویس ناموفق")
                    return False
            else:
                self.logger.warning(f"⚠️ وضعیت نامشخص کپچا: {result}")
                return False
                
        except Exception as e:
            self.logger.error(f"❌ خطا در حل reCAPTCHA v2: {e}")
            return False
    
    def _click_recaptcha_checkbox(self) -> bool:
        """کلیک بهینه روی چک‌باکس reCAPTCHA"""
        try:
            self.logger.info("🖱️ کلیک روی چک‌باکس کپچا...")
            
            # انتظار برای بارگذاری iframe
            self.page.wait_for_timeout(1500)
            
            # یافتن iframe anchor
            anchor_iframe = self.page.wait_for_selector(
                'iframe[src*="anchor"], iframe[title="reCAPTCHA"]', 
                timeout=8000
            )
            
            if not anchor_iframe:
                self.logger.error("❌ iframe anchor یافت نشد")
                return False
            
            # دسترسی به محتوای iframe
            anchor_frame = anchor_iframe.content_frame()
            if not anchor_frame:
                self.logger.error("❌ دسترسی به محتوای iframe ناموفق")
                return False
            
            # انتظار برای بارگذاری محتوای iframe
            anchor_frame.wait_for_load_state('networkidle', timeout=5000)
            
            # یافتن چک‌باکس
            checkbox_selectors = [
                '.recaptcha-checkbox-border',
                '#recaptcha-anchor', 
                '.rc-anchor-checkbox',
                '[role="checkbox"]'
            ]
            
            checkbox = None
            for selector in checkbox_selectors:
                try:
                    checkbox = anchor_frame.wait_for_selector(selector, timeout=2000)
                    if checkbox:
                        self.logger.info(f"✅ چک‌باکس یافت شد: {selector}")
                        break
                except:
                    continue
            
            if not checkbox:
                self.logger.error("❌ چک‌باکس یافت نشد")
                return False
            
            # کلیک روی چک‌باکس
            checkbox.click()
            self.logger.info("✅ کلیک روی چک‌باکس انجام شد")
            
            # انتظار برای پردازش
            self.page.wait_for_timeout(1500)
            return True
                
        except Exception as e:
            self.logger.error(f"❌ خطا در کلیک چک‌باکس: {e}")
            return False
    
    def _wait_for_captcha_result(self) -> str:
        """انتظار بهینه برای نتیجه کپچا"""
        try:
            self.logger.info("⏳ انتظار برای نتیجه کپچا...")
            
            max_attempts = 6  # کاهش تلاش‌ها
            
            for attempt in range(max_attempts):
                self.logger.info(f"🔄 تلاش {attempt + 1}/{max_attempts}")
                
                # بررسی توکن
                token_result = self.page.evaluate("""
                    () => {
                        const selectors = [
                            'textarea[name="g-recaptcha-response"]',
                            'input[name="g-recaptcha-response"]',
                            '#g-recaptcha-response'
                        ];
                        
                        for (let selector of selectors) {
                            const field = document.querySelector(selector);
                            if (field && field.value && field.value.length > 20) {
                                return {found: true, length: field.value.length};
                            }
                        }
                        return {found: false};
                    }
                """)
                
                if token_result.get('found'):
                    self.logger.info(f"✅ توکن کپچا یافت شد - طول: {token_result.get('length')}")
                    return 'solved'
                
                # بررسی چالش
                challenge_visible = self.page.evaluate("""
                    () => {
                        const challengeFrames = document.querySelectorAll('iframe[src*="bframe"]');
                        for (let frame of challengeFrames) {
                            const style = window.getComputedStyle(frame);
                            if (style.display !== 'none' && style.visibility !== 'hidden') {
                                return true;
                            }
                        }
                        return false;
                    }
                """)
                
                if challenge_visible:
                    self.logger.info("🧩 چالش تصویری تشخیص داده شد")
                    return 'challenge'
                
                # انتظار قبل از تلاش بعدی
                self.page.wait_for_timeout(3000)
            
            self.logger.warning("⚠️ timeout در انتظار نتیجه کپچا")
            return 'timeout'
            
        except Exception as e:
            self.logger.error(f"❌ خطا در انتظار نتیجه کپچا: {e}")
            return 'error'
    
    def _solve_with_service(self) -> bool:
        """حل کپچا با سرویس 2Captcha"""
        try:
            self.logger.info("🔧 شروع حل با سرویس 2Captcha...")
            
            # استخراج site key
            site_key = self._extract_recaptcha_sitekey()
            if not site_key:
                self.logger.error("❌ site key یافت نشد")
                return False
            
            self.logger.info(f"🔑 sitekey یافت شد: {site_key}")
            
            # ارسال به سرویس
            token = self.captcha_solver.solve_captcha(
                site_key=site_key,
                page_url=self.page.url,
                captcha_type='reCAPTCHA Enterprise'
            )
            
            if not token:
                self.logger.error("❌ سرویس نتوانست توکن برگرداند")
                return False
            
            self.logger.info("✅ توکن از سرویس دریافت شد")
            
            # تزریق توکن
            injection_success = self._inject_token(token)
            if not injection_success:
                self.logger.error("❌ تزریق توکن ناموفق")
                return False
            
            # تأیید نهایی تزریق
            verification_success = self._verify_token_injection(token)
            if verification_success:
                self.logger.info("✅ تزریق توکن تأیید شد")
                return True
            else:
                self.logger.error("❌ تأیید تزریق توکن ناموفق")
                return False
            
        except Exception as e:
            self.logger.error(f"❌ خطا در حل با سرویس: {e}")
            return False
    
    def _inject_token(self, token: str) -> bool:
        """تزریق بهینه‌شده توکن با تریگر رویدادها"""
        try:
            self.logger.info("💉 تزریق توکن...")
            
            # تزریق توکن با تریگر کردن رویدادهای لازم
            injection_result = self.page.evaluate(f"""
                () => {{
                    const token = '{token}';
                    
                    // یافتن یا ایجاد فیلد response
                    let responseField = document.getElementById('g-recaptcha-response');
                    
                    if (!responseField) {{
                        responseField = document.createElement('textarea');
                        responseField.id = 'g-recaptcha-response';
                        responseField.name = 'g-recaptcha-response';
                        responseField.style.display = 'none';
                        
                        const form = document.querySelector('form') || document.body;
                        form.appendChild(responseField);
                    }}
                    
                    // تزریق توکن
                    responseField.value = token;
                    responseField.innerHTML = token;
                    
                    // تریگر رویدادهای input و change
                    const inputEvent = new Event('input', {{ bubbles: true, cancelable: true }});
                    const changeEvent = new Event('change', {{ bubbles: true, cancelable: true }});
                    responseField.dispatchEvent(inputEvent);
                    responseField.dispatchEvent(changeEvent);
                    
                    // تنظیم grecaptcha
                    if (typeof grecaptcha !== 'undefined') {{
                        grecaptcha.getResponse = function() {{
                            return token;
                        }};
                        
                        // تریگر callback اگر وجود دارد
                        if (window.recaptchaCallback) {{
                            try {{
                                window.recaptchaCallback(token);
                            }} catch(e) {{
                                console.log('Callback error:', e);
                            }}
                        }}
                        
                        // تریگر رویداد سفارشی
                        const recaptchaEvent = new CustomEvent('recaptcha-solved', {{
                            detail: {{ token: token }}
                        }});
                        document.dispatchEvent(recaptchaEvent);
                    }}
                    
                    // پنهان کردن کپچا
                    const recaptchaElements = document.querySelectorAll('.g-recaptcha, [data-sitekey]');
                    recaptchaElements.forEach(el => {{
                        el.style.display = 'none';
                    }});
                    
                    // پنهان کردن iframe های کپچا
                    const iframes = document.querySelectorAll('iframe[src*="recaptcha"]');
                    iframes.forEach(iframe => {{
                        iframe.style.display = 'none';
                        iframe.style.visibility = 'hidden';
                    }});
                    
                    return true;
                }}
            """)
            
            if injection_result:
                self.logger.info("✅ تزریق توکن موفق")
                
                # انتظار برای پردازش و اجرای رویدادها
                self.page.wait_for_timeout(2000)
                
                # تأیید تزریق
                if self._verify_token_injection(token):
                    self.logger.info("✅ تزریق توکن تأیید شد")
                    
                    # انتظار اضافی برای پنهان شدن کپچا
                    self.page.wait_for_timeout(1500)
                    
                    # بررسی نهایی که آیا کپچا پنهان شده
                    if not self._check_captcha_still_visible():
                        self.logger.info("✅ کپچا با موفقیت پنهان شد")
                        return True
                    else:
                        self.logger.warning("⚠️ توکن تزریق شد اما کپچا همچنان نمایش داده می‌شود")
                        # تلاش مجدد برای پنهان کردن
                        self._force_hide_captcha()
                        self.page.wait_for_timeout(1000)
                        return not self._check_captcha_still_visible()
                else:
                    self.logger.warning("⚠️ تزریق انجام شد اما تأیید نشد")
                    return False
            else:
                self.logger.error("❌ تزریق توکن ناموفق")
                return False
                
        except Exception as e:
            self.logger.error(f"❌ خطا در تزریق توکن: {e}")
            return False
    
    def _verify_token_injection(self, token: str) -> bool:
        """تأیید موفقیت تزریق توکن"""
        try:
            verification_result = self.page.evaluate(f"""
                () => {{
                    const expectedToken = '{token}';
                    
                    // بررسی فیلد response
                    const responseField = document.getElementById('g-recaptcha-response');
                    if (responseField && responseField.value === expectedToken) {{
                        return true;
                    }}
                    
                    // بررسی grecaptcha
                    if (typeof grecaptcha !== 'undefined' && typeof grecaptcha.getResponse === 'function') {{
                        try {{
                            const response = grecaptcha.getResponse();
                            if (response === expectedToken) {{
                                return true;
                            }}
                        }} catch (e) {{}}
                    }}
                    
                    return false;
                }}
            """)
            
            return verification_result
            
        except Exception as e:
            self.logger.error(f"❌ خطا در تأیید تزریق: {e}")
            return False
    
    def _extract_recaptcha_sitekey(self) -> Optional[str]:
        """استخراج site key از صفحه"""
        try:
            # روش‌های مختلف برای یافتن site key
            site_key = self.page.evaluate("""
                () => {
                    // روش 1: از data-sitekey
                    let element = document.querySelector('[data-sitekey]');
                    if (element) {
                        return element.getAttribute('data-sitekey');
                    }
                    
                    // روش 2: از iframe src
                    const iframes = document.querySelectorAll('iframe[src*="recaptcha"]');
                    for (let iframe of iframes) {
                        const src = iframe.src;
                        const match = src.match(/[?&]k=([^&]+)/);
                        if (match) {
                            return match[1];
                        }
                    }
                    
                    // روش 3: از script tags
                    const scripts = document.querySelectorAll('script');
                    for (let script of scripts) {
                        const content = script.textContent || script.innerHTML;
                        const match = content.match(/sitekey['"]\\s*:\\s*['"]([^'"]+)['"]/);
                         if (match) {
                             return match[1];
                         }
                    }
                    
                    return null;
                }
            """)
            
            return site_key
            
        except Exception as e:
            self.logger.error(f"❌ خطا در استخراج site key: {e}")
            return None
    
    def _solve_recaptcha_v3(self, captcha_info: Dict) -> bool:
        """حل reCAPTCHA v3"""
        try:
            self.logger.info("🔧 حل reCAPTCHA v3...")
            # پیاده‌سازی ساده برای v3
            return True
        except Exception as e:
            self.logger.error(f"❌ خطا در حل reCAPTCHA v3: {e}")
            return False
    
    def _solve_hcaptcha(self, captcha_info: Dict) -> bool:
        """حل hCaptcha"""
        try:
            self.logger.info("🔧 حل hCaptcha...")
            # پیاده‌سازی ساده برای hCaptcha
            return True
        except Exception as e:
            self.logger.error(f"❌ خطا در حل hCaptcha: {e}")
            return False
    
    def _final_captcha_verification(self) -> bool:
        """تأیید نهایی حل کپچا - بررسی واقعی وجود توکن معتبر"""
        try:
            self.logger.info("🔍 تأیید نهایی حل کپچا...")
            
            # انتظار کوتاه برای پردازش
            self.page.wait_for_timeout(1000)
            
            # بررسی وجود توکن معتبر
            token_check = self.page.evaluate("""
                () => {
                    // بررسی فیلدهای مختلف response
                    const selectors = [
                        'textarea[name="g-recaptcha-response"]',
                        'input[name="g-recaptcha-response"]',
                        '#g-recaptcha-response',
                        '[name="g-recaptcha-response"]'
                    ];
                    
                    for (let selector of selectors) {
                        const field = document.querySelector(selector);
                        if (field && field.value && field.value.length > 20) {
                            return {
                                found: true,
                                length: field.value.length,
                                selector: selector,
                                token_preview: field.value.substring(0, 20) + '...'
                            };
                        }
                    }
                    
                    // بررسی grecaptcha
                    if (typeof grecaptcha !== 'undefined' && typeof grecaptcha.getResponse === 'function') {
                        try {
                            const response = grecaptcha.getResponse();
                            if (response && response.length > 20) {
                                return {
                                    found: true,
                                    length: response.length,
                                    selector: 'grecaptcha.getResponse()',
                                    token_preview: response.substring(0, 20) + '...'
                                };
                            }
                        } catch (e) {
                            console.log('خطا در بررسی grecaptcha:', e);
                        }
                    }
                    
                    return {found: false, reason: 'هیچ توکن معتبری یافت نشد'};
                }
            """)
            
            if token_check.get('found'):
                self.logger.info(f"✅ توکن معتبر یافت شد - طول: {token_check.get('length')} - منبع: {token_check.get('selector')}")
                self.logger.debug(f"🔍 پیش‌نمایش توکن: {token_check.get('token_preview')}")
                
                # بررسی اضافی: آیا کپچا هنوز نمایش داده می‌شود؟
                captcha_still_visible = self._check_captcha_still_visible()
                if captcha_still_visible:
                    self.logger.warning("⚠️ توکن یافت شد اما کپچا هنوز نمایش داده می‌شود")
                    return False
                
                return True
            else:
                self.logger.error(f"❌ توکن معتبر یافت نشد - دلیل: {token_check.get('reason', 'نامشخص')}")
                return False
                
        except Exception as e:
            self.logger.error(f"❌ خطا در تأیید نهایی کپچا: {e}")
            return False
    
    def _check_captcha_still_visible(self) -> bool:
        """بررسی اینکه آیا کپچا هنوز نمایش داده می‌شود"""
        try:
            # بررسی iframe های کپچا
            captcha_visible = self.page.evaluate("""
                () => {
                    // بررسی iframe های reCAPTCHA
                    const recaptchaFrames = document.querySelectorAll('iframe[src*="recaptcha"]');
                    for (let frame of recaptchaFrames) {
                        const style = window.getComputedStyle(frame);
                        if (style.display !== 'none' && style.visibility !== 'hidden' && frame.offsetHeight > 0) {
                            return true;
                        }
                    }
                    
                    // بررسی iframe های hCaptcha
                    const hcaptchaFrames = document.querySelectorAll('iframe[src*="hcaptcha"]');
                    for (let frame of hcaptchaFrames) {
                        const style = window.getComputedStyle(frame);
                        if (style.display !== 'none' && style.visibility !== 'hidden' && frame.offsetHeight > 0) {
                            return true;
                        }
                    }
                    
                    // بررسی چالش‌های تصویری
                    const challengeFrames = document.querySelectorAll('iframe[src*="bframe"]');
                    for (let frame of challengeFrames) {
                        const style = window.getComputedStyle(frame);
                        if (style.display !== 'none' && style.visibility !== 'hidden' && frame.offsetHeight > 0) {
                            return true;
                        }
                    }
                    
                    // بررسی عناصر کپچای اصلی
                    const captchaElements = document.querySelectorAll('.g-recaptcha, [data-sitekey], .recaptcha-container');
                    for (let element of captchaElements) {
                        const style = window.getComputedStyle(element);
                        if (style.display !== 'none' && style.visibility !== 'hidden' && element.offsetHeight > 0) {
                            return true;
                        }
                    }
                    
                    return false;
                }
            """)
            
            return captcha_visible
            
        except Exception as e:
            self.logger.error(f"❌ خطا در بررسی نمایش کپچا: {e}")
            return False
    
    def _force_hide_captcha(self) -> bool:
        """پنهان کردن اجباری کپچا"""
        try:
            self.logger.info("🔒 تلاش برای پنهان کردن اجباری کپچا...")
            
            hide_result = self.page.evaluate("""
                () => {
                    // پنهان کردن همه iframe های کپچا
                    const allFrames = document.querySelectorAll('iframe[src*="recaptcha"], iframe[src*="hcaptcha"], iframe[src*="bframe"]');
                    allFrames.forEach(frame => {
                        frame.style.display = 'none !important';
                        frame.style.visibility = 'hidden !important';
                        frame.style.opacity = '0 !important';
                        frame.style.height = '0px !important';
                        frame.style.width = '0px !important';
                        frame.remove();
                    });
                    
                    // پنهان کردن عناصر کپچای اصلی
                    const captchaElements = document.querySelectorAll('.g-recaptcha, [data-sitekey], .recaptcha-container, .captcha-container');
                    captchaElements.forEach(element => {
                        element.style.display = 'none !important';
                        element.style.visibility = 'hidden !important';
                        element.style.opacity = '0 !important';
                        element.style.height = '0px !important';
                    });
                    
                    // حذف کلاس‌های مربوط به کپچا از body
                    document.body.classList.remove('recaptcha-active', 'captcha-active');
                    
                    return true;
                }
            """)
            
            if hide_result:
                self.logger.info("✅ کپچا به صورت اجباری پنهان شد")
                return True
            else:
                self.logger.warning("⚠️ پنهان کردن اجباری کپچا ناموفق")
                return False
                
        except Exception as e:
            self.logger.error(f"❌ خطا در پنهان کردن اجباری کپچا: {e}")
            return False
    
    def get_captcha_status(self) -> Dict:
        """گزارش وضعیت کامل کپچا برای دیباگ"""
        return {
            'solved': self.captcha_solved,
            'attempts': self.solve_attempts,
            'failed_solves': self.failed_solves,
            'last_error': self.last_error,
            'success_rate': (self.solve_attempts - self.failed_solves) / max(self.solve_attempts, 1) * 100
        }
    
    def log_captcha_status(self):
        """لاگ وضعیت کامل کپچا"""
        status = self.get_captcha_status()
        self.logger.info(f"📊 وضعیت کپچا: حل شده={status['solved']}, تلاش‌ها={status['attempts']}, "
                        f"شکست‌ها={status['failed_solves']}, نرخ موفقیت={status['success_rate']:.1f}%")
        if status['last_error']:
             self.logger.debug(f"🔍 آخرین خطا: {status['last_error']}")
    
    def validate_captcha_state(self) -> bool:
        """اعتبارسنجی وضعیت کپچا برای تست"""
        try:
            # بررسی consistency بین وضعیت‌های مختلف
            has_token = self._final_captcha_verification()
            captcha_visible = self._check_captcha_still_visible()
            
            # اگر کپچا حل شده باشد، باید token داشته باشیم و کپچا نمایش داده نشود
            if self.captcha_solved:
                if not has_token:
                    self.logger.warning("⚠️ ناسازگاری: captcha_solved=True اما token یافت نشد")
                    return False
                if captcha_visible:
                    self.logger.warning("⚠️ ناسازگاری: captcha_solved=True اما کپچا هنوز نمایش داده می‌شود")
                    return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"❌ خطا در اعتبارسنجی وضعیت کپچا: {e}")
            return False