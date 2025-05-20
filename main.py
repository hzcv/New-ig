from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
import time
import json
import os
from getpass import getpass

# Configuration
USERNAME = input("Enter your Instagram username: ")
PASSWORD = getpass("Enter your Instagram password: ")
BOT_USERNAME = USERNAME
ADMINS = ["admin1", "admin2"]  # Replace with your admin usernames
HISTORY_FILE = "message_history.json"

# Load message history
if os.path.exists(HISTORY_FILE):
    with open(HISTORY_FILE, "r") as f:
        message_history = json.load(f)
else:
    message_history = {}

# Set up Chrome options for headless mode
chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")

# Set up WebDriver
driver = webdriver.Chrome(options=chrome_options)
driver.implicitly_wait(10)

monitoring = True

def save_history():
    with open(HISTORY_FILE, "w") as f:
        json.dump(message_history, f)

try:
    # Login retry loop
    while True:
        try:
            driver.get("https://www.instagram.com/accounts/login/")
            WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.NAME, "username")))
            driver.find_element(By.NAME, "username").send_keys(USERNAME)
            driver.find_element(By.NAME, "password").send_keys(PASSWORD)
            driver.find_element(By.NAME, "password").send_keys(Keys.RETURN)
            time.sleep(5)
            break
        except Exception as e:
            print("Login failed, retrying...", e)
            time.sleep(3)

    driver.get("https://www.instagram.com/direct/inbox/")
    time.sleep(5)

    while True:
        if not monitoring:
            print("[STATUS] Monitoring paused. Waiting...")
            time.sleep(10)
            continue

        try:
            chat_elements = WebDriverWait(driver, 10).until(
                EC.presence_of_all_elements_located((By.XPATH, "//a[contains(@href, '/direct/t/')]")
            ))
            group_chat_urls = [e.get_attribute("href") for e in chat_elements]
        except Exception as e:
            print(f"[ERROR] Could not fetch group chats: {e}")
            time.sleep(5)
            continue

        for chat_url in group_chat_urls:
            try:
                driver.get(chat_url)
                time.sleep(3)

                if chat_url not in message_history:
                    message_history[chat_url] = []

                messages = WebDriverWait(driver, 10).until(
                    EC.presence_of_all_elements_located((By.XPATH, "//div[contains(@class, 'x1lliihq') and descendant::span]"))
                )

                for message in messages[-5:]:  # only check last 5 messages
                    try:
                        username = message.find_element(By.XPATH, ".//h3//span").text
                        content_elem = message.find_element(By.XPATH, ".//div[contains(@dir, 'auto')]")
                        content = content_elem.text.strip()

                        if not content or content in message_history[chat_url]:
                            continue

                        print(f"[MSG] {username}: {content}")
                        message_history[chat_url].append(content)

                        if username in ADMINS:
                            if content == "!stop":
                                monitoring = False
                                print("[ADMIN] Monitoring stopped.")
                            elif content == "!start":
                                monitoring = True
                                print("[ADMIN] Monitoring resumed.")
                            elif content == "!status":
                                reply = driver.find_element(By.XPATH, "//textarea")
                                reply.send_keys("Bot is " + ("active" if monitoring else "paused"))
                                reply.send_keys(Keys.RETURN)
                        elif username != BOT_USERNAME:
                            reply = driver.find_element(By.XPATH, "//textarea")
                            reply.send_keys(f"@{username} oyy msg mt kr")
                            reply.send_keys(Keys.RETURN)
                            print(f"[REPLY] Sent to @{username}")

                        save_history()
                        time.sleep(1)
                    except Exception as e:
                        print(f"[WARN] Error processing message: {e}")

            except Exception as e:
                print(f"[ERROR] Failed to process chat {chat_url}: {e}")

        time.sleep(10)

except Exception as e:
    print(f"[FATAL] An error occurred: {e}")
finally:
    save_history()
    driver.quit()
