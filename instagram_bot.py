import os
import time
import pickle
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from config import INSTAGRAM_USERNAME, INSTAGRAM_PASSWORD, ADMIN_USERNAMES, COOLDOWN_SECONDS
from firebase_manager import is_group_enabled, set_group_status, get_scheduled_messages, clear_message

COOKIES_FILE = "cookies.pkl"
cooldowns = {}

def create_driver():
    options = webdriver.ChromeOptions()
    options.add_argument("--start-maximized")
    # options.add_argument("--headless")  # Optional
    driver = webdriver.Chrome(options=options)
    return driver

def login(driver):
    driver.get("https://www.instagram.com/")
    time.sleep(3)

    if os.path.exists(COOKIES_FILE):
        with open(COOKIES_FILE, "rb") as f:
            cookies = pickle.load(f)
            for cookie in cookies:
                if "expiry" in cookie:
                    del cookie["expiry"]
                driver.add_cookie(cookie)

        driver.get("https://www.instagram.com/direct/inbox/")
        time.sleep(5)

        if "login" not in driver.current_url:
            print("✅ Logged in with cookies.")
            return

    print("🔐 Logging in manually...")
    driver.get("https://www.instagram.com/accounts/login/")
    time.sleep(5)
    driver.find_element(By.NAME, "username").send_keys(INSTAGRAM_USERNAME)
    driver.find_element(By.NAME, "password").send_keys(INSTAGRAM_PASSWORD + Keys.RETURN)
    time.sleep(7)

    try:
        driver.find_element(By.XPATH, "//button[text()='Not Now']").click()
    except:
        pass

    with open(COOKIES_FILE, "wb") as f:
        pickle.dump(driver.get_cookies(), f)

    print("✅ Login complete and cookies saved.")

def open_inbox(driver):
    driver.get("https://www.instagram.com/direct/inbox/")
    time.sleep(5)

def get_conversations(driver):
    return driver.find_elements(By.CSS_SELECTOR, "._ab6-")

def get_group_name(driver):
    try:
        return driver.find_element(By.CSS_SELECTOR, "header span").text
    except:
        return "Unknown"

def is_group_chat(convo):
    try:
        return "+" in convo.text or "," in convo.text
    except:
        return False

def monitor_groups(driver):
    open_inbox(driver)
    conversations = get_conversations(driver)
    messages = get_scheduled_messages()

    for convo in conversations:
        if not is_group_chat(convo):
            continue

        try:
            convo.click()
            time.sleep(3)

            group_name = get_group_name(driver)
            if not is_group_enabled(group_name):
                continue

            # Scheduled Message from Firebase
            if group_name in messages:
                message = messages[group_name]
                reply_box = driver.find_element(By.TAG_NAME, "textarea")
                reply_box.send_keys(message)
                reply_box.send_keys(Keys.RETURN)
                clear_message(group_name)
                print(f"📨 Sent scheduled message to {group_name}")
                open_inbox(driver)
                continue

            # Check last message
            messages_el = driver.find_elements(By.CSS_SELECTOR, "div._a9zr span")
            senders_el = driver.find_elements(By.CSS_SELECTOR, "div._a9zv")
            if not messages_el or not senders_el:
                continue

            last_msg = messages_el[-1].text.strip()
            sender_label = senders_el[-1].get_attribute("aria-label") or "user"
            username = sender_label.lower().replace(" ", "_")

            if username in [admin.lower() for admin in ADMIN_USERNAMES]:
                if last_msg.lower() == "!stop":
                    set_group_status(group_name, False)
                elif last_msg.lower() == "!start":
                    set_group_status(group_name, True)
                continue

            last = cooldowns.get((group_name, username), 0)
            if time.time() - last < COOLDOWN_SECONDS:
                continue

            reply_box = driver.find_element(By.TAG_NAME, "textarea")
            reply_box.send_keys(f"@{username} oyy msg mt kr yha")
            reply_box.send_keys(Keys.RETURN)
            print(f"✅ Replied to {username} in {group_name}")
            cooldowns[(group_name, username)] = time.time()

        except Exception as e:
            print(f"⚠️ Error: {e}")
        finally:
            open_inbox(driver)
            time.sleep(2)
