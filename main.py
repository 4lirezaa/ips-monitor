import requests
import os

# 🔐 Load secrets from environment variables
API_KEY = os.getenv('API_KEY')
BOT_TOKEN = os.getenv('BOT_TOKEN')
CHAT_ID = os.getenv('CHAT_ID')

# Temporary files (used during GitHub Actions execution)
IP_FILE = 'ip_list.txt'
RUN_COUNT_FILE = 'run_count.txt'

# Send message to Telegram
def send_telegram_message(text):
    url = f'https://api.telegram.org/bot{BOT_TOKEN}/sendMessage'
    data = {'chat_id': CHAT_ID, 'text': text}
    try:
        requests.post(url, data=data)
    except Exception as e:
        print("❌ Error sending Telegram message:", e)

# Fetch current IPs for the domain using ViewDNS API
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

# Load previously saved IPs from file
def load_previous_ips():
    if not os.path.exists(IP_FILE):
        return set()
    with open(IP_FILE, 'r') as f:
        return set(f.read().splitlines())

# Save current IPs to file
def save_ips(ip_set):
    with open(IP_FILE, 'w') as f:
        for ip in sorted(ip_set):
            f.write(ip + '\n')

# Increment and save run count
def increment_run_count():
    count = 0
    if os.path.exists(RUN_COUNT_FILE):
        with open(RUN_COUNT_FILE, 'r') as f:
            try:
                count = int(f.read().strip())
            except:
                count = 0
    count += 1
    with open(RUN_COUNT_FILE, 'w') as f:
        f.write(str(count))
    return count

# Main execution function
def main():
    run_count = increment_run_count()
    current_ips = get_current_ips()
    previous_ips = load_previous_ips()

    new_ips = current_ips - previous_ips

    if new_ips:
        msg = f"🆕 New IP(s) detected for tawk.to:\n" + "\n".join(f" - {ip}" for ip in sorted(new_ips))
        send_telegram_message(msg)
        save_ips(current_ips)
    else:
        print("✅ No new IPs detected.")

    send_telegram_message(f"📊 Run #{run_count} completed.\nDomain: tawk.to")

if __name__ == '__main__':
    main()
