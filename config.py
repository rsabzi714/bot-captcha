# config.py
import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # اطلاعات ورود - سیستم چندگانه
    MNE_ACCOUNTS = [
        {'username': 'lida.mosaffaei@gmail.com', 'password': '912119427aA@'},
        {'username': 'Kasaei_1994@yahoo.com', 'password': '912119427aA@'},
        {'username': 'ghomashlooyanm@gmail.com', 'password': '912119427aA@'},
        {'username': 'golsan.hosseinzade@gmail.com', 'password': '912119427aA@'},
        {'username': 'ladann.moslemzade@gmail.com', 'password': '912119427aA@'},
        {'username': 'samaaneh.karimiii@gmail.com', 'password': '@912119427Aa'},
        {'username': 'majiid.zarrin@gmail.com', 'password': '@912119427Aa'},
        {'username': 'marziyehazita.shadkam@gmail.com', 'password': '@912119427Aa'},
        {'username': 'melan.keshishian@gmail.com', 'password': '@912119427Aa'},
        {'username': 'maryaam.madadian@gmail.com', 'password': '@912119427Aa'},
        {'username': 'nargess.safizadeh@gmail.com', 'password': '912119427aA@'},
        {'username': 'mahtab.shahnazikondoloji@gmail.com', 'password': '912119427aA@'},
        {'username': 'mostafaa.estaji@gmail.com', 'password': '912119427aA@'},
        {'username': 'takesh.siamak@gmail.com', 'password': '912119427aA@'},
        {'username': 'mohmmad.mobasheri@gmail.com', 'password': '@912119427aA'},
        {'username': 'babakk.motamedi@gmail.com', 'password': '@912119427Aa'}
        
    ]
    
    # اکانت فعلی (برای سازگاری با کد قبلی)
    MNE_USERNAME = os.getenv('MNE_USERNAME')
    MNE_PASSWORD = os.getenv('MNE_PASSWORD')
    
    # شاخص اکانت فعلی
    CURRENT_ACCOUNT_INDEX = 0
    
    # تنظیمات 2Captcha
    CAPTCHA_API_KEY = os.getenv('CAPTCHA_API_KEY', '3fedb7fa7ca2df09e5113f0818b7fad9')
    
    # تنظیمات تلگرام
    TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
    TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
    
    # تنظیمات پروکسی
    PROXY_CONFIG = {
        'type': 'residential_rotating',
        'host': os.getenv('PROXY_HOST'),
        'port': int(os.getenv('PROXY_PORT', 10000)),
        'username': os.getenv('PROXY_USERNAME'),
        'password': os.getenv('PROXY_PASSWORD')
    }
    
    @classmethod
    def get_current_account(cls):
        """دریافت اکانت فعلی"""
        if cls.MNE_USERNAME and cls.MNE_PASSWORD:
            return {'username': cls.MNE_USERNAME, 'password': cls.MNE_PASSWORD}
        elif cls.MNE_ACCOUNTS:
            return cls.MNE_ACCOUNTS[cls.CURRENT_ACCOUNT_INDEX]
        return None
    
    @classmethod
    def switch_to_next_account(cls):
        """تغییر به اکانت بعدی"""
        if cls.MNE_ACCOUNTS:
            cls.CURRENT_ACCOUNT_INDEX = (cls.CURRENT_ACCOUNT_INDEX + 1) % len(cls.MNE_ACCOUNTS)
            return cls.get_current_account()
        return None
    
    @classmethod
    def validate_config(cls):
        """اعتبارسنجی تنظیمات"""
        errors = []
        
        # بررسی وجود اکانت (از .env یا لیست داخلی)
        current_account = cls.get_current_account()
        if not current_account:
            errors.append("هیچ اکانت معتبری یافت نشد (نه در .env و نه در لیست داخلی)")
        else:
            # نمایش اکانت فعلی
            username = current_account['username']
            print(f"🔑 اکانت فعلی: {username}")
        
        # تلگرام اختیاری است
        if cls.TELEGRAM_BOT_TOKEN and not cls.TELEGRAM_CHAT_ID:
            errors.append("TELEGRAM_CHAT_ID در فایل .env تنظیم نشده است")
        if cls.TELEGRAM_CHAT_ID and not cls.TELEGRAM_BOT_TOKEN:
            errors.append("TELEGRAM_BOT_TOKEN در فایل .env تنظیم نشده است")
        
        # پروکسی ضروری است برای جلوگیری از شناسایی
        proxy_username = cls.PROXY_CONFIG.get('username')
        proxy_password = cls.PROXY_CONFIG.get('password')
        if not proxy_username:
            errors.append("PROXY_USERNAME در فایل .env تنظیم نشده است (ضروری برای امنیت)")
        if not proxy_password:
            errors.append("PROXY_PASSWORD در فایل .env تنظیم نشده است (ضروری برای امنیت)")
        
        return errors
    
    # تنظیمات عمومی
    CHECK_INTERVAL = 60  # ثانیه
    MONITORING_INTERVAL = 30  # ثانیه - فاصله زمانی نظارت
    MAX_RETRIES = 3
    HEADLESS = False
    BROWSER_TYPE = os.getenv('BROWSER_TYPE', 'chromium')  # chromium, firefox, webkit
    
    # تنظیمات لاگ‌گیری
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')  # DEBUG, INFO, WARNING, ERROR
    LOG_TO_FILE = True
    LOG_FILE_PATH = 'mne_bot.log'
    LOG_MAX_SIZE = 10 * 1024 * 1024  # 10MB
    LOG_BACKUP_COUNT = 5
    LOG_FORMAT = '%(asctime)s - %(levelname)s - %(message)s'
    LOG_DATE_FORMAT = '%Y-%m-%d %H:%M:%S'
    
    # URLs - بر اساس ساختار واقعی سایت
    MNE_BASE_URL = 'https://agendamentos.mne.gov.pt'
    MNE_LOGIN_URL = f'{MNE_BASE_URL}/pt/login'
    
    # تنظیمات امنیتی اضافی
    COOKIE_CONSENT_REQUIRED = True
    AUTHENTICATION_METHOD = 'credentials'  # 'credentials' یا 'autenticacao_gov'
    
    # تنظیمات مخصوص سایت
    SITE_LANGUAGE = 'pt'  # پرتغالی
    TIMEZONE = 'Europe/Lisbon'
    GEOLOCATION = {'latitude': 38.7223, 'longitude': -9.1393}  # لیسبون
    
    # تنظیمات مخصوص سرور ایران
    IRAN_SERVER_MODE = os.getenv('IRAN_SERVER_MODE', 'false').lower() == 'true'
    EXTENDED_TIMEOUT = 60 if IRAN_SERVER_MODE else 30
    USE_DOMESTIC_DNS = IRAN_SERVER_MODE
    BYPASS_SSL_VERIFICATION = IRAN_SERVER_MODE
    DISABLE_PROXY_ON_FAILURE = IRAN_SERVER_MODE