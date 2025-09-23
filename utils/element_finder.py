# utils/element_finder.py
import time
from typing import Optional, List, Union
from playwright.sync_api import Locator, ElementHandle

class ElementFinder:
    """ابزار یافتن و تعامل با المان‌های صفحه"""
    
    def __init__(self, page, logger):
        self.page = page
        self.logger = logger
        
        # تنظیمات پیش‌فرض
        self.default_timeout = 5000
        self.retry_count = 3
        self.retry_delay = 1
    
    def find_element(self, selector: str, timeout: int = None) -> Optional[Locator]:
        """یافتن المان با selector"""
        timeout = timeout or self.default_timeout
        
        try:
            self.page.wait_for_selector(selector, timeout=timeout)
            return self.page.locator(selector).first
        except Exception as e:
            self.logger.debug(f"المان یافت نشد: {selector} - {e}")
            return None
    
    def find_elements(self, selector: str, timeout: int = None) -> List[Locator]:
        """یافتن تمام المان‌های مطابق با selector"""
        timeout = timeout or self.default_timeout
        
        try:
            self.page.wait_for_selector(selector, timeout=timeout)
            locator = self.page.locator(selector)
            count = locator.count()
            return [locator.nth(i) for i in range(count)]
        except Exception as e:
            self.logger.debug(f"المان‌ها یافت نشدند: {selector} - {e}")
            return []
    
    def find_by_text(self, text: str, tag: str = None, exact: bool = False) -> Optional[Locator]:
        """یافتن المان بر اساس متن"""
        try:
            if tag:
                if exact:
                    selector = f'{tag}:has-text("{text}")'  # متن دقیق
                else:
                    selector = f'{tag}:text-matches("{text}", "i")'  # شامل متن
            else:
                if exact:
                    selector = f':has-text("{text}")'  # متن دقیق
                else:
                    selector = f':text-matches("{text}", "i")'  # شامل متن
            
            return self.find_element(selector)
        except Exception as e:
            self.logger.debug(f"المان با متن یافت نشد: {text} - {e}")
            return None
    
    def find_by_attribute(self, attribute: str, value: str, tag: str = None) -> Optional[Locator]:
        """یافتن المان بر اساس attribute"""
        try:
            if tag:
                selector = f'{tag}[{attribute}="{value}"]'
            else:
                selector = f'[{attribute}="{value}"]'
            
            return self.find_element(selector)
        except Exception as e:
            self.logger.debug(f"المان با attribute یافت نشد: {attribute}={value} - {e}")
            return None
    
    def find_input_by_name(self, name: str) -> Optional[Locator]:
        """یافتن input بر اساس name"""
        return self.find_by_attribute('name', name, 'input')
    
    def find_input_by_placeholder(self, placeholder: str, exact: bool = False) -> Optional[Locator]:
        """یافتن input بر اساس placeholder"""
        try:
            if exact:
                selector = f'input[placeholder="{placeholder}"]'
            else:
                selector = f'input[placeholder*="{placeholder}"]'
            
            return self.find_element(selector)
        except Exception as e:
            self.logger.debug(f"Input با placeholder یافت نشد: {placeholder} - {e}")
            return None
    
    def find_button_by_text(self, text: str, exact: bool = False) -> Optional[Locator]:
        """یافتن دکمه بر اساس متن"""
        return self.find_by_text(text, 'button', exact)
    
    def find_link_by_text(self, text: str, exact: bool = False) -> Optional[Locator]:
        """یافتن لینک بر اساس متن"""
        return self.find_by_text(text, 'a', exact)
    
    def find_with_multiple_selectors(self, selectors: List[str], timeout: int = None) -> Optional[Locator]:
        """یافتن المان با چندین selector (اولین یافته شده)"""
        timeout = timeout or self.default_timeout
        
        for selector in selectors:
            element = self.find_element(selector, timeout=1000)  # timeout کوتاه برای هر selector
            if element and element.count() > 0:
                self.logger.debug(f"المان یافت شد با selector: {selector}")
                return element
        
        self.logger.debug(f"هیچ المانی با selector های داده شده یافت نشد: {selectors}")
        return None
    
    def wait_for_element(self, selector: str, timeout: int = None, state: str = 'visible') -> bool:
        """انتظار برای نمایش المان"""
        timeout = timeout or self.default_timeout
        
        try:
            self.page.wait_for_selector(selector, timeout=timeout, state=state)
            return True
        except Exception as e:
            self.logger.debug(f"انتظار برای المان ناموفق: {selector} - {e}")
            return False
    
    def is_element_visible(self, selector: str) -> bool:
        """بررسی نمایان بودن المان"""
        try:
            element = self.page.locator(selector).first
            return element.count() > 0 and element.is_visible()
        except Exception:
            return False
    
    def is_element_enabled(self, selector: str) -> bool:
        """بررسی فعال بودن المان"""
        try:
            element = self.page.locator(selector).first
            return element.count() > 0 and element.is_enabled()
        except Exception:
            return False
    
    def click_element(self, element: Locator, force: bool = False) -> bool:
        """کلیک روی المان"""
        try:
            if element and element.count() > 0:
                element.click(force=force)
                return True
            return False
        except Exception as e:
            self.logger.debug(f"خطا در کلیک: {e}")
            return False
    
    def click_if_exists(self, selector: str, timeout: int = None, force: bool = False) -> bool:
        """کلیک روی المان در صورت وجود"""
        element = self.find_element(selector, timeout)
        if element and element.is_visible():
            return self.click_element(element, force)
        return False
    
    def fill_input(self, selector: str, value: str, clear_first: bool = True) -> bool:
        """پر کردن فیلد input"""
        try:
            element = self.find_element(selector)
            if element and element.count() > 0:
                if clear_first:
                    element.fill('')  # پاک کردن محتوای قبلی
                    time.sleep(0.1)
                
                element.fill(value)
                return True
            return False
        except Exception as e:
            self.logger.debug(f"خطا در پر کردن فیلد: {e}")
            return False
    
    def type_text(self, selector: str, text: str, delay: int = 50) -> bool:
        """تایپ کردن متن با تاخیر (شبیه‌سازی انسانی)"""
        try:
            element = self.find_element(selector)
            if element and element.count() > 0:
                element.type(text, delay=delay)
                return True
            return False
        except Exception as e:
            self.logger.debug(f"خطا در تایپ: {e}")
            return False
    
    def get_text(self, selector: str) -> Optional[str]:
        """دریافت متن المان"""
        try:
            element = self.find_element(selector)
            if element and element.count() > 0:
                return element.text_content()
            return None
        except Exception as e:
            self.logger.debug(f"خطا در دریافت متن: {e}")
            return None
    
    def get_attribute(self, selector: str, attribute: str) -> Optional[str]:
        """دریافت مقدار attribute"""
        try:
            element = self.find_element(selector)
            if element and element.count() > 0:
                return element.get_attribute(attribute)
            return None
        except Exception as e:
            self.logger.debug(f"خطا در دریافت attribute: {e}")
            return None
    
    def scroll_to_element(self, selector: str) -> bool:
        """اسکرول به المان"""
        try:
            element = self.find_element(selector)
            if element and element.count() > 0:
                element.scroll_into_view_if_needed()
                return True
            return False
        except Exception as e:
            self.logger.debug(f"خطا در اسکرول: {e}")
            return False
    
    def hover_element(self, selector: str) -> bool:
        """hover روی المان"""
        try:
            element = self.find_element(selector)
            if element and element.count() > 0:
                element.hover()
                return True
            return False
        except Exception as e:
            self.logger.debug(f"خطا در hover: {e}")
            return False
    
    def select_option(self, selector: str, value: str = None, label: str = None, index: int = None) -> bool:
        """انتخاب گزینه از select"""
        try:
            element = self.find_element(selector)
            if element and element.count() > 0:
                if value:
                    element.select_option(value=value)
                elif label:
                    element.select_option(label=label)
                elif index is not None:
                    element.select_option(index=index)
                return True
            return False
        except Exception as e:
            self.logger.debug(f"خطا در انتخاب گزینه: {e}")
            return False