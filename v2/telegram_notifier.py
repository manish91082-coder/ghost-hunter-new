import os
import time
import requests
from dotenv import load_dotenv

def send_telegram_message(message: str):
    """
    Sends a message to the configured Telegram chat.
    Requires TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID in .env
    """
    base_dir = os.path.dirname(__file__)
    env_path = os.path.join(base_dir, ".env")
    if os.path.exists(env_path):
        load_dotenv(env_path)
    else:
        load_dotenv()
    
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")
    
    if not bot_token or not chat_id:
        print("[!] Telegram credentials missing in .env file.")
        return False
        
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": message,
        "parse_mode": "Markdown"
    }
    
    for attempt in range(3):
        try:
            response = requests.post(url, json=payload, timeout=10)
            if response.status_code == 200:
                print("[+] Telegram message sent successfully!")
                return True
            elif response.status_code == 429:
                retry_after = 5
                try:
                    retry_after = int(response.json().get("parameters", {}).get("retry_after", 5))
                except Exception:
                    pass
                print(f"⚠️ Telegram Rate Limit (429). Retrying in {retry_after}s...")
                time.sleep(retry_after)
                continue
            else:
                # Fallback to Plain Text if Telegram Markdown entity parsing fails (HTTP 400)
                payload_plain = {
                    "chat_id": chat_id,
                    "text": message
                }
                res_plain = requests.post(url, json=payload_plain, timeout=10)
                if res_plain.status_code == 200:
                    print("[+] Telegram message sent successfully (Plain Text Fallback)!")
                    return True
                print(f"[!] Failed to send Telegram message: {response.text}")
                return False
        except Exception as e:
            print(f"[!] Exception while sending Telegram message: {e}")
            time.sleep(2)
    return False

if __name__ == "__main__":
    # Test execution
    test_msg = "🚀 *PhantomX AGI Update*\nThis is a test notification from your Ghost Hunter Bot."
    send_telegram_message(test_msg)
