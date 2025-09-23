# browser/viewport_manager.py
import random
from typing import Dict, List

class ViewportManager:
    """مدیریت اندازه‌های viewport مرورگر"""
    
    def __init__(self):
        self.viewport_sizes = self._get_viewport_sizes()
    
    def _get_viewport_sizes(self) -> List[Dict[str, int]]:
        """دریافت اندازه‌های مختلف viewport واقعی و متداول - بهینه شده برای مانیتورهای معمولی"""
        return [
            {'width': 1366, 'height': 768},   # HD - بسیار رایج در لپ‌تاپ‌ها
            {'width': 1280, 'height': 720},   # HD Ready - مناسب برای مانیتورهای کوچک
            {'width': 1440, 'height': 900},   # WXGA+ - رایج در مک‌ها
            {'width': 1536, 'height': 864},   # HD+ - رایج در لپ‌تاپ‌ها
            {'width': 1600, 'height': 900},   # HD+ Wide - مناسب
            {'width': 1680, 'height': 1050},  # WSXGA+ - مانیتورهای متوسط
            {'width': 1920, 'height': 1080}   # Full HD - فقط برای مانیتورهای بزرگ
        ]
    
    def get_random_viewport(self) -> Dict[str, int]:
        """انتخاب تصادفی viewport با اولویت اندازه‌های کوچک‌تر"""
        # اولویت بیشتر به اندازه‌های کوچک‌تر و متوسط
        weights = [3, 3, 2, 2, 1, 1, 1]  # وزن بیشتر برای اندازه‌های کوچک‌تر
        return random.choices(self.viewport_sizes, weights=weights)[0]
    
    def get_viewport_by_resolution(self, target_width: int) -> Dict[str, int]:
        """انتخاب viewport بر اساس عرض مورد نظر"""
        # پیدا کردن نزدیک‌ترین اندازه
        closest_viewport = min(
            self.viewport_sizes,
            key=lambda v: abs(v['width'] - target_width)
        )
        return closest_viewport
    
    def get_mobile_viewport(self) -> Dict[str, int]:
        """دریافت viewport موبایل"""
        mobile_viewports = [
            {'width': 375, 'height': 667},   # iPhone SE
            {'width': 414, 'height': 896},   # iPhone XR
            {'width': 390, 'height': 844},   # iPhone 12
            {'width': 360, 'height': 640},   # Android
        ]
        return random.choice(mobile_viewports)
    
    def get_tablet_viewport(self) -> Dict[str, int]:
        """دریافت viewport تبلت"""
        tablet_viewports = [
            {'width': 768, 'height': 1024},  # iPad
            {'width': 1024, 'height': 768},  # iPad Landscape
            {'width': 800, 'height': 1280},  # Android Tablet
        ]
        return random.choice(tablet_viewports)
    
    def get_desktop_viewport(self) -> Dict[str, int]:
        """دریافت viewport دسکتاپ - اندازه‌های مناسب برای مانیتورهای معمولی"""
        # فقط اندازه‌های مناسب برای دسکتاپ
        desktop_sizes = [
            {'width': 1366, 'height': 768},
            {'width': 1440, 'height': 900},
            {'width': 1536, 'height': 864},
            {'width': 1600, 'height': 900}
        ]
        return random.choice(desktop_sizes)
    
    def get_safe_viewport(self, max_width: int = 1600, max_height: int = 900) -> Dict[str, int]:
        """دریافت viewport امن که از حداکثر اندازه مشخص شده تجاوز نکند"""
        safe_sizes = [
            size for size in self.viewport_sizes 
            if size['width'] <= max_width and size['height'] <= max_height
        ]
        
        if not safe_sizes:
            # اگر هیچ اندازه امنی وجود نداشت، کوچک‌ترین اندازه را برگردان
            return {'width': 1280, 'height': 720}
        
        # اولویت به اندازه‌های کوچک‌تر
        weights = [3] * min(3, len(safe_sizes)) + [1] * max(0, len(safe_sizes) - 3)
        return random.choices(safe_sizes, weights=weights)[0]
    
    def get_optimal_viewport(self) -> Dict[str, int]:
        """دریافت viewport بهینه برای اکثر مانیتورها"""
        # اندازه‌های بهینه که در اکثر مانیتورها مشکلی ندارند
        optimal_sizes = [
            {'width': 1366, 'height': 768},   # رایج‌ترین
            {'width': 1280, 'height': 720},   # امن‌ترین
            {'width': 1440, 'height': 900},   # متوسط
            {'width': 1536, 'height': 864}    # لپ‌تاپ‌های جدید
        ]
        return random.choice(optimal_sizes)
    
    def is_mobile_size(self, viewport: Dict[str, int]) -> bool:
        """بررسی اینکه آیا viewport مربوط به موبایل است"""
        return viewport['width'] < 500
    
    def is_tablet_size(self, viewport: Dict[str, int]) -> bool:
        """بررسی اینکه آیا viewport مربوط به تبلت است"""
        return 500 <= viewport['width'] < 900
    
    def is_desktop_size(self, viewport: Dict[str, int]) -> bool:
        """بررسی اینکه آیا viewport مربوط به دسکتاپ است"""
        return viewport['width'] >= 900
    
    def get_aspect_ratio(self, viewport: Dict[str, int]) -> float:
        """محاسبه نسبت ابعاد"""
        return viewport['width'] / viewport['height']
    
    def scale_viewport(self, viewport: Dict[str, int], scale_factor: float) -> Dict[str, int]:
        """تغییر اندازه viewport با ضریب مشخص"""
        return {
            'width': int(viewport['width'] * scale_factor),
            'height': int(viewport['height'] * scale_factor)
        }
    
    def get_viewport_info(self, viewport: Dict[str, int]) -> Dict[str, any]:
        """دریافت اطلاعات کامل viewport"""
        return {
            'width': viewport['width'],
            'height': viewport['height'],
            'aspect_ratio': self.get_aspect_ratio(viewport),
            'device_type': self._get_device_type(viewport),
            'total_pixels': viewport['width'] * viewport['height']
        }
    
    def _get_device_type(self, viewport: Dict[str, int]) -> str:
        """تشخیص نوع دستگاه بر اساس viewport"""
        if self.is_mobile_size(viewport):
            return 'mobile'
        elif self.is_tablet_size(viewport):
            return 'tablet'
        else:
            return 'desktop'