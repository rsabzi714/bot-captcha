بسیار عالی\! از صبر و پیگیری شما بسیار سپاسگزارم. با اطلاعاتی که فرستادید، **مشکل اصلی را پیدا کردم** و راه حل آن را برایتان آماده کرده‌ام.

خبر خوب این است که مشکل از سمت وب‌سایت نیست، بلکه در کد پایتون شما و نحوه ارتباط با سرویس حل کپچا (2Captcha) است. خوشبختانه این مشکل قابل حل است.

### مشکل چیست؟

فایل `captcha_solver.py` شما از یک روش قدیمی برای ارسال درخواست به سرویس 2Captcha استفاده می‌کند. آدرس API و برخی از پارامترهایی که در کد شما استفاده شده، دیگر صحیح نیستند و به همین دلیل کپچا حل نمی‌شود.

### راه حل

باید محتوای فایل `captcha_solver.py` را با کد اصلاح‌شده جایگزین کنیم. لطفاً مراحل زیر را با دقت انجام دهید:

1.  فایل `captcha_solver.py` را در ویرایشگر کد خود باز کنید.
2.  **تمام محتوای فعلی** این فایل را به طور کامل پاک کنید.
3.  کد جدید زیر را کپی کرده و در فایل خالی `captcha_solver.py` جای‌گذاری (Paste) کنید:

<!-- end list -->

```python
import time
import requests
from utils.error_handler import handle_error

class CaptchaSolver:
    def __init__(self, api_key):
        self.api_key = api_key
        self.http_client = requests.Session()

    def solve_recaptcha_v2(self, site_key, page_url):
        try:
            # Step 1: Send initial request to 2Captcha
            initial_url = "http://2captcha.com/in.php"
            initial_params = {
                'key': self.api_key,
                'method': 'userrecaptcha',
                'googlekey': site_key,
                'pageurl': page_url,
                'json': 1
            }
            response = self.http_client.post(initial_url, params=initial_params)
            response.raise_for_status()
            initial_data = response.json()

            if initial_data['status'] != 1:
                handle_error("2Captcha: Error in initial request - " + initial_data.get('request', 'No error message'), "CaptchaSolver.solve_recaptcha_v2")
                return None

            captcha_id = initial_data['request']
            print(f"Captcha ID: {captcha_id}")

            # Step 2: Poll for the result
            time.sleep(20)  # Initial wait before first poll
            result_url = "http://2captcha.com/res.php"
            while True:
                result_params = {
                    'key': self.api_key,
                    'action': 'get',
                    'id': captcha_id,
                    'json': 1
                }
                response = self.http_client.get(result_url, params=result_params)
                response.raise_for_status()
                result_data = response.json()

                if result_data['status'] == 1:
                    print("Captcha solved successfully!")
                    return result_data['request']
                elif result_data['request'] == 'CAPCHA_NOT_READY':
                    print("Captcha not ready, waiting...")
                    time.sleep(5)
                else:
                    handle_error("2Captcha: Error solving captcha - " + result_data.get('request', 'No error message'), "CaptchaSolver.solve_recaptcha_v2")
                    return None

        except requests.exceptions.RequestException as e:
            handle_error(f"2Captcha: HTTP request failed: {e}", "CaptchaSolver.solve_recaptcha_v2")
            return None
        except Exception as e:
            handle_error(f"An unexpected error occurred in CaptchaSolver: {e}", "CaptchaSolver.solve_recaptcha_v2")
            return None

```

### چه چیزهایی تغییر کرده است؟

  * **آدرس API به‌روز شده:** کد جدید از آدرس‌های صحیح `in.php` و `res.php` برای ارتباط با 2Captcha استفاده می‌کند.
  * **روش صحیح درخواست:** کد جدید به درستی منتظر آماده شدن جواب کپچا می‌ماند.
  * **مدیریت بهتر خطا:** کدهای بیشتری برای مدیریت خطاها اضافه شده تا اگر در آینده مشکلی پیش آمد، راحت‌تر بتوانید آن را پیدا کنید.

پس از اینکه کد را در فایل `captcha_solver.py` جایگزین کردید، لطفاً اسکریپت خود را دوباره اجرا کنید. به احتمال زیاد مشکل حل خواهد شد.

اگر باز هم با مشکلی مواجه شدید، لطفاً خروجی جدید ترمینال یا لاگ‌های جدید را برای من ارسال کنید.