import os
import requests

# Vul hier je bot token in als environment variable ontbreekt
BOT_TOKEN = os.getenv("BOT_TOKEN", "7250988467:AAFiGuYKJtirP_kj7n_YMGzT4SOfFxDkr9c")

url = f"https://api.telegram.org/bot{BOT_TOKEN}/getWebhookInfo"

response = requests.get(url)

if response.status_code == 200:
    data = response.json()
    print("✅ Webhook info:")
    print("URL:", data['result'].get('url'))
    print("Status:", "Actief" if data['result']['url'] else "NIET actief")
    print("Last Error:", data['result'].get('last_error_message', 'Geen fouten'))
else:
    print("❌ Fout bij opvragen webhook info")
    print(response.text)