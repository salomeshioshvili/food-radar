from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import StaleElementReferenceException
from dotenv import load_dotenv
import time
import os
import datetime
import re
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
import pickle

load_dotenv()

EMAIL = os.environ.get("IE_EMAIL")
PASSWORD = os.environ.get("IE_PASSWORD")
SCOPES = ['https://www.googleapis.com/auth/calendar']
VISITED_FILE = "visited.txt"
OUTPUT_FILE = "food_events.txt"


def setup_driver():
    options = Options()
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    return webdriver.Chrome(options=options)


def safe_click(driver, by, value, timeout=15):
    wait = WebDriverWait(driver, timeout)
    wait.until(EC.presence_of_element_located((by, value)))
    for _ in range(3):
        try:
            driver.find_element(by, value).click()
            return
        except StaleElementReferenceException:
            time.sleep(0.5)
    raise Exception(f"Could not click {value} after retries")


def js_click(driver, by, value, timeout=15):
    wait = WebDriverWait(driver, timeout)
    wait.until(EC.presence_of_element_located((by, value)))
    for _ in range(3):
        try:
            el = driver.find_element(by, value)
            driver.execute_script("arguments[0].click();", el)
            return
        except StaleElementReferenceException:
            time.sleep(0.5)
    raise Exception(f"Could not click {value} after retries")


def login(driver):
    driver.get("https://ieconnects.ie.edu/webapp/auth/login")
    wait = WebDriverWait(driver, 15)

    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "a[href*='shibboleth/login']")))
    driver.find_element(By.CSS_SELECTOR, "a[href*='shibboleth/login?idp=ie']").click()

    wait.until(EC.presence_of_element_located((By.ID, "i0116")))
    driver.find_element(By.ID, "i0116").send_keys(EMAIL)
    js_click(driver, By.ID, "idSIButton9")

    wait.until(EC.presence_of_element_located((By.ID, "i0118")))
    driver.find_element(By.ID, "i0118").send_keys(PASSWORD)
    time.sleep(1)
    wait.until(EC.element_to_be_clickable((By.ID, "idSIButton9")))
    js_click(driver, By.ID, "idSIButton9")

    time.sleep(2)
    try:
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//input[@value='Yes']"))
        )
        WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//input[@value='Yes']"))
        )
        driver.execute_script("arguments[0].scrollIntoView(true);", driver.find_element(By.XPATH, "//input[@value='Yes']"))
        time.sleep(0.5)
        js_click(driver, By.XPATH, "//input[@value='Yes']")
        print("Yes button clicked successfully")
    except Exception as e:
        print(f"Yes button not found or not clickable: {e}")
        try:
            WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Yes')]"))
            )
            js_click(driver, By.XPATH, "//button[contains(text(), 'Yes')]")
            print("Alternative Yes button clicked")
        except:
            print("Could not find Yes button, continuing anyway...")

    wait.until(EC.url_contains("ieconnects.ie.edu"))


def get_google_calendar_service():
    creds = None

    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)

        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)

    return build('calendar', 'v3', credentials=creds)


def get_all_event_urls(driver):
    wait = WebDriverWait(driver, 15)
    urls = set()

    driver.get("https://ieconnects.ie.edu/home/events/?show=upcoming")
    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "li.list-group-item[id^='event_']")))
    time.sleep(3)

    last_height = driver.execute_script("return document.body.scrollHeight")
    while True:
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            break
        last_height = new_height

    items = driver.find_elements(By.CSS_SELECTOR, "li.list-group-item[id^='event_']")
    today = datetime.date.today()

    for item in items:
        try:
            links = item.find_elements(By.CSS_SELECTOR, "a[href*='rsvp_boot']")
            if not links:
                continue

            href = links[0].get_attribute("href")
            if not href:
                continue

            skip = False
            for el in item.find_elements(By.CSS_SELECTOR, "[aria-label]"):
                aria = el.get_attribute("aria-label") or ""
                match = re.search(r'(\d{1,2})\s+(\w+)\s+(\d{4})', aria)
                if match:
                    try:
                        event_date = datetime.datetime.strptime(match.group(0), "%d %B %Y").date()
                        if event_date < today:
                            skip = True
                    except:
                        pass
                    break

            if not skip:
                urls.add(href)

        except Exception as e:
            print(f"Skipping item: {e}")
            continue

    print(f"Collected {len(urls)} upcoming event URLs")
    return list(urls)


def get_events_with_food(driver, calendar_service):
    visited = set()
    if os.path.exists(VISITED_FILE):
        with open(VISITED_FILE, "r") as f:
            visited = set(line.strip() for line in f)

    all_urls = get_all_event_urls(driver)
    new_urls = [u for u in all_urls if u not in visited]
    print(f"Skipping {len(all_urls) - len(new_urls)} already visited. Checking {len(new_urls)} new events.")

    with open(VISITED_FILE, "a") as visited_f, open(OUTPUT_FILE, "a") as output_f:
        for i, url in enumerate(new_urls):
            print(f"Checking {i+1}/{len(new_urls)}: {url}")
            driver.get(url)
            time.sleep(1.5)
            visited_f.write(url + "\n")
            visited_f.flush()

            try:
                food_icons = driver.find_elements(By.CSS_SELECTOR, "span.mdi-food")
                if food_icons:
                    try:
                        title = driver.find_element(By.CSS_SELECTOR, "h1.rsvp__event-name").text.strip()
                    except:
                        title = driver.title

                    try:
                        month = driver.find_element(By.CSS_SELECTOR, "p.rsvp__event-month").text.strip()
                        day = driver.find_element(By.CSS_SELECTOR, "p.rsvp__event-day").text.strip()
                        year = datetime.date.today().year
                        event_date = datetime.datetime.strptime(f"{day} {month} {year}", "%d %b %Y").date()
                        if event_date < datetime.date.today():
                            event_date = event_date.replace(year=year + 1)
                    except:
                        event_date = datetime.date.today()

                    try:
                        location = driver.find_element(By.CSS_SELECTOR, "span.mdi-map-marker").find_element(By.XPATH, "..").text.strip()
                    except:
                        location = "N/A"

                    calendar_added = False
                    try:
                        event_body = {
                            "summary": title,
                            "description": f"Food provided\nURL: {url}",
                            "start": {"date": event_date.isoformat()},
                            "end": {"date": (event_date + datetime.timedelta(days=1)).isoformat()},
                            "reminders": {"useDefault": True},
                        }
                        if location != "N/A":
                            event_body["location"] = location
                        calendar_service.events().insert(calendarId="primary", body=event_body).execute()
                        calendar_added = True
                    except Exception as e:
                        print(f"  -> Calendar error: {e}")

                    output_f.write(f"{event_date} | {title} | {location} | calendar: {calendar_added} | {url}\n")
                    output_f.flush()
                    print(f"  -> Food found: {title} | Calendar: {calendar_added}")

            except Exception as e:
                print(f"  -> Error: {e}")


if __name__ == "__main__":
    calendar_service = get_google_calendar_service()
    driver = setup_driver()
    try:
        login(driver)
        get_events_with_food(driver, calendar_service)
        print("Done. Results saved to food_events.txt")
    finally:
        driver.quit()