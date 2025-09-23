class TelegramNotifier:
    """کلاس اطلاع‌رسانی تلگرام"""
    
    def __init__(self, bot_token=None, chat_id=None):
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.enabled = bool(bot_token and chat_id)
    
    def send_message(self, message: str) -> bool:
        """ارسال پیام به تلگرام"""
        if not self.enabled:
            return False
        
        try:
            # اینجا می‌توانید کد ارسال پیام تلگرام را اضافه کنید
            print(f"📱 Telegram: {message}")
            return True
        except Exception as e:
            print(f"❌ خطا در ارسال پیام تلگرام: {e}")
            return False
    
    def send_success(self, message: str) -> bool:
        """ارسال پیام موفقیت"""
        return self.send_message(f"✅ {message}")
    
    def send_error(self, message: str) -> bool:
        """ارسال پیام خطا"""
        return self.send_message(f"❌ {message}")
    
    def send_warning(self, message: str) -> bool:
        """ارسال پیام هشدار"""
        return self.send_message(f"⚠️ {message}")
    
    def send_status_update(self, title: str, message: str) -> bool:
        """ارسال به‌روزرسانی وضعیت"""
        full_message = f"📊 {title}\n{message}"
        return self.send_message(full_message)