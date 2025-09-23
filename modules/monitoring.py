# modules/monitoring.py
import time
import psutil
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from dataclasses import dataclass

@dataclass
class PerformanceMetrics:
    """متریک‌های عملکرد سیستم"""
    cpu_percent: float
    memory_percent: float
    memory_used_mb: float
    timestamp: datetime
    
class MonitoringService:
    """سرویس نظارت و گزارش‌دهی عملکرد ربات"""
    
    def __init__(self, telegram=None, logger=None):
        self.telegram = telegram
        self.logger = logger
        
        # آمار عملکرد
        self.start_time = datetime.now()
        self.performance_history: List[PerformanceMetrics] = []
        self.max_history_size = 100
        
        # آمار عملیات
        self.operation_stats = {
            'login_attempts': 0,
            'successful_logins': 0,
            'failed_logins': 0,
            'captcha_solved': 0,
            'captcha_failed': 0,
            'errors_total': 0,
            'page_loads': 0,
            'form_submissions': 0
        }
        
        # تنظیمات هشدار
        self.alert_thresholds = {
            'cpu_percent': 80.0,
            'memory_percent': 85.0,
            'error_rate': 0.3,  # 30% نرخ خطا
            'response_time': 30.0  # 30 ثانیه
        }
        
        # آخرین زمان ارسال هشدار (برای جلوگیری از spam)
        self.last_alert_times = {}
        self.alert_cooldown = 300  # 5 دقیقه
    
    def record_performance(self):
        """ثبت متریک‌های عملکرد فعلی"""
        try:
            # دریافت اطلاعات سیستم
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            
            metrics = PerformanceMetrics(
                cpu_percent=cpu_percent,
                memory_percent=memory.percent,
                memory_used_mb=memory.used / (1024 * 1024),
                timestamp=datetime.now()
            )
            
            # اضافه کردن به تاریخچه
            self.performance_history.append(metrics)
            
            # محدود کردن اندازه تاریخچه
            if len(self.performance_history) > self.max_history_size:
                self.performance_history.pop(0)
            
            # بررسی آستانه‌های هشدار
            self._check_performance_alerts(metrics)
            
            if self.logger:
                self.logger.debug(
                    f"📊 عملکرد: CPU={cpu_percent:.1f}%, "
                    f"RAM={memory.percent:.1f}% ({metrics.memory_used_mb:.1f}MB)"
                )
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"❌ خطا در ثبت عملکرد: {e}")
    
    def record_operation(self, operation: str, success: bool = True, details: str = None):
        """ثبت عملیات انجام شده"""
        try:
            # به‌روزرسانی آمار
            if operation == 'login_attempt':
                self.operation_stats['login_attempts'] += 1
                if success:
                    self.operation_stats['successful_logins'] += 1
                else:
                    self.operation_stats['failed_logins'] += 1
            
            elif operation == 'captcha_solve':
                if success:
                    self.operation_stats['captcha_solved'] += 1
                else:
                    self.operation_stats['captcha_failed'] += 1
            
            elif operation == 'error':
                self.operation_stats['errors_total'] += 1
            
            elif operation == 'page_load':
                self.operation_stats['page_loads'] += 1
            
            elif operation == 'form_submit':
                self.operation_stats['form_submissions'] += 1
            
            # لاگ عملیات
            if self.logger:
                status = "✅" if success else "❌"
                message = f"{status} {operation}"
                if details:
                    message += f": {details}"
                self.logger.info(message)
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"❌ خطا در ثبت عملیات: {e}")
    
    def get_performance_summary(self) -> Dict:
        """دریافت خلاصه عملکرد"""
        try:
            if not self.performance_history:
                return {'status': 'no_data'}
            
            # محاسبه میانگین‌ها
            recent_metrics = self.performance_history[-10:]  # 10 مورد اخیر
            
            avg_cpu = sum(m.cpu_percent for m in recent_metrics) / len(recent_metrics)
            avg_memory = sum(m.memory_percent for m in recent_metrics) / len(recent_metrics)
            avg_memory_mb = sum(m.memory_used_mb for m in recent_metrics) / len(recent_metrics)
            
            # محاسبه uptime
            uptime = datetime.now() - self.start_time
            
            # محاسبه نرخ موفقیت
            total_logins = self.operation_stats['login_attempts']
            success_rate = (
                self.operation_stats['successful_logins'] / total_logins * 100
                if total_logins > 0 else 0
            )
            
            return {
                'uptime_seconds': uptime.total_seconds(),
                'uptime_formatted': str(uptime).split('.')[0],
                'avg_cpu_percent': round(avg_cpu, 1),
                'avg_memory_percent': round(avg_memory, 1),
                'avg_memory_mb': round(avg_memory_mb, 1),
                'login_success_rate': round(success_rate, 1),
                'operations': self.operation_stats.copy(),
                'last_update': datetime.now().isoformat()
            }
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"❌ خطا در دریافت خلاصه عملکرد: {e}")
            return {'status': 'error', 'message': str(e)}
    
    def send_status_report(self, force: bool = False):
        """ارسال گزارش وضعیت"""
        try:
            if not self.telegram:
                return
            
            summary = self.get_performance_summary()
            
            if summary.get('status') == 'no_data':
                return
            
            # تشکیل پیام گزارش
            report = self._format_status_report(summary)
            
            # ارسال گزارش
            self.telegram.send_status_update("گزارش وضعیت ربات", report)
            
            if self.logger:
                self.logger.info("📊 گزارش وضعیت ارسال شد")
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"❌ خطا در ارسال گزارش: {e}")
    
    def _format_status_report(self, summary: Dict) -> str:
        """فرمت کردن گزارش وضعیت"""
        try:
            uptime = summary['uptime_formatted']
            cpu = summary['avg_cpu_percent']
            memory = summary['avg_memory_percent']
            memory_mb = summary['avg_memory_mb']
            success_rate = summary['login_success_rate']
            ops = summary['operations']
            
            report = f"""🤖 **گزارش عملکرد ربات MNE**

⏱️ **زمان فعالیت:** {uptime}

📊 **عملکرد سیستم:**
• CPU: {cpu}%
• حافظه: {memory}% ({memory_mb:.0f} MB)

🎯 **آمار عملیات:**
• تلاش‌های ورود: {ops['login_attempts']}
• ورود موفق: {ops['successful_logins']}
• نرخ موفقیت: {success_rate}%
• کپچای حل شده: {ops['captcha_solved']}
• کل خطاها: {ops['errors_total']}

📈 **وضعیت کلی:** {'🟢 عالی' if success_rate > 80 else '🟡 متوسط' if success_rate > 50 else '🔴 نیاز به بررسی'}"""
            
            return report
            
        except Exception as e:
            return f"خطا در تشکیل گزارش: {e}"
    
    def _check_performance_alerts(self, metrics: PerformanceMetrics):
        """بررسی آستانه‌های هشدار عملکرد"""
        try:
            current_time = datetime.now()
            
            # بررسی CPU
            if metrics.cpu_percent > self.alert_thresholds['cpu_percent']:
                self._send_alert(
                    'high_cpu',
                    f"🔴 هشدار CPU بالا: {metrics.cpu_percent:.1f}%",
                    current_time
                )
            
            # بررسی حافظه
            if metrics.memory_percent > self.alert_thresholds['memory_percent']:
                self._send_alert(
                    'high_memory',
                    f"🔴 هشدار حافظه بالا: {metrics.memory_percent:.1f}%",
                    current_time
                )
            
            # بررسی نرخ خطا
            error_rate = self._calculate_recent_error_rate()
            if error_rate > self.alert_thresholds['error_rate']:
                self._send_alert(
                    'high_error_rate',
                    f"🔴 هشدار نرخ خطای بالا: {error_rate:.1%}",
                    current_time
                )
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"❌ خطا در بررسی هشدارها: {e}")
    
    def _send_alert(self, alert_type: str, message: str, current_time: datetime):
        """ارسال هشدار با کنترل cooldown"""
        try:
            # بررسی cooldown
            last_alert = self.last_alert_times.get(alert_type)
            if last_alert:
                time_diff = (current_time - last_alert).total_seconds()
                if time_diff < self.alert_cooldown:
                    return  # هنوز در دوره cooldown
            
            # ارسال هشدار
            if self.telegram:
                self.telegram.send_alert(message)
            
            if self.logger:
                self.logger.warning(message)
            
            # به‌روزرسانی زمان آخرین هشدار
            self.last_alert_times[alert_type] = current_time
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"❌ خطا در ارسال هشدار: {e}")
    
    def _calculate_recent_error_rate(self) -> float:
        """محاسبه نرخ خطای اخیر"""
        try:
            # محاسبه بر اساس 10 عملیات اخیر
            recent_operations = 10
            total_operations = sum([
                self.operation_stats['login_attempts'],
                self.operation_stats['captcha_solved'] + self.operation_stats['captcha_failed'],
                self.operation_stats['form_submissions']
            ])
            
            if total_operations < recent_operations:
                return 0.0
            
            # تخمین نرخ خطا بر اساس آمار کلی
            total_errors = self.operation_stats['errors_total']
            return total_errors / total_operations if total_operations > 0 else 0.0
            
        except Exception:
            return 0.0
    
    def get_health_status(self) -> Dict:
        """دریافت وضعیت سلامت سیستم"""
        try:
            summary = self.get_performance_summary()
            
            if summary.get('status') == 'no_data':
                return {'status': 'unknown', 'message': 'داده‌ای موجود نیست'}
            
            # تعیین وضعیت بر اساس متریک‌ها
            cpu_ok = summary['avg_cpu_percent'] < self.alert_thresholds['cpu_percent']
            memory_ok = summary['avg_memory_percent'] < self.alert_thresholds['memory_percent']
            success_rate_ok = summary['login_success_rate'] > 70
            
            if cpu_ok and memory_ok and success_rate_ok:
                status = 'healthy'
                message = '✅ سیستم سالم است'
            elif cpu_ok and memory_ok:
                status = 'warning'
                message = '⚠️ عملکرد قابل بهبود است'
            else:
                status = 'critical'
                message = '🔴 سیستم نیاز به بررسی دارد'
            
            return {
                'status': status,
                'message': message,
                'details': {
                    'cpu_healthy': cpu_ok,
                    'memory_healthy': memory_ok,
                    'performance_healthy': success_rate_ok
                },
                'summary': summary
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'message': f'خطا در بررسی سلامت: {e}'
            }
    
    def reset_stats(self):
        """ریست آمار عملیات"""
        try:
            self.operation_stats = {
                'login_attempts': 0,
                'successful_logins': 0,
                'failed_logins': 0,
                'captcha_solved': 0,
                'captcha_failed': 0,
                'errors_total': 0,
                'page_loads': 0,
                'form_submissions': 0
            }
            
            self.performance_history.clear()
            self.start_time = datetime.now()
            
            if self.logger:
                self.logger.info("📊 آمار نظارت ریست شد")
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"❌ خطا در ریست آمار: {e}")
    
    def export_metrics(self) -> Dict:
        """صادرات تمام متریک‌ها"""
        try:
            return {
                'performance_history': [
                    {
                        'cpu_percent': m.cpu_percent,
                        'memory_percent': m.memory_percent,
                        'memory_used_mb': m.memory_used_mb,
                        'timestamp': m.timestamp.isoformat()
                    }
                    for m in self.performance_history
                ],
                'operation_stats': self.operation_stats.copy(),
                'start_time': self.start_time.isoformat(),
                'alert_thresholds': self.alert_thresholds.copy(),
                'health_status': self.get_health_status()
            }
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"❌ خطا در صادرات متریک‌ها: {e}")
            return {}