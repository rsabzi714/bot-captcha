# modules/form_automation.py
import time
from typing import List, Dict, Optional
from utils.element_finder import ElementFinder
from human_behavior import HumanBehavior

class FormAutomation:
    """اتوماسیون پر کردن فرم‌ها با رفتار انسانی"""
    
    def __init__(self, page, logger):
        self.page = page
        self.logger = logger
        
        # ابزارهای کمکی
        self.element_finder = ElementFinder(page, logger)
        self.human_behavior = HumanBehavior(page)
        
        # تنظیمات فرم
        self.typing_delay = 50  # میلی‌ثانیه بین کاراکترها
        self.field_delay = (1, 3)  # ثانیه بین فیلدها
        
        # Selector های مختلف برای فیلدها
        self.username_selectors = [
            'input[name="username"]',
            'input[aria-label="username"]',
            'input[name="email"]',
            'input[id="email"]',
            'input[type="email"]',
            'input[placeholder*="email" i]',
            'input[placeholder*="utilizador" i]',
            'form.login-identificacao input[name="username"]',
            '.login-identificacao input[type="text"]',
            'input[placeholder*="###" i]'
        ]
        
        self.password_selectors = [
            'input[name="password"]',
            'input[aria-label="password"]',
            'input[id="password"]',
            'input[type="password"]',
            'input[placeholder*="password" i]',
            'input[placeholder*="palavra-passe" i]',
            'input[placeholder*="senha" i]',
            'form.login-identificacao input[name="password"]',
            '.login-identificacao input[type="password"]',
            'input[placeholder*="***" i]'
        ]
    
    def fill_username_field(self, username: str) -> bool:
        """پر کردن فیلد نام کاربری با رفتار انسانی"""
        if not username:
            self.logger.error("❌ نام کاربری خالی است")
            return False
        self.logger.info("📝 پر کردن فیلد نام کاربری...")
        
        try:
            # انتظار برای بارگذاری کامل فرم
            time.sleep(2)
            
            # یافتن فیلد نام کاربری
            username_field = None
            for selector in self.username_selectors:
                try:
                    elements = self.page.locator(selector)
                    if elements.count() > 0:
                        for i in range(elements.count()):
                            element = elements.nth(i)
                            try:
                                if element.is_visible(timeout=2000) and element.is_enabled():
                                    username_field = element
                                    self.logger.info(f"🎯 فیلد نام کاربری یافت شد: {selector}")
                                    break
                            except:
                                continue
                        if username_field:
                            break
                except Exception as e:
                    self.logger.debug(f"خطا در بررسی selector {selector}: {e}")
                    continue
            
            if not username_field:
                self.logger.error("❌ فیلد نام کاربری یافت نشد")
                return False
            
            # اسکرول به فیلد
            username_field.scroll_into_view_if_needed()
            self.human_behavior.human_delay(0.5, 1)
            
            # کلیک برای فوکوس
            username_field.click()
            self.human_behavior.human_delay(0.5, 1)
            
            # پاک کردن محتوای قبلی
            username_field.fill('')
            self.human_behavior.human_delay(0.3, 0.7)
            
            # تایپ کردن نام کاربری
            self._type_with_human_behavior(username_field, username)
            
            # بررسی موفقیت
            try:
                filled_value = username_field.input_value()
                if filled_value == username:
                    self.logger.info("✅ نام کاربری با موفقیت وارد شد")
                    return True
                else:
                    self.logger.warning(f"⚠️ مقدار وارد شده متفاوت است: انتظار '{username}', دریافت '{filled_value}'")
                    # تلاش مجدد
                    username_field.fill(username)
                    self.human_behavior.human_delay(0.5, 1)
                    return True
            except:
                # برای فیلدهای password نمی‌توان مقدار را خواند
                self.logger.info("✅ نام کاربری وارد شد (تأیید مقدار ممکن نیست)")
                return True
                
        except Exception as e:
            self.logger.error(f"❌ خطا در پر کردن نام کاربری: {e}")
            return False
    
    def fill_password_field(self, password: str) -> bool:
        """پر کردن فیلد رمز عبور"""
        self.logger.info("🔐 پر کردن فیلد رمز عبور...")
        
        try:
            # یافتن فیلد رمز عبور
            password_field = None
            for selector in self.password_selectors:
                try:
                    elements = self.page.locator(selector)
                    if elements.count() > 0:
                        for i in range(elements.count()):
                            element = elements.nth(i)
                            try:
                                if element.is_visible(timeout=2000) and element.is_enabled():
                                    password_field = element
                                    self.logger.info(f"🎯 فیلد رمز عبور یافت شد: {selector}")
                                    break
                            except:
                                continue
                        if password_field:
                            break
                except Exception as e:
                    self.logger.debug(f"خطا در بررسی selector {selector}: {e}")
                    continue
            
            if not password_field:
                self.logger.error("❌ فیلد رمز عبور یافت نشد")
                return False
            
            # اسکرول به فیلد
            password_field.scroll_into_view_if_needed()
            self.human_behavior.human_delay(0.5, 1)
            
            # کلیک برای فوکوس
            password_field.click()
            self.human_behavior.human_delay(0.5, 1)
            
            # پاک کردن محتوای قبلی
            password_field.fill('')
            self.human_behavior.human_delay(0.3, 0.7)
            
            # تایپ کردن رمز عبور
            self._type_with_human_behavior(password_field, password)
            
            # بررسی موفقیت (برای password نمی‌توان مقدار را خواند)
            self.logger.info("✅ رمز عبور با موفقیت وارد شد")
            return True
                
        except Exception as e:
            self.logger.error(f"❌ خطا در پر کردن رمز عبور: {e}")
            return False
    
    def fill_form_fields(self, field_data: Dict[str, str]) -> bool:
        """پر کردن چندین فیلد فرم"""
        self.logger.info(f"📝 پر کردن {len(field_data)} فیلد فرم...")
        
        success_count = 0
        total_fields = len(field_data)
        
        for field_name, field_value in field_data.items():
            try:
                self.logger.info(f"📝 پر کردن فیلد: {field_name}")
                
                # یافتن فیلد
                field_selectors = self._get_field_selectors(field_name)
                field_element = self.element_finder.find_with_multiple_selectors(field_selectors)
                
                if not field_element:
                    self.logger.warning(f"⚠️ فیلد {field_name} یافت نشد")
                    continue
                
                # پر کردن فیلد
                if self._fill_field(field_element, field_value):
                    success_count += 1
                    self.logger.info(f"✅ فیلد {field_name} پر شد")
                else:
                    self.logger.warning(f"⚠️ خطا در پر کردن فیلد {field_name}")
                
                # تاخیر بین فیلدها
                self.human_behavior.human_delay(*self.field_delay)
                
            except Exception as e:
                self.logger.error(f"❌ خطا در پر کردن فیلد {field_name}: {e}")
        
        success_rate = success_count / total_fields if total_fields > 0 else 0
        self.logger.info(f"📊 نتیجه: {success_count}/{total_fields} فیلد پر شد ({success_rate:.1%})")
        
        return success_rate >= 0.8  # حداقل 80% موفقیت
    
    def _fill_field(self, field_element, value: str) -> bool:
        """پر کردن یک فیلد خاص"""
        try:
            # بررسی نوع فیلد
            field_type = field_element.get_attribute('type') or 'text'
            
            # کلیک برای فوکوس
            field_element.click()
            self.human_behavior.human_delay(0.3, 0.7)
            
            # پاک کردن محتوای قبلی
            field_element.fill('')
            self.human_behavior.human_delay(0.2, 0.5)
            
            # پر کردن بر اساس نوع فیلد
            if field_type in ['text', 'email', 'password']:
                self._type_with_human_behavior(field_element, value)
            elif field_type == 'select':
                field_element.select_option(value)
            elif field_type == 'checkbox':
                if value.lower() in ['true', '1', 'yes', 'on']:
                    field_element.check()
                else:
                    field_element.uncheck()
            elif field_type == 'radio':
                field_element.check()
            else:
                # پیش‌فرض: تایپ معمولی
                self._type_with_human_behavior(field_element, value)
            
            return True
            
        except Exception as e:
            self.logger.debug(f"خطا در پر کردن فیلد: {e}")
            return False
    
    def _type_with_human_behavior(self, element, text: str):
        """تایپ کردن با رفتار انسانی"""
        try:
            # تایپ با تاخیر طبیعی
            element.type(text, delay=self.typing_delay)
            
            # شبیه‌سازی اشتباهات تایپی (گاهی اوقات)
            if len(text) > 5 and self.human_behavior._random.random() < 0.1:  # 10% احتمال
                # تایپ کاراکتر اضافی و سپس حذف آن
                element.type('x', delay=self.typing_delay)
                time.sleep(0.1)
                element.press('Backspace')
                time.sleep(0.2)
            
        except Exception as e:
            self.logger.debug(f"خطا در تایپ انسانی: {e}")
            # fallback به روش معمولی
            element.fill(text)
    
    def _get_field_selectors(self, field_name: str) -> List[str]:
        """دریافت selector های مناسب برای فیلد"""
        field_name_lower = field_name.lower()
        
        # selector های عمومی
        selectors = [
            f'input[name="{field_name}"]',
            f'input[id="{field_name}"]',
            f'input[name="{field_name_lower}"]',
            f'input[id="{field_name_lower}"]',
            f'textarea[name="{field_name}"]',
            f'select[name="{field_name}"]'
        ]
        
        # selector های خاص بر اساس نام فیلد
        if 'email' in field_name_lower or 'username' in field_name_lower:
            selectors.extend(self.username_selectors)
        elif 'password' in field_name_lower or 'senha' in field_name_lower:
            selectors.extend(self.password_selectors)
        elif 'phone' in field_name_lower or 'telefone' in field_name_lower:
            selectors.extend([
                'input[type="tel"]',
                'input[placeholder*="phone" i]',
                'input[placeholder*="telefone" i]'
            ])
        elif 'date' in field_name_lower or 'data' in field_name_lower:
            selectors.extend([
                'input[type="date"]',
                'input[placeholder*="date" i]',
                'input[placeholder*="data" i]'
            ])
        
        return selectors
    
    def submit_form(self, form_selector: str = None) -> bool:
        """ارسال فرم"""
        self.logger.info("📤 ارسال فرم...")
        
        try:
            # selector های دکمه ارسال
            submit_selectors = [
                'button[type="submit"]',
                'input[type="submit"]',
                'button:has-text("Submit")',
                'button:has-text("Entrar")',
                'button:has-text("Login")',
                'button:has-text("Enviar")',
                '.submit-button',
                '#submit-button'
            ]
            
            # اگر form selector داده شده، آن را اولویت بده
            if form_selector:
                submit_selectors.insert(0, f'{form_selector} button[type="submit"]')
                submit_selectors.insert(1, f'{form_selector} input[type="submit"]')
            
            # یافتن دکمه ارسال
            submit_button = self.element_finder.find_with_multiple_selectors(submit_selectors)
            
            if not submit_button:
                self.logger.error("❌ دکمه ارسال یافت نشد")
                return False
            
            # کلیک روی دکمه ارسال
            submit_button.click()
            
            # انتظار برای پردازش
            self.human_behavior.human_delay(2, 4)
            
            self.logger.info("✅ فرم ارسال شد")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ خطا در ارسال فرم: {e}")
            return False
    
    def clear_form(self, form_selector: str = None) -> bool:
        """پاک کردن تمام فیلدهای فرم"""
        self.logger.info("🧹 پاک کردن فرم...")
        
        try:
            # selector های فیلدهای ورودی
            if form_selector:
                input_selectors = [
                    f'{form_selector} input[type="text"]',
                    f'{form_selector} input[type="email"]',
                    f'{form_selector} input[type="password"]',
                    f'{form_selector} textarea'
                ]
            else:
                input_selectors = [
                    'input[type="text"]',
                    'input[type="email"]',
                    'input[type="password"]',
                    'textarea'
                ]
            
            cleared_count = 0
            
            for selector in input_selectors:
                try:
                    elements = self.element_finder.find_elements(selector)
                    for element in elements:
                        if element.is_visible() and element.is_enabled():
                            element.fill('')
                            cleared_count += 1
                except:
                    continue
            
            self.logger.info(f"✅ {cleared_count} فیلد پاک شد")
            return cleared_count > 0
            
        except Exception as e:
            self.logger.error(f"❌ خطا در پاک کردن فرم: {e}")
            return False