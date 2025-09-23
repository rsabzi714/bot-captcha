from typing import Optional

class StealthInjector:
    """اعمال تکنیک‌های stealth برای مخفی کردن ماهیت اتوماسیون"""
    
    def __init__(self, page, logger):
        self.page = page
        self.logger = logger
    
    def apply_all_stealth_techniques(self):
        """اعمال تمام تکنیک‌های stealth"""
        try:
            # استفاده از اسکریپت سفارشی بهینه‌شده
            self._inject_optimized_stealth_script()
            self.logger.info("✅ تکنیک‌های stealth بهینه‌شده اعمال شد")
            
        except Exception as e:
            self.logger.warning(f"⚠️ خطا در اعمال stealth: {e}")

    def _inject_optimized_stealth_script(self):
        """تزریق اسکریپت stealth بهینه‌شده و کارآمد"""
        stealth_script = """
        (function() {
            'use strict';
            
            // جلوگیری از اجرای مکرر
            if (window.__stealthApplied) return;
            window.__stealthApplied = true;
            
            // مخفی کردن webdriver
            try {
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined,
                    configurable: true
                });
            } catch(e) {}
            
            // تنظیم navigator properties
            try {
                const originalNavigator = navigator;
                Object.defineProperties(navigator, {
                    plugins: {
                        get: () => {
                            const plugins = Array.from({length: 3}, () => ({}));
                            return plugins;
                        },
                        configurable: true
                    },
                    languages: {
                        get: () => ['pt-PT', 'pt', 'en-US', 'en'],
                        configurable: true
                    },
                    headless: {
                        get: () => false,
                        configurable: true
                    }
                });
            } catch(e) {}
            
            // تنظیم Chrome runtime
            try {
                window.chrome = window.chrome || {};
                window.chrome.runtime = window.chrome.runtime || {
                    onConnect: { addListener: () => {} },
                    onMessage: { addListener: () => {} }
                };
                window.chrome.loadTimes = () => ({
                    requestTime: Date.now() / 1000,
                    startLoadTime: Date.now() / 1000,
                    commitLoadTime: Date.now() / 1000,
                    finishDocumentLoadTime: Date.now() / 1000,
                    finishLoadTime: Date.now() / 1000,
                    firstPaintTime: Date.now() / 1000,
                    firstPaintAfterLoadTime: 0,
                    navigationType: 'Other',
                    wasFetchedViaSpdy: false,
                    wasNpnNegotiated: false,
                    npnNegotiatedProtocol: 'unknown',
                    wasAlternateProtocolAvailable: false,
                    connectionInfo: 'http/1.1'
                });
            } catch(e) {}
            
            // حذف متغیرهای مشکوک
            const suspiciousVars = [
                'callPhantom', '_phantom', 'phantom', 'driver', 'selenium',
                '__webdriver_evaluate', '__selenium_evaluate', '__fxdriver_evaluate',
                '__driver_unwrapped', '__webdriver_unwrapped', '__selenium_unwrapped'
            ];
            
            suspiciousVars.forEach(varName => {
                try {
                    if (window.hasOwnProperty(varName)) {
                        delete window[varName];
                    }
                } catch(e) {}
            });
            
            // مخفی کردن خطاهای مرتبط با automation
            try {
                const originalError = console.error;
                const originalWarn = console.warn;
                
                console.error = function(...args) {
                    const message = args.join(' ');
                    if (!message.includes('webdriver') && !message.includes('automation')) {
                        originalError.apply(this, args);
                    }
                };
                
                console.warn = function(...args) {
                    const message = args.join(' ');
                    if (!message.includes('webdriver') && !message.includes('automation')) {
                        originalWarn.apply(this, args);
                    }
                };
            } catch(e) {}
            
        })();
        """
        try:
            self.page.add_init_script(stealth_script)
            self.logger.debug("✅ اسکریپت stealth بهینه‌شده تزریق شد")
        except Exception as e:
            self.logger.warning(f"⚠️ خطا در تزریق اسکریپت stealth: {e}")