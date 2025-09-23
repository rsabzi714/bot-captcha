# main.py
# main.py - نقطه ورود اصلی ربات MNE بازسازی شده
import signal
import sys
from core.bot_manager import BotManager

def signal_handler(sig, frame):
    """مدیریت سیگنال‌های سیستم"""
    print("\n🛑 دریافت سیگنال توقف...")
    if 'bot_manager' in globals():
        bot_manager.stop()
    sys.exit(0)

def main():
    """تابع اصلی"""
    global bot_manager
    
    try:
        print("🚀 راه‌اندازی ربات MNE نسخه بازسازی شده...")
        
        # تنظیم signal handler
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        # ایجاد و راه‌اندازی مدیر ربات
        bot_manager = BotManager()
        
        # شروع عملیات
        bot_manager.start()
        
    except KeyboardInterrupt:
        print("\n⏹️ توقف ربات توسط کاربر")
    except Exception as e:
        print(f"❌ خطای غیرمنتظره: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if 'bot_manager' in locals():
            bot_manager.cleanup()
        print("👋 ربات متوقف شد")

if __name__ == "__main__":
    main()