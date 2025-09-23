# utils/error_handler.py
import traceback
import time
from datetime import datetime
from typing import Dict, List, Optional, Callable
from enum import Enum

class ErrorSeverity(Enum):
    """سطح شدت خطا"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class ErrorCategory(Enum):
    """دسته‌بندی خطاها"""
    NETWORK = "network"
    BROWSER = "browser"
    ELEMENT = "element"
    AUTHENTICATION = "authentication"
    CAPTCHA = "captcha"
    PROXY = "proxy"
    TIMEOUT = "timeout"
    UNKNOWN = "unknown"

class ErrorHandler:
    """مدیریت پیشرفته خطاها با قابلیت بازیابی خودکار"""
    
    def __init__(self, logger):
        self.logger = logger
        
        # آمار خطاها
        self.error_stats = {
            'total_errors': 0,
            'by_category': {},
            'by_severity': {},
            'recent_errors': []
        }
        
        # تنظیمات بازیابی
        self.retry_strategies = {
            ErrorCategory.NETWORK: {'max_retries': 3, 'delay': 5, 'backoff': 2},
            ErrorCategory.BROWSER: {'max_retries': 2, 'delay': 3, 'backoff': 1.5},
            ErrorCategory.ELEMENT: {'max_retries': 3, 'delay': 2, 'backoff': 1},
            ErrorCategory.TIMEOUT: {'max_retries': 2, 'delay': 10, 'backoff': 2},
            ErrorCategory.PROXY: {'max_retries': 1, 'delay': 15, 'backoff': 1}
        }
        
        # الگوهای تشخیص خطا
        self.error_patterns = {
            ErrorCategory.NETWORK: [
                'ERR_TUNNEL_CONNECTION_FAILED',
                'ERR_TIMED_OUT',
                'ERR_CONNECTION_REFUSED',
                'ERR_CONNECTION_CLOSED',
                'ERR_PROXY_CONNECTION_FAILED',
                'net::ERR_',
                'Connection refused',
                'Connection timeout',
                'connection was closed',
                'fechou a ligação',
                'ligação inesperadamente',
                'Connection closed'
            ],
            ErrorCategory.BROWSER: [
                'Browser has been closed',
                'Target page, context or browser has been closed',
                'Execution context was destroyed',
                'Protocol error'
            ],
            ErrorCategory.ELEMENT: [
                'Element not found',
                'No such element',
                'Element is not visible',
                'Element is not clickable',
                'Selector resolved to hidden'
            ],
            ErrorCategory.AUTHENTICATION: [
                'Invalid credentials',
                'Login failed',
                'Authentication error',
                'Unauthorized',
                'Access denied'
            ],
            ErrorCategory.CAPTCHA: [
                'Captcha required',
                'Captcha failed',
                'reCAPTCHA',
                'hCaptcha'
            ],
            ErrorCategory.PROXY: [
                'Proxy error',
                'Proxy authentication',
                'Proxy connection failed'
            ],
            ErrorCategory.TIMEOUT: [
                'Timeout',
                'TimeoutError',
                'Page.goto: Timeout',
                'waiting for selector'
            ]
        }
    
    def is_ip_blocked_error(self, error: Exception) -> bool:
        """تشخیص خطاهای مربوط به مسدود شدن IP"""
        error_msg = str(error).lower()
        
        blocked_indicators = [
            'err_connection_closed',
            'connection was closed',
            'fechou a ligação',
            'ligação inesperadamente',
            'connection closed unexpectedly',
            'net::err_connection_closed',
            'the connection was reset',
            'connection reset by peer'
        ]
        
        return any(indicator in error_msg for indicator in blocked_indicators)
    
    def handle_ip_blocked_error(self, context: str, error: Exception, proxy_manager=None) -> bool:
        """مدیریت خطاهای مسدود شدن IP"""
        try:
            self.logger.warning(f"🚫 تشخیص مسدود شدن IP در {context}: {error}")
            
            # ثبت خطا
            self._record_error(error, ErrorCategory.NETWORK, ErrorSeverity.HIGH, context)
            
            if proxy_manager:
                # تغییر فوری پروکسی
                if proxy_manager.force_proxy_rotation():
                    self.logger.info("✅ پروکسی با موفقیت تغییر کرد")
                    return True
                else:
                    self.logger.error("❌ شکست در تغییر پروکسی")
                    return False
            else:
                self.logger.warning("⚠️ proxy_manager در دسترس نیست")
                return False
                
        except Exception as e:
            self.logger.error(f"❌ خطا در مدیریت مسدود شدن IP: {e}")
            return False
    
    def handle_error(self, context: str, error: Exception, 
                    retry_function: Callable = None, *args, **kwargs) -> bool:
        """مدیریت خطا با امکان بازیابی خودکار"""
        try:
            # تحلیل خطا
            error_info = self._analyze_error(error)
            
            # ثبت خطا
            self._log_error(context, error, error_info)
            
            # به‌روزرسانی آمار
            self._update_stats(error_info)
            
            # تلاش برای بازیابی
            if retry_function and self._should_retry(error_info):
                return self._attempt_recovery(error_info, retry_function, *args, **kwargs)
            
            return False
            
        except Exception as e:
            self.logger.error(f"خطا در مدیریت خطا: {e}")
            return False
    
    def _analyze_error(self, error: Exception) -> Dict:
        """تحلیل و دسته‌بندی خطا"""
        error_str = str(error)
        error_type = type(error).__name__
        
        # تشخیص دسته خطا
        category = self._categorize_error(error_str)
        
        # تعیین شدت خطا
        severity = self._determine_severity(category, error_str)
        
        return {
            'message': error_str,
            'type': error_type,
            'category': category,
            'severity': severity,
            'timestamp': datetime.now(),
            'traceback': traceback.format_exc()
        }
    
    def _categorize_error(self, error_str: str) -> ErrorCategory:
        """دسته‌بندی خطا بر اساس پیام"""
        for category, patterns in self.error_patterns.items():
            for pattern in patterns:
                if pattern.lower() in error_str.lower():
                    return category
        
        return ErrorCategory.UNKNOWN
    
    def _determine_severity(self, category: ErrorCategory, error_str: str) -> ErrorSeverity:
        """تعیین شدت خطا"""
        # خطاهای بحرانی
        critical_patterns = [
            'Browser has been closed',
            'Execution context was destroyed',
            'Protocol error'
        ]
        
        for pattern in critical_patterns:
            if pattern.lower() in error_str.lower():
                return ErrorSeverity.CRITICAL
        
        # بر اساس دسته
        severity_map = {
            ErrorCategory.NETWORK: ErrorSeverity.MEDIUM,
            ErrorCategory.BROWSER: ErrorSeverity.HIGH,
            ErrorCategory.ELEMENT: ErrorSeverity.LOW,
            ErrorCategory.AUTHENTICATION: ErrorSeverity.HIGH,
            ErrorCategory.CAPTCHA: ErrorSeverity.MEDIUM,
            ErrorCategory.PROXY: ErrorSeverity.MEDIUM,
            ErrorCategory.TIMEOUT: ErrorSeverity.MEDIUM,
            ErrorCategory.UNKNOWN: ErrorSeverity.LOW
        }
        
        return severity_map.get(category, ErrorSeverity.LOW)
    
    def _log_error(self, context: str, error: Exception, error_info: Dict):
        """ثبت خطا در لاگ"""
        severity_emoji = {
            ErrorSeverity.LOW: "⚠️",
            ErrorSeverity.MEDIUM: "🔶",
            ErrorSeverity.HIGH: "🔴",
            ErrorSeverity.CRITICAL: "💥"
        }
        
        emoji = severity_emoji.get(error_info['severity'], "❌")
        
        log_message = (
            f"{emoji} خطا در {context}: "
            f"[{error_info['category'].value.upper()}] "
            f"{error_info['message']}"
        )
        
        # انتخاب سطح لاگ بر اساس شدت
        if error_info['severity'] == ErrorSeverity.CRITICAL:
            self.logger.critical(log_message)
        elif error_info['severity'] == ErrorSeverity.HIGH:
            self.logger.error(log_message)
        elif error_info['severity'] == ErrorSeverity.MEDIUM:
            self.logger.warning(log_message)
        else:
            self.logger.info(log_message)
        
        # ثبت traceback برای خطاهای مهم
        if error_info['severity'] in [ErrorSeverity.HIGH, ErrorSeverity.CRITICAL]:
            self.logger.debug(f"Traceback: {error_info['traceback']}")
    
    def _update_stats(self, error_info: Dict):
        """به‌روزرسانی آمار خطاها"""
        self.error_stats['total_errors'] += 1
        
        # آمار بر اساس دسته
        category = error_info['category'].value
        self.error_stats['by_category'][category] = \
            self.error_stats['by_category'].get(category, 0) + 1
        
        # آمار بر اساس شدت
        severity = error_info['severity'].value
        self.error_stats['by_severity'][severity] = \
            self.error_stats['by_severity'].get(severity, 0) + 1
        
        # خطاهای اخیر (حداکثر 50 مورد)
        self.error_stats['recent_errors'].append({
            'timestamp': error_info['timestamp'],
            'category': category,
            'severity': severity,
            'message': error_info['message'][:100]  # محدود کردن طول پیام
        })
        
        if len(self.error_stats['recent_errors']) > 50:
            self.error_stats['recent_errors'].pop(0)
    
    def _should_retry(self, error_info: Dict) -> bool:
        """تعیین اینکه آیا باید تلاش مجدد کرد"""
        # خطاهای بحرانی قابل بازیابی نیستند
        if error_info['severity'] == ErrorSeverity.CRITICAL:
            return False
        
        # بررسی استراتژی بازیابی
        category = error_info['category']
        return category in self.retry_strategies
    
    def _attempt_recovery(self, error_info: Dict, retry_function: Callable, 
                         *args, **kwargs) -> bool:
        """تلاش برای بازیابی خودکار"""
        category = error_info['category']
        strategy = self.retry_strategies.get(category)
        
        if not strategy:
            return False
        
        max_retries = strategy['max_retries']
        base_delay = strategy['delay']
        backoff = strategy['backoff']
        
        self.logger.info(f"🔄 شروع تلاش بازیابی برای {category.value} (حداکثر {max_retries} تلاش)")
        
        for attempt in range(max_retries):
            try:
                # محاسبه تاخیر با exponential backoff
                delay = base_delay * (backoff ** attempt)
                
                if attempt > 0:
                    self.logger.info(f"⏳ انتظار {delay} ثانیه قبل از تلاش {attempt + 1}...")
                    time.sleep(delay)
                
                self.logger.info(f"🔄 تلاش بازیابی {attempt + 1}/{max_retries}")
                
                # اجرای تابع بازیابی
                result = retry_function(*args, **kwargs)
                
                if result:
                    self.logger.info(f"✅ بازیابی موفق در تلاش {attempt + 1}")
                    return True
                
            except Exception as retry_error:
                self.logger.warning(f"⚠️ تلاش {attempt + 1} ناموفق: {retry_error}")
                
                # اگر خطای جدید از نوع متفاوتی باشد، تحلیل کن
                new_error_info = self._analyze_error(retry_error)
                if new_error_info['category'] != category:
                    self.logger.warning(f"🔄 نوع خطا تغییر کرد: {category.value} -> {new_error_info['category'].value}")
                    break
        
        self.logger.error(f"❌ بازیابی ناموفق پس از {max_retries} تلاش")
        return False
    
    def get_error_stats(self) -> Dict:
        """دریافت آمار خطاها"""
        return self.error_stats.copy()
    
    def reset_stats(self):
        """ریست آمار خطاها"""
        self.error_stats = {
            'total_errors': 0,
            'by_category': {},
            'by_severity': {},
            'recent_errors': []
        }
        self.logger.info("📊 آمار خطاها ریست شد")
    
    def get_error_summary(self) -> str:
        """خلاصه آمار خطاها"""
        stats = self.error_stats
        
        if stats['total_errors'] == 0:
            return "📊 هیچ خطایی ثبت نشده است"
        
        summary = f"📊 خلاصه خطاها:\n"
        summary += f"   کل خطاها: {stats['total_errors']}\n"
        
        if stats['by_category']:
            summary += "   بر اساس دسته:\n"
            for category, count in stats['by_category'].items():
                summary += f"     - {category}: {count}\n"
        
        if stats['by_severity']:
            summary += "   بر اساس شدت:\n"
            for severity, count in stats['by_severity'].items():
                summary += f"     - {severity}: {count}\n"
        
        return summary
    
    def is_error_rate_high(self, threshold: float = 0.1, time_window: int = 300) -> bool:
        """بررسی اینکه آیا نرخ خطا بالا است"""
        try:
            current_time = datetime.now()
            recent_errors = [
                error for error in self.error_stats['recent_errors']
                if (current_time - error['timestamp']).total_seconds() <= time_window
            ]
            
            error_rate = len(recent_errors) / (time_window / 60)  # خطا در دقیقه
            return error_rate > threshold
            
        except Exception:
            return False