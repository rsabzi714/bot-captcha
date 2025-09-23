# human_behavior.py
import random
import time
import math
from typing import Tuple, List, Dict, Optional
import logging

class HumanBehavior:
    """کلاس پیشرفته شبیه‌سازی رفتار انسانی برای جلوگیری از تشخیص ربات"""
    
    def __init__(self, page):
        self.page = page
        self.logger = logging.getLogger(__name__)
        
        # پارامترهای شخصیت‌سازی
        self.typing_speed_wpm = random.uniform(35, 65)  # کلمه در دقیقه
        self.reaction_time_base = random.uniform(0.8, 1.5)  # زمان واکنش پایه
        self.reading_speed_wpm = random.uniform(200, 300)  # سرعت خواندن
        self.mouse_precision = random.uniform(0.7, 0.95)  # دقت ماوس
        
        # آمار رفتاری
        self.session_actions = 0
        self.total_typing_time = 0
        self.total_reading_time = 0
        
        # Session Memory - حافظه کاربر
        self.current_mouse_x = random.uniform(400, 800)
        self.current_mouse_y = random.uniform(300, 500)
        self.last_typing_speed = self.typing_speed_wpm
        self.last_delay_pattern = 'normal'
        self.user_behavior_profile = random.choice(['careful', 'quick', 'hesitant', 'confident'])
        self.session_start_time = time.time()
        
        # الگوهای رفتاری پیشرفته
        self.copy_paste_probability = 0.15  # احتمال کپی-پیست
        self.rewrite_probability = 0.08     # احتمال بازنویسی
        self.distraction_probability = 0.12  # احتمال حواس‌پرتی
        self.mistake_probability = 0.05      # احتمال اشتباه کلیک
    
    def human_delay(self, min_delay: float = 0.8, max_delay: float = 2.5, 
                   context: str = "general") -> None:
        """تاخیر بهینه‌شده انسان‌گونه برای عملکرد سریع‌تر"""
        try:
            # تنظیم تاخیر بهینه بر اساس زمینه
            context_multipliers = {
                "thinking": random.uniform(0.8, 1.5),   # بهینه‌سازی برای سرعت
                "reading": random.uniform(0.3, 0.8),    # کاهش زمان خواندن
                "typing": random.uniform(0.1, 0.6),     # تایپ سریع‌تر
                "clicking": random.uniform(0.1, 0.5),   # کلیک سریع‌تر
                "hesitation": random.uniform(0.5, 1.2), # تردید کمتر
                "distraction": random.uniform(2.0, 4.0), # کاهش از 8.0 به 4.0
                "general": random.uniform(0.8, 1.5)
            }
            
            multiplier = context_multipliers.get(context, 1.0)
            
            # تاخیر پایه با توزیع غیرخطی (محدود شده)
            if random.random() < 0.10:  # کاهش از 15% به 10%
                base_delay = random.uniform(max_delay * 1.2, max_delay * 2.0)  # کاهش از 3.0 به 2.0
            elif random.random() < 0.25:  # 25% احتمال تاخیر کوتاه
                base_delay = random.uniform(min_delay * 0.3, min_delay * 0.7)
            else:
                base_delay = random.uniform(min_delay, max_delay)
            
            # عوامل انسانی
            fatigue_factor = 1 + (self.session_actions * 0.001)  # کاهش تأثیر خستگی
            time_of_day_factor = self._get_time_of_day_factor()  # عامل زمان روز
            mood_factor = random.uniform(0.8, 1.2)  # کاهش تنوع از 0.7-1.4 به 0.8-1.2
            
            final_delay = base_delay * multiplier * fatigue_factor * time_of_day_factor * mood_factor
            
            # حداقل و حداکثر منطقی (کاهش حداکثر از 15 به 8 ثانیه)
            final_delay = max(0.1, min(final_delay, 8.0))
            
            self.logger.debug(f"Human delay: {final_delay:.2f}s (context: {context})")
            time.sleep(final_delay)
            self.session_actions += 1
            
        except Exception as e:
            self.logger.error(f"خطا در human_delay: {e}")
            # fallback delay
            time.sleep(random.uniform(0.5, 2.0))
    
    def _get_time_of_day_factor(self) -> float:
        """عامل زمان روز برای شبیه‌سازی خستگی طبیعی"""
        import datetime
        hour = datetime.datetime.now().hour
        
        if 6 <= hour <= 9:  # صبح زود - کمی آهسته
            return random.uniform(1.1, 1.3)
        elif 9 <= hour <= 12:  # صبح - سریع
            return random.uniform(0.8, 1.0)
        elif 12 <= hour <= 14:  # ظهر - کمی آهسته (ناهار)
            return random.uniform(1.0, 1.2)
        elif 14 <= hour <= 18:  # بعدازظهر - سریع
            return random.uniform(0.9, 1.1)
        elif 18 <= hour <= 22:  # عصر - متوسط
            return random.uniform(1.0, 1.2)
        else:  # شب - آهسته
            return random.uniform(1.2, 1.5)
    
    def human_type(self, selector: str, text: str, clear_first: bool = True,
                  simulate_errors: bool = True) -> None:
        """تایپ انسان‌گونه پیشرفته با شبیه‌سازی خطاها و الگوهای واقعی"""
        try:
            # بررسی وجود page
            if not self.page or self.page.is_closed():
                self.logger.error("صفحه در دسترس نیست")
                return
            
            element = self.page.locator(selector)
            
            # انتظار برای آماده شدن عنصر با timeout
            element.wait_for(state='visible', timeout=10000)
            
            # بررسی اینکه عنصر واقعاً قابل تایپ است
            if not element.is_enabled():
                self.logger.warning(f"عنصر {selector} غیرفعال است")
                return
            
            # فوکوس روی عنصر
            self.human_click_element(element)
            self.human_delay(0.3, 0.8, "thinking")
            
            # پاک کردن فیلد در صورت نیاز
            if clear_first:
                try:
                    self.page.keyboard.press('Control+a')
                    self.human_delay(0.1, 0.3)
                    self.page.keyboard.press('Delete')
                    self.human_delay(0.2, 0.5)
                except Exception as e:
                    self.logger.warning(f"خطا در پاک کردن فیلد: {e}")
            
            # تصمیم‌گیری برای نوع تایپ
            typing_method = self._choose_typing_method(text)
            
            if typing_method == 'copy_paste':
                self._type_with_copy_paste(text)
            elif typing_method == 'rewrite':
                self._type_with_rewrite(text)
            elif typing_method == 'distracted':
                self._type_with_distraction(text, simulate_errors)
            else:
                self._type_normally(text, simulate_errors)
            
            # به‌روزرسانی آمار
            chars_per_second = (self.last_typing_speed * 5) / 60
            self.total_typing_time += len(text) / chars_per_second
            self.logger.debug(f"Typed '{text}' using method: {typing_method}")
            
        except Exception as e:
            self.logger.error(f"خطا در human_type: {e}")
            # fallback: تایپ ساده
            try:
                if self.page and not self.page.is_closed():
                    self.page.keyboard.type(text, delay=random.uniform(50, 150))
            except Exception as fallback_error:
                self.logger.error(f"خطا در fallback typing: {fallback_error}")
    
    def _choose_typing_method(self, text: str) -> str:
        """انتخاب روش تایپ بر اساس پروفایل کاربر و احتمالات"""
        # کپی-پیست برای متن‌های طولانی
        if len(text) > 20 and random.random() < self.copy_paste_probability:
            return 'copy_paste'
        
        # بازنویسی برای کاربران دقیق
        if self.user_behavior_profile == 'careful' and random.random() < self.rewrite_probability:
            return 'rewrite'
        
        # حواس‌پرتی
        if random.random() < self.distraction_probability:
            return 'distracted'
        
        return 'normal'
    
    def _type_with_copy_paste(self, text: str) -> None:
        """شبیه‌سازی کپی-پیست"""
        # شبیه‌سازی کپی از جای دیگر
        self.human_delay(1, 3, "thinking")
        
        # تایپ سریع (شبیه‌سازی پیست)
        self.page.keyboard.type(text, delay=random.uniform(10, 30))
        
        # بررسی نتیجه
        self.human_delay(0.5, 1.5, "reading")
    
    def _type_with_rewrite(self, text: str) -> None:
        """شبیه‌سازی بازنویسی متن"""
        # تایپ اول
        self._type_normally(text, simulate_errors=False)
        
        # تصمیم برای بازنویسی
        self.human_delay(1, 2, "thinking")
        
        # انتخاب و حذف
        self.page.keyboard.press('Control+a')
        self.human_delay(0.2, 0.5)
        self.page.keyboard.press('Delete')
        self.human_delay(0.5, 1, "thinking")
        
        # تایپ مجدد
        self._type_normally(text, simulate_errors=False)
    
    def _type_with_distraction(self, text: str, simulate_errors: bool) -> None:
        """شبیه‌سازی تایپ با حواس‌پرتی"""
        words = text.split()
        typed_words = []
        
        for i, word in enumerate(words):
            # تایپ کلمه
            if typed_words:
                self.page.keyboard.type(' ', delay=self._get_char_delay())
            
            self._type_word_with_errors(word, simulate_errors)
            typed_words.append(word)
            
            # حواس‌پرتی در وسط
            if i < len(words) - 1 and random.random() < 0.3:
                self.human_delay(2, 5, "distraction")
                # شبیه‌سازی Alt+Tab
                if random.random() < 0.1:
                    self.human_delay(3, 8, "distraction")
    
    def _type_normally(self, text: str, simulate_errors: bool) -> None:
        """تایپ عادی کاراکتر به کاراکتر"""
        for i, char in enumerate(text):
            # شبیه‌سازی خطای تایپ
            if simulate_errors and random.random() < 0.02:  # 2% احتمال خطا
                wrong_char = self._get_adjacent_key(char)
                self.page.keyboard.type(wrong_char, delay=self._get_char_delay())
                self.human_delay(0.2, 0.5)
                # اصلاح خطا
                self.page.keyboard.press('Backspace')
                self.human_delay(0.1, 0.3)
            
            # تایپ کاراکتر صحیح
            self.page.keyboard.type(char, delay=self._get_char_delay())
            
            # مکث تفکر گاه‌به‌گاه
            if random.random() < 0.08:  # 8% احتمال مکث
                self.human_delay(0.5, 2.0, "thinking")
            
            # مکث طولانی‌تر در نقطه‌گذاری
            if char in '.,!?;:':
                self.human_delay(0.2, 0.8, "thinking")
    
    def _type_word_with_errors(self, word: str, simulate_errors: bool) -> None:
        """تایپ یک کلمه با احتمال خطا"""
        for char in word:
            if simulate_errors and random.random() < 0.02:
                wrong_char = self._get_adjacent_key(char)
                self.page.keyboard.type(wrong_char, delay=self._get_char_delay())
                self.human_delay(0.2, 0.5)
                self.page.keyboard.press('Backspace')
                self.human_delay(0.1, 0.3)
            
            self.page.keyboard.type(char, delay=self._get_char_delay())
    
    def _get_char_delay(self) -> float:
        """محاسبه تاخیر بین کاراکترها با الگوهای پیچیده‌تر و session memory"""
        # استفاده از سرعت تایپ به‌روزرسانی شده
        base_delay = 60 / (self.last_typing_speed * 5)
        
        # تطبیق سرعت تایپ با زمان session
        session_duration = time.time() - self.session_start_time
        if session_duration > 300:  # بعد از 5 دقیقه، کمی آهسته‌تر
            self.last_typing_speed *= 0.98
        
        # الگوهای مختلف تایپ بر اساس پروفایل کاربر (کاهش delayهای طولانی)
        if self.user_behavior_profile == 'quick':
            if random.random() < 0.02:  # کاهش از 3% به 2%
                variation = random.uniform(3, 6)  # کاهش از 5-12 به 3-6
            elif random.random() < 0.35:  # 35% تایپ سریع
                variation = random.uniform(0.2, 0.6)
            else:
                variation = random.uniform(0.6, 1.5)
        elif self.user_behavior_profile == 'careful':
            if random.random() < 0.05:  # کاهش از 8% به 5%
                variation = random.uniform(4, 8)  # کاهش از 8-25 به 4-8
            elif random.random() < 0.15:  # 15% توقف متوسط
                variation = random.uniform(2, 5)  # کاهش از 3-8 به 2-5
            else:
                variation = random.uniform(1.0, 2.5)
        elif self.user_behavior_profile == 'hesitant':
            if random.random() < 0.08:  # کاهش از 12% به 8%
                variation = random.uniform(5, 10)  # کاهش از 10-30 به 5-10
            elif random.random() < 0.20:  # 20% توقف متوسط
                variation = random.uniform(3, 6)  # کاهش از 4-10 به 3-6
            else:
                variation = random.uniform(1.2, 2.5)  # کاهش از 3.0 به 2.5
        else:  # confident
            if random.random() < 0.03:  # کاهش از 5% به 3%
                variation = random.uniform(3, 6)  # کاهش از 6-15 به 3-6
            elif random.random() < 0.30:  # 30% تایپ سریع
                variation = random.uniform(0.3, 0.8)
            else:
                variation = random.uniform(0.7, 1.8)
        
        # عامل خستگی دست (بیشتر از قبل)
        finger_fatigue = 1 + (self.session_actions * 0.0003)
        
        # الگوی ریتمیک بر اساس الگوی قبلی
        if self.last_delay_pattern == 'fast':
            rhythm_factor = random.uniform(0.8, 1.2)  # ادامه ریتم سریع
            if random.random() < 0.7:
                self.last_delay_pattern = 'fast'
            else:
                self.last_delay_pattern = 'normal'
        elif self.last_delay_pattern == 'slow':
            rhythm_factor = random.uniform(1.2, 1.8)  # ادامه ریتم آهسته
            if random.random() < 0.6:
                self.last_delay_pattern = 'slow'
            else:
                self.last_delay_pattern = 'normal'
        else:  # normal
            rhythm_factor = random.uniform(0.9, 1.3)
            # تغییر الگو
            rand = random.random()
            if rand < 0.1:
                self.last_delay_pattern = 'fast'
            elif rand < 0.2:
                self.last_delay_pattern = 'slow'
        
        final_delay = base_delay * variation * finger_fatigue * rhythm_factor
        
        # محدود کردن به بازه منطقی
        return max(0.01, min(final_delay, 5.0))
    
    def _get_adjacent_key(self, char: str) -> str:
        """دریافت کلید مجاور برای شبیه‌سازی خطای تایپ"""
        keyboard_layout = {
            'a': ['s', 'q', 'w'],
            's': ['a', 'd', 'w', 'e'],
            'd': ['s', 'f', 'e', 'r'],
            'f': ['d', 'g', 'r', 't'],
            'g': ['f', 'h', 't', 'y'],
            'h': ['g', 'j', 'y', 'u'],
            'j': ['h', 'k', 'u', 'i'],
            'k': ['j', 'l', 'i', 'o'],
            'l': ['k', 'o', 'p'],
            'q': ['w', 'a'],
            'w': ['q', 'e', 'a', 's'],
            'e': ['w', 'r', 's', 'd'],
            'r': ['e', 't', 'd', 'f'],
            't': ['r', 'y', 'f', 'g'],
            'y': ['t', 'u', 'g', 'h'],
            'u': ['y', 'i', 'h', 'j'],
            'i': ['u', 'o', 'j', 'k'],
            'o': ['i', 'p', 'k', 'l'],
            'p': ['o', 'l']
        }
        
        adjacent_keys = keyboard_layout.get(char.lower(), [char])
        return random.choice(adjacent_keys) if adjacent_keys else char
    
    def human_click_element(self, element) -> None:
        """کلیک انسان‌گونه روی عنصر با حرکت طبیعی ماوس و شبیه‌سازی اشتباهات"""
        try:
            # بررسی وجود page
            if not self.page or self.page.is_closed():
                self.logger.error("صفحه در دسترس نیست")
                return
            
            # انتظار برای نمایش عنصر با timeout
            element.wait_for(state='visible', timeout=10000)
            
            # بررسی اینکه عنصر قابل کلیک است
            if not element.is_enabled():
                self.logger.warning("عنصر غیرفعال است")
                return
            
            # دریافت مختصات عنصر
            box = element.bounding_box()
            if not box:
                self.logger.error("نمی‌توان مختصات عنصر را دریافت کرد")
                return
            
            # تصمیم‌گیری برای نوع کلیک
            click_success = self._attempt_click_with_mistakes(box)
            
            if not click_success:
                # تلاش مجدد با دقت بیشتر
                self.human_delay(0.5, 1.0, "thinking")
                self._click_precisely(box)
            
            # تاخیر پس از کلیک
            self.human_delay(0.3, 1.0, "clicking")
            
        except Exception as e:
            self.logger.error(f"خطا در human_click_element: {e}")
            # fallback: کلیک ساده
            try:
                if element and self.page and not self.page.is_closed():
                    element.click(timeout=5000)
                    self.human_delay(0.5, 1.0, "clicking")
            except Exception as fallback_error:
                self.logger.error(f"خطا در fallback click: {fallback_error}")
    
    def _attempt_click_with_mistakes(self, box: dict) -> bool:
        """تلاش برای کلیک با احتمال اشتباه"""
        # محاسبه نقطه کلیک بر اساس پروفایل کاربر
        if self.user_behavior_profile == 'careful':
            precision = random.uniform(0.85, 0.95)
        elif self.user_behavior_profile == 'quick':
            precision = random.uniform(0.6, 0.8)
        elif self.user_behavior_profile == 'hesitant':
            precision = random.uniform(0.7, 0.9)
        else:  # confident
            precision = random.uniform(0.75, 0.9)
        
        # احتمال اشتباه کلیک
        if random.random() < self.mistake_probability:
            return self._click_with_mistake(box)
        else:
            return self._click_precisely(box)
    
    def _click_with_mistake(self, box: dict) -> bool:
        """کلیک اشتباه و تصحیح آن"""
        # کلیک در نقطه اشتباه (خارج از عنصر یا لبه)
        mistake_type = random.choice(['outside', 'edge', 'corner'])
        
        if mistake_type == 'outside':
            # کلیک خارج از عنصر
            offset_x = random.uniform(-30, 30)
            offset_y = random.uniform(-30, 30)
            click_x = box['x'] + box['width']/2 + offset_x
            click_y = box['y'] + box['height']/2 + offset_y
        elif mistake_type == 'edge':
            # کلیک روی لبه
            if random.random() < 0.5:
                click_x = box['x'] + random.uniform(-5, 5)
                click_y = box['y'] + box['height']/2
            else:
                click_x = box['x'] + box['width']/2
                click_y = box['y'] + random.uniform(-5, 5)
        else:  # corner
            # کلیک روی گوشه
            click_x = box['x'] + random.uniform(-5, 5)
            click_y = box['y'] + random.uniform(-5, 5)
        
        # حرکت و کلیک اشتباه
        self._move_mouse_naturally(click_x, click_y)
        self.page.mouse.click(click_x, click_y)
        
        # تشخیص اشتباه و واکنش
        self.human_delay(0.3, 0.8, "thinking")
        
        return False  # کلیک ناموفق
    
    def _click_precisely(self, box: dict) -> bool:
        """کلیک دقیق روی عنصر"""
        # محاسبه نقطه کلیک با دقت بالا
        margin_ratio = 0.2  # 20% حاشیه از هر طرف
        
        click_x = box['x'] + box['width'] * random.uniform(margin_ratio, 1 - margin_ratio)
        click_y = box['y'] + box['height'] * random.uniform(margin_ratio, 1 - margin_ratio)
        
        # حرکت ماوس به صورت طبیعی
        self._move_mouse_naturally(click_x, click_y)
        
        # کلیک
        self.page.mouse.click(click_x, click_y)
        
        return True  # کلیک موفق
    
    def human_click(self, selector: str, offset_randomization: bool = True):
        """کلیک انسان‌گونه با حرکت ماوس"""
        element = self.page.locator(selector)
        
        # انتظار برای نمایش عنصر
        element.wait_for(state='visible')
        
        # دریافت مختصات عنصر
        box = element.bounding_box()
        if not box:
            raise Exception(f"عنصر {selector} یافت نشد")
        
        # محاسبه نقطه کلیک
        if offset_randomization:
            # کلیک در نقطه تصادفی داخل عنصر
            click_x = box['x'] + random.uniform(box['width'] * 0.2, box['width'] * 0.8)
            click_y = box['y'] + random.uniform(box['height'] * 0.2, box['height'] * 0.8)
        else:
            # کلیک در مرکز
            click_x = box['x'] + box['width'] / 2
            click_y = box['y'] + box['height'] / 2
        
        # حرکت ماوس به صورت طبیعی
        self._move_mouse_naturally(click_x, click_y)
        
        # کلیک
        self.page.mouse.click(click_x, click_y)
        
        # تاخیر پس از کلیک
        self.human_delay(0.5, 1.5)
    
    def _move_mouse_naturally(self, target_x: float, target_y: float):
        """حرکت طبیعی ماوس با منحنی بزیه و حافظه موقعیت"""
        try:
            # بررسی وجود page
            if not self.page or self.page.is_closed():
                self.logger.error("صفحه در دسترس نیست")
                return
            
            # استفاده از موقعیت فعلی ذخیره شده
            current_x = self.current_mouse_x
            current_y = self.current_mouse_y
            
            # محاسبه فاصله برای تعیین پیچیدگی مسیر
            distance = math.sqrt((target_x - current_x)**2 + (target_y - current_y)**2)
            
            # تولید نقاط کنترل برای منحنی بزیه بر اساس فاصله
            if distance < 50:  # حرکت کوتاه - مسیر ساده
                control_x1 = current_x + random.uniform(-20, 20)
                control_y1 = current_y + random.uniform(-20, 20)
                control_x2 = target_x + random.uniform(-10, 10)
                control_y2 = target_y + random.uniform(-10, 10)
                steps = random.randint(5, 10)
            elif distance < 200:  # حرکت متوسط
                control_x1 = current_x + random.uniform(-80, 80)
                control_y1 = current_y + random.uniform(-80, 80)
                control_x2 = target_x + random.uniform(-40, 40)
                control_y2 = target_y + random.uniform(-40, 40)
                steps = random.randint(10, 20)
            else:  # حرکت طولانی - مسیر پیچیده
                control_x1 = current_x + random.uniform(-150, 150)
                control_y1 = current_y + random.uniform(-150, 150)
                control_x2 = target_x + random.uniform(-80, 80)
                control_y2 = target_y + random.uniform(-80, 80)
                steps = random.randint(15, 30)
            
            # حرکت در طول منحنی
            for i in range(steps + 1):
                try:
                    t = i / steps
                    
                    # محاسبه نقطه روی منحنی بزیه
                    x = self._bezier_point(t, current_x, control_x1, control_x2, target_x)
                    y = self._bezier_point(t, current_y, control_y1, control_y2, target_y)
                    
                    # حرکت ماوس
                    self.page.mouse.move(x, y)
                    
                    # تاخیر متغیر بر اساس سرعت حرکت (کاهش یافته)
                    if distance > 300:  # حرکت طولانی - آهسته‌تر
                        time.sleep(random.uniform(0.01, 0.03))  # کاهش از 0.02-0.05
                    else:
                        time.sleep(random.uniform(0.005, 0.02))  # کاهش از 0.01-0.03
                        
                except Exception as step_error:
                    self.logger.warning(f"خطا در مرحله {i} حرکت ماوس: {step_error}")
                    continue
            
            # به‌روزرسانی موقعیت فعلی
            self.current_mouse_x = target_x
            self.current_mouse_y = target_y
            
        except Exception as e:
            self.logger.error(f"خطا در _move_mouse_naturally: {e}")
            # fallback: به‌روزرسانی موقعیت حداقل
            self.current_mouse_x = target_x
            self.current_mouse_y = target_y
    
    def _bezier_point(self, t: float, p0: float, p1: float, p2: float, p3: float) -> float:
        """محاسبه نقطه روی منحنی بزیه مکعبی"""
        return (1-t)**3 * p0 + 3*(1-t)**2 * t * p1 + 3*(1-t) * t**2 * p2 + t**3 * p3
    
    def scroll_naturally(self, direction: str = 'down', amount: int = 3):
        """اسکرول طبیعی صفحه با الگوهای متنوع"""
        try:
            # بررسی وجود page
            if not self.page or self.page.is_closed():
                self.logger.error("صفحه در دسترس نیست")
                return
            
            for i in range(amount):
                try:
                    # تعیین مقدار اسکرول بر اساس الگوهای مختلف
                    scroll_amount = self._get_scroll_amount(i, amount)
                    
                    if direction == 'down':
                        self.page.mouse.wheel(0, scroll_amount)
                    else:
                        self.page.mouse.wheel(0, -scroll_amount)
                    
                    # تاخیر متغیر بر اساس پروفایل کاربر
                    delay = self._get_scroll_delay(i, amount)
                    self.human_delay(delay[0], delay[1])
                    
                except Exception as scroll_error:
                    self.logger.warning(f"خطا در اسکرول {i+1}: {scroll_error}")
                    # ادامه به اسکرول بعدی
                    continue
                    
        except Exception as e:
            self.logger.error(f"خطا در scroll_naturally: {e}")
    
    def _get_scroll_amount(self, current_scroll: int, total_scrolls: int) -> int:
        """محاسبه مقدار اسکرول بر اساس الگوهای مختلف"""
        # الگوهای مختلف اسکرول
        if random.random() < 0.1:  # 10% اسکرول خیلی کم
            return random.randint(30, 80)
        elif random.random() < 0.15:  # 15% اسکرول زیاد
            return random.randint(400, 800)
        elif random.random() < 0.2:  # 20% اسکرول خیلی زیاد
            return random.randint(600, 1200)
        elif self.user_behavior_profile == 'quick':  # کاربر سریع
            return random.randint(200, 500)
        elif self.user_behavior_profile == 'careful':  # کاربر دقیق
            return random.randint(80, 200)
        else:  # عادی
            return random.randint(120, 350)
    
    def _get_scroll_delay(self, current_scroll: int, total_scrolls: int) -> tuple:
        """محاسبه تاخیر اسکرول بر اساس الگو"""
        if self.user_behavior_profile == 'quick':
            return (0.2, 0.8)
        elif self.user_behavior_profile == 'careful':
            return (1.0, 2.5)
        elif self.user_behavior_profile == 'hesitant':
            return (0.8, 2.0)
        else:  # confident
            return (0.4, 1.2)
    
    def random_mouse_movement(self):
        """حرکت تصادفی ماوس (شبیه‌سازی بررسی صفحه) با حافظه موقعیت"""
        try:
            # بررسی وجود page
            if not self.page or self.page.is_closed():
                self.logger.error("صفحه در دسترس نیست")
                return
            
            movements = random.randint(2, 5)
            
            for i in range(movements):
                try:
                    # تعیین نقطه هدف بر اساس موقعیت فعلی
                    if i == 0:  # حرکت اول - ممکن است دورتر باشد
                        max_distance = random.uniform(200, 400)
                    else:  # حرکات بعدی - نزدیک‌تر
                        max_distance = random.uniform(100, 250)
                    
                    # محاسبه نقطه هدف
                    angle = random.uniform(0, 2 * math.pi)
                    distance = random.uniform(50, max_distance)
                    
                    target_x = self.current_mouse_x + distance * math.cos(angle)
                    target_y = self.current_mouse_y + distance * math.sin(angle)
                    
                    # محدود کردن به مرزهای صفحه
                    target_x = max(50, min(target_x, 1200))
                    target_y = max(50, min(target_y, 700))
                    
                    # حرکت طبیعی
                    self._move_mouse_naturally(target_x, target_y)
                    
                    # تاخیر بر اساس پروفایل کاربر
                    if self.user_behavior_profile == 'quick':
                        self.human_delay(0.3, 1.0)
                    elif self.user_behavior_profile == 'careful':
                        self.human_delay(1.0, 2.0)  # کاهش از 3.0 به 2.0
                    else:
                        self.human_delay(0.5, 1.5)  # کاهش از 2.0 به 1.5
                        
                except Exception as move_error:
                    self.logger.warning(f"خطا در حرکت ماوس {i+1}: {move_error}")
                    continue
                    
        except Exception as e:
            self.logger.error(f"خطا در random_mouse_movement: {e}")
    
    def simulate_reading_pause(self):
        """شبیه‌سازی مکث برای خواندن"""
        reading_time = random.uniform(3.0, 8.0)
        time.sleep(reading_time)
    
    def visit_decoy_pages(self, base_url: str):
        """بازدید از صفحات انحرافی"""
        decoy_pages = [
            '/privacy-policy',
            '/terms-conditions',
            '/contact',
            '/help',
            '/faq'
        ]
        
        if random.random() < 0.3:  # 30% احتمال بازدید انحرافی
            decoy_page = random.choice(decoy_pages)
            try:
                self.page.goto(f"{base_url}{decoy_page}")
                self.simulate_reading_pause()
                self.scroll_naturally()
                self.human_delay(2.0, 5.0)
            except:
                pass  # اگر صفحه وجود نداشت، ادامه بده
    
    def simulate_human_form_interaction(self):
        """شبیه‌سازی رفتار انسانی پیشرفته قبل از پر کردن فرم"""
        try:
            # مرحله 1: بررسی اولیه صفحه
            self.random_mouse_movement()
            self.human_delay(1, 3, "thinking")
            
            # مرحله 2: اسکرول اکتشافی
            scroll_pattern = random.choice(['thorough', 'quick', 'hesitant'])
            
            if scroll_pattern == 'thorough':
                # بررسی دقیق صفحه
                self.scroll_naturally('down', random.randint(3, 5))
                self.human_delay(2, 4, "reading")
                self.scroll_naturally('up', random.randint(2, 3))
                self.human_delay(1, 2, "reading")
                self.scroll_naturally('down', 1)
            elif scroll_pattern == 'quick':
                # نگاه سریع
                self.scroll_naturally('down', 2)
                self.human_delay(0.5, 1, "reading")
                self.scroll_naturally('up', 1)
            else:  # hesitant
                # تردید و بررسی مجدد
                self.scroll_naturally('down', 1)
                self.human_delay(1, 2, "hesitation")
                self.scroll_naturally('up', 1)
                self.human_delay(0.5, 1, "thinking")
                self.scroll_naturally('down', 2)
            
            # مرحله 3: شبیه‌سازی خواندن متن
            reading_time = random.uniform(2, 6)
            if random.random() < 0.3:  # 30% احتمال خواندن دوباره
                reading_time *= 1.5
            self.human_delay(reading_time, reading_time + 1, "reading")
            
            # مرحله 4: حرکت ماوس اکتشافی
            exploration_moves = random.randint(2, 4)
            for _ in range(exploration_moves):
                self.random_mouse_movement()
                self.human_delay(0.3, 1, "thinking")
            
            # مرحله 5: تمرکز روی فرم
            if random.random() < 0.4:  # 40% احتمال تردید نهایی
                self.human_delay(1, 3, "hesitation")
            
            self.human_delay(0.5, 1.5, "thinking")
            
            self.logger.debug(f"✅ رفتار انسانی پیشرفته شبیه‌سازی شد (الگو: {scroll_pattern})")
            
        except Exception as e:
            self.logger.warning(f"⚠️ خطا در شبیه‌سازی رفتار انسانی: {e}")
    
    def simulate_captcha_thinking(self):
        """شبیه‌سازی فکر کردن قبل از حل کپچا"""
        try:
            # توقف برای نگاه کردن به کپچا
            self.human_delay(2, 4, "thinking")
            
            # حرکت ماوس روی کپچا
            self.random_mouse_movement()
            self.human_delay(1, 2, "reading")
            
            # توقف اضافی برای تفکر
            self.human_delay(1.5, 3, "thinking")
            
            self.logger.debug("✅ رفتار فکر کردن برای کپچا شبیه‌سازی شد")
            
        except Exception as e:
            self.logger.warning(f"⚠️ خطا در شبیه‌سازی فکر کپچا: {e}")