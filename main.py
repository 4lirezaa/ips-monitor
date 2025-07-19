import os
import requests
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime

# === Load secrets ===
API_KEY = os.getenv('API_KEY')
BOT_TOKEN = os.getenv('BOT_TOKEN')
CHAT_ID = os.getenv('CHAT_ID')
SHEET_ID = '1Ws_Tr81EAbwm6fRUr9XJ_fN63-QwVuBDUp6uNlPE3Mw'

# === Save credentials.json from GitHub Secret ===
import base64

creds_b64 = os.getenv('GOOGLE_CREDENTIALS_BASE64')
if not creds_b64:
    raise ValueError("❌ GOOGLE_CREDENTIALS_BASE64 is missing!")

with open('credentials.json', 'wb') as f:
    f.write(base64.b64decode(creds_b64))


# === Connect to Google Sheet ===
scopes = ['https://www.googleapis.com/auth/spreadsheets']
credentials = Credentials.from_service_account_file('credentials.json', scopes=scopes)
gc = gspread.authorize(credentials)
sheet = gc.open_by_key(SHEET_ID).sheet1  # first tab of the sheet

# === Helper: Send Telegram notification ===
def send_telegram_message(text):
    url = f'https://api.telegram.org/bot{BOT_TOKEN}/sendMessage'
    data = {'chat_id': CHAT_ID, 'text': text}
    try:
        requests.post(url, data=data)
    except Exception as e:
        print("❌ Error sending Telegram message:", e)

# === Get current IPs from ViewDNS ===
def get_current_ips():
    url = f"https://api.viewdns.info/iphistory/?domain=tawk.to&apikey={API_KEY}&output=json"
    response = requests.get(url)
    data = response.json()
    ip_set = set()

    if 'response' in data and 'records' in data['response']:
        for record in data['response']['records']:
            ip = record.get('ip', '').strip()
            if ip:
                ip_set.add(ip)

    return ip_set

# === Load previous IPs from sheet ===
def load_previous_ips():
    try:
        ip_col = sheet.col_values(1)[1:]  # skip header
        return set(ip_col)
    except:
        return set()

# === Save new IPs to sheet ===
def save_ips(new_ips, run_count):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    for ip in sorted(new_ips):
        sheet.append_row([ip, now, str(run_count)])

# === Get and increment run count ===
def get_and_increment_run_count():
    run_count_cells = sheet.col_values(3)[1:]  # col C
    count = len(run_count_cells) + 1
    return count

# === Main ===
def main():
    run_count = get_and_increment_run_count()
    current_ips = get_current_ips()
    previous_ips = load_previous_ips()

    new_ips = current_ips - previous_ips

    if new_ips:
        message = f"🆕 New IP(s) detected for tawk.to:\n" + "\n".join(f" - {ip}" for ip in sorted(new_ips))
        send_telegram_message(message)
        save_ips(new_ips, run_count)
    else:
        print("✅ No new IPs found.")

    send_telegram_message(f"📊 Run #{run_count} completed.\nDomain: tawk.to")

if __name__ == '__main__':
    main()
