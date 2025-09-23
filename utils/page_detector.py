# utils/page_detector.py
import re
from typing import Dict, List, Optional
from urllib.parse import urlparse

class PageDetector:
    """تشخیص نوع صفحات و وضعیت کاربر"""
    
    def __init__(self, page, logger):
        self.page = page
        self.logger = logger
        
        # الگوهای تشخیص صفحات
        self.page_patterns = {
            'login': {
                'url_patterns': ['/login', '/signin', '/auth'],
                'element_selectors': [
                    'input[type="password"]',
                    'input[name="password"]',
                    'form[action*="login"]',
                    '.login-form',
                    '#login-form'
                ],
                'text_patterns': ['login', 'entrar', 'sign in', 'autenticação']
            },
            'dashboard': {
                'url_patterns': ['/dashboard', '/home', '/main'],
                'element_selectors': [
                    '.dashboard',
                    '#dashboard',
                    '.user-menu',
                    '.logout',
                    '.profile'
                ],
                'text_patterns': ['dashboard', 'painel', 'bem-vindo']
            },

            'error': {
                'url_patterns': ['/error', '/404', '/500'],
                'element_selectors': [
                    '.error',
                    '#error',
                    '.error-message',
                    '.alert-danger'
                ],
                'text_patterns': ['error', 'erro', 'not found', 'server error']
            },
            'captcha': {
                'element_selectors': [
                    '.captcha',
                    '#captcha',
                    '.recaptcha',
                    '.hcaptcha',
                    'iframe[src*="recaptcha"]',
                    'iframe[src*="hcaptcha"]'
                ],
                'text_patterns': ['captcha', 'verification', 'verificação']
            }
        }
    
    def detect_current_page(self) -> str:
        """تشخیص نوع صفحه فعلی"""
        try:
            current_url = self.page.url
            page_title = self.page.title()
            page_content = self.page.content()
            
            self.logger.debug(f"تشخیص صفحه: URL={current_url}, Title={page_title}")
            
            # بررسی هر نوع صفحه
            for page_type, patterns in self.page_patterns.items():
                score = self._calculate_page_score(current_url, page_title, page_content, patterns)
                
                if score > 0.5:  # آستانه تشخیص
                    self.logger.debug(f"صفحه تشخیص داده شد: {page_type} (امتیاز: {score:.2f})")
                    return page_type
            
            return 'unknown'
            
        except Exception as e:
            self.logger.error(f"خطا در تشخیص صفحه: {e}")
            return 'unknown'
    
    def _calculate_page_score(self, url: str, title: str, content: str, patterns: Dict) -> float:
        """محاسبه امتیاز تطبیق صفحه"""
        score = 0.0
        total_checks = 0
        
        # بررسی URL
        if 'url_patterns' in patterns:
            total_checks += 1
            for pattern in patterns['url_patterns']:
                if pattern.lower() in url.lower():
                    score += 0.4
                    break
        
        # بررسی المان‌ها
        if 'element_selectors' in patterns:
            total_checks += 1
            element_found = False
            for selector in patterns['element_selectors']:
                try:
                    if self.page.locator(selector).count() > 0:
                        element_found = True
                        break
                except:
                    continue
            
            if element_found:
                score += 0.4
        
        # بررسی متن
        if 'text_patterns' in patterns:
            total_checks += 1
            text_found = False
            combined_text = f"{title} {content}".lower()
            
            for pattern in patterns['text_patterns']:
                if pattern.lower() in combined_text:
                    text_found = True
                    break
            
            if text_found:
                score += 0.2
        
        return score / max(total_checks, 1) if total_checks > 0 else 0.0
    
    def is_login_page(self) -> bool:
        """بررسی اینکه آیا در صفحه ورود هستیم"""
        return self.detect_current_page() == 'login'
    
    def is_logged_in(self) -> bool:
        """بررسی وضعیت ورود کاربر"""
        try:
            current_url = self.page.url
            
            # بررسی URL
            logged_in_indicators = [
                '/dashboard', '/home', '/main',
                '/profile', '/account'
            ]
            
            for indicator in logged_in_indicators:
                if indicator in current_url.lower():
                    self.logger.debug(f"ورود تأیید شد از URL: {current_url}")
                    return True
            
            # بررسی المان‌های مشخص کننده ورود
            login_indicators = [
                '.user-menu',
                '.logout',
                '.profile-menu',
                'a[href*="logout"]',
                'button:has-text("Sair")',
                'button:has-text("Logout")',
                '.dashboard',
                '#dashboard'
            ]
            
            for selector in login_indicators:
                try:
                    if self.page.locator(selector).count() > 0:
                        self.logger.debug(f"ورود تأیید شد از المان: {selector}")
                        return True
                except:
                    continue
            
            # بررسی عدم وجود فرم ورود
            login_form_selectors = [
                'input[type="password"]',
                'input[name="password"]',
                'form[action*="login"]'
            ]
            
            has_login_form = False
            for selector in login_form_selectors:
                try:
                    if self.page.locator(selector).count() > 0:
                        has_login_form = True
                        break
                except:
                    continue
            
            if not has_login_form and 'login' not in current_url.lower():
                self.logger.debug("ورود تأیید شد: فرم ورود وجود ندارد")
                return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"خطا در بررسی وضعیت ورود: {e}")
            return False
    
    def is_error_page(self) -> bool:
        """بررسی اینکه آیا در صفحه خطا هستیم"""
        return self.detect_current_page() == 'error'
    
    def has_captcha(self) -> bool:
        """بررسی وجود کپچا در صفحه"""
        return self.detect_current_page() == 'captcha' or self._check_captcha_elements()
    
    def _check_captcha_elements(self) -> bool:
        """بررسی وجود المان‌های کپچا"""
        captcha_selectors = [
            '.captcha',
            '#captcha',
            '.recaptcha',
            '.hcaptcha',
            'iframe[src*="recaptcha"]',
            'iframe[src*="hcaptcha"]',
            '[data-sitekey]',
            '.g-recaptcha'
        ]
        
        for selector in captcha_selectors:
            try:
                if self.page.locator(selector).count() > 0:
                    return True
            except:
                continue
        
        return False
    
    def get_page_info(self) -> Dict[str, any]:
        """دریافت اطلاعات کامل صفحه"""
        try:
            return {
                'url': self.page.url,
                'title': self.page.title(),
                'page_type': self.detect_current_page(),
                'is_logged_in': self.is_logged_in(),
                'has_captcha': self.has_captcha(),
                'is_error': self.is_error_page(),
                'viewport': self.page.viewport_size,
                'user_agent': self.page.evaluate('navigator.userAgent')
            }
        except Exception as e:
            self.logger.error(f"خطا در دریافت اطلاعات صفحه: {e}")
            return {}
    
    def wait_for_page_load(self, timeout: int = 30000) -> bool:
        """انتظار برای بارگذاری کامل صفحه"""
        try:
            # انتظار برای load state
            self.page.wait_for_load_state('networkidle', timeout=timeout)
            
            # انتظار برای document ready
            self.page.wait_for_function(
                "document.readyState === 'complete'",
                timeout=5000
            )
            
            return True
            
        except Exception as e:
            self.logger.warning(f"انتظار برای بارگذاری صفحه timeout شد: {e}")
            return False
    
    def check_for_redirects(self, expected_url_pattern: str = None) -> bool:
        """بررسی redirect های غیرمنتظره"""
        try:
            current_url = self.page.url
            
            if expected_url_pattern:
                if expected_url_pattern not in current_url:
                    self.logger.warning(f"Redirect غیرمنتظره: انتظار {expected_url_pattern}, دریافت {current_url}")
                    return True
            
            # بررسی redirect به صفحات خطا
            error_patterns = ['error', '404', '500', 'forbidden', 'unauthorized']
            for pattern in error_patterns:
                if pattern in current_url.lower():
                    self.logger.warning(f"Redirect به صفحه خطا: {current_url}")
                    return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"خطا در بررسی redirect: {e}")
            return False
    
    def extract_error_message(self) -> Optional[str]:
        """استخراج پیام خطا از صفحه"""
        try:
            error_selectors = [
                '.error-message',
                '.alert-danger',
                '.error',
                '#error',
                '.message.error',
                '.notification.error'
            ]
            
            for selector in error_selectors:
                try:
                    element = self.page.locator(selector).first
                    if element.count() > 0:
                        error_text = element.text_content()
                        if error_text and error_text.strip():
                            return error_text.strip()
                except:
                    continue
            
            return None
            
        except Exception as e:
            self.logger.error(f"خطا در استخراج پیام خطا: {e}")
            return None