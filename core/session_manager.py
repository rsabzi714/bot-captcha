# core/session_manager.py
import json
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Dict, Any

class SessionManager:
    """مدیریت جلسات کاربری و ذخیره وضعیت"""
    
    def __init__(self, browser, config, logger):
        self.browser = browser
        self.config = config
        self.logger = logger
        
        # تنظیمات جلسه
        self.session_dir = Path("sessions")
        self.session_dir.mkdir(exist_ok=True)
        
        self.current_session_name = "default"
        self.session_timeout = timedelta(hours=2)  # مدت اعتبار جلسه
        
    def load_session(self, session_name: str = "default") -> bool:
        """بارگذاری جلسه ذخیره شده"""
        try:
            session_file = self.session_dir / f"{session_name}.json"
            
            if not session_file.exists():
                self.logger.info(f"📂 فایل جلسه {session_name} وجود ندارد")
                return False
            
            # بررسی تاریخ انقضا
            if not self._is_session_valid(session_file):
                self.logger.warning(f"⏰ جلسه {session_name} منقضی شده")
                self._delete_session(session_name)
                return False
            
            # بارگذاری وضعیت
            with open(session_file, 'r', encoding='utf-8') as f:
                storage_state = json.load(f)
            
            # اعمال وضعیت به context
            if hasattr(self.browser, 'context') and self.browser.context:
                try:
                    # بستن context و page قدیمی
                    if hasattr(self.browser, 'page') and self.browser.page:
                        self.browser.page.close()
                    if self.browser.context:
                        self.browser.context.close()
                    
                    # ایجاد context جدید با وضعیت ذخیره شده
                    new_context = self.browser.browser.new_context(storage_state=storage_state)
                    self.browser.context = new_context
                    self.browser.page = new_context.new_page()
                    
                except Exception as e:
                    self.logger.warning(f"⚠️ خطا در بازیابی context: {e}")
                    return False
                
                if old_context:
                    old_context.close()
                
                self.current_session_name = session_name
                self.logger.info(f"✅ جلسه {session_name} بارگذاری شد")
                return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"❌ خطا در بارگذاری جلسه {session_name}: {e}")
            return False
    
    def save_session(self, session_name: str = None) -> bool:
        """ذخیره وضعیت فعلی جلسه"""
        try:
            if session_name is None:
                session_name = self.current_session_name
            
            if not hasattr(self.browser, 'context') or not self.browser.context:
                self.logger.warning("⚠️ context فعالی برای ذخیره وجود ندارد")
                return False
            
            # دریافت وضعیت فعلی
            storage_state = self.browser.context.storage_state()
            
            # اضافه کردن metadata
            session_data = {
                'storage_state': storage_state,
                'metadata': {
                    'created_at': datetime.now().isoformat(),
                    'user_agent': self.browser.page.evaluate('navigator.userAgent'),
                    'url': self.browser.page.url,
                    'account': self.config.get_current_account()['username'] if self.config.get_current_account() else None
                }
            }
            
            # ذخیره در فایل
            session_file = self.session_dir / f"{session_name}.json"
            with open(session_file, 'w', encoding='utf-8') as f:
                json.dump(session_data, f, ensure_ascii=False, indent=2)
            
            self.current_session_name = session_name
            self.logger.info(f"💾 جلسه {session_name} ذخیره شد")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ خطا در ذخیره جلسه {session_name}: {e}")
            return False
    
    def save_current_session(self) -> bool:
        """ذخیره جلسه فعلی"""
        return self.save_session(self.current_session_name)
    
    def delete_session(self, session_name: str) -> bool:
        """حذف جلسه"""
        return self._delete_session(session_name)
    
    def _delete_session(self, session_name: str) -> bool:
        """حذف فایل جلسه"""
        try:
            session_file = self.session_dir / f"{session_name}.json"
            if session_file.exists():
                session_file.unlink()
                self.logger.info(f"🗑️ جلسه {session_name} حذف شد")
                return True
            return False
            
        except Exception as e:
            self.logger.error(f"❌ خطا در حذف جلسه {session_name}: {e}")
            return False
    
    def _is_session_valid(self, session_file: Path) -> bool:
        """بررسی اعتبار جلسه"""
        try:
            with open(session_file, 'r', encoding='utf-8') as f:
                session_data = json.load(f)
            
            # بررسی وجود metadata
            if 'metadata' not in session_data:
                return False
            
            # بررسی تاریخ ایجاد
            created_at_str = session_data['metadata'].get('created_at')
            if not created_at_str:
                return False
            
            created_at = datetime.fromisoformat(created_at_str)
            now = datetime.now()
            
            # بررسی انقضا
            if now - created_at > self.session_timeout:
                return False
            
            return True
            
        except Exception as e:
            self.logger.debug(f"خطا در بررسی اعتبار جلسه: {e}")
            return False
    
    def list_sessions(self) -> list:
        """لیست جلسات موجود"""
        try:
            sessions = []
            for session_file in self.session_dir.glob("*.json"):
                session_name = session_file.stem
                
                # بررسی اعتبار
                is_valid = self._is_session_valid(session_file)
                
                # دریافت metadata
                try:
                    with open(session_file, 'r', encoding='utf-8') as f:
                        session_data = json.load(f)
                    metadata = session_data.get('metadata', {})
                except:
                    metadata = {}
                
                sessions.append({
                    'name': session_name,
                    'valid': is_valid,
                    'created_at': metadata.get('created_at'),
                    'account': metadata.get('account'),
                    'file_size': session_file.stat().st_size
                })
            
            return sessions
            
        except Exception as e:
            self.logger.error(f"❌ خطا در لیست جلسات: {e}")
            return []
    
    def cleanup_expired_sessions(self) -> int:
        """پاکسازی جلسات منقضی شده"""
        try:
            deleted_count = 0
            
            for session_file in self.session_dir.glob("*.json"):
                if not self._is_session_valid(session_file):
                    session_name = session_file.stem
                    if self._delete_session(session_name):
                        deleted_count += 1
            
            if deleted_count > 0:
                self.logger.info(f"🧹 {deleted_count} جلسه منقضی شده پاک شد")
            
            return deleted_count
            
        except Exception as e:
            self.logger.error(f"❌ خطا در پاکسازی جلسات: {e}")
            return 0
    
    def get_session_info(self, session_name: str) -> Optional[Dict[str, Any]]:
        """دریافت اطلاعات جلسه"""
        try:
            session_file = self.session_dir / f"{session_name}.json"
            
            if not session_file.exists():
                return None
            
            with open(session_file, 'r', encoding='utf-8') as f:
                session_data = json.load(f)
            
            metadata = session_data.get('metadata', {})
            
            return {
                'name': session_name,
                'valid': self._is_session_valid(session_file),
                'created_at': metadata.get('created_at'),
                'account': metadata.get('account'),
                'url': metadata.get('url'),
                'user_agent': metadata.get('user_agent'),
                'file_size': session_file.stat().st_size,
                'cookies_count': len(session_data.get('storage_state', {}).get('cookies', [])),
                'local_storage_count': len(session_data.get('storage_state', {}).get('origins', []))
            }
            
        except Exception as e:
            self.logger.error(f"❌ خطا در دریافت اطلاعات جلسه {session_name}: {e}")
            return None